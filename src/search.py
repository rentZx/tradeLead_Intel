from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import requests

from src.db import execute, get_connection, query_df, update
from src.prompts import deterministic_keywords

LANGUAGE_KEYS = {
    "英语": "en",
    "俄语": "ru",
    "阿语": "ar",
    "法语": "fr",
    "English": "en",
    "Russian": "ru",
    "Arabic": "ar",
    "French": "fr",
}


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str = ""
    domain: str = ""
    country_guess: str = ""
    language_guess: str = ""
    is_company_site: int = 0


def generate_search_keywords(product: dict[str, Any], countries: list[str], languages: list[str]) -> list[dict[str, str]]:
    product_name = product.get("product_name_en") or product.get("product_name_cn") or ""
    keyword_map = deterministic_keywords(product_name, ", ".join(countries))
    rows: list[dict[str, str]] = []
    for country in countries:
        for language in languages:
            key = LANGUAGE_KEYS.get(language, language)
            for keyword in keyword_map.get(key, []):
                localized = f"{keyword} {country}".strip()
                rows.append({"country": country, "language": language, "keyword": localized})
    return dedupe_keyword_rows(rows)


def run_search_provider(
    provider: str,
    keyword: str,
    country: str,
    language: str,
    api_key: str = "",
    endpoint: str = "",
    cse_id: str = "",
    limit: int = 10,
) -> list[SearchResult]:
    provider_key = provider.lower().strip()
    if provider_key == "mock":
        return mock_search(keyword, country, language, limit)
    if provider_key == "serpapi":
        return serpapi_search(keyword, country, language, api_key or os.getenv("SERPAPI_API_KEY", ""), limit)
    if provider_key == "bing":
        return bing_search(
            keyword,
            country,
            language,
            api_key or os.getenv("BING_SEARCH_API_KEY", ""),
            endpoint or os.getenv("BING_SEARCH_ENDPOINT", "https://api.bing.microsoft.com/v7.0/search"),
            limit,
        )
    if provider_key == "google_cse":
        return google_cse_search(
            keyword,
            api_key or os.getenv("GOOGLE_CSE_API_KEY", ""),
            cse_id or os.getenv("GOOGLE_CSE_ID", ""),
            limit,
        )
    raise ValueError(f"Unsupported search provider: {provider}")


