"""
TradeLead V3.0 — Lead Scraper
Uses DuckDuckGo Lite via Cloudflare Worker proxy. No mock data.

Proxy modes (env TRADELEAD_PROXY):
  1. Cloudflare Worker: https://xxx.workers.dev  → URL rewrite (?url=target)
  2. SOCKS5:            socks5://127.0.0.1:1080  → requests.proxies
  3. Empty              → direct connection
"""

from __future__ import annotations

import os
import time
import random
import re
from urllib.parse import urlparse, quote_plus, urlencode, unquote

import requests
from bs4 import BeautifulSoup

from src.market_data import search_keywords_template, get_country_code

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
]

REQUEST_TIMEOUT = 15
MIN_DELAY = 0.5
MAX_DELAY = 1.5

PROXY = os.environ.get("TRADELEAD_PROXY", "").rstrip("/")

# DuckDuckGo Lite URL
DDG_LITE = "https://lite.duckduckgo.com/lite/"


def _is_worker_proxy() -> bool:
    """Check if proxy is a Cloudflare Worker URL (http/https)."""
    return PROXY.startswith(("http://", "https://"))


def _wrap_url(target_url: str) -> str:
    """If using Cloudflare Worker proxy, rewrite URL; otherwise return as-is."""
    if _is_worker_proxy():
        return f"{PROXY}?{urlencode({'url': target_url})}"
    return target_url


def _get_proxies() -> dict | None:
    """Return proxies dict for SOCKS5 mode; None for Worker/direct mode."""
    if PROXY and PROXY.startswith("socks"):
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
    """Check if we can reach DuckDuckGo (via proxy or direct)."""
    try:
        s = _get_session()
        test_url = _wrap_url(f"{DDG_LITE}?q=test")
        resp = s.get(test_url, timeout=10)
        return resp.status_code in (200, 202)
    except Exception:
        return False


def _extract_ddg_results(html: str, max_results: int) -> list[dict]:
    """Parse DuckDuckGo Lite HTML and extract search results.

    DDG Lite structure (table-based):
      - <a href="//duckduckgo.com/l/?uddg=ENCODED_URL">Title</a>
      - Snippet in a nearby <td> (text content)
      - Display URL in another <td>
    """
    results: list[dict] = []
    soup = BeautifulSoup(html, "html.parser")

    # Find all result links containing uddg redirect
    for a_tag in soup.find_all("a", href=re.compile(r"uddg=")):
        href = a_tag.get("href", "")
        # Extract real URL from uddg= parameter
        match = re.search(r"uddg=([^&]+)", href)
        if not match:
            continue
        real_url = unquote(match.group(1))
        if not real_url.startswith("http"):
            continue

        # Skip DDG ads (y.js redirects to bing/aclick)
        if "duckduckgo.com/y.js" in real_url or "ad_type=" in real_url:
            continue

        title = a_tag.get_text(strip=True)
        if not title:
            continue

        domain = urlparse(real_url).netloc.replace("www.", "")

        # Find snippet: look at parent <tr>, then next sibling row's td.result-snippet
        snippet = ""
        parent_td = a_tag.find_parent("td")
        if parent_td:
            parent_tr = parent_td.find_parent("tr")
            if parent_tr:
                next_tr = parent_tr.find_next_sibling("tr")
                if next_tr:
                    # DDG lite: snippet is in <td class="result-snippet">
                    snippet_td = next_tr.find("td", class_="result-snippet")
                    if snippet_td:
                        snippet = snippet_td.get_text(strip=True)

        results.append({
            "title": title,
            "url": real_url,
            "snippet": snippet[:200],
            "domain": domain,
        })
        if len(results) >= max_results:
            break

    return results


def search_web(keyword: str, max_results: int = 8, country_code: str = "") -> list[dict]:
    """Search DuckDuckGo Lite. Returns [{title, url, snippet, domain}].

    Note: DDG Lite doesn't support cc= parameter for country targeting.
    Country targeting is handled via keywords in search_keywords_template().
    """
    results: list[dict] = []
    query = quote_plus(keyword)
    ddg_url = f"{DDG_LITE}?q={query}"

    # If using Worker proxy, wrap URL
    fetch_url = _wrap_url(ddg_url)

    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
    try:
        s = _get_session()
        resp = s.get(fetch_url, timeout=REQUEST_TIMEOUT)
        if resp.status_code not in (200, 202):
            return []
        resp.encoding = resp.apparent_encoding or "utf-8"
        results = _extract_ddg_results(resp.text, max_results)
    except Exception:
        return []

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
            "无法通过代理访问搜索引擎。\n"
            "请检查 TRADELEAD_PROXY 环境变量是否正确设置。\n"
            f"当前代理: {PROXY or '(未设置)'}"
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
