"""
TradeLead V3.0 — Database Layer
Simple SQLite wrapper, zero config.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

DB_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DB_DIR / "tradelead_v3.sqlite3"


def get_conn() -> sqlite3.Connection:
    """Get a connection to the V3 database."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Initialize database schema from schema_v3.sql."""
    schema_path = Path(__file__).resolve().parent.parent / "schema_v3.sql"
    conn = get_conn()
    with open(schema_path, encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


def query(sql: str, params: tuple = ()) -> list[dict]:
    """Run a SELECT query and return list of dicts."""
    conn = get_conn()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def query_df(sql: str, params: tuple = ()) -> pd.DataFrame:
    """Run a SELECT query and return a DataFrame."""
    conn = get_conn()
    try:
        return pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()


def execute(sql: str, params: tuple = ()) -> int:
    """Run INSERT/UPDATE/DELETE, return lastrowid."""
    conn = get_conn()
    cur = conn.execute(sql, params)
    conn.commit()
    rowid = cur.lastrowid
    conn.close()
    return rowid


def update(sql: str, params: tuple = ()) -> int:
    """Run an UPDATE/DELETE, return rowcount."""
    conn = get_conn()
    cur = conn.execute(sql, params)
    conn.commit()
    rc = cur.rowcount
    conn.close()
    return rc


# ============================================================
#  Product CRUD
# ============================================================

def add_product(data: dict) -> int:
    return execute(
        """INSERT INTO products(product_name_cn, product_name_en, category, sub_category,
           keywords_en, description_cn, description_en, specifications, material,
           fob_price, moq, image_paths) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            data["product_name_cn"], data["product_name_en"],
            data.get("category", ""), data.get("sub_category", ""),
            data["keywords_en"], data.get("description_cn", ""),
            data.get("description_en", ""), data.get("specifications", ""),
            data.get("material", ""), data.get("fob_price", 0),
            data.get("moq", ""), data.get("image_paths", ""),
        ),
    )


def get_products() -> list[dict]:
    return query("SELECT * FROM products ORDER BY created_at DESC")


def get_product(product_id: int) -> dict | None:
    rows = query("SELECT * FROM products WHERE id = ?", (product_id,))
    return rows[0] if rows else None


def delete_product(product_id: int):
    update("DELETE FROM products WHERE id = ?", (product_id,))


# ============================================================
#  Leads CRUD
# ============================================================

def add_lead(data: dict) -> int:
    return execute(
        """INSERT INTO leads(task_id, company_name, country, city, website, email,
           phone, whatsapp, telegram, social_links, business_summary,
           source_channel, source_url, match_keyword, domain, confidence)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            data.get("task_id"), data["company_name"], data.get("country", ""),
            data.get("city", ""), data.get("website", ""), data.get("email", ""),
            data.get("phone", ""), data.get("whatsapp", ""), data.get("telegram", ""),
            data.get("social_links", ""), data.get("business_summary", ""),
            data["source_channel"], data.get("source_url", ""),
            data.get("match_keyword", ""), data.get("domain", ""),
            data.get("confidence", "unknown"),
        ),
    )


def get_leads(status: str | None = None, country: str | None = None,
              confidence: str | None = None) -> list[dict]:
    conditions = []
    params: list = []
    if status:
        conditions.append("status = ?")
        params.append(status)
    if country:
        conditions.append("country = ?")
        params.append(country)
    if confidence:
        conditions.append("confidence = ?")
        params.append(confidence)
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    return query(
        f"SELECT * FROM leads {where} ORDER BY created_at DESC",
        tuple(params),
    )


def update_lead(lead_id: int, **kwargs):
    if not kwargs:
        return
    sets = ", ".join(f"{k} = ?" for k in kwargs)
    vals = tuple(kwargs.values()) + (lead_id,)
    update(f"UPDATE leads SET {sets} WHERE id = ?", vals)


