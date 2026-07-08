from __future__ import annotations

import html
import json
import re
import threading
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from src.db import BASE_DIR, execute, query_df, update

LANDING_DIR = BASE_DIR / "outputs" / "landing_pages"
DEFAULT_PORT = 8765
_SERVER: ThreadingHTTPServer | None = None
_SERVER_THREAD: threading.Thread | None = None

LANG_TEXT = {
    "英语": {
        "title": "Product Inquiry",
        "specs": "Specifications",
        "uses": "Applications",
        "advantages": "Advantages",
        "contact": "Inquiry Form",
        "company": "Company Name",
        "name": "Contact Name",
        "country": "Country",
        "email": "Email",
        "whatsapp": "WhatsApp",
        "telegram": "Telegram",
        "quantity": "Quantity",
        "message": "Message",
        "submit": "Submit Inquiry",
        "thanks": "Thank you. Your inquiry has been saved.",
    },
    "俄语": {
        "title": "Запрос по продукту",
        "specs": "Характеристики",
        "uses": "Применение",
        "advantages": "Преимущества",
        "contact": "Форма запроса",
        "company": "Компания",
        "name": "Контактное лицо",
        "country": "Страна",
        "email": "Email",
        "whatsapp": "WhatsApp",
        "telegram": "Telegram",
        "quantity": "Количество",
        "message": "Сообщение",
        "submit": "Отправить запрос",
        "thanks": "Спасибо. Ваш запрос сохранен.",
    },
    "阿语": {
        "title": "استفسار المنتج",
        "specs": "المواصفات",
        "uses": "الاستخدامات",
        "advantages": "المزايا",
        "contact": "نموذج الاستفسار",
        "company": "اسم الشركة",
        "name": "اسم جهة الاتصال",
        "country": "الدولة",
        "email": "البريد الإلكتروني",
        "whatsapp": "واتساب",
        "telegram": "تيليجرام",
        "quantity": "الكمية",
        "message": "الرسالة",
        "submit": "إرسال الاستفسار",
        "thanks": "شكراً لك. تم حفظ استفسارك.",
    },
    "法语": {
        "title": "Demande produit",
        "specs": "Specifications",
        "uses": "Applications",
        "advantages": "Avantages",
        "contact": "Formulaire de demande",
        "company": "Nom de l'entreprise",
        "name": "Contact",
        "country": "Pays",
        "email": "Email",
        "whatsapp": "WhatsApp",
        "telegram": "Telegram",
        "quantity": "Quantite",
        "message": "Message",
        "submit": "Envoyer la demande",
        "thanks": "Merci. Votre demande a ete enregistree.",
    },
}


def generate_landing_page(product: dict[str, Any], language: str, port: int = DEFAULT_PORT) -> Path:
    LANDING_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"product-{product['id']}-{language_key(language)}.html"
    path = LANDING_DIR / filename
    path.write_text(render_landing_page(product, language, port), encoding="utf-8")
    return path


def landing_page_url(path: Path, port: int = DEFAULT_PORT) -> str:
    return f"http://127.0.0.1:{port}/pages/{path.name}"


