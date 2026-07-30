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
    _ensure_columns(
        conn,
        "products",
        {
            "buyer_types": "TEXT DEFAULT ''",
            "end_user_types": "TEXT DEFAULT ''",
            "exclude_terms": "TEXT DEFAULT ''",
            "analysis_reasoning": "TEXT DEFAULT ''",
        },
    )
    _ensure_columns(
        conn,
        "acquisition_tasks",
        {"subregion": "TEXT DEFAULT ''"},
    )
    _ensure_columns(
        conn,
        "leads",
        {
            "address": "TEXT DEFAULT ''",
            "subregion": "TEXT DEFAULT ''",
        },
    )
    _ensure_columns(
        conn,
        "lead_qualifications",
        {"model_version": "TEXT DEFAULT ''"},
    )
    _ensure_columns(
        conn,
        "due_diligence",
        {"matched_product_terms": "TEXT DEFAULT ''"},
    )
    conn.commit()
    conn.close()


def _ensure_columns(conn: sqlite3.Connection, table: str, columns: dict[str, str]) -> None:
    existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
    for name, definition in columns.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")


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
           keywords_en, buyer_types, end_user_types, exclude_terms, analysis_reasoning,
           description_cn, description_en, specifications, material,
           fob_price, moq, image_paths) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            data["product_name_cn"], data["product_name_en"],
            data.get("category", ""), data.get("sub_category", ""),
            data["keywords_en"], data.get("buyer_types", ""),
            data.get("end_user_types", ""), data.get("exclude_terms", ""),
            data.get("analysis_reasoning", ""), data.get("description_cn", ""),
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
        """INSERT INTO leads(task_id, company_name, country, subregion, city, address, website, email,
           phone, whatsapp, telegram, social_links, business_summary,
           source_channel, source_url, match_keyword, domain, confidence)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            data.get("task_id"), data["company_name"], data.get("country", ""),
            data.get("subregion", ""), data.get("city", ""), data.get("address", ""),
            data.get("website", ""),
            data.get("email", ""),
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


def get_lead(lead_id: int) -> dict | None:
    rows = query("SELECT * FROM leads WHERE id = ?", (lead_id,))
    return rows[0] if rows else None


def find_existing_lead(
    domain: str = "",
    company_name: str = "",
    phone: str = "",
) -> dict | None:
    if domain:
        rows = query(
            "SELECT * FROM leads WHERE lower(domain)=lower(?) LIMIT 1",
            (domain,),
        )
    elif phone:
        rows = query("SELECT * FROM leads WHERE phone=? LIMIT 1", (phone,))
    elif company_name:
        rows = query(
            "SELECT * FROM leads WHERE lower(company_name)=lower(?) LIMIT 1",
            (company_name.strip(),),
        )
    else:
        rows = []
    return rows[0] if rows else None


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


def lead_exists(domain: str = "", company_name: str = "", phone: str = "") -> bool:
    """Check cross-channel duplicates using the strongest available identity."""
    return find_existing_lead(domain, company_name, phone) is not None


def save_qualification(data: dict) -> int:
    return execute(
        """INSERT INTO lead_qualifications(
               lead_id, product_id, buyer_role, verdict,
               product_fit_score, channel_fit_score, end_user_fit_score,
               demand_signal_score, contactability_score, overall_score,
               reasons, evidence, rejection_reasons, model_version, evaluated_at
           ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now','localtime'))
           ON CONFLICT(lead_id, product_id) DO UPDATE SET
               buyer_role=excluded.buyer_role,
               verdict=excluded.verdict,
               product_fit_score=excluded.product_fit_score,
               channel_fit_score=excluded.channel_fit_score,
               end_user_fit_score=excluded.end_user_fit_score,
               demand_signal_score=excluded.demand_signal_score,
               contactability_score=excluded.contactability_score,
               overall_score=excluded.overall_score,
               reasons=excluded.reasons,
               evidence=excluded.evidence,
               rejection_reasons=excluded.rejection_reasons,
               model_version=excluded.model_version,
               evaluated_at=datetime('now','localtime')""",
        (
            data["lead_id"],
            data["product_id"],
            data.get("buyer_role", "unknown"),
            data.get("verdict", "review"),
            data.get("product_fit_score", 0),
            data.get("channel_fit_score", 0),
            data.get("end_user_fit_score", 0),
            data.get("demand_signal_score", 0),
            data.get("contactability_score", 0),
            data.get("overall_score", 0),
            data.get("reasons", "[]"),
            data.get("evidence", "[]"),
            data.get("rejection_reasons", "[]"),
            data.get("model_version", ""),
        ),
    )


def get_qualifications(product_id: int | None = None) -> list[dict]:
    if product_id:
        return query(
            """SELECT q.*, p.product_name_cn, p.product_name_en
               FROM lead_qualifications q
               JOIN products p ON p.id=q.product_id
               WHERE q.product_id=?
               ORDER BY q.overall_score DESC, q.evaluated_at DESC""",
            (product_id,),
        )
    return query(
        """SELECT q.*, p.product_name_cn, p.product_name_en
           FROM lead_qualifications q
           JOIN products p ON p.id=q.product_id
           ORDER BY q.evaluated_at DESC"""
    )


def get_lead_qualification(lead_id: int, product_id: int) -> dict | None:
    rows = query(
        """SELECT q.*, p.product_name_cn, p.product_name_en
           FROM lead_qualifications q
           JOIN products p ON p.id=q.product_id
           WHERE q.lead_id=? AND q.product_id=?""",
        (lead_id, product_id),
    )
    return rows[0] if rows else None


# ============================================================
#  Tasks CRUD
# ============================================================

def create_task(data: dict) -> int:
    return execute(
        """INSERT INTO acquisition_tasks(product_id, region, country, subregion, city,
           channel, channel_source, search_keyword)
           VALUES (?,?,?,?,?,?,?,?)""",
        (
            data["product_id"], data.get("region", ""), data.get("country", ""),
            data.get("subregion", ""), data.get("city", ""), data["channel"],
            data.get("channel_source", ""),
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
           about_text, products_found, matched_product_terms,
           email_count, phone_count, has_whatsapp,
           has_product_page, has_contact_page, summary)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            data["lead_id"], data.get("website_alive", 0), data.get("website_title", ""),
            data.get("about_text", ""), data.get("products_found", ""),
            data.get("matched_product_terms", ""),
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
        f"""SELECT l.company_name, l.country, l.city, l.address, l.website, l.email, l.phone,
                   l.whatsapp, l.telegram, l.business_summary, l.source_channel,
                   dd.summary as diligence_summary, l.confidence
            FROM leads l
            LEFT JOIN due_diligence dd ON dd.lead_id = l.id
            {where}
            ORDER BY l.created_at DESC""",
        tuple(params),
    )
