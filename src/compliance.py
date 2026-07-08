from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

import pandas as pd
from rapidfuzz import fuzz

from src.db import execute, query_df, update
from src.risk import detect_risk_keywords
from src.search import log_task

HIGH_RISK_STATUS = "风险池"

DEFAULT_RISK_KEYWORDS = [
    ("sanction", "en", "制裁", "critical", "Sanctions or sanctions-list related wording."),
    ("restricted party", "en", "制裁", "critical", "Restricted party wording."),
    ("blocked person", "en", "制裁", "critical", "Blocked person or entity."),
    ("sdn", "en", "制裁", "critical", "OFAC SDN related wording."),
    ("dual use", "en", "两用物项", "high", "Potential dual-use goods."),
    ("military", "en", "军工", "critical", "Military or defense use."),
    ("defense", "en", "军工", "critical", "Defense sector wording."),
    ("weapon", "en", "军工", "critical", "Weapon-related wording."),
    ("missile", "en", "军工", "critical", "Missile-related wording."),
    ("drone", "en", "敏感用途", "high", "Drone-related use."),
    ("uav", "en", "敏感用途", "high", "UAV-related use."),
    ("nuclear", "en", "高敏感用途", "critical", "Nuclear-related wording."),
    ("chemical weapon", "en", "高敏感用途", "critical", "Chemical weapons wording."),
    ("third country transshipment", "en", "转运", "high", "Third-country transshipment risk."),
    ("false declaration", "en", "报关", "critical", "False customs declaration."),
    ("制裁", "zh", "制裁", "critical", "制裁相关表达。"),
    ("受限主体", "zh", "制裁", "critical", "受限制公司或个人。"),
    ("特别指定国民", "zh", "制裁", "critical", "OFAC SDN 相关表达。"),
    ("军工", "zh", "军工", "critical", "军工用途。"),
    ("国防", "zh", "军工", "critical", "国防相关用途。"),
    ("武器", "zh", "军工", "critical", "武器相关。"),
    ("导弹", "zh", "军工", "critical", "导弹相关。"),
    ("无人机", "zh", "敏感用途", "high", "无人机相关用途。"),
    ("两用物项", "zh", "两用物项", "high", "军民两用物项。"),
    ("最终用户异常", "zh", "最终用户", "high", "最终用户不清晰或异常。"),
    ("第三国转运", "zh", "转运", "high", "第三国转运。"),
    ("虚假报关", "zh", "报关", "critical", "虚假申报或报关风险。"),
    ("规避监管", "zh", "合规规避", "critical", "规避监管表达。"),
]


@dataclass
class SanctionsMatch:
    company_id: int
    company_name: str
    entity_id: int
    entity_name: str
    source: str
    score: float
    match_type: str
    reason: str


def seed_enhanced_risk_keywords() -> int:
    inserted = 0
    existing = {
        str(row.keyword).lower()
        for row in query_df("SELECT keyword FROM risk_keywords").itertuples(index=False)
    }
    for keyword, language, category, risk_level, description in DEFAULT_RISK_KEYWORDS:
        if keyword.lower() in existing:
            continue
        execute(
            """
            INSERT INTO risk_keywords(keyword, language, category, risk_level, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            (keyword, language, category, risk_level, description),
        )
        inserted += 1
    return inserted


def import_sanctions_csv(df: pd.DataFrame, source_default: str = "CSV") -> int:
    normalized = normalize_sanctions_dataframe(df)
    count = 0
    for row in normalized.to_dict(orient="records"):
        if not row["entity_name"]:
            continue
        execute(
            """
            INSERT INTO sanctions_entities(source, entity_name, aliases, country, address, entity_type, program, remarks, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row.get("source") or source_default,
                row["entity_name"],
                row.get("aliases"),
                row.get("country"),
                row.get("address"),
                row.get("entity_type"),
                row.get("program"),
                row.get("remarks"),
                json.dumps(row, ensure_ascii=False),
            ),
        )
        count += 1
    log_task(None, "compliance_import", "Completed", f"Imported {count} sanctions entities from CSV")
    return count


def screen_companies(threshold: int = 88, include_keyword_screen: bool = True) -> dict[str, int]:
    companies = query_df(
        """
        SELECT id, company_name, country, website, email, phone, whatsapp, telegram,
               business_summary, source_url, source_domain, risk_status
        FROM companies
        ORDER BY id DESC
        """
    )
    sanctions = query_df("SELECT id, source, entity_name, aliases, country, remarks FROM sanctions_entities")
    matches: list[SanctionsMatch] = []
    keyword_flagged = 0
    for company in companies.itertuples(index=False):
        company_text = " ".join(str(getattr(company, field) or "") for field in company._fields)
        company_matches = match_company_against_sanctions(company, sanctions, threshold)
        if company_matches:
            matches.extend(company_matches)
            mark_company_risk_pool(
                int(company.id),
                "制裁名单模糊匹配",
                "; ".join(f"{m.entity_name}({m.score:.0f})" for m in company_matches[:3]),
            )
        elif include_keyword_screen:
            hits = detect_risk_keywords(company_text)
            high_hits = [hit for hit in hits if hit.level in {"critical", "high"}]
            if high_hits:
                keyword_flagged += 1
                mark_company_risk_pool(
                    int(company.id),
                    "高风险关键词命中",
                    "; ".join(f"{hit.keyword}/{hit.category}/{hit.level}" for hit in high_hits[:6]),
                )

    log_task(
        None,
        "compliance_screen",
        "Completed",
        f"Screened {len(companies)} companies, sanctions_matches={len(matches)}, keyword_flagged={keyword_flagged}",
    )
    return {
        "screened": int(len(companies)),
        "sanctions_matches": len(matches),
        "keyword_flagged": keyword_flagged,
        "risk_pool": count_risk_pool(),
    }


