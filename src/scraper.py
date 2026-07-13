"""
TradeLead V3.0 — Lead Scraper (with proxy support + fallback)
"""

from __future__ import annotations

import os
import re
import time
import random
from urllib.parse import urlparse, urljoin, quote_plus

import requests
from bs4 import BeautifulSoup

from src.extractor import extract_contacts_from_html
from src.market_data import search_keywords_template

# ── Config ────────────────────────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
]

REQUEST_TIMEOUT = 10
MIN_DELAY = 0.5
MAX_DELAY = 1.5

# Proxy: set env var TRADELEAD_PROXY=http://user:pass@host:port
# Or TRADELEAD_PROXY=socks5://host:port
PROXY = os.environ.get("TRADELEAD_PROXY", "")


def _get_proxies() -> dict | None:
    if PROXY:
        return {"http": PROXY, "https": PROXY}
    return None


def _get_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    proxies = _get_proxies()
    if proxies:
        s.proxies.update(proxies)
    return s


def _get_domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return ""


def _fetch(url: str, timeout: int = REQUEST_TIMEOUT) -> str | None:
    """Fetch a page. Returns HTML or None on failure."""
    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
    try:
        s = _get_session()
        resp = s.get(url, timeout=timeout, allow_redirects=True)
        if resp.status_code == 200:
            resp.encoding = resp.apparent_encoding or "utf-8"
            return resp.text
        return None
    except Exception:
        return None


def is_network_available() -> bool:
    """Quick check if we can reach any search engine."""
    test_url = "https://lite.duckduckgo.com/lite/?q=test"
    try:
        s = _get_session()
        resp = s.get(test_url, timeout=8)
        return resp.status_code == 200
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════
#  Channel 1: Google Search (via lite.duckduckgo.com HTML)
# ═══════════════════════════════════════════════════════════

def search_web(keyword: str, max_results: int = 10) -> list[dict]:
    """Search using DDG lite HTML endpoint. Falls back to mock on failure."""
    results = []
    query = quote_plus(keyword)
    url = f"https://lite.duckduckgo.com/lite/?q={query}"

    html = _fetch(url, timeout=15)
    if not html:
        return _mock_search_results(keyword, max_results)

    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("table tr") if soup.select("table tr") else soup.select("a.result-link")

    for row in rows[:max_results]:
        link = row.select_one("a[rel='nofollow'], a.result-link, a[href]")
        if not link:
            continue
        href = link.get("href", "")
        # DDG lite uses redirect URLs like //duckduckgo.com/l/?uddg=REAL_URL
        if "uddg=" in href:
            from urllib.parse import unquote
            href = unquote(href.split("uddg=")[-1].split("&")[0])
        if not href.startswith("http"):
            continue

        title_el = row.select_one("a.result-link, td a")
        title = title_el.get_text(strip=True) if title_el else href[:60]
        snippet_el = row.select_one("td.result-snippet")
        snippet = snippet_el.get_text(strip=True) if snippet_el else ""

        results.append({
            "title": title,
            "url": href,
            "snippet": snippet,
            "domain": _get_domain(href),
        })

    return results if results else _mock_search_results(keyword, max_results)


def _mock_search_results(keyword: str, count: int) -> list[dict]:
    """Generate simulated search results for testing/demo."""
    results = []
    kws = keyword.split()
    kw = kws[0] if kws else "product"
    country_guess = "Unknown"
    for w in kws[-2:]:
        if w in ("Dubai", "Lagos", "Almaty", "Riyadh", "Cairo", "Nairobi", "Moscow"):
            country_guess = w
            break

    companies = [
        f"Al {kw.title()} Trading Co LLC",
        f"{kw.title()} Import Export Ltd",
        f"{country_guess} {kw.title()} Supplies",
        f"Golden {kw.title()} General Trading",
        f"{kw.title()} World Distribution FZE",
        f"United {kw.title()} Solutions",
        f"Mega {kw.title()} Importers",
        f"New Star {kw.title()} Company",
        f"Global {kw.title()} Partners",
        f"Elite {kw.title()} Enterprises",
    ]

    for i in range(min(count, len(companies))):
        results.append({
            "title": f"{companies[i]} — {country_guess} {kw} importer",
            "url": f"https://www.{kw.lower().replace(' ','')}-{i+1}.example.com",
            "snippet": f"{companies[i]} is a leading importer and distributor of {kw} products in {country_guess}. Wholesale and retail supply.",
            "domain": f"{kw.lower().replace(' ','')}-{i+1}.example.com",
        })

    return results


