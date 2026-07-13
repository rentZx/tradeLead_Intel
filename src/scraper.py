"""
TradeLead V3.0 — Lead Scraper
Uses Bing search via proxy. No mock data.
"""

from __future__ import annotations

import os
import time
import random
from urllib.parse import urlparse, quote_plus

import requests
from bs4 import BeautifulSoup

from src.market_data import search_keywords_template, get_country_code

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
]

REQUEST_TIMEOUT = 10
MIN_DELAY = 0.5
MAX_DELAY = 1.5

PROXY = os.environ.get("TRADELEAD_PROXY", "")


def _get_proxies() -> dict | None:
    if PROXY:
        return {"http": PROXY, "https": PROXY}
    return None


def _get_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    proxies = _get_proxies()
    if proxies:
        s.proxies.update(proxies)
    return s


def is_network_available() -> bool:
    try:
        s = _get_session()
        resp = s.get("https://www.bing.com/search?q=test&count=1", timeout=6)
        return resp.status_code in (200, 202)
    except Exception:
        return False


def search_web(keyword: str, max_results: int = 8, country_code: str = "") -> list[dict]:
    """Search Bing. Returns [{title, url, snippet, domain}]."""
    results = []
    query = quote_plus(keyword)
    # Build URL with country targeting
    if country_code:
        url = f"https://www.bing.com/search?q={query}&count={max_results}&setlang=en&cc={country_code}"
    else:
        url = f"https://www.bing.com/search?q={query}&count={max_results}&setlang=en"

    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
    try:
        s = _get_session()
        resp = s.get(url, timeout=REQUEST_TIMEOUT)
        if resp.status_code not in (200, 202):
            return []
        resp.encoding = resp.apparent_encoding or "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
    except Exception:
        return []

    for item in soup.select("li.b_algo"):
        title_el = item.select_one("h2 a")
        if not title_el:
            continue
        href = title_el.get("href", "")
        if not href.startswith("http"):
            continue
        title = title_el.get_text(strip=True)
        snippet_el = item.select_one(".b_caption p, .b_lineclamp2, .b_algoSlug")
        snippet = snippet_el.get_text(strip=True) if snippet_el else ""
        results.append({
            "title": title, "url": href,
            "snippet": snippet, "domain": urlparse(href).netloc.replace("www.", ""),
        })
        if len(results) >= max_results:
            break

    return results


def run_acquisition(
    product_id: int,
    product_keywords: str,
    region: str,
    country_cn: str,
    city_en: str = "",
    channels: list[str] | None = None,
    category: str = "",
) -> dict:
    """Run lead acquisition. Raises RuntimeError if network unreachable."""
    from src.db_v3 import add_lead, create_task, update_task

    if channels is None:
        channels = ["web_search"]

    if not is_network_available():
        raise RuntimeError(
            "当前服务器无法访问海外搜索引擎。\n"
            "请确保代理隧道已连通：\n"
            "  ssh -R 17890:127.0.0.1:7892 -N ubuntu@49.233.197.213"
        )

    keywords = search_keywords_template(product_keywords, country_cn, city_en, category, region)
    country_code = get_country_code(country_cn)
    summary = {}

    for channel in channels:
        task_id = create_task({
            "product_id": product_id,
            "region": region,
            "country": country_cn,
            "city": city_en,
            "channel": channel,
            "channel_source": "",
            "search_keyword": keywords[0] if keywords else "",
        })
        update_task(task_id, status="running")

        leads_found = 0
        seen_domains: set = set()

        if channel in ("web_search", "google_search", "yellow_pages"):
            for kw in keywords[:4]:
                results = search_web(kw, max_results=6, country_code=country_code)
                for r in results:
                    domain = r["domain"]
                    if domain in seen_domains:
                        continue
                    seen_domains.add(domain)
                    add_lead({
                        "task_id": task_id,
                        "company_name": r["title"][:100],
                        "website": r["url"],
                        "source_channel": "网络搜索",
                        "source_url": r["url"],
                        "match_keyword": kw,
                        "domain": domain,
                        "country": country_cn,
                        "city": city_en,
                        "business_summary": r.get("snippet", "")[:200],
                        "confidence": "unknown",
                    })
                    leads_found += 1

        update_task(task_id, status="done", leads_found=leads_found)
        summary[channel] = leads_found

    return summary
