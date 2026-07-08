from __future__ import annotations

from src.risk import RiskHit, risk_penalty


def calculate_score(
    business_match: int,
    purchase_probability: int,
    authenticity: int,
    contactability: int,
    risk_hits: list[RiskHit],
) -> dict[str, int | str]:
    """PRD scoring model: 30 + 20 + 20 + 15 - risk penalty."""
    business_match = clamp(business_match, 0, 30)
    purchase_probability = clamp(purchase_probability, 0, 20)
    authenticity = clamp(authenticity, 0, 20)
    contactability = clamp(contactability, 0, 15)
    penalty = risk_penalty(risk_hits)
    final_score = max(0, business_match + purchase_probability + authenticity + contactability - penalty)
    return {
        "business_match_score": business_match,
        "purchase_probability_score": purchase_probability,
        "authenticity_score": authenticity,
        "contactability_score": contactability,
        "risk_score": penalty,
        "final_score": final_score,
        "final_grade": grade(final_score, penalty),
    }


def grade(score: int, penalty: int) -> str:
    if penalty >= 30:
        return "D"
    if score >= 75:
        return "A"
    if score >= 60:
        return "B"
    if score >= 45:
        return "C"
    return "D"


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, int(value)))
