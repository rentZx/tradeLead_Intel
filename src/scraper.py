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

from src.market_data import (
    search_keywords_template,
    get_country_code,
    get_country_english_name,
    get_cities_for_country,
    CATEGORY_BUYER_TYPES,
)
from src.provider_gateway import provider_configured

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
]

REQUEST_TIMEOUT = 15
MIN_DELAY = 0.5
MAX_DELAY = 1.5

# DuckDuckGo Lite URL
DDG_LITE = "https://lite.duckduckgo.com/lite/"


class SearchBlockedError(RuntimeError):
    pass

PROVIDER_LABELS = {
    "auto": "自动选择",
    "ddg": "DuckDuckGo 免费搜索",
    "brave": "Brave Search API",
    "osm": "OpenStreetMap 商家",
    "yellow_pages": "公开黄页",
    "google_places": "Google Places",
    "serpapi": "SerpAPI",
    "foursquare": "Foursquare Places",
    "opencorporates": "OpenCorporates 企业注册",
    "pdl": "People Data Labs 企业库",
}


def configured_providers() -> dict[str, bool]:
    """Report provider readiness without exposing credentials."""
    network_ready = is_network_available()
    return {
        "ddg": network_ready,
        "brave": provider_configured("brave", "BRAVE_SEARCH_API_KEY"),
        "osm": True,
        "yellow_pages": network_ready,
        "google_places": provider_configured("google_places", "GOOGLE_MAPS_API_KEY"),
        "serpapi": provider_configured("serpapi", "SERPAPI_API_KEY"),
        "foursquare": provider_configured("foursquare", "FOURSQUARE_API_KEY"),
        "opencorporates": provider_configured(
            "opencorporates", "OPENCORPORATES_API_TOKEN"
        ),
        "pdl": provider_configured("pdl", "PDL_API_KEY"),
    }


def resolve_provider(provider: str) -> str:
    if provider != "auto":
        return provider
    configured = configured_providers()
    for candidate in ("brave", "serpapi", "ddg"):
        if configured[candidate]:
            return candidate
    return "ddg"


