from __future__ import annotations

from datetime import date, timedelta

from src.db import execute, query_df, update

DEMO_MARK = "DEMO_DATA"
DEMO_WARNING = "演示数据，不可用于真实联系"
DEMO_SANCTIONS_SOURCE = "DEMO_SANCTIONS"


PRODUCTS = [
    ("塑料收纳箱", "Plastic Storage Box", "пластиковый контейнер", "صندوق تخزين بلاستيكي", "Boite de rangement plastique", "塑料制品", "收纳用品", "PP材质，多规格，适合批发和商超渠道。", "PP plastic storage box for wholesale and retail channels.", "PP; 10L/25L/50L; custom color", "PP", "全新", "PSB-25", "Wenan Demo", "500 pcs", 1.8, 3.2),
    ("厨房塑料用品套装", "Kitchen Plasticware Set", "кухонные пластиковые изделия", "أدوات مطبخ بلاستيكية", "Articles de cuisine en plastique", "塑料制品", "厨房用品", "厨房收纳、沥水、食品盒组合。", "Kitchen plasticware set for distributors.", "Food-grade PP; 12-piece set", "PP", "全新", "KPS-12", "Wenan Demo", "300 sets", 2.5, 4.6),
    ("园艺塑料水壶", "Plastic Garden Watering Can", "пластиковая лейка", "إبريق ري بلاستيكي", "Arrosoir plastique", "塑料制品", "园艺用品", "轻便园艺浇水壶，适合商超和五金渠道。", "Light plastic watering can for garden retail.", "3L/5L/8L; HDPE", "HDPE", "全新", "PGW-5", "Wenan Demo", "600 pcs", 1.2, 2.4),
    ("车载塑料工具盒", "Plastic Car Tool Box", "пластиковый ящик для инструментов", "صندوق أدوات بلاستيكي", "Boite a outils plastique", "塑料制品", "工具收纳", "车载和五金工具收纳盒。", "Plastic tool box for auto and hardware channels.", "ABS/PP; reinforced handle", "ABS/PP", "全新", "PCT-18", "Wenan Demo", "400 pcs", 3.8, 6.9),
    ("普通二手车床", "Used Conventional Lathe", "токарный станок б/у", "مخرطة مستعملة", "Tour conventionnel d'occasion", "普通二手机床", "车床", "普通二手车床，需人工核查设备参数和出口合规。", "Used conventional lathe, manual compliance review required.", "Swing 400mm; distance 1000mm", "Cast iron", "二手", "CW6140", "Demo Machine", "1 set", 2800, 4200),
    ("普通二手铣床", "Used Milling Machine", "фрезерный станок б/у", "آلة تفريز مستعملة", "Fraiseuse d'occasion", "普通二手机床", "铣床", "普通二手铣床，适合维修厂和加工厂询盘测试。", "Used milling machine for repair workshops and metalworking buyers.", "Table 320x1250mm; manual type", "Cast iron", "二手", "X6132", "Demo Machine", "1 set", 3200, 4800),
    ("普通二手钻床", "Used Drilling Machine", "сверлильный станок б/у", "آلة حفر مستعملة", "Perceuse industrielle d'occasion", "普通二手机床", "钻床", "普通二手钻床，参数需人工确认。", "Used drilling machine with manual parameter confirmation.", "Z3050; radial drilling", "Steel", "二手", "Z3050", "Demo Machine", "1 set", 1900, 3100),
    ("塑料破碎机", "Plastic Crusher", "дробилка для пластика", "كسارة بلاستيك", "Broyeur plastique", "塑料机械", "破碎机", "塑料回收破碎设备，适合再生塑料工厂。", "Plastic crusher for recycling factories.", "15kW; 500kg/h", "Steel", "全新", "PC-500", "Demo Plastic Machinery", "1 set", 2200, 3600),
    ("塑料拌料机", "Plastic Mixer", "смеситель пластика", "خلاط بلاستيك", "Melangeur plastique", "塑料机械", "拌料机", "塑料颗粒混料设备。", "Plastic material mixer for granules.", "100kg/batch; stainless tank", "Stainless steel", "全新", "PM-100", "Demo Plastic Machinery", "1 set", 800, 1450),
    ("塑料干燥机", "Plastic Hopper Dryer", "сушилка для пластика", "مجفف بلاستيك", "Secheur plastique", "塑料机械", "干燥机", "注塑辅机干燥设备。", "Plastic hopper dryer for injection molding auxiliary line.", "50kg; electric heating", "Steel", "全新", "PHD-50", "Demo Plastic Machinery", "1 set", 650, 1200),
]

