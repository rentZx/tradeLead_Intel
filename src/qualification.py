"""Product-specific buyer profiling and lead qualification."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import re
from typing import Any


CHANNEL_MARKERS = [
    "distributor", "importer", "wholesaler", "dealer", "reseller",
    "stockist", "supplier", "trading company", "general trading",
    "hardware store", "hardware", "building materials", "retailer", "shop",
    "distribuidor", "distribuidora", "importador", "mayorista",
    "ferreteria", "grossiste", "negociant",
]

END_USER_MARKERS = [
    "contractor", "construction company", "installer", "applicator",
    "manufacturer", "factory", "fabricator", "engineering company",
    "project developer", "property developer", "procurement",
    "builder", "maintenance company",
]

DEMAND_MARKERS = [
    "request a quote", "request quote", "rfq", "tender", "procurement",
    "project", "contractor", "installer", "construction", "manufacturer",
    "factory", "production line", "engineering", "application",
]

GENERIC_BUYER_PHRASES = {
    "hardware store", "building materials supplier", "building materials",
    "construction supply", "construction supply company", "tools supplier",
    "trading company", "general trading company", "importer", "distributor",
    "wholesaler", "dealer", "supplier",
}

STOPWORDS = {
    "the", "and", "for", "with", "from", "into", "products", "product",
    "company", "supplier", "distributor", "manufacturer", "materials",
    "system", "systems", "equipment", "machine", "store", "shop",
}

QUALIFICATION_MODEL_VERSION = "buyer-qualification-v1.2"


@dataclass(frozen=True)
class BuyerProfile:
    product_id: int
    product_name: str
    product_phrases: list[str]
    channel_phrases: list[str]
    end_user_phrases: list[str]
    exclude_phrases: list[str]


@dataclass(frozen=True)
class QualificationResult:
    buyer_role: str
    verdict: str
    product_fit_score: int
    channel_fit_score: int
    end_user_fit_score: int
    demand_signal_score: int
    contactability_score: int
    overall_score: int
    reasons: list[str]
    evidence: list[dict[str, Any]]
    rejection_reasons: list[str]

    def to_record(self, lead_id: int, product_id: int) -> dict:
        data = asdict(self)
        data.update({"lead_id": lead_id, "product_id": product_id})
        data["reasons"] = json.dumps(self.reasons, ensure_ascii=False)
        data["evidence"] = json.dumps(self.evidence, ensure_ascii=False)
        data["rejection_reasons"] = json.dumps(
            self.rejection_reasons, ensure_ascii=False
        )
        data["model_version"] = QUALIFICATION_MODEL_VERSION
        return data


def build_buyer_profile(product: dict) -> BuyerProfile:
    product_phrases = _dedupe([
        product.get("product_name_en", ""),
        product.get("product_name_cn", ""),
        product.get("sub_category", ""),
        *_split(product.get("keywords_en", "")),
    ])
    return BuyerProfile(
        product_id=int(product["id"]),
        product_name=(
            product.get("product_name_en")
            or product.get("product_name_cn")
            or "目标产品"
        ),
        product_phrases=product_phrases,
        channel_phrases=_dedupe(_split(product.get("buyer_types", ""))),
        end_user_phrases=_dedupe(_split(product.get("end_user_types", ""))),
        exclude_phrases=_dedupe(_split(product.get("exclude_terms", ""))),
    )


def qualify_lead(
    lead: dict,
    product: dict,
    diligence: dict | None = None,
) -> QualificationResult:
    """Evaluate one company for one product using explainable public evidence."""
    profile = build_buyer_profile(product)
    diligence = diligence or {}
    strong_sources = {
        "公司名称": lead.get("company_name", ""),
        "公司简介": lead.get("business_summary", ""),
        "官网标题": diligence.get("website_title", ""),
        "官网介绍": diligence.get("about_text", ""),
        "官网产品词": diligence.get("products_found", ""),
        "目标产品命中": diligence.get("matched_product_terms", ""),
    }
    strong_text = _normalize(" ".join(str(value) for value in strong_sources.values()))
    weak_text = _normalize(
        " ".join([
            str(lead.get("match_keyword", "")),
            str(lead.get("source_channel", "")),
        ])
    )
    evidence: list[dict[str, Any]] = []
    reasons: list[str] = []
    rejection_reasons: list[str] = []

    excluded = _matches(strong_text, profile.exclude_phrases)
    if excluded:
        rejection_reasons.append(
            "命中排除词：" + "、".join(excluded[:4])
        )
        _add_evidence(
            evidence, "排除证据", "官网或公司信息", excluded, -100
        )

    product_matches = _matches(strong_text, profile.product_phrases)
    product_score = min(75, len(product_matches) * 35)
    if product_matches:
        _add_evidence(
            evidence, "产品匹配", "公司/官网公开信息", product_matches, product_score
        )

    product_tokens = _meaningful_tokens(profile.product_phrases)
    matched_tokens = [
        token for token in product_tokens
        if re.search(rf"\b{re.escape(token)}\b", strong_text)
    ]
    token_points = min(20, len(matched_tokens) * 5)
    product_score += token_points
    if matched_tokens:
        _add_evidence(
            evidence, "产品相关词", "公司/官网公开信息",
            matched_tokens[:8], token_points,
        )

    channel_matches = _matches(strong_text, profile.channel_phrases)
    specific_channel_matches = [
        phrase for phrase in channel_matches
        if _normalize(phrase) not in GENERIC_BUYER_PHRASES
    ]
    adjacent_points = min(20, len(specific_channel_matches) * 15)
    product_score += adjacent_points
    if specific_channel_matches:
        _add_evidence(
            evidence, "相邻品类", "目标渠道经营范围",
            specific_channel_matches, adjacent_points,
        )

    weak_product_matches = _matches(weak_text, profile.product_phrases)
    weak_product_points = min(12, len(weak_product_matches) * 6)
    product_score += weak_product_points
    if weak_product_matches:
        _add_evidence(
            evidence, "搜索匹配", "搜索词（弱证据）",
            weak_product_matches, weak_product_points,
        )

    if diligence.get("has_product_page") and product_score:
        product_score += 5
        _add_evidence(evidence, "官网结构", "产品目录", ["存在产品页面"], 5)
    product_score = min(100, product_score)
    if excluded:
        product_score = 0

    channel_target_points = min(70, len(channel_matches) * 24)
    channel_marker_matches = _matches(strong_text, CHANNEL_MARKERS)
    channel_marker_points = min(45, len(channel_marker_matches) * 15)
    weak_channel_matches = _matches(weak_text, profile.channel_phrases)
    weak_channel_points = min(12, len(weak_channel_matches) * 4)
    channel_score = min(
        100,
        channel_target_points + channel_marker_points + weak_channel_points,
    )
    if channel_matches:
        _add_evidence(
            evidence, "渠道角色", "公司/官网公开信息",
            channel_matches, channel_target_points,
        )
    if channel_marker_matches:
        _add_evidence(
            evidence, "渠道特征", "公司/官网公开信息",
            channel_marker_matches, channel_marker_points,
        )

    end_user_matches = _matches(strong_text, profile.end_user_phrases)
    end_marker_matches = _matches(strong_text, END_USER_MARKERS)
    weak_end_matches = _matches(weak_text, profile.end_user_phrases)
    end_user_score = min(
        100,
        min(70, len(end_user_matches) * 24)
        + min(30, len(end_marker_matches) * 10)
        + min(12, len(weak_end_matches) * 4),
    )
    if end_user_matches:
        _add_evidence(
            evidence, "需求方角色", "公司/官网公开信息",
            end_user_matches, min(70, len(end_user_matches) * 24),
        )
    if end_marker_matches:
        _add_evidence(
            evidence, "终端特征", "公司/官网公开信息",
            end_marker_matches, min(30, len(end_marker_matches) * 10),
        )

    demand_matches = _matches(strong_text, DEMAND_MARKERS)
    demand_score = min(
        100,
        min(60, len(demand_matches) * 10)
        + min(40, len(end_user_matches) * 15),
    )
    if demand_matches:
        _add_evidence(
            evidence, "需求信号", "公司/官网公开信息",
            demand_matches, demand_score,
        )

    contact_score = 0
    contact_signals: list[str] = []
    if lead.get("website"):
        contact_score += 20
        contact_signals.append("官网")
    if lead.get("email"):
        contact_score += 35
        contact_signals.append("邮箱")
    if lead.get("phone"):
        contact_score += 25
        contact_signals.append("电话")
    if lead.get("whatsapp"):
        contact_score += 20
        contact_signals.append("WhatsApp")
    if lead.get("social_links"):
        contact_score += 5
        contact_signals.append("社交账号")
    contact_score = min(100, contact_score)
    if contact_signals:
        _add_evidence(
            evidence, "可触达性", "公开联系方式",
            contact_signals, contact_score,
        )

    if channel_score >= 30 and end_user_score >= 30:
        buyer_role = "mixed"
        role_score = max(channel_score, end_user_score)
    elif channel_score >= end_user_score and channel_score >= 15:
        buyer_role = "channel_partner"
        role_score = channel_score
    elif end_user_score >= 15:
        buyer_role = "end_user"
        role_score = end_user_score
    else:
        buyer_role = "unknown"
        role_score = max(channel_score, end_user_score)

    overall_score = round(
        product_score * 0.45
        + role_score * 0.35
        + contact_score * 0.20
    )

    if excluded:
        verdict = "rejected"
        overall_score = min(overall_score, 15)
    elif (
        product_score >= 50
        and role_score >= 30
        and contact_score >= 20
        and overall_score >= 45
    ):
        verdict = "qualified"
    elif product_score >= 25 and role_score >= 25 and overall_score >= 35:
        verdict = "promising"
    elif (
        diligence.get("website_alive")
        and product_score < 10
        and role_score < 20
    ):
        verdict = "rejected"
        rejection_reasons.append("官网未发现目标产品、相邻品类或买家角色证据")
    else:
        verdict = "review"

    role_labels = {
        "channel_partner": "经销/渠道客户",
        "end_user": "终端需求方",
        "mixed": "渠道兼终端客户",
        "unknown": "角色待确认",
    }
    reasons.append(f"角色判定：{role_labels[buyer_role]}")
    reasons.append(f"产品匹配 {product_score} 分，角色匹配 {role_score} 分")
    reasons.append(f"公开联系方式完整度 {contact_score} 分")
    if not product_matches and not specific_channel_matches:
        reasons.append("尚缺少官网经营目标产品的强证据")
    if buyer_role == "end_user" and not demand_matches:
        reasons.append("已识别终端属性，但尚未发现明确询价或项目需求信号")

    return QualificationResult(
        buyer_role=buyer_role,
        verdict=verdict,
        product_fit_score=product_score,
        channel_fit_score=channel_score,
        end_user_fit_score=end_user_score,
        demand_signal_score=demand_score,
        contactability_score=contact_score,
        overall_score=overall_score,
        reasons=reasons,
        evidence=evidence,
        rejection_reasons=rejection_reasons,
    )


def evaluate_and_save(
    lead_id: int,
    product_id: int,
    lead_override: dict | None = None,
) -> QualificationResult | None:
    from src.db_v3 import (
        get_diligence,
        get_lead,
        get_product,
        save_qualification,
    )

    lead = lead_override or get_lead(lead_id)
    product = get_product(product_id)
    if not lead or not product:
        return None
    result = qualify_lead(lead, product, get_diligence(lead_id))
    save_qualification(result.to_record(lead_id, product_id))
    return result


def backfill_missing_qualifications() -> int:
    from src.db_v3 import query

    rows = query(
        """SELECT l.id AS lead_id, t.product_id
           FROM leads l
           JOIN acquisition_tasks t ON t.id=l.task_id
           LEFT JOIN lead_qualifications q
             ON q.lead_id=l.id AND q.product_id=t.product_id
           WHERE t.product_id IS NOT NULL
             AND (q.id IS NULL OR COALESCE(q.model_version, '') != ?)""",
        (QUALIFICATION_MODEL_VERSION,),
    )
    saved = 0
    for row in rows:
        if evaluate_and_save(row["lead_id"], row["product_id"]):
            saved += 1
    return saved


def _split(value: str) -> list[str]:
    return [
        item.strip()
        for item in re.split(r"[,，;\n]+", value or "")
        if item.strip()
    ]


def _dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = _normalize(value)
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(value.strip())
    return result


def _normalize(value: str) -> str:
    value = value.replace("_", " ")
    return re.sub(r"\s+", " ", re.sub(r"[^\w]+", " ", value.lower())).strip()


def _matches(text: str, phrases: list[str]) -> list[str]:
    matches: list[str] = []
    for phrase in phrases:
        normalized = _normalize(phrase)
        if normalized and normalized in text:
            matches.append(phrase)
    return _dedupe(matches)


def _meaningful_tokens(phrases: list[str]) -> list[str]:
    tokens: list[str] = []
    for phrase in phrases:
        for token in re.findall(r"[a-z0-9]+", phrase.lower()):
            if len(token) >= 4 and token not in STOPWORDS:
                tokens.append(token)
    return _dedupe(tokens)


def _add_evidence(
    evidence: list[dict[str, Any]],
    category: str,
    source: str,
    matches: list[str],
    points: int,
) -> None:
    if not matches:
        return
    evidence.append({
        "category": category,
        "source": source,
        "matches": matches[:8],
        "points": points,
    })