def create_search_task(product_id: int, product_name: str, countries: list[str], languages: list[str], provider: str) -> int:
    task_name = f"Auto search - {product_name} - {', '.join(countries)}"
    return execute(
        """
        INSERT INTO search_tasks(task_name, product_id, target_region, target_countries, languages, source_type, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (task_name, product_id, "auto_search", ", ".join(countries), ", ".join(languages), provider, "Running"),
    )


def save_search_query(task_id: int, product_id: int, row: dict[str, str], provider: str) -> int:
    return execute(
        """
        INSERT INTO search_queries(task_id, product_id, country, language, keyword, search_engine, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (task_id, product_id, row["country"], row["language"], row["keyword"], provider, "Running"),
    )


def save_search_results(task_id: int, query_id: int, results: list[SearchResult]) -> dict[str, int]:
    stats = {"inserted": 0, "duplicate_url": 0, "duplicate_domain": 0}
    seen_domains = existing_domains()
    for result in results:
        normalized_url = normalize_url(result.url)
        if not normalized_url:
            continue
        domain = result.domain or extract_domain(normalized_url)
        if url_exists(normalized_url):
            stats["duplicate_url"] += 1
            continue
        is_duplicate_domain = 1 if domain and domain in seen_domains else 0
        if is_duplicate_domain:
            stats["duplicate_domain"] += 1
        execute(
            """
            INSERT OR IGNORE INTO search_results(
                task_id, query_id, title, url, snippet, domain, country_guess,
                language_guess, is_company_site, is_duplicate, imported_to_companies
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """,
            (
                task_id,
                query_id,
                result.title,
                normalized_url,
                result.snippet,
                domain,
                result.country_guess,
                result.language_guess,
                result.is_company_site,
                is_duplicate_domain,
            ),
        )
        seen_domains.add(domain)
        stats["inserted"] += 1
    return stats


def import_search_results_to_companies(product_id: int, result_ids: list[int] | None = None) -> dict[str, int]:
    where = "imported_to_companies = 0 AND is_duplicate = 0 AND is_company_site = 1"
    params: list[Any] = []
    if result_ids:
        placeholders = ",".join("?" for _ in result_ids)
        where += f" AND id IN ({placeholders})"
        params.extend(result_ids)
    df = query_df(
        f"""
        SELECT id, title, url, snippet, domain, country_guess
        FROM search_results
        WHERE {where}
        ORDER BY id DESC
        """,
        tuple(params),
    )

    imported = 0
    skipped = 0
    for row in df.itertuples(index=False):
        website = normalize_url(row.url)
        domain = row.domain or extract_domain(website)
        if company_exists(website, domain):
            update("UPDATE search_results SET imported_to_companies = 1 WHERE id = ?", (int(row.id),))
            skipped += 1
            continue
        company_name = infer_company_name(row.title, domain)
        execute(
            """
            INSERT INTO companies(
                company_name, country, website, business_summary, source_url, source_type,
                related_product_id, match_keywords, lead_status, risk_status, source_domain,
                extraction_confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                company_name,
                row.country_guess,
                website,
                row.snippet,
                website,
                "search_api",
                product_id,
                row.title,
                "待背调",
                "未筛查",
                domain,
                0.45,
            ),
        )
        update("UPDATE search_results SET imported_to_companies = 1 WHERE id = ?", (int(row.id),))
        imported += 1
    return {"imported": imported, "skipped_existing": skipped}


def log_task(task_id: int | None, task_type: str, status: str, message: str, error_detail: str = "") -> None:
    execute(
        """
        INSERT INTO task_logs(task_id, task_type, status, message, error_detail, finished_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (task_id, task_type, status, message, error_detail),
    )


def update_task_counts(task_id: int) -> None:
    row = query_df(
        """
        SELECT
            COUNT(*) AS discovered,
            SUM(CASE WHEN is_duplicate = 1 THEN 1 ELSE 0 END) AS duplicated
        FROM search_results
        WHERE task_id = ?
        """,
        (task_id,),
    ).iloc[0]
    update(
        """
        UPDATE search_tasks
        SET discovered_company_count = ?, status = ?, completed_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (int(row["discovered"] or 0), "Completed", task_id),
    )


def mock_search(keyword: str, country: str, language: str, limit: int) -> list[SearchResult]:
    slug = re.sub(r"[^a-z0-9]+", "-", keyword.lower()).strip("-") or "trade-lead"
    country_slug = re.sub(r"[^a-z0-9]+", "-", country.lower()).strip("-") or "market"
    results: list[SearchResult] = []
    for idx in range(1, min(limit, 10) + 1):
        domain = f"{slug}-{country_slug}-{idx}.example.com"
        results.append(
            SearchResult(
                title=f"{keyword} supplier {idx}",
                url=f"https://{domain}/products",
                snippet=f"Mock search result for {keyword} in {country}. Replace Mock with a configured API for live search.",
                domain=domain,
                country_guess=country,
                language_guess=language,
                is_company_site=1,
            )
        )
    return results


def serpapi_search(keyword: str, country: str, language: str, api_key: str, limit: int) -> list[SearchResult]:
    require_key(api_key, "SERPAPI_API_KEY")
    response = requests.get(
        "https://serpapi.com/search.json",
        params={"engine": "google", "q": keyword, "api_key": api_key, "num": limit},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    return [
        normalize_provider_result(item.get("title"), item.get("link"), item.get("snippet"), country, language)
        for item in data.get("organic_results", [])[:limit]
        if item.get("link")
    ]


def bing_search(keyword: str, country: str, language: str, api_key: str, endpoint: str, limit: int) -> list[SearchResult]:
    require_key(api_key, "BING_SEARCH_API_KEY")
    response = requests.get(
        endpoint,
        headers={"Ocp-Apim-Subscription-Key": api_key},
        params={"q": keyword, "count": limit, "responseFilter": "Webpages"},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    items = data.get("webPages", {}).get("value", [])
    return [
        normalize_provider_result(item.get("name"), item.get("url"), item.get("snippet"), country, language)
        for item in items[:limit]
        if item.get("url")
    ]


def google_cse_search(keyword: str, api_key: str, cse_id: str, limit: int) -> list[SearchResult]:
    require_key(api_key, "GOOGLE_CSE_API_KEY")
    require_key(cse_id, "GOOGLE_CSE_ID")
    response = requests.get(
        "https://www.googleapis.com/customsearch/v1",
        params={"q": keyword, "key": api_key, "cx": cse_id, "num": min(limit, 10)},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    return [
        normalize_provider_result(item.get("title"), item.get("link"), item.get("snippet"), "", "")
        for item in data.get("items", [])[:limit]
        if item.get("link")
    ]


def normalize_provider_result(title: str | None, url: str | None, snippet: str | None, country: str, language: str) -> SearchResult:
    normalized_url = normalize_url(url or "")
    domain = extract_domain(normalized_url)
    return SearchResult(
        title=title or domain or normalized_url,
        url=normalized_url,
        snippet=snippet or "",
        domain=domain,
        country_guess=country,
        language_guess=language,
        is_company_site=guess_company_site(normalized_url),
    )


def normalize_url(url: str) -> str:
    value = (url or "").strip()
    if not value:
        return ""
    if not value.startswith(("http://", "https://")):
        value = "https://" + value
    parsed = urlparse(value)
    if not parsed.netloc:
        return ""
    path = parsed.path.rstrip("/")
    return parsed._replace(netloc=parsed.netloc.lower(), path=path, params="", query="", fragment="").geturl()


def extract_domain(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def guess_company_site(url: str) -> int:
    domain = extract_domain(url)
    blocked = ("linkedin.com", "facebook.com", "instagram.com", "youtube.com", "wikipedia.org", "amazon.", "alibaba.")
    return 0 if any(item in domain for item in blocked) else 1


def existing_domains() -> set[str]:
    df = query_df("SELECT DISTINCT domain FROM search_results WHERE domain IS NOT NULL AND domain != ''")
    return {str(row.domain) for row in df.itertuples(index=False)}


def url_exists(url: str) -> bool:
    df = query_df("SELECT 1 FROM search_results WHERE url = ? LIMIT 1", (url,))
    return not df.empty


def company_exists(website: str, domain: str) -> bool:
    df = query_df(
        """
        SELECT 1 FROM companies
        WHERE website = ? OR source_url = ? OR source_domain = ?
        LIMIT 1
        """,
        (website, website, domain),
    )
    return not df.empty


def infer_company_name(title: str, domain: str) -> str:
    cleaned = re.split(r"[-|–—]", title or "")[0].strip()
    if cleaned:
        return cleaned[:160]
    return domain or "Unknown company"


def dedupe_keyword_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str, str]] = set()
    unique_rows: list[dict[str, str]] = []
    for row in rows:
        key = (row["country"], row["language"], row["keyword"].lower())
        if key in seen:
            continue
        seen.add(key)
        unique_rows.append(row)
    return unique_rows


def require_key(value: str, name: str) -> None:
    if not value:
        raise ValueError(f"Missing API key/config: {name}")