COUNTRIES = ["俄罗斯", "哈萨克斯坦", "乌兹别克斯坦", "阿联酋", "埃及", "尼日利亚"]
COMPANY_TYPES = ["Importer", "Distributor", "Wholesaler", "Dealer", "Trading", "Industrial Supplier"]


def generate_demo_data() -> dict[str, int]:
    clear_demo_data()
    product_ids = create_products()
    company_ids = create_companies(product_ids)
    sanctions_count = create_sanctions()
    inquiries_count = create_inquiries(product_ids)
    interactions_count = create_interactions(company_ids, product_ids)
    return {
        "products": len(product_ids),
        "companies": len(company_ids),
        "sanctions_entities": sanctions_count,
        "inquiries": inquiries_count,
        "interactions": interactions_count,
    }


def clear_demo_data() -> dict[str, int]:
    counts = {
        "interactions": count("interactions", "notes LIKE ?", (f"%{DEMO_MARK}%",)),
        "inquiries": count("inquiries", "source_page LIKE ?", ("demo://%",)),
        "sanctions_entities": count("sanctions_entities", "source = ?", (DEMO_SANCTIONS_SOURCE,)),
        "companies": count("companies", "source_type = ?", ("demo",)),
        "products": count("products", "supplier_name = ?", (DEMO_MARK,)),
    }
    update("DELETE FROM interactions WHERE notes LIKE ?", (f"%{DEMO_MARK}%",))
    update("DELETE FROM inquiries WHERE source_page LIKE ?", ("demo://%",))
    update("DELETE FROM sanctions_entities WHERE source = ?", (DEMO_SANCTIONS_SOURCE,))
    update("DELETE FROM companies WHERE source_type = ?", ("demo",))
    update("DELETE FROM products WHERE supplier_name = ?", (DEMO_MARK,))
    return counts


def demo_counts() -> dict[str, int]:
    return {
        "products": count("products", "supplier_name = ?", (DEMO_MARK,)),
        "companies": count("companies", "source_type = ?", ("demo",)),
        "sanctions_entities": count("sanctions_entities", "source = ?", (DEMO_SANCTIONS_SOURCE,)),
        "inquiries": count("inquiries", "source_page LIKE ?", ("demo://%",)),
        "interactions": count("interactions", "notes LIKE ?", (f"%{DEMO_MARK}%",)),
    }


def create_products() -> list[int]:
    ids = []
    for item in PRODUCTS:
        ids.append(
            execute(
                """
                INSERT INTO products(
                    product_name_cn, product_name_en, product_name_ru, product_name_ar, product_name_fr,
                    category, sub_category, description_cn, description_en, specifications, material,
                    condition, model, brand, moq, purchase_price, quote_price, currency,
                    supplier_name, supplier_contact, compliance_status, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (*item, "USD", DEMO_MARK, DEMO_WARNING, "演示数据", "在售"),
            )
        )
    return ids


def create_companies(product_ids: list[int]) -> list[int]:
    ids = []
    for idx in range(30):
        country = COUNTRIES[idx % len(COUNTRIES)]
        company_type = COMPANY_TYPES[idx % len(COMPANY_TYPES)]
        product_id = product_ids[idx % len(product_ids)]
        domain = f"demo-buyer-{idx+1:02d}.example.com"
        ids.append(
            execute(
                """
                INSERT INTO companies(
                    company_name, country, city, website, email, phone, whatsapp, telegram,
                    business_summary, source_url, source_type, related_product_id, match_keywords,
                    lead_status, risk_status, source_domain, extraction_confidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"Demo {country} {company_type} {idx+1:02d}",
                    country,
                    demo_city(country),
                    f"https://{domain}",
                    f"demo{idx+1:02d}@example.com",
                    f"+1000000{idx+1:03d}",
                    f"https://wa.me/1000000{idx+1:03d}",
                    f"https://t.me/demo_buyer_{idx+1:02d}",
                    f"{DEMO_WARNING}。用于测试{company_type}客户画像、背调、搜索导入和CRM流程。",
                    f"demo://company/{idx+1:02d}",
                    "demo",
                    product_id,
                    f"demo {company_type.lower()} import wholesale",
                    "演示线索",
                    "演示数据",
                    domain,
                    0.5,
                ),
            )
        )
    return ids


