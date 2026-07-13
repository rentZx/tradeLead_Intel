"""
TradeLead V3.0 — Outreach Generator
Multi-language email templates + landing page HTML.
All pre-configured, zero user input needed.
"""

from __future__ import annotations

from src.market_data import COUNTRY_LANGUAGES

# ═══════════════════════════════════════════════════════════
#  Email Templates (keyed by language + type)
# ═══════════════════════════════════════════════════════════

EMAIL_TEMPLATES: dict[str, dict] = {
    "en": {
        "first_contact": {
            "subject": "{product_name_en} — Quality Supplier from China",
            "body": """Dear {contact_name},

Greetings from {sender_company}!

We are a professional manufacturer of **{product_name_en}** based in China, with over 10 years of export experience.

**Product Highlights:**
- {product_name_en}
- Material: {material}
- Specifications: {specifications}
- FOB Price: ${fob_price}/pc
- MOQ: {moq}

Our products are exported to over 20 countries across the Middle East, Africa, and Southeast Asia. We are looking for reliable partners in {country}.

We would be happy to send you samples, catalogs, and a competitive quotation. Please let us know your requirements.

Best regards,
{sender_name}
{sender_company}
Email: {sender_email}
Phone/WhatsApp: {sender_phone}""",
            "whatsapp": """Hello {contact_name}, this is {sender_name} from {sender_company}. We manufacture {product_name_en} (FOB ${fob_price}/pc, MOQ {moq}). We export to 20+ countries and are looking for partners in {country}. Would you be interested in a quotation? Thanks!""",
        },
        "quote": {
            "subject": "Quotation for {product_name_en} — {sender_company}",
            "body": """Dear {contact_name},

Thank you for your interest in our **{product_name_en}**. Please find our quotation below:

| Item | Details |
|------|---------|
| Product | {product_name_en} |
| Material | {material} |
| Specifications | {specifications} |
| FOB Price | ${fob_price}/pc |
| MOQ | {moq} |
| Packaging | Standard export carton |
| Lead Time | 15-25 days after order confirmation |
| Payment Terms | T/T, L/C at sight |

Shipping to {country} is available via sea freight. We can also arrange air freight for samples.

Please let us know your target quantity so we can provide a more accurate offer.

Best regards,
{sender_name}
{sender_company}
Email: {sender_email}
Phone/WhatsApp: {sender_phone}""",
            "whatsapp": """Hi {contact_name}, here's the quotation for {product_name_en}: FOB ${fob_price}/pc, MOQ {moq}, lead time 15-25 days. Shipping to {country} via sea freight. Let me know your quantity for a precise offer. Thanks!""",
        },
        "followup": {
            "subject": "Following up — {product_name_en}",
            "body": """Dear {contact_name},

I hope this message finds you well. I wanted to follow up on our previous communication regarding **{product_name_en}**.

We have recently updated our product line and can now offer even more competitive pricing. Our latest FOB price is ${fob_price}/pc with MOQ of {moq}.

If you have any questions or would like to see samples, please don't hesitate to reach out. We are happy to provide a customized quotation based on your requirements.

Looking forward to hearing from you.

Best regards,
{sender_name}
{sender_company}
Email: {sender_email}
Phone/WhatsApp: {sender_phone}""",
            "whatsapp": """Hi {contact_name}, just following up on our {product_name_en} offer (FOB ${fob_price}/pc). We've updated our pricing — would you like an updated quotation? Let me know!""",
        },
    },
    "ar": {
        "first_contact": {
            "subject": "{product_name_en} — مورد عالي الجودة من الصين",
            "body": """عزيزي {contact_name},

تحية طيبة من {sender_company}!

نحن شركة متخصصة في تصنيع **{product_name_en}** في الصين، مع أكثر من 10 سنوات من الخبرة في التصدير.

**مميزات المنتج:**
- {product_name_en}
- الخامة: {material}
- المواصفات: {specifications}
- سعر FOB: ${fob_price}/قطعة
- الحد الأدنى للطلب: {moq}

نصدر منتجاتنا إلى أكثر من 20 دولة في الشرق الأوسط وأفريقيا وجنوب شرق آسيا. نبحث عن شركاء موثوقين في {country}.

يسعدنا إرسال عينات وكتالوجات وعرض أسعار تنافسي. يرجى إعلامنا بمتطلباتكم.

مع أطيب التحيات،
{sender_name}
{sender_company}
البريد: {sender_email}
هاتف/واتساب: {sender_phone}""",
            "whatsapp": """مرحباً {contact_name}، أنا {sender_name} من {sender_company}. نصنع {product_name_en} (سعر FOB ${fob_price}/قطعة، الحد الأدنى {moq}). نصدر لأكثر من 20 دولة. هل أنت مهتم بعرض سعر؟ شكراً!""",
        },
    },
    "ru": {
        "first_contact": {
            "subject": "{product_name_en} — Качественный поставщик из Китая",
            "body": """Уважаемый(ая) {contact_name},

Приветствуем вас от компании {sender_company}!

Мы являемся профессиональным производителем **{product_name_en}** в Китае с более чем 10-летним опытом экспорта.

**Характеристики продукта:**
- {product_name_en}
- Материал: {material}
- Спецификации: {specifications}
- Цена FOB: ${fob_price}/шт
- Минимальный заказ: {moq}

Наша продукция экспортируется в более чем 20 стран Ближнего Востока, Африки и Юго-Восточной Азии. Мы ищем надежных партнеров в {country}.

Будем рады отправить образцы, каталоги и конкурентоспособное предложение. Сообщите нам ваши требования.

С уважением,
{sender_name}
{sender_company}
Email: {sender_email}
Тел/WhatsApp: {sender_phone}""",
            "whatsapp": """Здравствуйте {contact_name}, это {sender_name} из {sender_company}. Мы производим {product_name_en} (FOB ${fob_price}/шт, мин. заказ {moq}). Экспортируем в 20+ стран. Интересует предложение? Спасибо!""",
        },
    },
    "fr": {
        "first_contact": {
            "subject": "{product_name_en} — Fournisseur de qualité de Chine",
            "body": """Cher {contact_name},

Salutations de {sender_company}!

Nous sommes un fabricant professionnel de **{product_name_en}** basé en Chine, avec plus de 10 ans d'expérience à l'exportation.

**Points forts du produit:**
- {product_name_en}
- Matériau: {material}
- Spécifications: {specifications}
- Prix FOB: ${fob_price}/pc
- Quantité minimum: {moq}

Nos produits sont exportés vers plus de 20 pays au Moyen-Orient, en Afrique et en Asie du Sud-Est. Nous recherchons des partenaires fiables en {country}.

Nous serions heureux de vous envoyer des échantillons, catalogues et un devis compétitif. Veuillez nous faire part de vos besoins.

Cordialement,
{sender_name}
{sender_company}
Email: {sender_email}
Tél/WhatsApp: {sender_phone}""",
            "whatsapp": """Bonjour {contact_name}, je suis {sender_name} de {sender_company}. Nous fabriquons {product_name_en} (FOB ${fob_price}/pc, MOQ {moq}). Nous exportons vers 20+ pays. Souhaitez-vous un devis? Merci!""",
        },
    },
    "es": {
        "first_contact": {
            "subject": "{product_name_en} — Proveedor de calidad de China",
            "body": """Estimado(a) {contact_name},

Saludos de {sender_company}!

Somos un fabricante profesional de **{product_name_en}** con sede en China, con más de 10 años de experiencia en exportación.

**Destacados del producto:**
- {product_name_en}
- Material: {material}
- Especificaciones: {specifications}
- Precio FOB: ${fob_price}/pc
- Cantidad mínima: {moq}

Nuestros productos se exportan a más de 20 países en Medio Oriente, África y el Sudeste Asiático. Buscamos socios confiables en {country}.

Estaremos encantados de enviarle muestras, catálogos y una cotización competitiva. Por favor, háganos saber sus requisitos.

Saludos cordiales,
{sender_name}
{sender_company}
Email: {sender_email}
Tel/WhatsApp: {sender_phone}""",
            "whatsapp": """Hola {contact_name}, soy {sender_name} de {sender_company}. Fabricamos {product_name_en} (FOB ${fob_price}/pc, MOQ {moq}). Exportamos a 20+ países. ¿Le interesaría una cotización? ¡Gracias!""",
        },
    },
    "pt": {
        "first_contact": {
            "subject": "{product_name_en} — Fornecedor de qualidade da China",
            "body": """Prezado(a) {contact_name},

Saudações da {sender_company}!

Somos um fabricante profissional de **{product_name_en}** sediado na China, com mais de 10 anos de experiência em exportação.

**Destaques do produto:**
- {product_name_en}
- Material: {material}
- Especificações: {specifications}
- Preço FOB: ${fob_price}/pc
- Quantidade mínima: {moq}

Nossos produtos são exportados para mais de 20 países no Oriente Médio, África e Sudeste Asiático. Buscamos parceiros confiáveis em {country}.

Teremos prazer em enviar amostras, catálogos e uma cotação competitiva. Por favor, informe-nos suas necessidades.

Atenciosamente,
{sender_name}
{sender_company}
Email: {sender_email}
Tel/WhatsApp: {sender_phone}""",
            "whatsapp": """Olá {contact_name}, sou {sender_name} da {sender_company}. Fabricamos {product_name_en} (FOB ${fob_price}/pc, MOQ {moq}). Exportamos para 20+ países. Gostaria de uma cotação? Obrigado!""",
        },
    },
}


