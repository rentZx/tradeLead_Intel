"""TradeLead Intel — 免费获客模块

四大零成本获客渠道：
1. 黄页采集    — 解析 B2B 商业目录 HTML
2. Google 搜索  — 直接抓取 SERP 结果页
3. WHOIS 反查   — 域名注册人信息提取
4. Google Maps  — Places API 免费额度搜索
"""

from __future__ import annotations

import hashlib
import json
import re
import socket
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote_plus, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from src.db import execute, query_df, update

# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
]

COUNTRY_TLD_MAP = {
    "kz": "哈萨克斯坦", "ru": "俄罗斯", "uz": "乌兹别克斯坦",
    "ae": "阿联酋", "eg": "埃及", "ng": "尼日利亚",
    "tr": "土耳其", "ir": "伊朗", "in": "印度",
    "pk": "巴基斯坦", "sa": "沙特阿拉伯", "qa": "卡塔尔",
    "kw": "科威特", "om": "阿曼", "bh": "巴林",
    "ma": "摩洛哥", "dz": "阿尔及利亚", "tn": "突尼斯",
    "za": "南非", "ke": "肯尼亚", "gh": "加纳",
    "br": "巴西", "mx": "墨西哥", "vn": "越南",
    "id": "印尼", "th": "泰国", "my": "马来西亚",
    "ph": "菲律宾", "bd": "孟加拉国", "lk": "斯里兰卡",
    "ua": "乌克兰", "pl": "波兰", "ro": "罗马尼亚",
}


def _random_headers() -> dict[str, str]:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,ru;q=0.8,zh;q=0.7",
        "Accept-Encoding": "gzip, deflate",
        "DNT": "1",
    }


def _guess_country_from_domain(domain: str) -> str:
    """从域名后缀猜测国家。"""
    if not domain:
        return ""
    parts = domain.rstrip("/").split(".")
    if len(parts) >= 2:
        tld = parts[-1].lower()
        return COUNTRY_TLD_MAP.get(tld, "")
    return ""


def _extract_emails(text: str) -> list[str]:
    """从文本中提取邮箱地址。"""
    return list(set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)))


def _extract_phones(text: str) -> list[str]:
    """从文本中提取国际电话号码。"""
    phones = re.findall(
        r"(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}",
        text,
    )
    return [p.strip() for p in phones if len(re.sub(r"\D", "", p)) >= 7]


