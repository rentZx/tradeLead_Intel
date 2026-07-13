"""
TradeLead V3.0 — Lead Scraper
Real search only, no mock data. Proxy-aware.
"""

from __future__ import annotations

import os
import re
import time
import random
from urllib.parse import urlparse, quote_plus

import requests
from bs4 import BeautifulSoup

from src.market_data import search_keywords_template

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
]

REQUEST_TIMEOUT = 8
MIN_DELAY = 0.4
MAX_DELAY = 1.0

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


def _get_domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return ""


def is_network_available() -> bool:
    """Quick connectivity check (1 attempt, short timeout)."""
    try:
        s = _get_session()
        resp = s.get("https://lite.duckduckgo.com/lite/?q=test", timeout=6)
        return resp.status_code == 200
    except Exception:
        return False


def search_web(keyword: str, max_results: int = 8) -> list[dict]:
    """Search via DDG lite HTML. Returns empty list on failure."""
    results = []
    query = quote_plus(keyword)
    url = f"https://lite.duckduckgo.com/lite/?q={query}"

    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
    try:
        s = _get_session()
        resp = s.get(url, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            return []
        resp.encoding = resp.apparent_encoding or "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
    except Exception:
        return []

    rows = soup.select("table tr") or soup.select("a.result-link")
    for row in rows[:max_results]:
        link = row.select_one("a[rel='nofollow'], a.result-link, a[href]")
        if not link:
            continue
        href = link.get("href", "")
        if "uddg=" in href:
            from urllib.parse import unquote
            href = unquote(href.split("uddg=")[-1].split("&")[0])
        if not href.startswith("http"):
            continue
        title_el = row.select_one("a.result-link, td a")
        title = title_el.get_text(strip=True) if title_el else href[:60]
        snippet_el = row.select_one("td.result-snippet")
        snippet = snippet_el.get_text(strip=True) if snippet_el else ""
        results.append({"title": title, "url": href, "snippet": snippet, "domain": _get_domain(href)})

    return results


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
    Run lead acquisition. Returns {channel: lead_count}.
    Raises RuntimeError if network is unreachable.
    """
    from src.db_v3 import add_lead, create_task, update_task

    if channels is None:
        channels = ["web_search", "yellow_pages"]
    if yellow_page_sources is None:
        yellow_page_sources = ["europages.com", "tradekey.com"]

    # Fast connectivity check before doing anything
    if not is_network_available():
        raise RuntimeError(
            "⚠️ 当前服务器无法访问海外搜索引擎（国内服务器受网络限制）。\n\n"
            "解决方案：在设置页面配置代理地址，或在启动服务时设置环境变量：\n"
            "TRADELEAD_PROXY=http://代理IP:端口\n"
            "例如：sudo TRADELEAD_PROXY=http://127.0.0.1:7890 systemctl restart tradelead-intel-v3"
        )

    keywords = search_keywords_template(product_keywords, country_cn, city_en)
    summary = {}

    for channel in channels:
        task_id = create_task({
            "product_id": product_id,
            "region": region,
            "country": country_cn,
            "city": city_en,
            "channel": channel,
            "channel_source": ",".join(yellow_page_sources),
            "search_keyword": keywords[0] if keywords else "",
        })
        update_task(task_id, status="running")

        leads_found = 0
        seen_domains: set = set()

        if channel in ("web_search", "google_search"):
            for kw in keywords[:3]:
                results = search_web(kw, max_results=6)
                for r in results:
                    domain = r.get("domain", "")
                    if domain in seen_domains or not r.get("title") or domain.endswith(".example.com"):
                        continue
                    seen_domains.add(domain)
                    add_lead({
                        "task_id": task_id, "company_name": r["title"].split(" —")[0].strip(),
                        "website": r["url"], "source_channel": "网络搜索",
                        "source_url": r["url"], "match_keyword": kw, "domain": domain,
                        "country": country_cn, "city": city_en,
                        "business_summary": r.get("snippet", ""), "confidence": "unknown",
                    })
                    leads_found += 1

        elif channel in ("yellow_pages",):
            for kw in keywords[:3]:
                q = f"site:{yellow_page_sources[0]} {kw}" if yellow_page_sources else f"{kw} importer distributor"
                results = search_web(q, max_results=5)
                for r in results:
                    domain = r.get("domain", "")
                    if domain in seen_domains or not r.get("title") or domain.endswith(".example.com"):
                        continue
                    seen_domains.add(domain)
                    add_lead({
                        "task_id": task_id, "company_name": r["title"].split(" —")[0].strip(),
                        "website": r["url"], "source_channel": "黄页采集",
                        "source_url": r["url"], "match_keyword": kw, "domain": domain,
                        "country": country_cn, "city": city_en,
                        "business_summary": r.get("snippet", ""), "confidence": "unknown",
                    })
                    leads_found += 1

        update_task(task_id, status="done", leads_found=leads_found)
        summary[channel] = leads_found

    return summary
