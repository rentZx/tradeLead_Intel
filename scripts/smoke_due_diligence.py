from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import src.db as db
from src.due_diligence import build_due_diligence
from src.risk import detect_risk_keywords, format_risk_hits

TEST_DB = ROOT / "work" / "due_diligence_smoke.sqlite3"


def main() -> None:
    TEST_DB.unlink(missing_ok=True)
    db.DB_PATH = TEST_DB
    db.init_db()

    product_id = db.execute(
        """
        INSERT INTO products(product_name_cn, product_name_en, category, status)
        VALUES (?, ?, ?, ?)
        """,
        ("塑料收纳箱", "plastic storage box", "塑料小件制品", "在售"),
    )
    company_id = db.execute(
        """
        INSERT INTO companies(company_name, country, website, email, whatsapp, related_product_id, source_domain)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "Demo Distributor",
            "Kazakhstan",
            "https://demo.example.com",
            "sales@demo.example.com",
            "https://wa.me/77771234567",
            product_id,
            "demo.example.com",
        ),
    )
    db.execute(
        """
        INSERT INTO webpage_snapshots(
            company_id, url, page_type, http_status, raw_title, extracted_text,
            extracted_emails, extracted_phones, extracted_social_links, fetch_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            company_id,
            "https://demo.example.com/products",
            "products",
            200,
            "Demo Distributor plastic storage products",
            "We are an importer and distributor of plastic storage box products for wholesale buyers.",
            json.dumps(["sales@demo.example.com"]),
            json.dumps(["+7 777 123 4567"]),
            json.dumps({"whatsapp": ["https://wa.me/77771234567"], "telegram": ["https://t.me/demo"]}),
            "Success",
        ),
    )

    company = db.query_df("SELECT * FROM companies WHERE id = ?", (company_id,)).iloc[0].to_dict()
    product = db.query_df("SELECT * FROM products WHERE id = ?", (product_id,)).iloc[0].to_dict()
    hits = detect_risk_keywords(str(company) + str(product))
    diligence = build_due_diligence(company, product, "", hits)
    score = diligence["score"]
    db.execute(
        """
        INSERT INTO due_diligence (
            company_id, authenticity_score, business_match_score, purchase_probability_score,
            contactability_score, risk_score, final_score, final_grade, risk_flags,
            evidence_summary, ai_report, recommendation, evidence_json, matched_keywords_json,
            confidence_score, source_urls, review_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            company_id,
            score["authenticity_score"],
            score["business_match_score"],
            score["purchase_probability_score"],
            score["contactability_score"],
            score["risk_score"],
            score["final_score"],
            score["final_grade"],
            format_risk_hits(hits),
            diligence["summary"],
            diligence["report"],
            "可跟进",
            json.dumps(diligence["evidence"], ensure_ascii=False),
            json.dumps(diligence["matched_keywords"], ensure_ascii=False),
            diligence["confidence_score"],
            json.dumps(diligence["source_urls"], ensure_ascii=False),
            "Pending",
        ),
    )

    saved = db.query_df("SELECT * FROM due_diligence WHERE company_id = ?", (company_id,)).iloc[0]
    assert "评分理由" in saved["ai_report"]
    assert "证据片段" in saved["ai_report"]
    assert "来源URL" in saved["ai_report"]
    assert "置信度" in saved["ai_report"]
    assert json.loads(saved["evidence_json"])
    assert json.loads(saved["matched_keywords_json"])
    assert float(saved["confidence_score"]) > 0
    print(f"due diligence smoke passed: final_score={saved['final_score']}, confidence={saved['confidence_score']}")


if __name__ == "__main__":
    main()
