"""
TradeLead V3.0 — Contact Extractor
Extract emails, phones, WhatsApp, social links from HTML.
"""

import re
from urllib.parse import urljoin

# ── Email regex ──────────────────────────────────────────
EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)

# ── Phone regex (international format, loose) ────────────
PHONE_RE = re.compile(
    r"(?:\+?\d{1,4}[\s.-]?)?"           # country code
    r"(?:\(?\d{1,4}\)?[\s.-]?)?"        # area code
    r"(?:\d{2,4}[\s.-]?){2,4}"          # local number
    r"\d{2,4}",                          # last digits
)

# ── WhatsApp links ───────────────────────────────────────
WHATSAPP_RE = re.compile(
    r"https?://(?:wa\.me|api\.whatsapp\.com)/[+\w]+",
    re.IGNORECASE,
)

# ── Telegram links ───────────────────────────────────────
TELEGRAM_RE = re.compile(
    r"https?://t\.me/[\w+]+",
    re.IGNORECASE,
)

# ── Social media domains ─────────────────────────────────
SOCIAL_DOMAINS = [
    "linkedin.com", "facebook.com", "instagram.com", "twitter.com",
    "x.com", "youtube.com", "pinterest.com",
]


def extract_contacts_from_html(html: str, base_url: str = "") -> dict:
    """Extract all contact info from an HTML page."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "lxml" if _has_lxml() else "html.parser")

    # Get all visible text
    text = soup.get_text(separator=" ", strip=True)

    # Extract emails
    emails = list(set(EMAIL_RE.findall(text)))
    # Filter out common false positives
    emails = [e for e in emails if not e.endswith((".png", ".jpg", ".gif", ".svg", ".css", ".js"))
              and "example" not in e.lower()
              and len(e) < 100]

    # Extract phones
    raw_phones = PHONE_RE.findall(text)
    phones = _clean_phones(raw_phones)

    # Extract links
    all_links = [a.get("href", "") for a in soup.find_all("a", href=True)]

    # WhatsApp
    whatsapps = list(set(
        [l for l in all_links if "whatsapp" in l.lower() or "wa.me" in l.lower()]
    ))
    # Also try to identify phone numbers as WhatsApp
    for p in phones:
        if len(p.replace("+", "").replace("-", "").replace(" ", "")) >= 10:
            whatsapps.append(f"https://wa.me/{p.replace('+','').replace('-','').replace(' ','')}")

    # Telegram
    telegrams = list(set(
        [l for l in all_links if "t.me" in l.lower() or "telegram" in l.lower()]
    ))

    # Social links
    social_links = []
    for link in all_links:
        for sd in SOCIAL_DOMAINS:
            if sd in link.lower():
                social_links.append(link)
                break

    return {
        "emails": emails[:5],
        "phones": phones[:5],
        "whatsapps": whatsapps[:3],
        "telegrams": telegrams[:3],
        "social_links": list(set(social_links))[:5],
    }


def extract_keywords_from_html(html: str, max_keywords: int = 10) -> list[str]:
    """Extract product/business keywords from page text."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "lxml" if _has_lxml() else "html.parser")

    # Try meta keywords first
    meta_kw = soup.find("meta", attrs={"name": "keywords"})
    if meta_kw and meta_kw.get("content"):
        return [k.strip() for k in meta_kw["content"].split(",")][:max_keywords]

    # Try meta description
    meta_desc = soup.find("meta", attrs={"name": "description"})
    desc_text = meta_desc.get("content", "") if meta_desc else ""

    # Get title and headings
    title = soup.title.get_text(strip=True) if soup.title else ""
    h1s = " ".join(h.get_text(strip=True) for h in soup.find_all(["h1", "h2"])[:5])

    combined = f"{title} {desc_text} {h1s}"

    # Simple keyword extraction: split and take non-stop words
    stop_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "can", "shall", "you", "your",
        "we", "our", "they", "their", "its", "it", "this", "that", "these",
        "those", "all", "each", "every", "both", "few", "more", "most",
        "other", "some", "such", "no", "not", "only", "same", "so", "than",
        "too", "very", "just", "about", "above", "after", "again", "also",
    }
    words = re.findall(r"\b[a-zA-Z]{3,}\b", combined.lower())
    keywords = [w for w in words if w not in stop_words]
    # Count frequency, return top
    from collections import Counter
    return [kw for kw, _ in Counter(keywords).most_common(max_keywords)]


def _clean_phones(raw: list[str]) -> list[str]:
    """Filter and normalize phone numbers."""
    cleaned = []
    for p in raw:
        # Remove non-digit chars except +
        digits = re.sub(r"[^\d+]", "", p)
        if len(digits) >= 7 and len(digits) <= 20:
            cleaned.append(digits)
    return list(set(cleaned))


def _has_lxml() -> bool:
    try:
        import lxml  # noqa: F401
        return True
    except ImportError:
        return False
