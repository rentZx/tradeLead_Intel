from __future__ import annotations

import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import src.db as db
from src.landing_pages import convert_inquiry_to_crm, generate_landing_page, landing_page_url, start_inquiry_server

TEST_DB = ROOT / "work" / "landing_pages_smoke.sqlite3"


def main() -> None:
    TEST_DB.unlink(missing_ok=True)
    db.DB_PATH = TEST_DB
    db.init_db()

    product_id = db.execute(
        """
        INSERT INTO products(product_name_cn, product_name_en, category, specifications, image_urls, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "塑料收纳箱",
            "Plastic Storage Box",
            "塑料小件制品",
            "Material: PP; MOQ: negotiable; color: custom",
            "",
            "在售",
        ),
    )
    product = db.query_df("SELECT * FROM products WHERE id = ?", (product_id,)).iloc[0].to_dict()
    port = 8876
    start_inquiry_server(port)
    page_path = generate_landing_page(product, "英语", port)
    page_url = landing_page_url(page_path, port)
    page = requests.get(page_url, timeout=10)
    page.raise_for_status()
    assert "Plastic Storage Box" in page.text

    response = requests.post(
        f"http://127.0.0.1:{port}/inquiries",
        data={
            "product_id": str(product_id),
            "company_name": "Demo Buyer Ltd",
            "contact_name": "Alice",
            "country": "Kazakhstan",
            "email": "alice@example.test",
            "whatsapp": "+77771234567",
            "telegram": "@alice_demo",
            "product_interest": "Plastic Storage Box",
            "quantity": "500 pcs",
            "message": "Please send details.",
            "source_page": "/pages/" + page_path.name,
        },
        timeout=10,
    )
    response.raise_for_status()

    inquiry = db.query_df("SELECT * FROM inquiries ORDER BY id DESC LIMIT 1").iloc[0]
    company_id = convert_inquiry_to_crm(int(inquiry["id"]))
    interactions = db.query_df("SELECT * FROM interactions WHERE company_id = ?", (company_id,))
    company = db.query_df("SELECT * FROM companies WHERE id = ?", (company_id,)).iloc[0]

    assert inquiry["company_name"] == "Demo Buyer Ltd"
    assert company["email"] == "alice@example.test"
    assert not interactions.empty
    print(f"landing pages smoke passed: inquiry={inquiry['id']}, company={company_id}, page={page_path.name}")


if __name__ == "__main__":
    main()
