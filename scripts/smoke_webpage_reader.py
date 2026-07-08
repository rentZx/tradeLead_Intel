from __future__ import annotations

import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import src.db as db
from src.webpage_reader import read_company_website

TEST_DB = ROOT / "work" / "webpage_reader_smoke.sqlite3"


class DemoSiteHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        pages = {
            "/": """
                <html><head><title>Demo Machinery Importer</title></head>
                <body>
                  <h1>Demo Machinery Importer</h1>
                  <p>We import plastic storage boxes and used machine tools.</p>
                  <a href="/contact">Contact</a>
                  <a href="https://linkedin.com/company/demo-machinery">LinkedIn</a>
                </body></html>
            """,
            "/contact": """
                <html><head><title>Contact Demo</title></head>
                <body>
                  <p>Email: sales@example.test</p>
                  <p>Phone: +7 777 123 4567</p>
                  <a href="https://wa.me/77771234567">WhatsApp</a>
                  <a href="https://t.me/demo_trade">Telegram</a>
                </body></html>
            """,
            "/about": "<html><body><p>About our B2B distribution company.</p></body></html>",
            "/products": "<html><body><p>Products: storage boxes, tool boxes, garden plastic products.</p></body></html>",
        }
        body = pages.get(self.path, "<html><body>Not found</body></html>")
        status = 200 if self.path in pages else 404
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args) -> None:
        return


def main() -> None:
    TEST_DB.unlink(missing_ok=True)
    db.DB_PATH = TEST_DB
    db.init_db()

    server = ThreadingHTTPServer(("127.0.0.1", 0), DemoSiteHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base_url = f"http://127.0.0.1:{server.server_port}/"
        company_id = db.execute(
            """
            INSERT INTO companies(company_name, country, website, source_type)
            VALUES (?, ?, ?, ?)
            """,
            ("Demo Machinery Importer", "Kazakhstan", base_url, "smoke"),
        )
        stats = read_company_website(company_id, max_pages=4, timeout=5)
        snapshots = db.query_df("SELECT * FROM webpage_snapshots WHERE company_id = ?", (company_id,))
        company = db.query_df("SELECT email, phone, whatsapp, telegram, social_links FROM companies WHERE id = ?", (company_id,)).iloc[0]

        assert stats["success"] >= 3, stats
        assert not snapshots.empty, "expected webpage snapshots"
        assert "sales@example.test" in str(snapshots["extracted_emails"].to_list())
        assert "sales@example.test" == company["email"]
        assert "wa.me" in str(company["whatsapp"])
        assert "t.me" in str(company["telegram"])
        print(f"webpage reader smoke passed: snapshots={len(snapshots)}, success={stats['success']}, failed={stats['failed']}")
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
