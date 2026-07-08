from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "tradelead.sqlite3"
SCHEMA_PATH = BASE_DIR / "schema.sql"


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        seed_risk_keywords(conn)


def seed_risk_keywords(conn: sqlite3.Connection) -> None:
    count = conn.execute("SELECT COUNT(*) FROM risk_keywords").fetchone()[0]
    if count:
        return
    rows = [
        ("sanction", "en", "制裁", "critical", "制裁名单或制裁相关表达"),
        ("restricted party", "en", "制裁", "critical", "受限主体"),
        ("military", "en", "军工", "critical", "军工或军事用途"),
        ("dual use", "en", "两用物项", "high", "可能涉及两用物项"),
        ("end user", "en", "最终用户", "high", "需要核查最终用户"),
        ("no declaration", "en", "异常申报", "high", "疑似规避申报"),
        ("cash only", "en", "付款异常", "medium", "异常付款方式"),
        ("third country transshipment", "en", "转运", "high", "第三国转运风险"),
        ("制裁", "zh", "制裁", "critical", "制裁风险"),
        ("军工", "zh", "军工", "critical", "军工用途"),
        ("武器", "zh", "军工", "critical", "武器相关"),
        ("两用", "zh", "两用物项", "high", "两用物项"),
        ("无人机", "zh", "敏感用途", "high", "敏感用途"),
        ("规避", "zh", "合规规避", "high", "规避监管"),
        ("第三国转运", "zh", "转运", "high", "第三国转运"),
        ("虚假报关", "zh", "报关", "critical", "虚假申报"),
    ]
    conn.executemany(
        """
        INSERT INTO risk_keywords(keyword, language, category, risk_level, description)
        VALUES (?, ?, ?, ?, ?)
        """,
        rows,
    )


def query_df(sql: str, params: tuple[Any, ...] = ()) -> pd.DataFrame:
    with get_connection() as conn:
        return pd.read_sql_query(sql, conn, params=params)


def execute(sql: str, params: tuple[Any, ...] = ()) -> int:
    with get_connection() as conn:
        cur = conn.execute(sql, params)
        conn.commit()
        return int(cur.lastrowid or 0)


def update(sql: str, params: tuple[Any, ...] = ()) -> None:
    with get_connection() as conn:
        conn.execute(sql, params)
        conn.commit()


def get_options(table: str, label_field: str = "product_name_cn") -> dict[str, int]:
    df = query_df(f"SELECT id, {label_field} AS label FROM {table} ORDER BY id DESC")
    return {f"{row.label} (#{row.id})": int(row.id) for row in df.itertuples()}
