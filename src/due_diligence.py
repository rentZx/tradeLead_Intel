from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from typing import Any

from src.db import query_df
from src.risk import RiskHit, format_risk_hits
from src.scoring import calculate_score


@dataclass
class EvidenceItem:
    dimension: str
    reason: str
    snippet: str
    source_url: str
    keywords: list[str]
    confidence: float


BUSINESS_TYPE_KEYWORDS = [
    "importer",
    "distributor",
    "wholesaler",
    "dealer",
    "trading",
    "supplier",
    "manufacturer",
    "workshop",
    "factory",
    "retailer",
    "采购",
    "进口",
    "经销",
    "批发",
    "供应",
]


def build_due_diligence(
    company: dict[str, Any],
    product: dict[str, Any],
    public_text: str,
    risk_hits: list[RiskHit],
    score_override: dict[str, int] | None = None,
) -> dict[str, Any]:
    snapshots = load_snapshots(int(company["id"]))
    source_text = collect_source_text(company, snapshots, public_text)
    source_urls = collect_source_urls(company, snapshots)
    product_keywords = product_terms(product)
    business_hits = keyword_hits(source_text, product_keywords + BUSINESS_TYPE_KEYWORDS)
    contact_hits = contact_keywords(company, snapshots, source_text)

    scores = score_override or suggested_scores(company, snapshots, source_text, business_hits, contact_hits, risk_hits)
    score = calculate_score(
        scores["business_match_score"],
        scores["purchase_probability_score"],
        scores["authenticity_score"],
        scores["contactability_score"],
        risk_hits,
    )
    evidence = build_evidence_items(company, product, snapshots, source_text, source_urls, business_hits, contact_hits, risk_hits, score)
    confidence = confidence_score(evidence, snapshots, company)
    matched_keywords = {
        "product_or_business": sorted(set(business_hits)),
        "contact": sorted(set(contact_hits)),
        "risk": [asdict(hit) for hit in risk_hits],
    }
    report = render_report(company, product, score, evidence, matched_keywords, source_urls, confidence, risk_hits)
    summary = render_evidence_summary(evidence, confidence)
    return {
        "score": score,
        "evidence": [asdict(item) for item in evidence],
        "matched_keywords": matched_keywords,
        "confidence_score": confidence,
        "source_urls": source_urls,
        "report": report,
        "summary": summary,
    }


def load_snapshots(company_id: int) -> list[dict[str, Any]]:
    df = query_df(
        """
        SELECT url, page_type, http_status, raw_title, extracted_text, extracted_emails,
               extracted_phones, extracted_social_links, fetch_status, error_message, fetched_at
        FROM webpage_snapshots
        WHERE company_id = ?
        ORDER BY fetch_status = 'Success' DESC, fetched_at DESC
        """,
        (company_id,),
    )
    return [row._asdict() for row in df.itertuples(index=False)]


def collect_source_text(company: dict[str, Any], snapshots: list[dict[str, Any]], public_text: str) -> str:
    chunks = [
        str(company.get("company_name") or ""),
        str(company.get("business_summary") or ""),
        str(company.get("website") or ""),
        str(company.get("email") or ""),
        str(company.get("phone") or ""),
        str(company.get("whatsapp") or ""),
        str(company.get("telegram") or ""),
        public_text or "",
    ]
    for snapshot in snapshots:
        if snapshot.get("fetch_status") == "Success":
            chunks.extend(
                [
                    str(snapshot.get("raw_title") or ""),
                    str(snapshot.get("extracted_text") or ""),
                    str(snapshot.get("extracted_emails") or ""),
                    str(snapshot.get("extracted_phones") or ""),
                    str(snapshot.get("extracted_social_links") or ""),
                ]
            )
    return "\n".join(chunks)


def collect_source_urls(company: dict[str, Any], snapshots: list[dict[str, Any]]) -> list[str]:
    urls = [str(company.get("website") or ""), str(company.get("source_url") or "")]
    urls.extend(str(snapshot.get("url") or "") for snapshot in snapshots if snapshot.get("url"))
    return sorted({url for url in urls if url})


def product_terms(product: dict[str, Any]) -> list[str]:
    fields = [
        "product_name_cn",
        "product_name_en",
        "product_name_ru",
        "product_name_ar",
        "product_name_fr",
        "category",
        "sub_category",
        "description_cn",
        "description_en",
        "specifications",
        "material",
        "model",
        "brand",
    ]
    terms: list[str] = []
    for field in fields:
        value = str(product.get(field) or "").strip()
        if not value:
            continue
        terms.append(value)
        terms.extend(re.findall(r"[A-Za-z][A-Za-z0-9 -]{2,}", value))
    return [term.strip().lower() for term in terms if len(term.strip()) >= 2]