def _insert_company(data: dict[str, str], source_type: str) -> int | None:
    """插入公司到线索库，返回 company_id 或 None（去重跳过）。"""
    name = (data.get("company_name") or "").strip()
    if not name:
        return None

    website = (data.get("website") or "").strip().lower()
    website = website.rstrip("/") if website else ""

    # 按公司名 + 网站去重（如果都有）
    if website:
        existing = query_df(
            "SELECT id FROM companies WHERE company_name = ? AND website = ? LIMIT 1",
            (name, website),
        )
    else:
        existing = query_df(
            "SELECT id FROM companies WHERE company_name = ? LIMIT 1",
            (name,),
        )
    if not existing.empty:
        return None

    new_id = execute(
        """INSERT INTO companies (
            company_name, country, city, address, website, email, phone,
            business_summary, source_url, source_type, match_keywords
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            name,
            data.get("country", ""),
            data.get("city", ""),
            data.get("address", ""),
            website,
            data.get("email", ""),
            data.get("phone", ""),
            data.get("business_summary", ""),
            data.get("source_url", ""),
            source_type,
            data.get("match_keywords", ""),
        ),
    )

    return new_id if new_id > 0 else None


# ===================================================================
# 渠道 1: 黄页 / 商业目录采集
# ===================================================================

# 预置黄页采集模板
YELLOW_PAGE_TEMPLATES = {
    "europages": {
        "name": "Europages (欧洲B2B)",
        "base_url": "https://www.europages.com",
        "search_url_template": "https://www.europages.com/search/{keyword}",
        "list_selector": "article.product-line, div.company-listing, li.business-card",
        "name_selector": "h2 a, h3 a, .company-name a, .business-name",
        "country_selector": ".company-country, .location, .country",
        "website_selector": "a.website, a[href*='http']:not([href*='europages'])",
        "desc_selector": ".company-description, .description, .summary",
        "next_page_selector": "a.next, a[rel='next'], .pagination a:contains('►')",
        "notes": "自动搜索欧洲 B2B 供应商目录",
    },
    "kompass": {
        "name": "Kompass (全球B2B)",
        "base_url": "https://www.kompass.com",
        "search_url_template": "https://www.kompass.com/searchCompanies?q={keyword}",
        "list_selector": "div.company-card, li.result-item, div.search-result",
        "name_selector": ".company-name, h3, .title a",
        "country_selector": ".country, .location, .address",
        "website_selector": "a.website, a[href*='http']:not([href*='kompass'])",
        "desc_selector": ".description, .activity, .summary",
        "next_page_selector": "a.next-page, .pagination .next",
        "notes": "全球 B2B 公司数据库",
    },
    "yellowpages": {
        "name": "YellowPages (美国)",
        "base_url": "https://www.yellowpages.com",
        "search_url_template": "https://www.yellowpages.com/search?search_terms={keyword}",
        "list_selector": "div.result, div.srp-result, div.info",
        "name_selector": "a.business-name, h2 a, .n a",
        "country_selector": "",  # 默认美国
        "website_selector": "a.track-visit-website, a[href*='http']:not([href*='yellowpages'])",
        "desc_selector": ".body, .business-description, .categories",
        "next_page_selector": "a.next, .pagination a:contains('Next')",
        "notes": "美国本地商家目录",
    },
}


def _scrape_html_page(
    url: str,
    list_selector: str,
    name_selector: str,
    country_selector: str,
    website_selector: str,
    desc_selector: str,
    default_country: str = "",
) -> list[dict[str, str]]:
    """通用 HTML 列表页解析。"""
    results: list[dict[str, str]] = []
    try:
        resp = requests.get(url, headers=_random_headers(), timeout=20)
        resp.raise_for_status()
    except Exception:
        return results

    soup = BeautifulSoup(resp.text, "html.parser")
    items = soup.select(list_selector) if list_selector else [soup]

    for item in items:
        name_el = item.select_one(name_selector) if name_selector else None
        company_name = name_el.get_text(strip=True) if name_el else ""

        country_el = item.select_one(country_selector) if country_selector else None
        country = country_el.get_text(strip=True) if country_el else default_country

        website_el = item.select_one(website_selector) if website_selector else None
        website = ""
        if website_el:
            href = website_el.get("href", "")
            if href.startswith("http"):
                website = href
            else:
                website = urljoin(url, href)

        desc_el = item.select_one(desc_selector) if desc_selector else None
        desc = desc_el.get_text(strip=True)[:500] if desc_el else ""

        # 从描述和网站链接提取邮箱电话
        full_text = (company_name + " " + desc + " " + website)
        emails = _extract_emails(full_text)
        phones = _extract_phones(full_text)

        if company_name:
            results.append({
                "company_name": company_name,
                "country": country or default_country,
                "website": website,
                "email": emails[0] if emails else "",
                "phone": phones[0] if phones else "",
                "business_summary": desc,
                "source_url": url,
                "match_keywords": "",
            })

    return results


def scrape_yellow_pages(
    template_key: str | None = None,
    custom_url: str = "",
    custom_list_selector: str = "",
    custom_name_selector: str = "",
    custom_country_selector: str = "",
    custom_website_selector: str = "",
    custom_desc_selector: str = "",
    custom_next_selector: str = "",
    keyword: str = "",
    default_country: str = "",
    max_pages: int = 3,
) -> dict[str, Any]:
    """
    黄页采集主函数。

    Args:
        template_key: 预置模板 key (europages/kompass/yellowpages)，与 custom 参数互斥
        custom_url: 自定义采集 URL
        custom_list_selector: 自定义列表 CSS 选择器
        custom_name_selector: 自定义名称 CSS 选择器
        custom_country_selector: 自定义国家 CSS 选择器
        custom_website_selector: 自定义网站 CSS 选择器
        custom_desc_selector: 自定义描述 CSS 选择器
        custom_next_selector: 自定义翻页 CSS 选择器
        keyword: 搜索关键词（用于预置模板）
        default_country: 默认国家
        max_pages: 最大翻页数

    Returns:
        {"total": int, "imported": int, "skipped": int, "results": list, "errors": list}
    """
    total_collected = 0
    imported = 0
    skipped = 0
    all_results: list[dict[str, str]] = []
    errors: list[str] = []

    # 确定采集参数
    if template_key and template_key in YELLOW_PAGE_TEMPLATES:
        tmpl = YELLOW_PAGE_TEMPLATES[template_key]
        search_url = tmpl["search_url_template"].format(keyword=quote_plus(keyword)) if keyword else tmpl["base_url"]
        list_sel = tmpl["list_selector"]
        name_sel = tmpl["name_selector"]
        country_sel = tmpl["country_selector"]
        website_sel = tmpl["website_selector"]
        desc_sel = tmpl["desc_selector"]
        next_sel = tmpl["next_page_selector"]
    else:
        search_url = custom_url
        list_sel = custom_list_selector
        name_sel = custom_name_selector
        country_sel = custom_country_selector
        website_sel = custom_website_selector
        desc_sel = custom_desc_selector
        next_sel = custom_next_selector

    if not search_url:
        errors.append("请提供采集 URL 或选择预置模板并输入关键词")
        return {"total": 0, "imported": 0, "skipped": 0, "results": [], "errors": errors}

    current_url = search_url
    for page in range(max_pages):
        try:
            page_results = _scrape_html_page(
                current_url, list_sel, name_sel, country_sel,
                website_sel, desc_sel, default_country,
            )
            total_collected += len(page_results)
            all_results.extend(page_results)

            for r in page_results:
                cid = _insert_company(r, "yellow_pages")
                if cid:
                    imported += 1
                else:
                    skipped += 1

            # 翻页
            if not next_sel or page >= max_pages - 1:
                break
            try:
                resp = requests.get(current_url, headers=_random_headers(), timeout=15)
                soup = BeautifulSoup(resp.text, "html.parser")
                next_link = soup.select_one(next_sel)
                if next_link and next_link.get("href"):
                    href = next_link["href"]
                    current_url = href if href.startswith("http") else urljoin(current_url, href)
                    time.sleep(random.uniform(1.5, 3.0))
                else:
                    break
            except Exception:
                break

        except Exception as exc:
            errors.append(f"第 {page+1} 页采集失败: {exc}")
            break

    return {
        "total": total_collected,
        "imported": imported,
        "skipped": skipped,
        "results": all_results,
        "errors": errors,
    }


# ===================================================================
# 渠道 2: Google 直接搜索（绕过 API）
# ===================================================================

def search_google_direct(
    keyword: str,
    num_results: int = 20,
) -> dict[str, Any]:
    """
    直接抓取 Google 搜索 HTML 结果页。

    Args:
        keyword: 搜索关键词，如 "plastic products buyer Kazakhstan"
        num_results: 最大结果数

    Returns:
        {"total": int, "imported": int, "skipped": int, "results": list}
    """
    results: list[dict[str, str]] = []
    imported = 0
    skipped = 0
    errors: list[str] = []

    query = quote_plus(keyword)
    url = f"https://www.google.com/search?q={query}&num={min(num_results, 100)}&hl=en"

    try:
        resp = requests.get(url, headers=_random_headers(), timeout=15)
        resp.raise_for_status()
    except Exception as exc:
        return {"total": 0, "imported": 0, "skipped": 0, "results": [], "errors": [f"请求失败: {exc}"]}

    soup = BeautifulSoup(resp.text, "html.parser")

    # Google SERP 结构：每个自然结果在 .g 或 div[data-sokoban-container] 等容器中
    result_blocks = soup.select("div.g, div[data-sokoban-container], div.MjjYud")

    for block in result_blocks:
        # 标题和链接
        link_el = block.select_one("a[href^='http'], a[href^='/url?q=']")
        if not link_el:
            continue

        href = link_el.get("href", "")
        if href.startswith("/url?q="):
            href = href.split("/url?q=")[1].split("&")[0]

        # 跳过来自 google.com 自身的链接和广告
        if "google.com" in href or not href.startswith("http"):
            continue

        title_el = block.select_one("h3")
        title = title_el.get_text(strip=True) if title_el else ""

        snippet_el = block.select_one("div.VwiC3b, span.aCOpRe, div[data-sncf]")
        snippet = snippet_el.get_text(strip=True)[:500] if snippet_el else ""

        domain = urlparse(href).netloc.replace("www.", "")
        country = _guess_country_from_domain(domain)

        full_text = title + " " + snippet + " " + href
        emails = _extract_emails(full_text)
        phones = _extract_phones(full_text)

        company_name = title.split(" - ")[0].split(" | ")[0].strip()
        if len(company_name) > 80:
            company_name = company_name[:80]

        results.append({
            "company_name": company_name,
            "country": country,
            "website": href,
            "email": emails[0] if emails else "",
            "phone": phones[0] if phones else "",
            "business_summary": snippet,
            "source_url": url,
            "match_keywords": keyword,
        })

    # 导入线索库
    for r in results:
        cid = _insert_company(r, "google_search")
        if cid:
            imported += 1
        else:
            skipped += 1

    return {
        "total": len(results),
        "imported": imported,
        "skipped": skipped,
        "results": results,
        "errors": errors,
    }


# ===================================================================
# 渠道 3: WHOIS 域名反查
# ===================================================================

# WHOIS 服务器映射
WHOIS_SERVERS = {
    "com": ("whois.verisign-grs.com", 43),
    "net": ("whois.verisign-grs.com", 43),
    "org": ("whois.pir.org", 43),
    "ru": ("whois.tcinet.ru", 43),
    "kz": ("whois.nic.kz", 43),
    "cn": ("whois.cnnic.cn", 43),
    "de": ("whois.denic.de", 43),
    "uk": ("whois.nic.uk", 43),
    "fr": ("whois.nic.fr", 43),
    "eu": ("whois.eu", 43),
    "io": ("whois.nic.io", 43),
    "co": ("whois.nic.co", 43),
    "ae": ("whois.aeda.net.ae", 43),
    "in": ("whois.registry.in", 43),
    "br": ("whois.registro.br", 43),
    "tr": ("whois.nic.tr", 43),
}


def _whois_query(domain: str, server: str, port: int = 43) -> str:
    """直接连接 WHOIS 服务器查询。"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((server, port))
        sock.send(f"{domain}\r\n".encode())
        data = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk
        sock.close()
        return data.decode("utf-8", errors="ignore")
    except Exception:
        return ""


def lookup_whois(domain: str) -> dict[str, Any]:
    """
    WHOIS 域名反查。

    提取：注册机构、注册人邮箱、国家、注册日期、域名到期日。
    """
    domain = domain.strip().lower()
    domain = domain.replace("https://", "").replace("http://", "").rstrip("/")
    # 提取裸域名
    parsed = urlparse(f"http://{domain}" if "://" not in domain else domain)
    domain = parsed.netloc or parsed.path
    domain = domain.replace("www.", "")

    tld = domain.split(".")[-1] if "." in domain else "com"
    whois_info = WHOIS_SERVERS.get(tld, ("whois.iana.org", 43))

    raw = _whois_query(domain, whois_info[0], whois_info[1])

    result = {
        "domain": domain,
        "organization": "",
        "email": "",
        "phone": "",
        "country": "",
        "creation_date": "",
        "expiry_date": "",
        "raw_available": not bool(raw),
    }

    if not raw:
        return result

    # 提取组织名
    org_match = re.search(
        r"(?:Registrant\s+Organization|Org(?:anization)?)[:\s]+(.+)",
        raw, re.IGNORECASE,
    )
    if org_match:
        result["organization"] = org_match.group(1).strip()

    # 提取邮箱
    emails = _extract_emails(raw)
    if emails:
        result["email"] = emails[0]

    # 提取电话
    phones = _extract_phones(raw)
    if phones:
        result["phone"] = phones[0]

    # 提取国家
    country_match = re.search(
        r"(?:Registrant\s+Country|Country)[:\s]+([A-Z]{2})",
        raw, re.IGNORECASE,
    )
    if country_match:
        code = country_match.group(1).upper()
        result["country"] = COUNTRY_TLD_MAP.get(code.lower(), code)

    # 提取创建/到期日期
    creation_match = re.search(
        r"(?:Creation\s+Date|Created\s+on|Registered\s+on)[:\s]+([\d\-T:.Z]+)",
        raw, re.IGNORECASE,
    )
    if creation_match:
        result["creation_date"] = creation_match.group(1)

    expiry_match = re.search(
        r"(?:Registry\s+Expiry\s+Date|Expir(?:y|ation)\s+Date|Expires\s+on)[:\s]+([\d\-T:.Z]+)",
        raw, re.IGNORECASE,
    )
    if expiry_match:
        result["expiry_date"] = expiry_match.group(1)

    return result


def whois_batch_import(domains: list[str]) -> dict[str, Any]:
    """
    批量 WHOIS 查询并导入公司线索库。

    Args:
        domains: 域名列表，如 ["example.com", "test.kz"]

    Returns:
        {"total": int, "imported": int, "skipped": int, "results": list}
    """
    imported = 0
    skipped = 0
    results: list[dict[str, Any]] = []

    for domain in domains:
        if not domain.strip():
            continue
        info = lookup_whois(domain.strip())
        info["source_url"] = f"whois://{info['domain']}"
        results.append(info)

        if info.get("organization") or info.get("email"):
            company_data = {
                "company_name": info.get("organization") or info["domain"],
                "country": info.get("country", ""),
                "website": info["domain"],
                "email": info.get("email", ""),
                "phone": info.get("phone", ""),
                "business_summary": f"WHOIS: created {info.get('creation_date', '?')}, expires {info.get('expiry_date', '?')}",
                "source_url": f"whois://{info['domain']}",
                "match_keywords": domain,
            }
            cid = _insert_company(company_data, "whois")
            if cid:
                imported += 1
            else:
                skipped += 1
        else:
            skipped += 1

        time.sleep(random.uniform(0.8, 2.0))

    return {
        "total": len(results),
        "imported": imported,
        "skipped": skipped,
        "results": results,
    }


# ===================================================================
# 渠道 4: Google Maps Places API
# ===================================================================

GOOGLE_MAPS_BASE = "https://maps.googleapis.com/maps/api/place"


def search_google_maps(
    query: str,
    api_key: str = "",
    location: str = "",
    radius: int = 50000,
    max_results: int = 20,
) -> dict[str, Any]:
    """
    Google Maps Places API 搜索。

    使用 Text Search（免费额度 $200/月 ≈ 28000 次）。

    Args:
        query: 搜索词，如 "plastic manufacturers in Dubai"
        api_key: Google Cloud API Key（需要启用 Places API）
        location: 中心坐标 "lat,lng"（可选）
        radius: 搜索半径（米）
        max_results: 最大结果数
    """
    results: list[dict[str, str]] = []
    imported = 0
    skipped = 0
    errors: list[str] = []

    if not api_key:
        key_from_env = ""
        try:
            import os
            key_from_env = os.getenv("GOOGLE_MAPS_API_KEY", os.getenv("GOOGLE_CSE_API_KEY", ""))
        except Exception:
            pass
        if not key_from_env:
            errors.append("需要 Google Maps API Key。请在 Google Cloud Console 启用 Places API。")
            return {"total": 0, "imported": 0, "skipped": 0, "results": [], "errors": errors}
        api_key = key_from_env

    # Text Search
    params: dict[str, str] = {
        "query": query,
        "key": api_key,
    }
    if location:
        params["location"] = location
        params["radius"] = str(radius)

    url = f"{GOOGLE_MAPS_BASE}/textsearch/json"

    try:
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()
    except Exception as exc:
        errors.append(f"API 请求失败: {exc}")
        return {"total": 0, "imported": 0, "skipped": 0, "results": [], "errors": errors}

    if data.get("status") not in ("OK", "ZERO_RESULTS"):
        error_msg = data.get("error_message", data.get("status", "Unknown error"))
        errors.append(f"API 错误: {error_msg}")
        return {"total": 0, "imported": 0, "skipped": 0, "results": [], "errors": errors}

    for place in data.get("results", [])[:max_results]:
        name = place.get("name", "")
        address = place.get("formatted_address", "")
        place_id = place.get("place_id", "")

        # 从地址提取国家
        country = ""
        if address:
            parts = address.split(",")
            if len(parts) >= 1:
                country = parts[-1].strip()

        results.append({
            "company_name": name,
            "country": country,
            "city": "",
            "address": address,
            "website": "",
            "email": "",
            "phone": "",
            "business_summary": f"Google Maps · {', '.join(place.get('types', []))} · rating: {place.get('rating', 'N/A')}",
            "source_url": f"https://www.google.com/maps/place/?q=place_id:{place_id}",
            "match_keywords": query,
        })

    # 获取详情（网站、电话）
    for i, r in enumerate(results):
        place_id = r.get("source_url", "").split("place_id:")[-1] if r.get("source_url") else ""
        if not place_id:
            continue

        detail_url = f"{GOOGLE_MAPS_BASE}/details/json"
        try:
            detail_resp = requests.get(
                detail_url,
                params={"place_id": place_id, "fields": "website,formatted_phone_number,international_phone_number", "key": api_key},
                timeout=10,
            )
            detail_data = detail_resp.json()
            if detail_data.get("status") == "OK":
                info = detail_data.get("result", {})
                r["website"] = info.get("website", "")
                r["phone"] = info.get("international_phone_number") or info.get("formatted_phone_number", "")
        except Exception:
            pass

        time.sleep(random.uniform(0.3, 1.0))

    # 导入线索库
    for r in results:
        cid = _insert_company(r, "google_maps")
        if cid:
            imported += 1
        else:
            skipped += 1

    return {
        "total": len(results),
        "imported": imported,
        "skipped": skipped,
        "results": results,
        "errors": errors,
    }
