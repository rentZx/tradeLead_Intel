"""
TradeLead V3.0 — Lead Scraper
Yellow pages / Google search / WHOIS / Google Maps
All free, all rate-limited to avoid bans.
"""

from __future__ import annotations

import re
import time
import random
import hashlib
from datetime import datetime
from urllib.parse import urlparse, urljoin, quote_plus

import requests
from bs4 import BeautifulSoup

from src.extractor import extract_contacts_from_html
from src.market_data import search_keywords_template

# ── User-Agent rotation pool ──────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
]

REQUEST_TIMEOUT = 15
MIN_DELAY = 2.0
MAX_DELAY = 5.0


def _random_delay():
    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))


def _get_headers(referer: str = "") -> dict:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": referer or "https://www.google.com/",
    }


def _get_domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return ""


def _fetch_page(url: str, timeout: int = REQUEST_TIMEOUT) -> str | None:
    """Fetch a page with rate limiting. Returns HTML or None."""
    _random_delay()
    try:
        resp = requests.get(url, headers=_get_headers(), timeout=timeout, allow_redirects=True)
        if resp.status_code == 200:
            resp.encoding = resp.apparent_encoding or "utf-8"
            return resp.text
        return None
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════
#  Channel 1: Google Search
# ═══════════════════════════════════════════════════════════

def scrape_google_search(keyword: str, max_results: int = 15) -> list[dict]:
    """
    Search Google directly (no API key) and return list of results.
    Each result: {title, url, snippet, domain}
    """
    results = []
    query = quote_plus(keyword)
    url = f"https://www.google.com/search?q={query}&num={max_results}&hl=en"

    html = _fetch_page(url, timeout=10)
    if not html:
        return results

    soup = BeautifulSoup(html, "lxml" if _has_lxml() else "html.parser")

    for g in soup.select("div.g") if soup.select("div.g") else soup.select("div[data-sokoban-container]"):
        link = g.select_one("a[href]")
        title_el = g.select_one("h3")
        snippet_el = g.select_one("div.VwiC3b, span.aCOpRe, div[data-sncf]")

        href = link.get("href", "") if link else ""
        if not href.startswith("http"):
            continue

        title = title_el.get_text(strip=True) if title_el else ""
        snippet = snippet_el.get_text(strip=True) if snippet_el else ""

        results.append({
            "title": title,
            "url": href,
            "snippet": snippet,
            "domain": _get_domain(href),
        })

    return results


# ═══════════════════════════════════════════════════════════
#  Channel 2: Yellow Pages Scraping
# ═══════════════════════════════════════════════════════════

YELLOW_PAGES_PARSERS = {
    "europages.com": "_parse_europages",
    "kompass.com": "_parse_kompass",
    "tradekey.com": "_parse_tradekey",
    "yellowpages.ae": "_parse_yellowpages_generic",
    "yellowpages.co.za": "_parse_yellowpages_generic",
    "yellowpages.com.ng": "_parse_yellowpages_generic",
    "exportersindia.com": "_parse_exportersindia",
    "alibaba.com": "_parse_alibaba",
}


def scrape_yellow_pages(source_domain: str, keyword: str, country: str = "", max_pages: int = 3) -> list[dict]:
    """
    Scrape a yellow pages website for company listings.
    Returns list of {company_name, website, email, phone, country, city, source_url}
    """
    results = []

    # Build search URL based on source
    search_url = _build_yp_search_url(source_domain, keyword, country)
    if not search_url:
        return results

    for page in range(1, max_pages + 1):
        page_url = _add_page_param(search_url, source_domain, page)
        html = _fetch_page(page_url)
        if not html:
            continue

        soup = BeautifulSoup(html, "lxml" if _has_lxml() else "html.parser")
        parser_func = globals().get(YELLOW_PAGES_PARSERS.get(source_domain, "_parse_yellowpages_generic"))
        page_results = parser_func(soup, source_domain) if parser_func else _parse_yellowpages_generic(soup, source_domain)
        results.extend(page_results)

        if len(page_results) < 5:
            break  # No more results

    return results


def _build_yp_search_url(source_domain: str, keyword: str, country: str) -> str | None:
    kw = quote_plus(keyword)
    urls = {
        "europages.com": f"https://www.europages.com/en/search?q={kw}",
        "kompass.com": f"https://{country.lower() if country else 'www'}.kompass.com/searchCompanies?text={kw}",
        "tradekey.com": f"https://www.tradekey.com/products/{kw.replace('+', '-')}/",
        "yellowpages.ae": f"https://www.yellowpages.ae/categories-by-keyword/{kw}.html",
        "yellowpages.co.za": f"https://www.yellowpages.co.za/search?keyword={kw}",
        "yellowpages.com.ng": f"https://www.yellowpages.com.ng/search?q={kw}",
        "exportersindia.com": f"https://www.exportersindia.com/search.aspx?q={kw}",
        "alibaba.com": f"https://www.alibaba.com/trade/search?SearchText={kw}",
    }
    return urls.get(source_domain)