def match_company_against_sanctions(company: Any, sanctions: pd.DataFrame, threshold: int) -> list[SanctionsMatch]:
    company_name = str(company.company_name or "")
    company_norm = normalize_name(company_name)
    if not company_norm or sanctions.empty:
        return []
    matches: list[SanctionsMatch] = []
    for row in sanctions.itertuples(index=False):
        names = [str(row.entity_name or "")]
        names.extend(split_aliases(str(row.aliases or "")))
        best_score = 0.0
        best_name = ""
        for candidate in names:
            candidate_norm = normalize_name(candidate)
            if not candidate_norm:
                continue
            score = max(
                fuzz.token_set_ratio(company_norm, candidate_norm),
                fuzz.WRatio(company_norm, candidate_norm),
            )
            if score > best_score:
                best_score = float(score)
                best_name = candidate
        country_bonus = 3 if company.country and row.country and str(company.country).lower() in str(row.country).lower() else 0
        final_score = min(100.0, best_score + country_bonus)
        if final_score >= threshold:
            matches.append(
                SanctionsMatch(
                    company_id=int(company.id),
                    company_name=company_name,
                    entity_id=int(row.id),
                    entity_name=str(row.entity_name or best_name),
                    source=str(row.source or ""),
                    score=final_score,
                    match_type="name_fuzzy",
                    reason=f"Company name matched sanctions entity/alias '{best_name}' with score {final_score:.1f}.",
                )
            )
    return sorted(matches, key=lambda item: item.score, reverse=True)


def mark_company_risk_pool(company_id: int, reason: str, detail: str) -> None:
    update(
        """
        UPDATE companies
        SET risk_status = ?, lead_status = ?, business_summary = COALESCE(NULLIF(business_summary, ''), ?),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (HIGH_RISK_STATUS, HIGH_RISK_STATUS, f"{reason}: {detail}", company_id),
    )


def risk_pool_df() -> pd.DataFrame:
    return query_df(
        """
        SELECT id, company_name, country, website, email, phone, whatsapp, telegram,
               risk_status, lead_status, business_summary, updated_at
        FROM companies
        WHERE risk_status = ? OR lead_status = ?
        ORDER BY updated_at DESC, id DESC
        """,
        (HIGH_RISK_STATUS, HIGH_RISK_STATUS),
    )


def sanctions_entities_df() -> pd.DataFrame:
    return query_df(
        """
        SELECT id, source, entity_name, aliases, country, entity_type, program, remarks, imported_at
        FROM sanctions_entities
        ORDER BY id DESC
        LIMIT 1000
        """
    )


def normalize_sanctions_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    column_map = {clean_col(col): col for col in df.columns}

    def pick(*names: str) -> pd.Series:
        for name in names:
            key = clean_col(name)
            if key in column_map:
                return df[column_map[key]].fillna("").astype(str)
        return pd.Series([""] * len(df))

    normalized = pd.DataFrame(
        {
            "source": pick("source", "list", "program source"),
            "entity_name": pick("entity_name", "name", "sdn_name", "primary_name", "full_name", "名称", "姓名", "实体名称"),
            "aliases": pick("aliases", "alias", "aka", "weak_alias", "别名"),
            "country": pick("country", "countries", "nationality", "国家"),
            "address": pick("address", "addresses", "地址"),
            "entity_type": pick("entity_type", "type", "sdn_type", "类型"),
            "program": pick("program", "programs", "sanctions_program", "制裁项目"),
            "remarks": pick("remarks", "comment", "comments", "note", "notes", "备注"),
        }
    )
    normalized["entity_name"] = normalized["entity_name"].map(lambda item: str(item).strip())
    return normalized


def clean_col(value: object) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", str(value).strip().lower())


def normalize_name(value: str) -> str:
    value = re.sub(r"[\W_]+", " ", value.lower(), flags=re.UNICODE)
    stop_words = {"llc", "ltd", "limited", "inc", "co", "company", "corp", "corporation", "ooo", "too", "gmbh", "sa"}
    tokens = [token for token in value.split() if token not in stop_words]
    return " ".join(tokens)


def split_aliases(value: str) -> list[str]:
    if not value:
        return []
    parts = re.split(r"[;|,/]\s*|\n+", value)
    return [part.strip() for part in parts if part.strip()]


def count_risk_pool() -> int:
    return int(query_df("SELECT COUNT(*) AS n FROM companies WHERE risk_status = ? OR lead_status = ?", (HIGH_RISK_STATUS, HIGH_RISK_STATUS)).iloc[0]["n"])