# ═══════════════════════════════════════════════════════════
#  Template filling functions
# ═══════════════════════════════════════════════════════════

def get_template(language: str, template_type: str = "first_contact") -> dict:
    """Get email template for a language and type."""
    lang_templates = EMAIL_TEMPLATES.get(language, EMAIL_TEMPLATES["en"])
    return lang_templates.get(template_type, lang_templates.get("first_contact", {}))


def fill_template(template: dict, context: dict) -> dict:
    """Fill template placeholders with actual data."""
    subject = template.get("subject", "").format(**context)
    body = template.get("body", "").format(**context)
    whatsapp = template.get("whatsapp", "").format(**context)
    return {"subject": subject, "body": body, "whatsapp": whatsapp}


def generate_outreach(
    product: dict,
    lead: dict,
    company_name: str | None = None,
    sender_name: str | None = None,
    sender_phone: str | None = None,
    language: str | None = None,
    template_type: str = "first_contact",
) -> dict:
    """
    Generate personalized outreach email and WhatsApp message.

    Args:
        product: Product dict from DB
        lead: Lead dict from DB
        language: 'en'/'ar'/'ru'/'fr'/'es'/'pt', auto-detected if None
        template_type: 'first_contact'/'quote'/'followup'
    """
    # Auto-detect language from country
    if language is None:
        country = lead.get("country", "")
        language = COUNTRY_LANGUAGES.get(country, "en")

    # Get sender info from settings or defaults
    from src.db_v3 import get_setting
    if sender_name is None:
        sender_name = get_setting("sender_name") or "Sales Manager"
    if company_name is None:
        company_name = get_setting("sender_company") or "Your Company Name"
    if sender_phone is None:
        sender_phone = get_setting("sender_phone") or ""

    # Build context
    context = {
        "contact_name": lead.get("company_name", "Sir/Madam"),
        "sender_name": sender_name,
        "sender_company": company_name,
        "sender_email": get_setting("sender_email") or "",
        "sender_phone": sender_phone,
        "product_name_en": product.get("product_name_en", ""),
        "product_name_cn": product.get("product_name_cn", ""),
        "material": product.get("material", "N/A"),
        "specifications": product.get("specifications", "N/A"),
        "fob_price": product.get("fob_price", "TBD"),
        "moq": product.get("moq", "TBD"),
        "country": lead.get("country", "your country"),
        "category": product.get("category", ""),
    }

    template = get_template(language, template_type)
    return fill_template(template, context)


