from __future__ import annotations

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "tradelead.sqlite3"

REQUIRED_TABLES = {
    "search_queries",
    "search_results",
    "webpage_snapshots",
    "sanctions_entities",
    "inquiries",
    "task_logs",
}

REQUIRED_COMPANY_COLUMNS = {
    "extraction_confidence",
    "company_name_confidence",
    "contact_confidence",
    "business_match_confidence",
    "duplicate_group_id",
    "source_domain",
}

REQUIRED_DUE_DILIGENCE_COLUMNS = {
    "evidence_json",
    "matched_keywords_json",
    "confidence_score",
    "source_urls",
    "manual_override_score",
    "manual_override_reason",
    "review_status",
}


def main() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        company_columns = {row[1] for row in conn.execute("PRAGMA table_info(companies)")}
        due_diligence_columns = {row[1] for row in conn.execute("PRAGMA table_info(due_diligence)")}
        indexes = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'index'")}

    assert_present("tables", REQUIRED_TABLES, tables)
    assert_present("companies columns", REQUIRED_COMPANY_COLUMNS, company_columns)
    assert_present("due_diligence columns", REQUIRED_DUE_DILIGENCE_COLUMNS, due_diligence_columns)
    assert "idx_search_results_url_unique" in indexes, "missing idx_search_results_url_unique"

    print("V2.0 database verification passed.")


def assert_present(label: str, required: set[str], actual: set[str]) -> None:
    missing = sorted(required - actual)
    if missing:
        raise SystemExit(f"Missing {label}: {', '.join(missing)}")


if __name__ == "__main__":
    main()
