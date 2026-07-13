"""
TradeLead V3.0 — Market Data (Regions, Countries, Cities)
Pre-configured, zero user input needed.
"""

# 区域 → 国家映射
REGION_COUNTRIES: dict[str, list[tuple[str, str]]] = {
    "中东": [
        ("AE", "阿联酋"), ("SA", "沙特阿拉伯"), ("QA", "卡塔尔"),
        ("KW", "科威特"), ("OM", "阿曼"), ("TR", "土耳其"),
        ("IR", "伊朗"), ("IQ", "伊拉克"), ("JO", "约旦"),
        ("BH", "巴林"), ("LB", "黎巴嫩"),
    ],
    "非洲": [
        ("NG", "尼日利亚"), ("KE", "肯尼亚"), ("EG", "埃及"),
        ("ZA", "南非"), ("MA", "摩洛哥"), ("ET", "埃塞俄比亚"),
        ("TZ", "坦桑尼亚"), ("GH", "加纳"), ("CI", "科特迪瓦"),
        ("UG", "乌干达"), ("SN", "塞内加尔"), ("SD", "苏丹"),
        ("DZ", "阿尔及利亚"), ("AO", "安哥拉"), ("CM", "喀麦隆"),
    ],
    "中亚": [
        ("KZ", "哈萨克斯坦"), ("UZ", "乌兹别克斯坦"), ("TM", "土库曼斯坦"),
        ("KG", "吉尔吉斯斯坦"), ("TJ", "塔吉克斯坦"),
    ],
    "东南亚": [
        ("ID", "印度尼西亚"), ("TH", "泰国"), ("VN", "越南"),
        ("PH", "菲律宾"), ("MY", "马来西亚"), ("MM", "缅甸"),
        ("KH", "柬埔寨"), ("LA", "老挝"),
    ],
    "南亚": [
        ("BD", "孟加拉国"), ("PK", "巴基斯坦"), ("LK", "斯里兰卡"),
        ("NP", "尼泊尔"), ("IN", "印度"),
    ],
    "拉美": [
        ("BR", "巴西"), ("MX", "墨西哥"), ("AR", "阿根廷"),
        ("CO", "哥伦比亚"), ("PE", "秘鲁"), ("CL", "智利"),
        ("EC", "厄瓜多尔"), ("VE", "委内瑞拉"), ("BO", "玻利维亚"),
    ],
    "东欧": [
        ("RU", "俄罗斯"), ("BY", "白俄罗斯"), ("UA", "乌克兰"),
        ("PL", "波兰"), ("RO", "罗马尼亚"), ("BG", "保加利亚"),
        ("RS", "塞尔维亚"),
    ],
}

# 国家 → 城市映射
COUNTRY_CITIES: dict[str, list[tuple[str, str]]] = {
    "阿联酋": [("Dubai", "迪拜"), ("Abu Dhabi", "阿布扎比"), ("Sharjah", "沙迦")],
    "沙特阿拉伯": [("Riyadh", "利雅得"), ("Jeddah", "吉达"), ("Dammam", "达曼")],
    "卡塔尔": [("Doha", "多哈")],
    "科威特": [("Kuwait City", "科威特城")],
    "阿曼": [("Muscat", "马斯喀特")],
    "土耳其": [("Istanbul", "伊斯坦布尔"), ("Ankara", "安卡拉"), ("Izmir", "伊兹密尔")],
    "伊朗": [("Tehran", "德黑兰")],
    "伊拉克": [("Baghdad", "巴格达"), ("Erbil", "埃尔比勒")],
    "约旦": [("Amman", "安曼")],

    "尼日利亚": [("Lagos", "拉各斯"), ("Abuja", "阿布贾"), ("Kano", "卡诺")],
    "肯尼亚": [("Nairobi", "内罗毕"), ("Mombasa", "蒙巴萨")],
    "埃及": [("Cairo", "开罗"), ("Alexandria", "亚历山大")],
    "南非": [("Johannesburg", "约翰内斯堡"), ("Cape Town", "开普敦"), ("Durban", "德班")],
    "摩洛哥": [("Casablanca", "卡萨布兰卡")],
    "埃塞俄比亚": [("Addis Ababa", "亚的斯亚贝巴")],
    "坦桑尼亚": [("Dar es Salaam", "达累斯萨拉姆")],
    "加纳": [("Accra", "阿克拉")],

    "哈萨克斯坦": [("Almaty", "阿拉木图"), ("Astana", "阿斯塔纳")],
    "乌兹别克斯坦": [("Tashkent", "塔什干"), ("Samarkand", "撒马尔罕")],
    "土库曼斯坦": [("Ashgabat", "阿什哈巴德")],
    "吉尔吉斯斯坦": [("Bishkek", "比什凯克")],
    "塔吉克斯坦": [("Dushanbe", "杜尚别")],

    "印度尼西亚": [("Jakarta", "雅加达"), ("Surabaya", "泗水")],
    "泰国": [("Bangkok", "曼谷")],
    "越南": [("Ho Chi Minh City", "胡志明市"), ("Hanoi", "河内")],
    "菲律宾": [("Manila", "马尼拉")],
    "马来西亚": [("Kuala Lumpur", "吉隆坡")],
    "缅甸": [("Yangon", "仰光")],
    "柬埔寨": [("Phnom Penh", "金边")],

    "孟加拉国": [("Dhaka", "达卡"), ("Chittagong", "吉大港")],
    "巴基斯坦": [("Karachi", "卡拉奇"), ("Lahore", "拉合尔")],
    "斯里兰卡": [("Colombo", "科伦坡")],
    "尼泊尔": [("Kathmandu", "加德满都")],
    "印度": [("Mumbai", "孟买"), ("Delhi", "德里"), ("Chennai", "金奈")],

    "巴西": [("Sao Paulo", "圣保罗"), ("Rio de Janeiro", "里约热内卢")],
    "墨西哥": [("Mexico City", "墨西哥城")],
    "阿根廷": [("Buenos Aires", "布宜诺斯艾利斯")],
    "哥伦比亚": [("Bogota", "波哥大")],
    "秘鲁": [("Lima", "利马")],
    "智利": [("Santiago", "圣地亚哥")],

    "俄罗斯": [("Moscow", "莫斯科"), ("Saint Petersburg", "圣彼得堡")],
    "白俄罗斯": [("Minsk", "明斯克")],
    "乌克兰": [("Kyiv", "基辅")],
    "波兰": [("Warsaw", "华沙")],
    "罗马尼亚": [("Bucharest", "布加勒斯特")],
}

