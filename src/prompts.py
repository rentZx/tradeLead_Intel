KEYWORD_PROMPT = """你是B2B外贸获客策略助手。
请根据产品资料生成英语、俄语、阿语、法语关键词，覆盖：
1. 产品通用名
2. 采购商类型
3. 进口商/批发商/经销商表达
4. 目标国家本地搜索组合
5. 风险或合规需要人工复核的提示

产品资料：
{product}

目标国家/地区：
{countries}

请用JSON结构输出，字段为 en, ru, ar, fr, compliance_notes。
"""

DUE_DILIGENCE_PROMPT = """你是B2B公司背调分析助手。
只基于用户提供的公开信息进行基础判断，不编造事实，不给规避制裁、出口管制或报关监管的建议。

公司资料：
{company}

产品资料：
{product}

网页/公开文本：
{public_text}

请输出：
1. 公司真实性
2. 业务匹配度
3. 采购可能性
4. 联系可达性
5. 合规风险
6. 证据摘要
7. 人工复核建议
"""

OUTREACH_PROMPT = """你是合规的B2B外贸开发信助手。
请根据客户和产品资料生成{language}开发信、WhatsApp开场白、两次跟进话术。
要求：
- 不夸大库存、认证、价格、交期
- 不自动承诺交易、报价、合同或收款
- 对机床、工业设备、二手设备、高精度设备保留人工合规复核提醒
- 语气简洁、真实、适合人工确认后发送

客户资料：
{company}

产品资料：
{product}
"""


def deterministic_keywords(product_name: str, countries: str) -> dict[str, list[str]]:
    base = product_name.strip() or "product"
    country_bits = [c.strip() for c in countries.replace("，", ",").split(",") if c.strip()]
    suffixes = country_bits or ["target market"]
    return {
        "en": [f"{base} importer", f"{base} distributor", f"{base} wholesale supplier"] + [f"{base} buyers {c}" for c in suffixes],
        "ru": [f"{base} импортер", f"{base} дистрибьютор", f"{base} оптом"],
        "ar": [f"{base} مستورد", f"{base} موزع", f"{base} جملة"],
        "fr": [f"{base} importateur", f"{base} distributeur", f"{base} grossiste"],
        "compliance_notes": ["外部联系前人工确认客户、最终用途、付款路径和出口申报信息。"],
    }


def generate_outreach(language: str, company_name: str, product_name: str) -> dict[str, str]:
    subject_map = {
        "英语": f"Supply inquiry: {product_name}",
        "俄语": f"Предложение по товару: {product_name}",
        "阿语": f"استفسار توريد: {product_name}",
        "法语": f"Proposition fournisseur: {product_name}",
    }
    subject = subject_map.get(language, f"Supply inquiry: {product_name}")
    body = (
        f"Hello {company_name},\n\n"
        f"We are organizing local supply resources for {product_name}. "
        "If this product matches your purchasing scope, I can share basic specifications, photos, and availability after manual confirmation.\n\n"
        "Before any quotation or shipment discussion, we will confirm product details, end use, and export compliance requirements.\n\n"
        "Best regards"
    )
    return {
        "email_subject": subject,
        "email_body": body,
        "whatsapp_message": f"Hello, this is about {product_name}. May I confirm whether your company imports or distributes this category?",
        "followup_1": "Just checking whether this product category is relevant to your current sourcing plan.",
        "followup_2": "If useful, I can send photos/specifications after confirming the exact model and availability.",
        "quote_followup": "Quotation should be confirmed manually after checking specification, stock, packing, logistics, and compliance.",
    }