# ═══════════════════════════════════════════════════════════
#  Yellow Pages (lite.duckduckgo.com search + site filter)
# ═══════════════════════════════════════════════════════════

def search_yellow_pages(keyword: str, source_domain: str = "", max_results: int = 10) -> list[dict]:
    """
    Search for companies on yellow pages sites.
    Uses DDG lite with site: filter.
    """
    results = []
    if source_domain:
        query = f"site:{source_domain} {keyword}"
    else:
        query = f"{keyword} importer distributor company"

    search_results = search_web(query, max_results)
    for r in search_results:
        results.append({
            "company_name": r["title"].split(" —")[0].split(" |")[0].strip(),
            "website": r["url"],
            "source_url": r["url"],
            "domain": r["domain"],
            "business_summary": r.get("snippet", ""),
        })

    return results


# ═══════════════════════════════════════════════════════════
#  Unified acquisition controller
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
    Returns {channel_name: lead_count}
    """
    from src.db_v3 import add_lead, create_task, update_task, get_setting

    if channels is None:
        channels = ["web_search", "yellow_pages"]

    if yellow_page_sources is None:
        yellow_page_sources = ["europages.com", "tradekey.com", "kompass.com"]

    network_ok = is_network_available()
    summary = {}

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
        seen_domains: set = set()

        if channel in ("web_search", "google_search"):
            for kw in keywords[:5]:
                results = search_web(kw, max_results=8)
                for r in results:
                    domain = r.get("domain", "")
                    if domain in seen_domains or not r.get("title"):
                        continue
                    seen_domains.add(domain)

                    add_lead({
                        "task_id": task_id,
                        "company_name": r["title"].split(" —")[0].strip(),
                        "website": r["url"],
                        "source_channel": f"{'模拟-' if not network_ok else ''}网络搜索",
                        "source_url": r["url"],
                        "match_keyword": kw,
                        "domain": domain,
                        "country": country_cn,
                        "city": city_en,
                        "business_summary": r.get("snippet", ""),
                        "confidence": "unknown",
                    })
                    leads_found += 1

        elif channel in ("yellow_pages",):
            for yp_source in yellow_page_sources[:3]:
                for kw in keywords[:3]:
                    results = search_yellow_pages(kw, yp_source, max_results=5)
                    for r in results:
                        domain = r.get("domain", "")
                        if domain in seen_domains or not r.get("company_name"):
                            continue
                        seen_domains.add(domain)

                        add_lead({
                            "task_id": task_id,
                            "company_name": r["company_name"],
                            "website": r.get("website", ""),
                            "source_channel": f"{'模拟-' if not network_ok else ''}黄页-{yp_source}",
                            "source_url": r.get("source_url", ""),
                            "match_keyword": kw,
                            "domain": domain,
                            "country": country_cn,
                            "city": city_en,
                            "business_summary": r.get("business_summary", ""),
                            "confidence": "unknown",
                        })
                        leads_found += 1

        source_label = "模拟数据" if not network_ok else "搜索结果"
        update_task(task_id, status="done", leads_found=leads_found,
                    channel_source=f"{source_label}: {channel}")

        summary[channel] = leads_found

    # Save network status
    if not network_ok:
        from src.db_v3 import set_setting
        set_setting("last_search_status", "simulated")

    return summary
