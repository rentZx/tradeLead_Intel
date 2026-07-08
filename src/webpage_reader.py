from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from src.db import execute, query_df, update
from src.search import extract_domain, normalize_url

DEFAULT_HEADERS = {
    "User-Agent": "TradeLeadIntel/2.0 (+local due diligence tool; respects public pages)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

EMAIL_RE = re.compile(r"(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?![\w.-])")
PHONE_RE = re.compile(r"(?:(?:\+|00)\d{1,3}[\s().-]?)?(?:\(?\d{2,5}\)?[\s().-]?){2,}\d{2,6}")
CONTACT_HINTS = ("contact", "about", "product", "products", "catalog", "company", "profile")
SOCIAL_DOMAINS = (
    "linkedin.com",
    "facebook.com",
    "instagram.com",
    "youtube.com",
    "x.com",
    "twitter.com",
    "tiktok.com",
    "vk.com",
)


@dataclass
class SnapshotResult:
    company_id: int
    url: str
    page_type: str
    http_status: int | None = None
    raw_title: str = ""
    extracted_text: str = ""
    extracted_emails: list[str] | None = None
    extracted_phones: list[str] | None = None
    extracted_social_links: list[str] | None = None
    whatsapp_links: list[str] | None = None
    telegram_links: list[str] | None = None
    page_links: list[str] | None = None
    fetch_status: str = "Pending"
    error_message: str = ""


def read_company_website(company_id: int, max_pages: int = 4, timeout: int = 15) -> dict[str, int]:
    company_df = query_df("SELECT id, website FROM companies WHERE id = ?", (company_id,))
    if company_df.empty:
        return {"success": 0, "failed": 1, "skipped": 0}
    website = normalize_url(str(company_df.iloc[0]["website"] or ""))
    if not website:
        save_failed_snapshot(company_id, "", "home", "Missing company website")
        return {"success": 0, "failed": 1, "skipped": 0}

    stats = {"success": 0, "failed": 0, "skipped": 0}
    urls = [website]
    first = fetch_and_save(company_id, website, "home", timeout)
    if first.fetch_status == "Success":
        stats["success"] += 1
        urls.extend(discover_public_company_pages(website, first.page_links or [], max_pages=max_pages))
    else:
        stats["failed"] += 1

    for url in dedupe_urls(urls)[1:max_pages]:
        page_type = guess_page_type(url)
        result = fetch_and_save(company_id, url, page_type, timeout)
        if result.fetch_status == "Success":
            stats["success"] += 1
        else:
            stats["failed"] += 1

    refresh_company_contact_fields(company_id)
    return stats


def fetch_and_save(company_id: int, url: str, page_type: str, timeout: int = 15) -> SnapshotResult:
    normalized = normalize_url(url)
    if not normalized:
        return save_failed_snapshot(company_id, url, page_type, "Invalid URL")
    if urlparse(normalized).scheme not in {"http", "https"}:
        return save_failed_snapshot(company_id, normalized, page_type, "Only http/https URLs are supported")

    try:
        response = requests.get(normalized, headers=DEFAULT_HEADERS, timeout=timeout, allow_redirects=True)
        status = int(response.status_code)
        content_type = response.headers.get("content-type", "")
        final_url = normalize_url(response.url) or normalized
        if status >= 400:
            return save_failed_snapshot(company_id, final_url, page_type, f"HTTP {status}", status)
        if "text/html" not in content_type and "application/xhtml" not in content_type and content_type:
            return save_failed_snapshot(company_id, final_url, page_type, f"Unsupported content type: {content_type}", status)
        parsed = parse_html(response.text, final_url)
        result = SnapshotResult(
            company_id=company_id,
            url=final_url,
            page_type=page_type,
            http_status=status,
            raw_title=parsed["title"],
            extracted_text=parsed["text"],
            extracted_emails=parsed["emails"],
            extracted_phones=parsed["phones"],
            extracted_social_links=parsed["social_links"],
            whatsapp_links=parsed["whatsapp_links"],
            telegram_links=parsed["telegram_links"],
            page_links=parsed["links"],
            fetch_status="Success",
        )
        save_snapshot(result)
        return result
    except requests.RequestException as exc:
        return save_failed_snapshot(company_id, normalized, page_type, str(exc))


def parse_html(html: str, base_url: str) -> dict[str, object]:
    soup = BeautifulSoup(html or "", "html.parser")
    for element in soup(["script", "style", "noscript", "svg", "canvas"]):
        element.decompose()
    title = (soup.title.string if soup.title and soup.title.string else "").strip()
    text = clean_text(soup.get_text("\n"))
    links = [urljoin(base_url, link.get("href", "").strip()) for link in soup.find_all("a") if link.get("href")]
    href_text = "\n".join(links)
    combined = f"{text}\n{href_text}"
    social_links = sorted({link for link in links if is_social_link(link)})
    whatsapp_links = sorted({link for link in links if is_whatsapp_link(link)})
    telegram_links = sorted({link for link in links if is_telegram_link(link)})
    emails = sorted({item.strip(".,;:()[]<>") for item in EMAIL_RE.findall(combined)})
    phones = normalize_phones(PHONE_RE.findall(combined))
    return {
        "title": title,
        "text": text[:60000],
        "emails": emails,
        "phones": phones,
        "social_links": social_links,
        "whatsapp_links": whatsapp_links,
        "telegram_links": telegram_links,
        "links": links,
    }


def discover_public_company_pages(base_url: str, links: list[str], max_pages: int = 4) -> list[str]:
    parsed = urlparse(base_url)
    root = f"{parsed.scheme}://{parsed.netloc}"
    base_domain = extract_domain(base_url)
    discovered = [
        link
        for link in links
        if extract_domain(normalize_url(link)) == base_domain and any(hint in urlparse(link).path.lower() for hint in CONTACT_HINTS)
    ]
    candidates = [
        base_url,
        *discovered,
        urljoin(root, "/contact"),
        urljoin(root, "/contact-us"),
        urljoin(root, "/products"),
        urljoin(root, "/product"),
        urljoin(root, "/about"),
        urljoin(root, "/about-us"),
        urljoin(root, "/company"),
        urljoin(root, "/catalog"),
    ]
    return dedupe_urls(candidates)[:max_pages]


def save_snapshot(result: SnapshotResult) -> int:
    social_payload = {
        "social": result.extracted_social_links or [],
        "whatsapp": result.whatsapp_links or [],
        "telegram": result.telegram_links or [],
    }
    return execute(
        """
        INSERT INTO webpage_snapshots(
            company_id, url, page_type, http_status, raw_title, extracted_text,
            extracted_emails, extracted_phones, extracted_social_links,
            fetch_status, error_message, fetched_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (
            result.company_id,
            result.url,
            result.page_type,
            result.http_status,
            result.raw_title,
            result.extracted_text,
            json.dumps(result.extracted_emails or [], ensure_ascii=False),
            json.dumps(result.extracted_phones or [], ensure_ascii=False),
            json.dumps(social_payload, ensure_ascii=False),
            result.fetch_status,
            result.error_message,
        ),
    )


def save_failed_snapshot(company_id: int, url: str, page_type: str, error_message: str, http_status: int | None = None) -> SnapshotResult:
    result = SnapshotResult(
        company_id=company_id,
        url=url,
        page_type=page_type,
        http_status=http_status,
        fetch_status="Failed",
        error_message=error_message[:1000],
        extracted_emails=[],
        extracted_phones=[],
        extracted_social_links=[],
        whatsapp_links=[],
        telegram_links=[],
    )
    save_snapshot(result)
    return result


def refresh_company_contact_fields(company_id: int) -> None:
    df = query_df(
        """
        SELECT extracted_text, extracted_emails, extracted_phones, extracted_social_links
        FROM webpage_snapshots
        WHERE company_id = ? AND fetch_status = 'Success'
        ORDER BY fetched_at DESC
        """,
        (company_id,),
    )
    if df.empty:
        return

    emails: list[str] = []
    phones: list[str] = []
    social_links: list[str] = []
    whatsapp_links: list[str] = []
    telegram_links: list[str] = []
    summary_parts: list[str] = []
    for row in df.itertuples(index=False):
        emails.extend(load_json_list(row.extracted_emails))
        phones.extend(load_json_list(row.extracted_phones))
        payload = load_json(row.extracted_social_links)
        if isinstance(payload, dict):
            social_links.extend(payload.get("social", []))
            whatsapp_links.extend(payload.get("whatsapp", []))
            telegram_links.extend(payload.get("telegram", []))
        elif isinstance(payload, list):
            social_links.extend(payload)
        if row.extracted_text and len(" ".join(summary_parts)) < 1500:
            summary_parts.append(str(row.extracted_text)[:800])

    update(
        """
        UPDATE companies
        SET email = COALESCE(NULLIF(email, ''), ?),
            phone = COALESCE(NULLIF(phone, ''), ?),
            whatsapp = COALESCE(NULLIF(whatsapp, ''), ?),
            telegram = COALESCE(NULLIF(telegram, ''), ?),
            social_links = ?,
            business_summary = COALESCE(NULLIF(business_summary, ''), ?),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            first_or_empty(emails),
            first_or_empty(phones),
            first_or_empty(whatsapp_links),
            first_or_empty(telegram_links),
            json.dumps(sorted(set(social_links)), ensure_ascii=False),
            clean_text("\n".join(summary_parts))[:1500],
            company_id,
        ),
    )