def render_landing_page(product: dict[str, Any], language: str, port: int = DEFAULT_PORT) -> str:
    text = LANG_TEXT.get(language, LANG_TEXT["英语"])
    product_name = localized_product_name(product, language)
    description = product.get("description_en") or product.get("description_cn") or product.get("specifications") or ""
    specs = product.get("specifications") or product.get("model") or product.get("material") or ""
    uses = product.get("category") or product.get("sub_category") or "B2B wholesale and distribution."
    advantages = build_advantages(product)
    image_urls = split_lines(product.get("image_urls"))
    video_urls = split_lines(product.get("video_urls"))
    hero_image = image_urls[0] if image_urls else ""
    direction = "rtl" if language == "阿语" else "ltr"
    return f"""<!doctype html>
<html lang="{html.escape(language_key(language))}" dir="{direction}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(product_name)} - {html.escape(text['title'])}</title>
  <style>
    :root {{ color-scheme: light; --ink:#17212b; --muted:#5d6975; --line:#d8dee5; --brand:#0f766e; --soft:#eef7f5; }}
    body {{ margin:0; font-family: Arial, Helvetica, sans-serif; color:var(--ink); background:#f7f9fb; line-height:1.55; }}
    header {{ background:#ffffff; border-bottom:1px solid var(--line); }}
    .wrap {{ max-width:1040px; margin:0 auto; padding:28px 20px; }}
    .hero {{ display:grid; grid-template-columns:1.2fr .8fr; gap:28px; align-items:center; }}
    h1 {{ font-size:36px; line-height:1.15; margin:0 0 12px; letter-spacing:0; }}
    h2 {{ font-size:20px; margin:0 0 12px; }}
    p {{ margin:0 0 14px; }}
    .muted {{ color:var(--muted); }}
    .media {{ aspect-ratio:4/3; background:var(--soft); border:1px solid var(--line); display:flex; align-items:center; justify-content:center; overflow:hidden; }}
    .media img {{ width:100%; height:100%; object-fit:cover; }}
    .grid {{ display:grid; grid-template-columns:repeat(3, 1fr); gap:16px; margin-top:20px; }}
    section {{ background:#ffffff; border-bottom:1px solid var(--line); }}
    .box {{ border:1px solid var(--line); padding:16px; background:#ffffff; }}
    ul {{ padding-inline-start:20px; margin:0; }}
    form {{ display:grid; grid-template-columns:repeat(2, 1fr); gap:14px; }}
    label {{ display:block; font-weight:700; font-size:13px; margin-bottom:5px; }}
    input, textarea {{ width:100%; box-sizing:border-box; border:1px solid var(--line); padding:10px; font:inherit; background:#fff; }}
    textarea {{ min-height:110px; grid-column:1/-1; }}
    button {{ border:0; background:var(--brand); color:#fff; padding:12px 16px; font-weight:700; cursor:pointer; }}
    .full {{ grid-column:1/-1; }}
    footer {{ color:var(--muted); font-size:13px; }}
    @media (max-width:760px) {{ .hero, .grid, form {{ grid-template-columns:1fr; }} h1 {{ font-size:28px; }} }}
  </style>
</head>
<body>
  <header>
    <div class="wrap hero">
      <div>
        <h1>{html.escape(product_name)}</h1>
        <p class="muted">{html.escape(description)}</p>
      </div>
      <div class="media">{render_media(hero_image, product_name)}</div>
    </div>
  </header>
  <section>
    <div class="wrap grid">
      <div class="box"><h2>{html.escape(text['specs'])}</h2><p>{html.escape(specs or 'Available on request.')}</p></div>
      <div class="box"><h2>{html.escape(text['uses'])}</h2><p>{html.escape(uses)}</p></div>
      <div class="box"><h2>{html.escape(text['advantages'])}</h2><ul>{advantages}</ul></div>
    </div>
  </section>
  {render_video_links(video_urls)}
  <section>
    <div class="wrap">
      <h2>{html.escape(text['contact'])}</h2>
      <form method="post" action="http://127.0.0.1:{port}/inquiries">
        <input type="hidden" name="product_id" value="{int(product['id'])}">
        <input type="hidden" name="product_interest" value="{html.escape(product_name)}">
        <input type="hidden" name="source_page" value="{html.escape('/pages/product-' + str(product['id']) + '-' + language_key(language) + '.html')}">
        {field(text['company'], 'company_name', True)}
        {field(text['name'], 'contact_name', True)}
        {field(text['country'], 'country', False)}
        {field(text['email'], 'email', True, 'email')}
        {field(text['whatsapp'], 'whatsapp', False)}
        {field(text['telegram'], 'telegram', False)}
        {field(text['quantity'], 'quantity', False)}
        <div class="full"><label>{html.escape(text['message'])}</label><textarea name="message"></textarea></div>
        <div class="full"><button type="submit">{html.escape(text['submit'])}</button></div>
      </form>
    </div>
  </section>
  <footer><div class="wrap">TradeLead Intel local landing page. Inquiries are saved only when the local inquiry service is running.</div></footer>
</body>
</html>"""