def _add_page_param(url: str, source_domain: str, page: int) -> str:
    if page <= 1:
        return url
    params = {
        "europages.com": f"&page={page}",
        "kompass.com": f"&page={page}",
        "tradekey.com": f"&page={page}",
        "exportersindia.com": f"&page={page}",
        "alibaba.com": f"&page={page}",
    }
    suffix = params.get(source_domain, f"&page={page}")
    return url + suffix


def _parse_europages(soup: BeautifulSoup, _source: str) -> list[dict]:
    results = []
    for card in soup.select("article[data-cy='company-card'], div.company-card, div.annuaire-item"):
        name = _safe_text(card, "h2, h3, .company-name, .annuaire-title")
        link = card.select_one("a[href]")
        url = ""
        if link:
            href = link.get("href", "")
            url = href if href.startswith("http") else f"https://www.europages.com{href}"
        results.append({
            "company_name": name,
            "website": url,
            "source_url": url,
            "domain": _get_domain(url),
        })
    return results


def _parse_kompass(soup: BeautifulSoup, _source: str) -> list[dict]:
    results = []
    for item in soup.select("div.company-card, div.search-result-item, li.company-item"):
        name = _safe_text(item, "h2, h3, .company-name, .title")
        link = item.select_one("a[href]")
        url = ""
        if link:
            href = link.get("href", "")
            url = href if href.startswith("http") else f"https://www.kompass.com{href}"
        phone = _safe_text(item, ".phone, .tel, [itemprop='telephone']")
        results.append({
            "company_name": name,
            "website": url,
            "phone": phone,
            "source_url": url,
            "domain": _get_domain(url),
        })
    return results


def _parse_tradekey(soup: BeautifulSoup, _source: str) -> list[dict]:
    results = []
    for card in soup.select("div.product-card, div.company-card, div.search-result"):
        name = _safe_text(card, "h2, h3, .company-name, .supplier-name")
        link = card.select_one("a[href]")
        url = ""
        if link:
            href = link.get("href", "")
            url = href if href.startswith("http") else f"https://www.tradekey.com{href}"
        results.append({
            "company_name": name,
            "website": url,
            "source_url": url,
            "domain": _get_domain(url),
        })
    return results


def _parse_exportersindia(soup: BeautifulSoup, _source: str) -> list[dict]:
    results = []
    for card in soup.select("div.company-block, div.listing, div.result-item"):
        name = _safe_text(card, "h2, h3, .company-name, a[title]")
        link = card.select_one("a[href]")
        url = ""
        if link:
            href = link.get("href", "")
            url = href if href.startswith("http") else f"https://www.exportersindia.com{href}"
        phone = _safe_text(card, ".phone, .contact, .tel")
        results.append({
            "company_name": name,
            "website": url,
            "phone": phone,
            "source_url": url,
            "domain": _get_domain(url),
        })
    return results


def _parse_alibaba(soup: BeautifulSoup, _source: str) -> list[dict]:
    results = []
    for card in soup.select("div.search-card, div.list-item, div[data-card-info]"):
        name = _safe_text(card, "h2, .title, .company-name")
        link = card.select_one("a[href]")
        url = ""
        if link:
            href = link.get("href", "")
            url = href if href.startswith("http") else f"https:{href}"
        results.append({
            "company_name": name,
            "website": url,
            "source_url": url,
            "domain": _get_domain(url),
        })
    return results


def _parse_yellowpages_generic(soup: BeautifulSoup, _source: str) -> list[dict]:
    """Generic parser for yellow pages style sites."""
    results = []
    for card in soup.select("div.listing, div.result, div.business, article, li.business, div.company-item"):
        name = _safe_text(card, "h2, h3, h4, .business-name, .company-name, a[itemprop='name']")
        link = card.select_one("a[href]")
        url = ""
        if link:
            href = link.get("href", "")
            if href.startswith("/"):
                url = f"https://{_source}{href}"
            elif href.startswith("http"):
                url = href
        phone = _safe_text(card, ".phone, .tel, [itemprop='telephone'], .contact-phone")
        email = _safe_text(card, ".email, [itemprop='email'], .contact-email")
        address = _safe_text(card, ".address, [itemprop='address'], .location")
        results.append({
            "company_name": name,
            "website": url,
            "phone": phone,
            "email": email,
            "source_url": url,
            "domain": _get_domain(url),
        })
    return results


# ═══════════════════════════════════════════════════════════
#  Channel 3: WHOIS Lookup
# ═══════════════════════════════════════════════════════════