def create_sanctions() -> int:
    rows = [
        ("Demo Restricted Trading LLC", "DRT Demo; Demo Restricted Trading", "俄罗斯", "company", "DEMO-RISK", "演示制裁名单样本，用于测试模糊匹配"),
        ("Kazakh Demo Dual Use Supply", "KDD Supply", "哈萨克斯坦", "company", "DEMO-DUAL", "演示两用物项风险"),
        ("Uzbek Demo Military Parts", "UDMP", "乌兹别克斯坦", "company", "DEMO-MIL", "演示军工关键词风险"),
        ("Nile Demo Transshipment", "NDT Logistics", "埃及", "company", "DEMO-TRANS", "演示第三国转运风险"),
        ("Lagos Demo Blocked Buyer", "LDB Buyer", "尼日利亚", "company", "DEMO-BLOCK", "演示受限买家"),
    ]
    for entity_name, aliases, country, entity_type, program, remarks in rows:
        execute(
            """
            INSERT INTO sanctions_entities(source, entity_name, aliases, country, entity_type, program, remarks, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                DEMO_SANCTIONS_SOURCE,
                entity_name,
                aliases,
                country,
                entity_type,
                program,
                remarks,
                f"{DEMO_MARK}: {DEMO_WARNING}",
            ),
        )
    return len(rows)


def create_inquiries(product_ids: list[int]) -> int:
    for idx in range(5):
        product_id = product_ids[idx % len(product_ids)]
        execute(
            """
            INSERT INTO inquiries(product_id, company_name, contact_name, country, email, whatsapp, telegram,
                                  product_interest, quantity, message, source_page, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product_id,
                f"Demo Inquiry Buyer {idx+1}",
                f"Demo Contact {idx+1}",
                COUNTRIES[idx % len(COUNTRIES)],
                f"inquiry{idx+1}@example.com",
                f"+1999000{idx+1:03d}",
                f"@demo_inquiry_{idx+1}",
                "演示产品询盘",
                f"{(idx+1)*100} pcs",
                f"{DEMO_WARNING}。这是第 {idx+1} 条演示询盘。",
                f"demo://inquiry/{idx+1}",
                "New",
            ),
        )
    return 5


def create_interactions(company_ids: list[int], product_ids: list[int]) -> int:
    base = date.today()
    for idx in range(10):
        execute(
            """
            INSERT INTO interactions(company_id, product_id, contact_date, channel, content, customer_reply,
                                     result, next_followup_date, stage, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                company_ids[idx % len(company_ids)],
                product_ids[idx % len(product_ids)],
                str(base - timedelta(days=idx)),
                ["Email", "WhatsApp", "表单"][idx % 3],
                f"{DEMO_WARNING}。演示第 {idx+1} 次联系记录。",
                "演示回复：请发送产品规格和价格区间。",
                "演示跟进中",
                str(base + timedelta(days=idx + 1)),
                ["已联系", "已回复", "有意向"][idx % 3],
                f"{DEMO_MARK}; {DEMO_WARNING}",
            ),
        )
    return 10


def demo_city(country: str) -> str:
    return {
        "俄罗斯": "Moscow",
        "哈萨克斯坦": "Almaty",
        "乌兹别克斯坦": "Tashkent",
        "阿联酋": "Dubai",
        "埃及": "Cairo",
        "尼日利亚": "Lagos",
    }.get(country, "Demo City")


def count(table: str, where: str, params: tuple) -> int:
    return int(query_df(f"SELECT COUNT(*) AS n FROM {table} WHERE {where}", params).iloc[0]["n"])
