"""
TradeLead V3.0 — Company Due Diligence
Visit company website, extract info, rate confidence.
No API keys needed.
"""

from __future__ import annotations

import re
import time
import random
import os
from urllib.parse import urljoin, urlparse
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

from src.extractor import extract_contacts_from_html, extract_keywords_from_html

REQUEST_TIMEOUT = 15
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]


def run_diligence(
    lead_id: int,
    website: str,
    target_keywords: str | list[str] = "",
) -> dict:
    """
    Visit a company's website and extract business intelligence.
    Returns diligence result dict.
    """
    result = {
        "lead_id": lead_id,
        "website_alive": 0,
        "website_title": "",
        "about_text": "",
        "products_found": "",
        "matched_product_terms": "",
        "email_count": 0,
        "phone_count": 0,
        "has_whatsapp": 0,
        "has_product_page": 0,
        "has_contact_page": 0,
        "summary": "",
        "emails": [],
        "phones": [],
        "whatsapps": [],
    }

    if not website or not website.startswith("http"):
        result["summary"] = "无官网或URL无效，无法背调"
        return result

    domain = urlparse(website).netloc

    try:
        time.sleep(random.uniform(1.0, 2.0))
        resp = _request(website, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            result["summary"] = f"官网无法访问 (HTTP {resp.status_code})"
            return result

        resp.encoding = resp.apparent_encoding or "utf-8"
        html = resp.text
        soup = BeautifulSoup(html, "lxml" if _has_lxml() else "html.parser")

        result["website_alive"] = 1
        result["website_title"] = soup.title.get_text(strip=True) if soup.title else ""

        # Check for product page
        product_indicators = ["product", "products", "category", "catalog", "shop", "store"]
        has_products = any(
            soup.find("a", href=re.compile(rf"/{pi}[s]?[/-]?", re.I))
            for pi in product_indicators
        ) or any(
            soup.find(string=re.compile(rf"\b{pi}s?\b", re.I))
            for pi in product_indicators
        )
        result["has_product_page"] = 1 if has_products else 0

        # Check for contact page
        contact_indicators = ["contact", "about", "enquiry", "inquiry", "reach"]
        has_contact = any(
            soup.find("a", href=re.compile(rf"/{ci}[/-]?", re.I))
            for ci in contact_indicators
        ) or any(
            soup.find(string=re.compile(rf"\b{ci}\b", re.I))
            for ci in contact_indicators
        )
        result["has_contact_page"] = 1 if has_contact else 0

        # Fetch a few public About/Contact pages. Contact details frequently do
        # not appear on the homepage, so all fetched HTML participates in
        # extraction.
        page_htmls = [html]
        detail_links: list[tuple[str, str]] = []
        for a_link in soup.find_all("a", href=True):
            href = a_link.get("href", "")
            label = a_link.get_text(" ", strip=True)
            candidate = f"{href} {label}"
            match = re.search(
                r"(about|company|contact|enquiry|inquiry|reach|"
                r"product|catalog|category)",
                candidate,
                re.I,
            )
            if not match:
                continue
            detail_url = urljoin(website, href)
            if urlparse(detail_url).netloc != urlparse(website).netloc:
                continue
            if detail_url not in [url for url, _ in detail_links]:
                detail_links.append((detail_url, match.group(1).lower()))

        detail_links.sort(
            key=lambda item: (
                0 if item[1] in ("product", "catalog", "category") else 1
            )
        )
        product_page_count = 0
        info_page_count = 0
        selected_detail_links: list[tuple[str, str]] = []
        for detail_url, page_kind in detail_links:
            is_product_page = page_kind in ("product", "catalog", "category")
            if is_product_page and product_page_count < 3:
                selected_detail_links.append((detail_url, page_kind))
                product_page_count += 1
            elif not is_product_page and info_page_count < 3:
                selected_detail_links.append((detail_url, page_kind))
                info_page_count += 1
            if product_page_count >= 3 and info_page_count >= 3:
                break

        for detail_url, page_kind in selected_detail_links:
            try:
                time.sleep(random.uniform(0.3, 0.8))
                detail_response = _request(detail_url, timeout=10)
                if detail_response.status_code != 200:
                    continue
                detail_response.encoding = detail_response.apparent_encoding or "utf-8"
                page_htmls.append(detail_response.text)
                detail_soup = BeautifulSoup(
                    detail_response.text, "lxml" if _has_lxml() else "html.parser"
                )
                if not result["about_text"] and page_kind in ("about", "company"):
                    result["about_text"] = detail_soup.get_text(
                        separator=" ", strip=True
                    )[:1500]
            except Exception:
                continue

        # Extract contacts
        contacts = extract_contacts_from_html("\n".join(page_htmls), website)
        result["emails"] = contacts.get("emails", [])
        result["phones"] = contacts.get("phones", [])
        result["whatsapps"] = contacts.get("whatsapps", [])
        result["email_count"] = len(contacts.get("emails", []))
        result["phone_count"] = len(contacts.get("phones", []))
        result["has_whatsapp"] = 1 if contacts.get("whatsapps") else 0

        # Extract product keywords
        keywords = extract_keywords_from_html("\n".join(page_htmls), 5)
        result["products_found"] = ", ".join(keywords)
        if isinstance(target_keywords, str):
            target_terms = [
                value.strip()
                for value in re.split(r"[,，;\n]+", target_keywords)
                if value.strip()
            ]
        else:
            target_terms = [
                value.strip() for value in target_keywords if value.strip()
            ]
        visible_text = " ".join(
            BeautifulSoup(
                page_html,
                "lxml" if _has_lxml() else "html.parser",
            ).get_text(" ", strip=True)
            for page_html in page_htmls
        ).lower()
        matched_product_terms = list(dict.fromkeys(
            term for term in target_terms
            if term.lower() in visible_text
        ))
        result["matched_product_terms"] = ", ".join(matched_product_terms)

        # Generate summary
        parts = []
        if result["website_alive"]:
            parts.append("官网可访问")
        if result["has_product_page"]:
            parts.append("有产品页面")
        if result["has_contact_page"]:
            parts.append("有联系页面")
        if result["email_count"]:
            parts.append(f"找到{result['email_count']}个邮箱")
        if result["phone_count"]:
            parts.append(f"找到{result['phone_count']}个电话")
        if result["has_whatsapp"]:
            parts.append("有WhatsApp")
        if keywords:
            parts.append(f"关键词: {', '.join(keywords[:3])}")
        if matched_product_terms:
            parts.append(
                "目标产品命中: " + ", ".join(matched_product_terms[:3])
            )

        result["summary"] = "；".join(parts) if parts else "官网信息较少"

    except requests.exceptions.SSLError:
        result["summary"] = "SSL证书错误，官网可能已过期"
    except requests.exceptions.ConnectionError:
        result["summary"] = "无法连接到官网"
    except requests.exceptions.Timeout:
        result["summary"] = "官网连接超时"
    except Exception as e:
        result["summary"] = f"背调过程出错：{str(e)[:100]}"

    return result


def _request(url: str, timeout: int) -> requests.Response:
    """Fetch a public page directly, through SOCKS, or through an edge relay."""
    proxy = os.getenv("TRADELEAD_PROXY", "").strip().rstrip("/")
    if not proxy:
        try:
            from src.db_v3 import get_setting
            proxy = (get_setting("proxy_url") or "").strip().rstrip("/")
        except Exception:
            proxy = ""
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    if proxy.startswith(("http://", "https://")):
        url = f"{proxy}?{urlencode({'url': url})}"
        return requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
    proxies = {"http": proxy, "https": proxy} if proxy.startswith("socks") else None
    return requests.get(
        url, headers=headers, timeout=timeout, allow_redirects=True, proxies=proxies
    )


def rate_confidence(diligence_result: dict) -> str:
    """Rate company confidence based on diligence results."""
    score = 0
    if diligence_result.get("website_alive"):
        score += 2
    if diligence_result.get("has_product_page"):
        score += 2
    if diligence_result.get("has_contact_page"):
        score += 1
    if diligence_result.get("email_count", 0) > 0:
        score += 2
    if diligence_result.get("phone_count", 0) > 0:
        score += 1
    if diligence_result.get("has_whatsapp"):
        score += 1
    if diligence_result.get("products_found"):
        score += 1

    if score >= 7:
        return "high"
    elif score >= 4:
        return "medium"
    elif score >= 1:
        return "low"
    else:
        return "unknown"


def batch_diligence(lead_ids: list[int], db_get_lead, db_save_diligence, db_update_lead,
                    progress_callback=None) -> dict:
    """
    Run diligence on multiple leads.
    progress_callback(current, total) called after each lead.
    """
    results = {"high": 0, "medium": 0, "low": 0, "unknown": 0, "errors": 0}
    total = len(lead_ids)

    for i, lead_id in enumerate(lead_ids):
        try:
            lead = db_get_lead(lead_id)
            if not lead:
                results["errors"] += 1
                continue

            website = lead.get("website", "")
            if not website:
                db_update_lead(lead_id, confidence="unknown", diligence_done=1)
                results["unknown"] += 1
                continue

            diligence = run_diligence(lead_id, website)
            confidence = rate_confidence(diligence)
            diligence["confidence"] = confidence
            db_save_diligence(diligence)
            db_update_lead(
                lead_id,
                confidence=confidence,
                diligence_done=1,
                email=", ".join(diligence.get("emails", [])),
                phone=", ".join(diligence.get("phones", [])),
                whatsapp=", ".join(diligence.get("whatsapps", [])),
            )

            results[confidence] += 1
        except Exception:
            results["errors"] += 1

        if progress_callback:
            progress_callback(i + 1, total)

    return results


def _has_lxml() -> bool:
    try:
        import lxml  # noqa: F401
        return True
    except ImportError:
        return False