def _env_int(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        value = default
    return max(minimum, min(value, maximum))


def _prioritize_buyer_types(values: list[str]) -> list[str]:
    generic = {
        "hardware store", "building materials", "building materials supplier",
        "construction supply", "construction supply company", "tools supplier",
        "trading company", "general trading company", "distributor",
        "wholesaler", "importer", "supplier",
    }
    return sorted(
        values,
        key=lambda value: (" ".join(value.lower().split()) in generic,),
    )


def _buyer_search_targets(
    product_terms: list[str],
    buyer_types: list[str],
    end_user_types: list[str],
    limit: int,
) -> list[str]:
    product = product_terms[0] if product_terms else ""
    candidates = []
    if product:
        candidates.append(f"{product} distributor")
    if buyer_types:
        candidates.append(buyer_types[0])
    if product and end_user_types:
        candidates.append(f"{product} {end_user_types[0]}")
    candidates.extend(buyer_types[1:])
    candidates.extend(
        f"{product} {value}" if product else value
        for value in end_user_types[1:]
    )
    return list(dict.fromkeys(candidates))[:limit]


def _proxy_value() -> str:
    env_proxy = os.environ.get("TRADELEAD_PROXY", "").strip()
    if env_proxy:
        return env_proxy.rstrip("/")
    try:
        from src.db_v3 import get_setting
        return (get_setting("proxy_url") or "").strip().rstrip("/")
    except Exception:
        return ""


def _is_worker_proxy() -> bool:
    """Check if proxy is a Cloudflare Worker URL (http/https)."""
    return _proxy_value().startswith(("http://", "https://"))


def _wrap_url(target_url: str) -> str:
    """If using Cloudflare Worker proxy, rewrite URL; otherwise return as-is."""
    if _is_worker_proxy():
        return f"{_proxy_value()}?{urlencode({'url': target_url})}"
    return target_url


def _get_proxies() -> dict | None:
    """Return proxies dict for SOCKS5 mode; None for Worker/direct mode."""
    proxy = _proxy_value()
    if proxy.startswith("socks"):
        return {"http": proxy, "https": proxy}
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
        text = resp.text.lower()
        is_challenge = (
            "please complete the following challenge" in text
            or "select all squares containing a duck" in text
        )
        return resp.status_code in (200, 202) and not is_challenge
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
            raise RuntimeError(f"DuckDuckGo HTTP {resp.status_code}")
        resp.encoding = resp.apparent_encoding or "utf-8"
        page_text = resp.text.lower()
        if (
            "please complete the following challenge" in page_text
            or "select all squares containing a duck" in page_text
        ):
            raise SearchBlockedError(
                "DuckDuckGo 触发了人机验证，当前出口 IP 暂时无法自动搜索；"
                "请稍后重试、配置海外代理，或改用 OpenStreetMap/Brave。"
            )
        results = _extract_ddg_results(resp.text, max_results)
    except SearchBlockedError:
        raise
    except requests.RequestException as exc:
        raise RuntimeError(f"DuckDuckGo 请求失败：{exc}") from exc

    return results


def search_with_provider(
    provider: str,
    keyword: str,
    country: str,
    max_results: int = 8,
) -> list[dict]:
    """Normalize free and paid search providers to the V3 lead shape."""
    selected = resolve_provider(provider)
    if selected == "ddg":
        return search_web(keyword, max_results=max_results, country_code=get_country_code(country))
    if selected == "brave":
        from src.acquisition_channels import brave_web_search
        return [
            {
                "title": item.company_name,
                "url": item.website,
                "snippet": item.business_summary,
                "domain": item.domain,
            }
            for item in brave_web_search(keyword, max_results)
        ]

    from src.search import run_search_provider

    results = run_search_provider(
        provider=selected,
        keyword=keyword,
        country=country,
        language="en",
        limit=max_results,
    )
    return [
        {
            "title": item.title,
            "url": item.url,
            "snippet": item.snippet,
            "domain": item.domain,
        }
        for item in results
    ]


def run_acquisition(
    product_id: int,
    product_keywords: str,
    region: str,
    country_cn: str,
    city_en: str = "",
    channels: list[str] | None = None,
    category: str = "",
    buyer_types: str = "",
    end_user_types: str = "",
    exclude_terms: str = "",
    subregion_en: str = "",
) -> dict:
    """Run lead acquisition. Raises RuntimeError if network unreachable."""
    from src.db_v3 import (
        add_lead,
        create_task,
        find_existing_lead,
        get_diligence,
        get_lead,
        get_product,
        update_task,
        save_diligence,
        save_qualification,
        update_lead,
    )
    from src.diligence import run_diligence, rate_confidence
    from src.qualification import qualify_lead
    from src.acquisition_channels import (
        directory_sites_for_country,
        foursquare_places_search,
        google_places_search,
        openstreetmap_search,
        opencorporates_search,
        pdl_company_search,
    )

    if channels is None:
        channels = ["auto"]

    if channels and all(channel in ("ddg", "yellow_pages") for channel in channels) and not is_network_available():
        raise RuntimeError(
            "无法通过代理访问搜索引擎。\n"
            "请检查 TRADELEAD_PROXY 环境变量是否正确设置。\n"
            f"当前代理: {_proxy_value() or '(未设置)'}"
        )

    country_en = get_country_english_name(country_cn)
    keywords = search_keywords_template(
        product_keywords,
        country_en,
        city_en,
        category,
        region,
        buyer_types,
        end_user_types,
        subregion_en=subregion_en,
    )
    product = get_product(product_id)
    country_code = get_country_code(country_cn)
    paid_query_cap = _env_int(
        "TRADELEAD_MAX_PAID_QUERIES_PER_CHANNEL", 3, 1, 10
    )
    result_cap = _env_int(
        "TRADELEAD_MAX_RESULTS_PER_CHANNEL", 60, 5, 300
    )
    pdl_result_cap = _env_int(
        "TRADELEAD_PDL_RESULTS_PER_QUERY", 10, 1, 100
    )
    summary = {}

    for channel in channels:
        task_id = create_task({
            "product_id": product_id,
            "region": region,
            "country": country_cn,
            "subregion": subregion_en,
            "city": city_en,
            "channel": channel,
            "channel_source": "",
            "search_keyword": keywords[0] if keywords else "",
        })
        update_task(task_id, status="running")

        leads_found = 0
        enriched_count = 0
        seen_identities: set = set()
        buyer_list = _prioritize_buyer_types([
            item.strip() for item in buyer_types.split(",") if item.strip()
        ])
        if not buyer_list:
            buyer_list = CATEGORY_BUYER_TYPES.get(
                category, CATEGORY_BUYER_TYPES["默认"]
            )
        end_user_list = [
            item.strip() for item in end_user_types.split(",") if item.strip()
        ]
        product_terms = [
            item.strip() for item in product_keywords.split(",") if item.strip()
        ]
        location = " ".join(
            dict.fromkeys(
                value
                for value in [city_en, subregion_en, country_en]
                if value
            )
        )
        try:
            channel_results: list[tuple[dict, str]] = []
            if channel in ("auto", "ddg", "brave", "serpapi"):
                selected_provider = resolve_provider(channel)
                query_cap = (
                    paid_query_cap
                    if selected_provider in ("brave", "serpapi")
                    else 4
                )
                for kw in keywords[:query_cap]:
                    for result in search_with_provider(
                        selected_provider, kw, country_cn, max_results=6
                    ):
                        channel_results.append((
                            {
                                "company_name": result["title"][:150],
                                "website": result["url"],
                                "domain": result["domain"],
                                "business_summary": result.get("snippet", "")[:500],
                                "source_url": result["url"],
                                "source_channel": PROVIDER_LABELS.get(
                                    selected_provider, selected_provider
                                ),
                            },
                            kw,
                        ))
            elif channel == "yellow_pages":
                sites = directory_sites_for_country(country_cn)
                targets = buyer_list[:2] or ["hardware store", "building materials supplier"]
                for site in sites[:5]:
                    for buyer in targets:
                        query_text = f'site:{site} "{buyer}" {location}'
                        for result in search_web(query_text, max_results=5):
                            channel_results.append((
                                {
                                    "company_name": result["title"][:150],
                                    "website": result["url"],
                                    "domain": result["domain"],
                                    "business_summary": result.get("snippet", "")[:500],
                                    "source_url": result["url"],
                                    "source_channel": f"公开黄页 · {site}",
                                },
                                query_text,
                            ))
            elif channel == "osm":
                osm_cities = [city_en] if city_en else (
                    [subregion_en] if subregion_en else [
                        city[0] for city in get_cities_for_country(country_cn)[:3]
                    ]
                )
                if not osm_cities:
                    osm_cities = [country_en]
                for osm_city in osm_cities:
                    for item in openstreetmap_search(
                        buyer_list,
                        country_en,
                        osm_city,
                        country_code=country_code,
                    ):
                        channel_results.append((
                            item.to_dict(),
                            f"{', '.join(buyer_list[:4])} · {osm_city}",
                        ))
            elif channel == "google_places":
                targets = _buyer_search_targets(
                    product_terms,
                    buyer_list or ["hardware store"],
                    end_user_list,
                    paid_query_cap,
                )
                for buyer in targets:
                    query_text = f"{buyer} in {location}"
                    for item in google_places_search(
                        query_text, country_code, min(20, result_cap)
                    ):
                        channel_results.append((item.to_dict(), query_text))
            elif channel == "foursquare":
                targets = _buyer_search_targets(
                    product_terms,
                    buyer_list or ["hardware store"],
                    end_user_list,
                    paid_query_cap,
                )
                for buyer in targets:
                    query_text = f"{buyer} in {location}"
                    for item in foursquare_places_search(
                        buyer, location, min(20, result_cap)
                    ):
                        channel_results.append((item.to_dict(), query_text))
            elif channel == "opencorporates":
                targets = list(dict.fromkeys(
                    [*product_terms[:1], *buyer_list[:1], *end_user_list[:1]]
                ))[:paid_query_cap]
                for target in targets:
                    query_text = f"{target} · {country_en}"
                    for item in opencorporates_search(
                        target, country_code, min(30, result_cap)
                    ):
                        channel_results.append((item.to_dict(), query_text))
            elif channel == "pdl":
                targets = _buyer_search_targets(
                    product_terms,
                    buyer_list,
                    end_user_list,
                    min(paid_query_cap, 2),
                )
                for target in targets:
                    query_text = f"{target} · {country_en}"
                    for item in pdl_company_search(
                        target,
                        country_en,
                        pdl_result_cap,
                        subregion=subregion_en,
                    ):
                        channel_results.append((item.to_dict(), query_text))
            else:
                raise ValueError(f"不支持的获客渠道: {channel}")

            for item, matched_keyword in channel_results[:result_cap]:
                domain = item.get("domain", "")
                company_name = item.get("company_name", "").strip()
                phone = item.get("phone", "")
                identity = domain or phone or company_name.lower()
                if not company_name or identity in seen_identities:
                    continue
                if channel == "osm" and not any(
                    item.get(field) for field in ("website", "phone", "email", "whatsapp")
                ):
                    continue
                seen_identities.add(identity)
                existing_lead = find_existing_lead(
                    domain=domain,
                    company_name=company_name,
                    phone=phone,
                )
                if existing_lead:
                    if product:
                        qualification_input = dict(existing_lead)
                        qualification_input["match_keyword"] = matched_keyword
                        if item.get("business_summary"):
                            qualification_input["business_summary"] = "；".join(
                                value for value in [
                                    existing_lead.get("business_summary", ""),
                                    item.get("business_summary", ""),
                                ] if value
                            )
                        qualification = qualify_lead(
                            qualification_input,
                            product,
                            get_diligence(existing_lead["id"]),
                        )
                        save_qualification(
                            qualification.to_record(
                                existing_lead["id"], product_id
                            )
                        )
                    continue
                lead_id = add_lead({
                    "task_id": task_id,
                    "company_name": company_name[:150],
                    "website": item.get("website", ""),
                    "address": item.get("address", ""),
                    "email": item.get("email", ""),
                    "phone": phone,
                    "whatsapp": item.get("whatsapp", ""),
                    "social_links": item.get("social_links", ""),
                    "source_channel": item.get(
                        "source_channel", PROVIDER_LABELS.get(channel, channel)
                    ),
                    "source_url": item.get("source_url", ""),
                    "match_keyword": matched_keyword,
                    "domain": domain,
                    "country": country_cn,
                    "subregion": subregion_en,
                    "city": city_en,
                    "business_summary": item.get("business_summary", "")[:500],
                    "confidence": "unknown",
                })
                leads_found += 1
                website = item.get("website", "")
                if website and enriched_count < 8:
                    target_keywords = ",".join(
                        value for value in [
                            product.get("product_name_en", "") if product else "",
                            product_keywords,
                        ] if value
                    )
                    diligence = run_diligence(
                        lead_id,
                        website,
                        target_keywords=target_keywords,
                    )
                    confidence = rate_confidence(diligence)
                    save_diligence(diligence)
                    updates = {
                        "confidence": confidence,
                        "diligence_done": 1,
                    }
                    if diligence.get("emails"):
                        updates["email"] = ", ".join(diligence["emails"])
                    if diligence.get("phones"):
                        updates["phone"] = ", ".join(diligence["phones"])
                    if diligence.get("whatsapps"):
                        updates["whatsapp"] = ", ".join(diligence["whatsapps"])
                    about = diligence.get("about_text", "").strip()
                    diligence_summary = diligence.get("summary", "").strip()
                    if about or diligence_summary:
                        updates["business_summary"] = "；".join(
                            value for value in [diligence_summary, about[:500]] if value
                        )
                    update_lead(lead_id, **updates)
                    enriched_count += 1
                if product:
                    saved_lead = get_lead(lead_id)
                    if saved_lead:
                        qualification = qualify_lead(
                            saved_lead,
                            product,
                            get_diligence(lead_id),
                        )
                        save_qualification(
                            qualification.to_record(lead_id, product_id)
                        )
        except Exception as exc:
            update_task(task_id, status="failed", leads_found=leads_found)
            summary[f"{channel}_error"] = str(exc)
            continue
        update_task(task_id, status="done", leads_found=leads_found)
        summary[channel] = leads_found

    return summary