def companies_with_websites(only_not_read: bool = False) -> list[dict[str, object]]:
    where = "website IS NOT NULL AND website != ''"
    if only_not_read:
        where += " AND id NOT IN (SELECT DISTINCT company_id FROM webpage_snapshots WHERE company_id IS NOT NULL)"
    df = query_df(
        f"""
        SELECT id, company_name, website, country, source_domain
        FROM companies
        WHERE {where}
        ORDER BY id DESC
        """
    )
    return [row._asdict() for row in df.itertuples(index=False)]


def clean_text(text: str) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in (text or "").splitlines()]
    return "\n".join(line for line in lines if line)


def normalize_phones(values: Iterable[str]) -> list[str]:
    cleaned = []
    for value in values:
        item = re.sub(r"\s+", " ", value).strip(" .,:;()[]")
        digits = re.sub(r"\D", "", item)
        if 7 <= len(digits) <= 18:
            cleaned.append(item)
    return sorted(set(cleaned))


def is_social_link(url: str) -> bool:
    domain = extract_domain(normalize_url(url))
    return any(item in domain for item in SOCIAL_DOMAINS)


def is_whatsapp_link(url: str) -> bool:
    value = url.lower()
    return "wa.me/" in value or "whatsapp.com" in value


def is_telegram_link(url: str) -> bool:
    value = url.lower()
    return "t.me/" in value or "telegram.me" in value or "telegram.org" in value


def guess_page_type(url: str) -> str:
    path = urlparse(url).path.lower()
    for hint in CONTACT_HINTS:
        if hint in path:
            return hint
    return "other"


def dedupe_urls(urls: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for url in urls:
        normalized = normalize_url(url)
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def load_json(value: object) -> object:
    if not value:
        return []
    try:
        return json.loads(str(value))
    except json.JSONDecodeError:
        return []


def load_json_list(value: object) -> list[str]:
    parsed = load_json(value)
    if isinstance(parsed, list):
        return [str(item) for item in parsed if item]
    return []


def first_or_empty(values: Iterable[str]) -> str:
    for value in values:
        if value:
            return value
    return ""