# ═══════════════════════════════════════════════════════════
#  Landing Page Generator
# ═══════════════════════════════════════════════════════════

def generate_landing_page(product: dict, language: str = "en") -> str:
    """
    Generate a simple one-page product landing page in HTML.
    User can download and host anywhere (GitHub Pages, Netlify, etc.)
    """
    labels = {
        "en": {"title": "Product", "specs": "Specifications", "price": "Price",
               "moq": "MOQ", "contact": "Contact Us", "desc": "Description",
               "material": "Material"},
        "ar": {"title": "المنتج", "specs": "المواصفات", "price": "السعر",
               "moq": "الحد الأدنى للطلب", "contact": "اتصل بنا", "desc": "الوصف",
               "material": "الخامة"},
        "ru": {"title": "Продукт", "specs": "Характеристики", "price": "Цена",
               "moq": "Мин. заказ", "contact": "Свяжитесь с нами", "desc": "Описание",
               "material": "Материал"},
        "fr": {"title": "Produit", "specs": "Spécifications", "price": "Prix",
               "moq": "Quantité min.", "contact": "Contactez-nous", "desc": "Description",
               "material": "Matériau"},
        "es": {"title": "Producto", "specs": "Especificaciones", "price": "Precio",
               "moq": "Cantidad mín.", "contact": "Contáctenos", "desc": "Descripción",
               "material": "Material"},
    }
    lbl = labels.get(language, labels["en"])

    desc_key = "description_en" if language in ("en", "ar", "ru", "fr", "es") else "description_en"
    product_name = product.get("product_name_en", "") if language in ("en", "ar", "ru", "fr", "es") else product.get("product_name_cn", "")

    html = f"""<!DOCTYPE html>
<html lang="{language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{product_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
        header {{ text-align: center; padding: 40px 0; border-bottom: 2px solid #2563eb; margin-bottom: 30px; }}
        h1 {{ color: #2563eb; font-size: 2em; margin-bottom: 10px; }}
        .product-img {{ max-width: 100%; height: auto; border-radius: 8px; margin: 20px 0; }}
        .section {{ margin: 25px 0; padding: 20px; background: #f8fafc; border-radius: 8px; }}
        .section h2 {{ color: #1e40af; margin-bottom: 10px; font-size: 1.3em; }}
        .spec-item {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e2e8f0; }}
        .spec-label {{ font-weight: 600; color: #64748b; }}
        .price-tag {{ font-size: 1.5em; color: #16a34a; font-weight: bold; }}
        .contact-box {{ background: #2563eb; color: white; padding: 20px; border-radius: 8px; text-align: center; margin: 30px 0; }}
        .contact-box a {{ color: #fbbf24; }}
        footer {{ text-align: center; color: #94a3b8; padding: 20px; font-size: 0.9em; }}
    </style>
</head>
<body>
    <header>
        <h1>{product_name}</h1>
        <p>{lbl['title']}: {product.get("category", "")} {"> " + product.get("sub_category", "") if product.get("sub_category") else ""}</p>
    </header>

    <div class="section">
        <h2>{lbl['desc']}</h2>
        <p>{product.get(desc_key, "")}</p>
    </div>

    <div class="section">
        <h2>{lbl['specs']}</h2>
        <div class="spec-item"><span class="spec-label">{lbl['material']}</span><span>{product.get("material", "N/A")}</span></div>
        <div class="spec-item"><span class="spec-label">{lbl['specs']}</span><span>{product.get("specifications", "N/A")}</span></div>
        <div class="spec-item"><span class="spec-label">{lbl['price']}</span><span class="price-tag">${product.get("fob_price", "N/A")}/pc</span></div>
        <div class="spec-item"><span class="spec-label">{lbl['moq']}</span><span>{product.get("moq", "N/A")}</span></div>
    </div>

    <div class="contact-box">
        <h2>{lbl['contact']}</h2>
        <p>Email: {company_email}</p>
        <p>WhatsApp: {company_whatsapp}</p>
    </div>

    <footer>
        <p>&copy; 2026. Powered by TradeLead Intel.</p>
    </footer>
</body>
</html>"""

    return html