def keyword_hits(text: str, keywords: list[str]) -> list[str]:
    lowered = text.lower()
    hits = []
    for keyword in keywords:
        item = str(keyword).strip().lower()
        if item and item in lowered:
            hits.append(item)
    return sorted(set(hits))


def contact_keywords(company: dict[str, Any], snapshots: list[dict[str, Any]], source_text: str) -> list[str]:
    hits: list[str] = []
    checks = {
        "email": company.get("email") or "@" in source_text,
        "phone": company.get("phone") or bool(re.search(r"\+?\d[\d\s().-]{6,}\d", source_text)),
        "whatsapp": company.get("whatsapp") or "wa.me" in source_text.lower() or "whatsapp" in source_text.lower(),
        "telegram": company.get("telegram") or "t.me/" in source_text.lower() or "telegram" in source_text.lower(),
        "contact_page": any(str(s.get("page_type") or "").lower().startswith("contact") and s.get("fetch_status") == "Success" for s in snapshots),
    }
    for key, present in checks.items():
        if present:
            hits.append(key)
    return hits


def suggested_scores(
    company: dict[str, Any],
    snapshots: list[dict[str, Any]],
    source_text: str,
    business_hits: list[str],
    contact_hits: list[str],
    risk_hits: list[RiskHit],
) -> dict[str, int]:
    success_snapshots = [s for s in snapshots if s.get("fetch_status") == "Success"]
    authenticity = 6
    if company.get("website"):
        authenticity += 4
    if success_snapshots:
        authenticity += 5
    if company.get("email") or "email" in contact_hits:
        authenticity += 3
    if company.get("source_domain"):
        authenticity += 2

    business_match = min(30, 8 + min(16, len(business_hits) * 4) + (6 if success_snapshots else 0))
    purchase_probability = min(20, 6 + min(8, len([h for h in business_hits if h in BUSINESS_TYPE_KEYWORDS]) * 2) + (4 if company.get("country") else 0) + (2 if not risk_hits else 0))
    contactability = min(15, 3 + min(10, len(contact_hits) * 3) + (2 if any("contact" in h for h in contact_hits) else 0))
    return {
        "authenticity_score": min(20, authenticity),
        "business_match_score": business_match,
        "purchase_probability_score": purchase_probability,
        "contactability_score": contactability,
    }


def build_evidence_items(
    company: dict[str, Any],
    product: dict[str, Any],
    snapshots: list[dict[str, Any]],
    source_text: str,
    source_urls: list[str],
    business_hits: list[str],
    contact_hits: list[str],
    risk_hits: list[RiskHit],
    score: dict[str, Any],
) -> list[EvidenceItem]:
    primary_url = source_urls[0] if source_urls else ""
    success_urls = [s.get("url", "") for s in snapshots if s.get("fetch_status") == "Success" and s.get("url")]
    text_snippet = best_snippet(source_text, business_hits) or truncate(source_text, 260)
    items = [
        EvidenceItem(
            dimension="公司真实性",
            reason=f"得分 {score['authenticity_score']}/20：依据官网、成功读取页面、公司名称/联系信息等公开线索判断主体可信度。",
            snippet=best_snapshot_snippet(snapshots) or truncate(str(company.get("business_summary") or company.get("company_name") or ""), 260),
            source_url=success_urls[0] if success_urls else primary_url,
            keywords=[str(company.get("company_name") or ""), "website" if company.get("website") else ""],
            confidence=dimension_confidence(score["authenticity_score"], 20, bool(success_urls)),
        ),
        EvidenceItem(
            dimension="业务匹配度",
            reason=f"得分 {score['business_match_score']}/30：根据产品词、业务类型词和官网正文匹配程度计算。",
            snippet=text_snippet,
            source_url=success_urls[0] if success_urls else primary_url,
            keywords=business_hits[:20],
            confidence=dimension_confidence(score["business_match_score"], 30, bool(business_hits)),
        ),
        EvidenceItem(
            dimension="采购可能性",
            reason=f"得分 {score['purchase_probability_score']}/20：根据 importer/distributor/wholesaler/dealer 等客户类型、所在国家和风险情况判断。",
            snippet=best_snippet(source_text, BUSINESS_TYPE_KEYWORDS) or text_snippet,
            source_url=success_urls[0] if success_urls else primary_url,
            keywords=[hit for hit in business_hits if hit in BUSINESS_TYPE_KEYWORDS],
            confidence=dimension_confidence(score["purchase_probability_score"], 20, bool(business_hits)),
        ),
        EvidenceItem(
            dimension="联系可达性",
            reason=f"得分 {score['contactability_score']}/15：根据邮箱、电话、WhatsApp、Telegram、联系页等可触达证据判断。",
            snippet=contact_snippet(company, snapshots, source_text),
            source_url=contact_source_url(snapshots) or primary_url,
            keywords=contact_hits,
            confidence=dimension_confidence(score["contactability_score"], 15, bool(contact_hits)),
        ),
        EvidenceItem(
            dimension="风险扣分",
            reason=f"扣分 {score['risk_score']}/30：根据内置风险关键词命中强度计算；未命中也不能替代人工合规复核。",
            snippet=best_snippet(source_text, [hit.keyword for hit in risk_hits]) if risk_hits else "未发现内置风险关键词命中。",
            source_url=success_urls[0] if success_urls else primary_url,
            keywords=[hit.keyword for hit in risk_hits],
            confidence=0.85 if risk_hits else 0.45,
        ),
    ]
    return items


