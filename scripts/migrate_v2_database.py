from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "tradelead.sqlite3"
MIGRATION_PATH = BASE_DIR / "migrations" / "001_v2_database_upgrade.sql"

COMPANY_COLUMNS: dict[str, str] = {
    "extraction_confidence": "REAL",
    "company_name_confidence": "REAL",
    "contact_confidence": "REAL",
    "business_match_confidence": "REAL",
    "duplicate_group_id": "TEXT",
    "source_domain": "TEXT",
}

DUE_DILIGENCE_COLUMNS: dict[str, str] = {
    "evidence_json": "TEXT",
    "matched_keywords_json": "TEXT",
    "confidence_score": "REAL",
    "source_urls": "TEXT",
    "manual_override_score": "INTEGER",
    "manual_override_reason": "TEXT",
    "review_status": "TEXT DEFAULT 'Pending'",
}


def main() -> None:
    DB_PATH.parent.mkdir(exist_ok=True)
    if not DB_PATH.exists():
        DB_PATH.touch()

    backup_path = backup_database(DB_PATH)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        with conn:
            conn.executescript(MIGRATION_PATH.read_text(encoding="utf-8"))
            add_missing_columns(conn, "companies", COMPANY_COLUMNS)
            add_missing_columns(conn, "due_diligence", DUE_DILIGENCE_COLUMNS)
            conn.execute(
                "INSERT OR IGNORE INTO schema_migrations(migration_name) VALUES (?)",
                ("001_v2_database_upgrade_columns",),
            )

    print(f"V2.0 database migration completed: {DB_PATH}")
    print(f"Backup created before migration: {backup_path}")


def backup_database(db_path: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.with_name(f"{db_path.stem}_before_v2_{timestamp}{db_path.suffix}")
    shutil.copy2(db_path, backup_path)
    return backup_path


def add_missing_columns(conn: sqlite3.Connection, table: str, columns: dict[str, str]) -> None:
    existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
    for name, definition in columns.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")


if __name__ == "__main__":
    main()
