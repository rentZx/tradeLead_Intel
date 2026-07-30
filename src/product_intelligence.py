"""Offline-first product understanding for TradeLead V3."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re


@dataclass(frozen=True)
class ProductProfile:
    product_name_en: str
    category: str
    sub_category: str
    keywords_en: list[str]
    buyer_types: list[str]
    end_user_types: list[str]
    exclude_terms: list[str]
    reasoning: str

    def to_dict(self) -> dict:
        return asdict(self)


PRODUCT_RULES = [
    {
        "terms": ("保温钉", "保温锚栓", "外墙锚栓", "锚固钉", "insulation anchor", "eifs anchor"),
        "name_en": "Insulation Anchor",
        "category": "建筑五金",
        "sub_category": "保温锚固件",
        "keywords": [
            "insulation anchor", "EIFS anchor", "thermal insulation fixing",
            "insulation fixing dowel", "facade insulation fastener",
        ],
        "buyers": [
            "insulation materials distributor", "construction fasteners distributor",
            "facade systems supplier", "building materials importer",
            "building materials supplier", "hardware store",
        ],
        "end_users": [
            "EIFS contractor", "facade contractor",
            "thermal insulation contractor", "construction company",
        ],
        "exclude": ["nail salon", "beauty", "artificial nails"],
    },
    {
        "terms": ("膨胀螺栓", "膨胀锚栓", "expansion bolt", "wedge anchor"),
        "name_en": "Expansion Anchor",
        "category": "建筑五金",
        "sub_category": "建筑锚固件",
        "keywords": ["expansion anchor", "wedge anchor", "anchor bolt", "concrete fastener"],
        "buyers": [
            "hardware store", "fasteners distributor",
            "building materials supplier", "industrial supply company",
        ],
        "end_users": ["construction company", "MEP contractor", "steel structure contractor"],
        "exclude": [],
    },
    {
        "terms": ("塑料颗粒机", "造粒机", "plastic granulator", "pelletizing machine"),
        "name_en": "Plastic Pelletizing Machine",
        "category": "塑料机械",
        "sub_category": "塑料造粒设备",
        "keywords": ["plastic pelletizing machine", "plastic granulator", "recycling pelletizer"],
        "buyers": [
            "plastic machinery dealer", "recycling equipment supplier",
            "industrial equipment importer",
        ],
        "end_users": ["plastic recycling factory", "plastic products manufacturer"],
        "exclude": ["food pellet", "animal feed"],
    },
]

CATEGORY_FALLBACKS = {
    "建筑五金": [
        "hardware store", "building materials supplier",
        "construction supply company", "building materials importer",
    ],
    "塑料制品": [
        "plastic products distributor", "household goods wholesaler", "general trading company",
    ],
    "塑料机械": [
        "plastic machinery dealer", "industrial equipment importer",
        "recycling equipment supplier",
    ],
    "汽车配件": ["auto parts store", "vehicle spare parts distributor", "auto parts importer"],
}

CATEGORY_END_USERS = {
    "建筑五金": ["construction company", "building contractor", "installation contractor"],
    "塑料制品": ["retail chain", "household goods brand", "packaging company"],
    "塑料机械": ["plastic products manufacturer", "plastic recycling factory"],
    "汽车配件": ["auto repair workshop", "vehicle fleet operator", "car service chain"],
}


def analyze_product(
    product_name_cn: str,
    product_name_en: str = "",
    category: str = "",
    sub_category: str = "",
    description: str = "",
    keywords_en: str = "",
    buyer_types: str = "",
    end_user_types: str = "",
    exclude_terms: str = "",
) -> ProductProfile:
    """Infer a search-ready profile without requiring an external AI service."""
    source = " ".join(
        [product_name_cn, product_name_en, category, sub_category, description, keywords_en]
    ).lower()
    matched = next(
        (rule for rule in PRODUCT_RULES if any(term.lower() in source for term in rule["terms"])),
        None,
    )
    supplied_keywords = _split_terms(keywords_en)
    supplied_buyers = _split_terms(buyer_types)
    supplied_end_users = _split_terms(end_user_types)
    supplied_excludes = _split_terms(exclude_terms)
    if matched:
        final_category = category.strip() or matched["category"]
        final_sub_category = sub_category.strip() or matched["sub_category"]
        final_name_en = product_name_en.strip() or matched["name_en"]
        return ProductProfile(
            product_name_en=final_name_en,
            category=final_category,
            sub_category=final_sub_category,
            keywords_en=_dedupe(supplied_keywords + matched["keywords"]),
            buyer_types=_dedupe(
                supplied_buyers
                or (matched["buyers"] + CATEGORY_FALLBACKS.get(final_category, []))
            ),
            end_user_types=_dedupe(supplied_end_users or matched["end_users"]),
            exclude_terms=_dedupe(supplied_excludes or matched["exclude"]),
            reasoning=f"根据“{product_name_cn}”识别为{final_sub_category}，优先寻找经销渠道和工程采购方。",
        )

    final_category = category.strip() or "其他"
    fallback_keywords = supplied_keywords or ([product_name_en.strip()] if product_name_en.strip() else [])
    product_specific_buyers = []
    if product_name_en.strip():
        product_specific_buyers = [
            f"{product_name_en.strip()} distributor",
            f"{product_name_en.strip()} importer",
            f"{product_name_en.strip()} wholesaler",
        ]
    return ProductProfile(
        product_name_en=product_name_en.strip(),
        category=final_category,
        sub_category=sub_category.strip(),
        keywords_en=fallback_keywords,
        buyer_types=_dedupe(
            supplied_buyers
            or (
                product_specific_buyers
                + CATEGORY_FALLBACKS.get(
                    final_category,
                    ["distributor", "wholesaler", "importer", "trading company"],
                )
            )
        ),
        end_user_types=_dedupe(
            supplied_end_users or CATEGORY_END_USERS.get(final_category, [])
        ),
        exclude_terms=_dedupe(supplied_excludes),
        reasoning=(
            "未命中内置产品知识库，已根据英文产品名和品类生成产品专属经销渠道；"
            "建议在保存前复核经销渠道、终端需求方和排除词。"
        ),
    )


def _split_terms(value: str) -> list[str]:
    return [item.strip() for item in re.split(r"[,，;\n]+", value or "") if item.strip()]


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = value.strip().lower()
        if key and key not in seen:
            seen.add(key)
            result.append(value.strip())
    return result