def confidence_score(evidence: list[EvidenceItem], snapshots: list[dict[str, Any]], company: dict[str, Any]) -> float:
    base = sum(item.confidence for item in evidence) / max(1, len(evidence))
    successful = len([s for s in snapshots if s.get("fetch_status") == "Success"])
    bonus = min(0.15, successful * 0.03)
    if company.get("extraction_confidence"):
        bonus += min(0.1, float(company["extraction_confidence"]) * 0.1)
    return round(min(0.98, base + bonus), 2)


def render_report(
    company: dict[str, Any],
    product: dict[str, Any],
    score: dict[str, Any],
    evidence: list[EvidenceItem],
    matched_keywords: dict[str, Any],
    source_urls: list[str],
    confidence: float,
    risk_hits: list[RiskHit],
) -> str:
    lines = [
        "# 背调报告",
        "",
        "## 结论",
        f"- 公司：{company.get('company_name', '')}",
        f"- 关联产品：{product.get('product_name_cn', '') or product.get('product_name_en', '') or '未关联'}",
        f"- 最终分：{score['final_score']}，评级：{score['final_grade']}，整体置信度：{confidence}",
        "",
        "## 分项评分与理由",
    ]
    for item in evidence:
        lines.extend(
            [
                f"### {item.dimension}",
                f"- 评分理由：{item.reason}",
                f"- 证据片段：{item.snippet or '暂无证据片段'}",
                f"- 来源URL：{item.source_url or '暂无来源URL'}",
                f"- 命中关键词：{', '.join([k for k in item.keywords if k]) or '无'}",
                f"- 置信度：{item.confidence}",
                "",
            ]
        )
    lines.extend(
        [
            "## 命中关键词汇总",
            json.dumps(matched_keywords, ensure_ascii=False, indent=2),
            "",
            "## 来源URL",
            "\n".join(f"- {url}" for url in source_urls) or "- 暂无来源URL",
            "",
            "## 风险提示",
            format_risk_hits(risk_hits),
            "",
            "## 人工复核",
            "本报告仅基于已录入资料和公开网页快照生成。涉及制裁、出口管制、最终用途、最终用户、付款路径、HS编码和报关申报时，必须人工复核。",
        ]
    )
    return "\n".join(lines)


def render_evidence_summary(evidence: list[EvidenceItem], confidence: float) -> str:
    lines = [f"整体置信度：{confidence}"]
    for item in evidence:
        lines.append(f"{item.dimension}：{item.reason} 来源：{item.source_url or '暂无'}")
    return "\n".join(lines)


def best_snapshot_snippet(snapshots: list[dict[str, Any]]) -> str:
    for snapshot in snapshots:
        if snapshot.get("fetch_status") == "Success" and snapshot.get("extracted_text"):
            return truncate(str(snapshot["extracted_text"]), 260)
    return ""


def best_snippet(text: str, keywords: list[str]) -> str:
    if not text:
        return ""
    lowered = text.lower()
    for keyword in keywords:
        if not keyword:
            continue
        index = lowered.find(str(keyword).lower())
        if index >= 0:
            start = max(0, index - 120)
            end = min(len(text), index + len(str(keyword)) + 160)
            return truncate(text[start:end], 320)
    return ""


def contact_snippet(company: dict[str, Any], snapshots: list[dict[str, Any]], source_text: str) -> str:
    fields = [company.get("email"), company.get("phone"), company.get("whatsapp"), company.get("telegram")]
    direct = " / ".join(str(field) for field in fields if field)
    if direct:
        return direct
    return best_snippet(source_text, ["@", "whatsapp", "telegram", "contact"]) or best_snapshot_snippet(snapshots)


def contact_source_url(snapshots: list[dict[str, Any]]) -> str:
    for snapshot in snapshots:
        if snapshot.get("fetch_status") == "Success" and "contact" in str(snapshot.get("page_type") or "").lower():
            return str(snapshot.get("url") or "")
    return ""


def dimension_confidence(score: int | float, max_score: int, has_evidence: bool) -> float:
    evidence_base = 0.55 if has_evidence else 0.25
    score_weight = min(0.35, (float(score) / max_score) * 0.35)
    return round(min(0.95, evidence_base + score_weight), 2)


def truncate(text: str, limit: int) -> str:
    cleaned = re.sub(r"\s+", " ", text or "").strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3] + "..."