# 国家 → 商业语言
COUNTRY_LANGUAGES: dict[str, str] = {
    "阿联酋": "ar", "沙特阿拉伯": "ar", "卡塔尔": "ar", "科威特": "ar",
    "阿曼": "ar", "巴林": "ar", "黎巴嫩": "ar", "约旦": "ar", "伊拉克": "ar",
    "伊朗": "ar",

    "尼日利亚": "en", "肯尼亚": "en", "南非": "en", "加纳": "en",
    "埃塞俄比亚": "en", "坦桑尼亚": "en", "乌干达": "en",

    "摩洛哥": "fr", "科特迪瓦": "fr", "塞内加尔": "fr", "阿尔及利亚": "fr", "喀麦隆": "fr",

    "埃及": "ar",

    "哈萨克斯坦": "ru", "乌兹别克斯坦": "ru", "土库曼斯坦": "ru",
    "吉尔吉斯斯坦": "ru", "塔吉克斯坦": "ru",

    "印度尼西亚": "en", "泰国": "en", "越南": "en", "菲律宾": "en",
    "马来西亚": "en", "缅甸": "en", "柬埔寨": "en",

    "孟加拉国": "en", "巴基斯坦": "en", "斯里兰卡": "en",
    "尼泊尔": "en", "印度": "en",

    "巴西": "pt", "墨西哥": "es", "阿根廷": "es", "哥伦比亚": "es",
    "秘鲁": "es", "智利": "es", "厄瓜多尔": "es", "委内瑞拉": "es",

    "俄罗斯": "ru", "白俄罗斯": "ru", "乌克兰": "ru",
    "波兰": "en", "罗马尼亚": "en", "保加利亚": "en",

    "土耳其": "en",
    "苏丹": "ar", "安哥拉": "pt",
}


def get_regions() -> list[str]:
    return list(REGION_COUNTRIES.keys())


def get_countries_for_region(region: str) -> list[tuple[str, str]]:
    return REGION_COUNTRIES.get(region, [])


def get_cities_for_country(country_cn: str) -> list[tuple[str, str]]:
    return COUNTRY_CITIES.get(country_cn, [])


def get_language_for_country(country_cn: str) -> str:
    return COUNTRY_LANGUAGES.get(country_cn, "en")


# 品类 → 目标客户类型
CATEGORY_BUYER_TYPES: dict[str, list[str]] = {
    "默认": ["hardware store", "building materials supplier", "construction supply", "trading company"],
    "建筑五金": ["hardware store", "building materials", "construction supply", "tools supplier"],
    "塑料制品": ["plastic products distributor", "household goods wholesaler", "kitchenware store", "home supply"],
    "塑料机械": ["plastic machinery dealer", "recycling equipment supplier", "industrial equipment trader"],
    "普通二手机床": ["used machinery dealer", "metalworking supplier", "industrial equipment trader"],
    "汽车配件": ["auto parts store", "car accessories distributor", "vehicle spare parts supplier"],
    "纺织品": ["fabric wholesaler", "textile distributor", "garment supplier"],
    "农产品": ["food importer", "agricultural products trader", "grocery wholesaler"],
}

REGION_BUYER_TERMS: dict[str, list[str]] = {
    "中东": ["trading company", "general trading", "building materials trading"],
    "非洲": ["wholesale supplier", "import company", "general merchant"],
    "中亚": ["construction materials", "wholesale market"],
    "东南亚": ["hardware shop", "construction supply", "building materials shop"],
    "南亚": ["hardware store", "building material dealer", "construction company"],
    "拉美": ["ferreteria", "materiales de construccion", "ferragens", "distribuidora"],
    "东欧": ["building supply", "construction wholesaler"],
}


def get_country_code(country_cn: str) -> str:
    """Get ISO country code from Chinese country name."""
    for region_data in REGION_COUNTRIES.values():
        for code, name in region_data:
            if name == country_cn:
                return code
    return ""

def search_keywords_template(product_keywords: str, country_en: str, city_en: str = "", category: str = "", region: str = "") -> list[str]:
    """Generate buyer-oriented search keywords for the target market."""
    location = f"{city_en} {country_en}" if city_en else country_en

    # Get buyer types for this product category
    buyer_types = CATEGORY_BUYER_TYPES.get(category, CATEGORY_BUYER_TYPES["默认"])
    # Add region-specific terms
    region_terms = REGION_BUYER_TERMS.get(region, [])

    queries = []
    for bt in buyer_types[:4]:
        queries.append(f'"{bt}" {location}')
    for bt in buyer_types[:2]:
        queries.append(f'{bt} {location}')
    for rt in region_terms[:2]:
        queries.append(f'{rt} {location}')

    # Also include product keywords for niche distributors
    main_kw = product_keywords.split(",")[0].strip()
    queries.append(f'{main_kw} distributor {location}')

    return queries