def start_inquiry_server(port: int = DEFAULT_PORT) -> str:
    global _SERVER, _SERVER_THREAD
    if _SERVER is not None:
        return f"http://127.0.0.1:{port}"
    LANDING_DIR.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(("127.0.0.1", port), InquiryHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    _SERVER = server
    _SERVER_THREAD = thread
    return f"http://127.0.0.1:{port}"


def save_inquiry(data: dict[str, str]) -> int:
    return execute(
        """
        INSERT INTO inquiries(product_id, company_name, contact_name, country, email, whatsapp, telegram,
                              product_interest, quantity, message, source_page, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            int(data.get("product_id") or 0) or None,
            data.get("company_name", ""),
            data.get("contact_name", ""),
            data.get("country", ""),
            data.get("email", ""),
            data.get("whatsapp", ""),
            data.get("telegram", ""),
            data.get("product_interest", ""),
            data.get("quantity", ""),
            data.get("message", ""),
            data.get("source_page", ""),
            "New",
        ),
    )


def convert_inquiry_to_crm(inquiry_id: int) -> int:
    df = query_df("SELECT * FROM inquiries WHERE id = ?", (inquiry_id,))
    if df.empty:
        raise ValueError(f"Inquiry not found: {inquiry_id}")
    inquiry = df.iloc[0].to_dict()
    company_id = find_or_create_company_from_inquiry(inquiry)
    execute(
        """
        INSERT INTO interactions(company_id, product_id, contact_date, channel, content, customer_reply, result, stage, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            company_id,
            inquiry.get("product_id"),
            str(date.today()),
            "Landing Page",
            inquiry.get("message") or "",
            "",
            "询盘转入CRM",
            "已回复" if inquiry.get("status") == "Replied" else "已联系",
            f"询盘ID #{inquiry_id}; 数量: {inquiry.get('quantity') or ''}; 来源: {inquiry.get('source_page') or ''}",
        ),
    )
    update("UPDATE inquiries SET status = ? WHERE id = ?", ("Converted", inquiry_id))
    update("UPDATE companies SET lead_status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", ("询盘转入CRM", company_id))
    return company_id


def find_or_create_company_from_inquiry(inquiry: dict[str, Any]) -> int:
    email = str(inquiry.get("email") or "").strip()
    whatsapp = str(inquiry.get("whatsapp") or "").strip()
    company_name = str(inquiry.get("company_name") or "").strip() or "Inquiry company"
    conditions = []
    params: list[Any] = []
    if email:
        conditions.append("email = ?")
        params.append(email)
    if whatsapp:
        conditions.append("whatsapp = ?")
        params.append(whatsapp)
    if company_name:
        conditions.append("company_name = ?")
        params.append(company_name)
    if conditions:
        existing = query_df(f"SELECT id FROM companies WHERE {' OR '.join(conditions)} LIMIT 1", tuple(params))
        if not existing.empty:
            return int(existing.iloc[0]["id"])
    return execute(
        """
        INSERT INTO companies(company_name, country, email, whatsapp, telegram, business_summary, source_url,
                              source_type, related_product_id, lead_status, risk_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            company_name,
            inquiry.get("country") or "",
            email,
            whatsapp,
            inquiry.get("telegram") or "",
            inquiry.get("message") or "",
            inquiry.get("source_page") or "",
            "landing_page_inquiry",
            inquiry.get("product_id"),
            "询盘",
            "未筛查",
        ),
    )


class InquiryHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path.startswith("/pages/"):
            self.serve_page(unquote(parsed.path.removeprefix("/pages/")))
            return
        self.respond_html("<h1>TradeLead Intel inquiry service</h1><p>Service is running.</p>")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/inquiries":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length).decode("utf-8", errors="replace")
        data = {key: values[0] if values else "" for key, values in parse_qs(raw, keep_blank_values=True).items()}
        inquiry_id = save_inquiry(data)
        product_name = html.escape(data.get("product_interest") or "product")
        self.respond_html(
            f"<h1>Inquiry saved</h1><p>Thank you. Your inquiry for <strong>{product_name}</strong> has been saved.</p><p>Inquiry ID: {inquiry_id}</p>"
        )

    def serve_page(self, filename: str) -> None:
        safe_name = Path(filename).name
        path = LANDING_DIR / safe_name
        if not path.exists():
            self.send_error(404)
            return
        content = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def respond_html(self, body: str) -> None:
        content = f"<!doctype html><meta charset='utf-8'><body>{body}</body>".encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format: str, *args: Any) -> None:
        return


def localized_product_name(product: dict[str, Any], language: str) -> str:
    field = {"英语": "product_name_en", "俄语": "product_name_ru", "阿语": "product_name_ar", "法语": "product_name_fr"}.get(language)
    return str(product.get(field or "") or product.get("product_name_en") or product.get("product_name_cn") or "Product")


def build_advantages(product: dict[str, Any]) -> str:
    items = [
        product.get("condition") or "Available supply",
        f"MOQ: {product.get('moq')}" if product.get("moq") else "",
        f"Material: {product.get('material')}" if product.get("material") else "",
        f"Lead time: {product.get('delivery_cycle')}" if product.get("delivery_cycle") else "",
        "Manual confirmation before quotation and shipment",
    ]
    return "".join(f"<li>{html.escape(str(item))}</li>" for item in items if item)


def render_media(url: str, product_name: str) -> str:
    if url:
        return f"<img src='{html.escape(url)}' alt='{html.escape(product_name)}'>"
    return f"<span class='muted'>{html.escape(product_name)}</span>"


def render_video_links(urls: list[str]) -> str:
    if not urls:
        return ""
    links = "".join(f"<li><a href='{html.escape(url)}'>{html.escape(url)}</a></li>" for url in urls)
    return f"<section><div class='wrap'><h2>Videos</h2><ul>{links}</ul></div></section>"


def field(label: str, name: str, required: bool = False, input_type: str = "text") -> str:
    required_attr = " required" if required else ""
    return f"<div><label>{html.escape(label)}</label><input type='{input_type}' name='{name}'{required_attr}></div>"


def split_lines(value: object) -> list[str]:
    return [line.strip() for line in str(value or "").splitlines() if line.strip()]


def language_key(language: str) -> str:
    return {"英语": "en", "俄语": "ru", "阿语": "ar", "法语": "fr"}.get(language, "en")
