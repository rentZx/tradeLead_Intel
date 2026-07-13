"""
TradeLead V3.0 — Company Due Diligence
Visit company website, extract info, rate confidence.
No API keys needed.
"""

from __future__ import annotations

import re
import time
import random
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from src.extractor import extract_contacts_from_html, extract_keywords_from_html

REQUEST_TIMEOUT = 15
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]


def run_diligence(lead_id: int, website: str) -> dict:
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
        "email_count": 0,
        "phone_count": 0,
        "has_whatsapp": 0,
        "has_product_page": 0,
        "has_contact_page": 0,
        "summary": "",
    }

    if not website or not website.startswith("http"):
        result["summary"] = "无官网或URL无效，无法背调"
        return result

    domain = urlparse(website).netloc

    try:
        time.sleep(random.uniform(1.0, 2.0))
        resp = requests.get(
            website,
            headers={"User-Agent": random.choice(USER_AGENTS)},
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )
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

        # Try to fetch About page
        about_links = soup.find_all("a", href=re.compile(r"/about[/-]?", re.I))
        for a_link in about_links[:2]:
            about_url = a_link.get("href", "")
            if about_url and not about_url.startswith("http"):
                about_url = urljoin(website, about_url)
            if about_url:
                try:
                    time.sleep(random.uniform(0.5, 1.0))
                    ar = requests.get(about_url, headers={"User-Agent": random.choice(USER_AGENTS)}, timeout=10)
                    if ar.status_code == 200:
                        ar.encoding = ar.apparent_encoding or "utf-8"
                        asoup = BeautifulSoup(ar.text, "lxml" if _has_lxml() else "html.parser")
                        result["about_text"] = asoup.get_text(separator=" ", strip=True)[:1000]
                        break
                except Exception:
                    pass

        # Extract contacts
        contacts = extract_contacts_from_html(html, website)
        result["email_count"] = len(contacts.get("emails", []))
        result["phone_count"] = len(contacts.get("phones", []))
        result["has_whatsapp"] = 1 if contacts.get("whatsapps") else 0

        # Extract product keywords
        keywords = extract_keywords_from_html(html, 5)
        result["products_found"] = ", ".join(keywords)

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
            db_update_lead(lead_id, confidence=confidence, diligence_done=1)

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