def whois_lookup(domain: str) -> dict | None:
    """Try WHOIS lookup on a domain. Returns registrant info."""
    try:
        import whois
        w = whois.whois(domain)
        return {
            "registrant_name": w.name if w.name else "",
            "registrant_email": w.email if w.email else "",
            "registrant_phone": w.phone if w.phone else "",
            "registrant_country": w.country if w.country else "",
            "creation_date": str(w.creation_date) if w.creation_date else "",
        }
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════
#  Channel 4: Google Maps (Places API free tier)
# ═══════════════════════════════════════════════════════════

def google_maps_search(keyword: str, location: str, api_key: str = "") -> list[dict]:
    """
    Search Google Maps Places API (free tier: $200/month ~28k queries).
    If no API key provided, skip.
    """
    if not api_key:
        return []
    query = quote_plus(f"{keyword} in {location}")
    url = (
        f"https://maps.googleapis.com/maps/api/place/textsearch/json"
        f"?query={query}&key={api_key}"
    )
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        results = []
        for place in data.get("results", []):
            results.append({
                "company_name": place.get("name", ""),
                "address": place.get("formatted_address", ""),
                "phone": "",  # Needs Place Details API call
                "website": "",  # Needs Place Details API call
            })
        return results
    except Exception:
        return []


# ═══════════════════════════════════════════════════════════
#  Unified scraping controller
# ═══════════════════════════════════════════════════════════

def run_acquisition(
    product_id: int,
    product_keywords: str,
    region: str,
    country_cn: str,
    city_en: str = "",
    channels: list[str] | None = None,
    yellow_page_sources: list[str] | None = None,
) -> dict:
    """
    Master function: run lead acquisition across channels.
    Returns {channel: lead_count}
    """
    from src.db_v3 import add_lead, create_task, update_task
    from src.market_data import get_language_for_country

    if channels is None:
        channels = ["yellow_pages", "google_search"]

    country_code = ""
    for code, name in __import__('src.market_data', fromlist=['REGION_COUNTRIES']).REGION_COUNTRIES.get(region, []):
        if name == country_cn:
            country_code = code
            break

    summary = {}

    # Generate search keywords
    keywords = search_keywords_template(product_keywords, country_cn, city_en)

    for channel in channels:
        task_id = create_task({
            "product_id": product_id,
            "region": region,
            "country": country_cn,
            "city": city_en,
            "channel": channel,
            "channel_source": ",".join(yellow_page_sources) if yellow_page_sources else "",
            "search_keyword": keywords[0] if keywords else "",
        })
        update_task(task_id, status="running")

        leads_found = 0

        if channel == "google_search":
            for kw in keywords[:5]:  # Limit keywords to avoid too many requests
                results = scrape_google_search(kw, max_results=10)
                for r in results:
                    lead_id = add_lead({
                        "task_id": task_id,
                        "company_name": r["title"],
                        "website": r["url"],
                        "source_channel": "Google搜索",
                        "source_url": r["url"],
                        "match_keyword": kw,
                        "domain": r["domain"],
                        "business_summary": r.get("snippet", ""),
                        "confidence": "unknown",
                    })
                    leads_found += 1
                    if lead_id:
                        # Extract contacts from the website if possible
                        html = _fetch_page(r["url"])
                        if html:
                            contacts = extract_contacts_from_html(html)
                            from src.db_v3 import update_lead
                            update_lead(lead_id,
                                email=", ".join(contacts.get("emails", [])[:3]),
                                phone=", ".join(contacts.get("phones", [])[:3]),
                                whatsapp=", ".join(contacts.get("whatsapps", [])[:2]),
                            )

        elif channel == "yellow_pages":
            if not yellow_page_sources:
                yellow_page_sources = ["europages.com", "tradekey.com"]
            for yp_source in yellow_page_sources:
                for kw in keywords[:3]:
                    results = scrape_yellow_pages(yp_source, kw, country_cn, max_pages=2)
                    for r in results:
                        lead_id = add_lead({
                            "task_id": task_id,
                            "company_name": r["company_name"],
                            "website": r.get("website", ""),
                            "email": r.get("email", ""),
                            "phone": r.get("phone", ""),
                            "source_channel": f"黄页-{yp_source}",
                            "source_url": r.get("source_url", ""),
                            "match_keyword": kw,
                            "domain": r.get("domain", ""),
                            "country": country_cn,
                            "city": city_en,
                            "confidence": "unknown",
                        })
                        leads_found += 1

        update_task(task_id, status="done", leads_found=leads_found)
        summary[channel] = leads_found

    return summary


# ═══════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════

def _has_lxml() -> bool:
    try:
        import lxml  # noqa: F401
        return True
    except ImportError:
        return False


def _safe_text(soup, selector: str) -> str:
    el = soup.select_one(selector)
    return el.get_text(strip=True) if el else ""