def count_leads() -> dict:
    """Return lead statistics."""
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    new_count = conn.execute("SELECT COUNT(*) FROM leads WHERE status='new'").fetchone()[0]
    contacted = conn.execute("SELECT COUNT(*) FROM leads WHERE status='contacted'").fetchone()[0]
    high = conn.execute("SELECT COUNT(*) FROM leads WHERE confidence='high'").fetchone()[0]
    medium = conn.execute("SELECT COUNT(*) FROM leads WHERE confidence='medium'").fetchone()[0]
    low = conn.execute("SELECT COUNT(*) FROM leads WHERE confidence='low'").fetchone()[0]
    conn.close()
    return {
        "total": total, "new": new_count, "contacted": contacted,
        "high": high, "medium": medium, "low": low,
    }


# ============================================================
#  Tasks CRUD
# ============================================================

def create_task(data: dict) -> int:
    return execute(
        """INSERT INTO acquisition_tasks(product_id, region, country, city,
           channel, channel_source, search_keyword)
           VALUES (?,?,?,?,?,?,?)""",
        (
            data["product_id"], data.get("region", ""), data.get("country", ""),
            data.get("city", ""), data["channel"], data.get("channel_source", ""),
            data.get("search_keyword", ""),
        ),
    )


def update_task(task_id: int, **kwargs):
    if not kwargs:
        return
    sets = ", ".join(f"{k} = ?" for k in kwargs)
    vals = tuple(kwargs.values()) + (task_id,)
    update(f"UPDATE acquisition_tasks SET {sets} WHERE id = ?", vals)


def get_tasks(product_id: int | None = None) -> list[dict]:
    if product_id:
        return query(
            "SELECT * FROM acquisition_tasks WHERE product_id = ? ORDER BY created_at DESC",
            (product_id,),
        )
    return query("SELECT * FROM acquisition_tasks ORDER BY created_at DESC")


# ============================================================
#  Due Diligence CRUD
# ============================================================

def save_diligence(data: dict) -> int:
    return execute(
        """INSERT OR REPLACE INTO due_diligence(lead_id, website_alive, website_title,
           about_text, products_found, email_count, phone_count, has_whatsapp,
           has_product_page, has_contact_page, summary)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (
            data["lead_id"], data.get("website_alive", 0), data.get("website_title", ""),
            data.get("about_text", ""), data.get("products_found", ""),
            data.get("email_count", 0), data.get("phone_count", 0),
            data.get("has_whatsapp", 0), data.get("has_product_page", 0),
            data.get("has_contact_page", 0), data.get("summary", ""),
        ),
    )


def get_diligence(lead_id: int) -> dict | None:
    rows = query("SELECT * FROM due_diligence WHERE lead_id = ?", (lead_id,))
    return rows[0] if rows else None


# ============================================================
#  Outreach CRUD
# ============================================================

def save_outreach(data: dict) -> int:
    return execute(
        """INSERT INTO outreach(lead_id, product_id, language, template_type,
           email_subject, email_body, whatsapp_msg)
           VALUES (?,?,?,?,?,?,?)""",
        (
            data["lead_id"], data["product_id"], data["language"],
            data.get("template_type", "first_contact"), data.get("email_subject", ""),
            data.get("email_body", ""), data.get("whatsapp_msg", ""),
        ),
    )


def get_outreach(lead_id: int) -> list[dict]:
    return query("SELECT * FROM outreach WHERE lead_id = ? ORDER BY created_at DESC", (lead_id,))


# ============================================================
#  Settings
# ============================================================

def get_setting(key: str) -> str | None:
    rows = query("SELECT value FROM settings WHERE key = ?", (key,))
    return rows[0]["value"] if rows else None


def set_setting(key: str, value: str):
    execute(
        "INSERT OR REPLACE INTO settings(key, value, updated_at) VALUES (?,?,datetime('now','localtime'))",
        (key, value),
    )


# ============================================================
#  Export
# ============================================================

def export_leads_to_df(status: str | None = None) -> pd.DataFrame:
    conditions = []
    params: list = []
    if status:
        conditions.append("l.status = ?")
        params.append(status)
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    return query_df(
        f"""SELECT l.company_name, l.country, l.city, l.website, l.email, l.phone,
                   l.whatsapp, l.telegram, l.business_summary, l.source_channel,
                   dd.summary as diligence_summary, l.confidence
            FROM leads l
            LEFT JOIN due_diligence dd ON dd.lead_id = l.id
            {where}
            ORDER BY l.created_at DESC""",
        tuple(params),
    )
