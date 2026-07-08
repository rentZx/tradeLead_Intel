from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import src.db as db
from src.compliance import import_sanctions_csv, risk_pool_df, screen_companies, seed_enhanced_risk_keywords

TEST_DB = ROOT / "work" / "compliance_smoke.sqlite3"


def main() -> None:
    TEST_DB.unlink(missing_ok=True)
    db.DB_PATH = TEST_DB
    db.init_db()

    inserted_keywords = seed_enhanced_risk_keywords()
    sanctions_df = pd.DataFrame(
        [
            {
                "source": "SmokeList",
                "entity_name": "Demo Restricted Trading LLC",
                "aliases": "Demo Restricted Trading; DRT LLC",
                "country": "Kazakhstan",
                "entity_type": "company",
                "program": "TEST",
                "remarks": "Smoke test entity",
            }
        ]
    )
    imported = import_sanctions_csv(sanctions_df, source_default="SmokeList")
    company_id = db.execute(
        """
        INSERT INTO companies(company_name, country, website, business_summary, risk_status, lead_status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "Demo Restricted Trading Limited",
            "Kazakhstan",
            "https://demo-restricted.example.com",
            "Importer of industrial goods.",
            "未筛查",
            "待背调",
        ),
    )

    stats = screen_companies(threshold=85, include_keyword_screen=True)
    company = db.query_df("SELECT risk_status, lead_status FROM companies WHERE id = ?", (company_id,)).iloc[0]
    pool = risk_pool_df()

    assert inserted_keywords >= 1
    assert imported == 1
    assert stats["sanctions_matches"] >= 1
    assert company["risk_status"] == "风险池"
    assert not pool.empty
    print(f"compliance smoke passed: imported={imported}, matches={stats['sanctions_matches']}, risk_pool={stats['risk_pool']}")


if __name__ == "__main__":
    main()
