from __future__ import annotations

from dataclasses import dataclass

from src.db import query_df


@dataclass
class RiskHit:
    keyword: str
    category: str
    level: str
    description: str


def detect_risk_keywords(text: str) -> list[RiskHit]:
    """Detect compliance risk hints from user-provided public text."""
    if not text:
        return []
    lowered = text.lower()
    keywords = query_df("SELECT keyword, category, risk_level, description FROM risk_keywords")
    hits: list[RiskHit] = []
    for row in keywords.itertuples(index=False):
        if str(row.keyword).lower() in lowered:
            hits.append(
                RiskHit(
                    keyword=row.keyword,
                    category=row.category or "未分类",
                    level=row.risk_level or "medium",
                    description=row.description or "",
                )
            )
    return hits


def risk_penalty(hits: list[RiskHit]) -> int:
    weight = {"critical": 30, "high": 18, "medium": 8, "low": 3}
    return min(30, sum(weight.get(hit.level, 5) for hit in hits))


def format_risk_hits(hits: list[RiskHit]) -> str:
    if not hits:
        return "未发现内置风险关键词。仍需人工复核制裁、出口管制、最终用途和最终用户。"
    return "\n".join(
        f"- [{hit.level}] {hit.keyword} / {hit.category}: {hit.description}" for hit in hits
    )
