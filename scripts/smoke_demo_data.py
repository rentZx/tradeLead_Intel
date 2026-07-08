from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import src.db as db
from src.demo_data import DEMO_WARNING, clear_demo_data, demo_counts, generate_demo_data

TEST_DB = ROOT / "work" / "demo_data_smoke.sqlite3"


def main() -> None:
    TEST_DB.unlink(missing_ok=True)
    db.DB_PATH = TEST_DB
    db.init_db()

    real_product_id = db.execute(
        "INSERT INTO products(product_name_cn, supplier_name, status) VALUES (?, ?, ?)",
        ("真实产品保留样本", "REAL_SUPPLIER", "在售"),
    )
    real_company_id = db.execute(
        "INSERT INTO companies(company_name, source_type, business_summary) VALUES (?, ?, ?)",
        ("Real Company Keep", "manual", "真实数据不应被清空"),
    )

    stats = generate_demo_data()
    counts = demo_counts()
    assert stats["products"] == 10
    assert stats["companies"] == 30
    assert stats["sanctions_entities"] == 5
    assert stats["inquiries"] == 5
    assert stats["interactions"] == 10
    assert counts == stats

    companies = db.query_df("SELECT business_summary FROM companies WHERE source_type = 'demo'")
    assert len(companies) == 30
    assert companies["business_summary"].str.contains(DEMO_WARNING, regex=False).all()

    deleted = clear_demo_data()
    assert deleted["products"] == 10
    assert deleted["companies"] == 30
    assert demo_counts() == {"products": 0, "companies": 0, "sanctions_entities": 0, "inquiries": 0, "interactions": 0}
    assert not db.query_df("SELECT id FROM products WHERE id = ?", (real_product_id,)).empty
    assert not db.query_df("SELECT id FROM companies WHERE id = ?", (real_company_id,)).empty
    print("demo data smoke passed: generated and cleared without touching real data")


if __name__ == "__main__":
    main()
