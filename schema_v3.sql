-- TradeLead Intel V3.0 Database Schema
-- 6 tables, zero-config, sales-ready

PRAGMA foreign_keys = ON;

-- ============================================================
-- 1. 产品库
-- ============================================================
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name_cn TEXT NOT NULL,              -- 中文名
    product_name_en TEXT NOT NULL,              -- 英文名
    category TEXT,                              -- 品类（如"建筑五金"）
    sub_category TEXT,                          -- 子类目（如"保温锚固件"）
    keywords_en TEXT NOT NULL,                  -- 英文搜索关键词，逗号分隔
    description_cn TEXT,                        -- 中文描述
    description_en TEXT,                        -- 英文描述（用于开发信和落地页）
    specifications TEXT,                        -- 规格/型号
    material TEXT,                              -- 材质
    fob_price REAL,                             -- FOB 报价 (USD)
    moq TEXT,                                   -- 起订量
    image_paths TEXT,                           -- 图片路径，逗号分隔
    status TEXT DEFAULT '在售',
    created_at TEXT DEFAULT (datetime('now','localtime')),
    updated_at TEXT DEFAULT (datetime('now','localtime'))
);

-- ============================================================
-- 2. 获客任务
-- ============================================================
CREATE TABLE IF NOT EXISTS acquisition_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    region TEXT,                                -- 大区域（中东/非洲/...）
    country TEXT,                               -- 目标国家
    city TEXT,                                  -- 目标城市（可为空）
    channel TEXT NOT NULL,                      -- 渠道：yellow_pages/google_search/whois/google_maps
    channel_source TEXT,                        -- 黄页具体网站名（如 europages）
    search_keyword TEXT,                        -- 实际使用的搜索词
    status TEXT DEFAULT 'pending',              -- pending/running/done/failed
    leads_found INTEGER DEFAULT 0,              -- 找到线索数
    created_at TEXT DEFAULT (datetime('now','localtime')),
    finished_at TEXT,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_tasks_product ON acquisition_tasks(product_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON acquisition_tasks(status);

-- ============================================================
-- 3. 线索库（统一汇入4个渠道的结果）
-- ============================================================
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER,
    company_name TEXT NOT NULL,                 -- 公司名
    country TEXT,                               -- 国家
    city TEXT,                                  -- 城市
    website TEXT,                               -- 官网 URL
    email TEXT,                                 -- 邮箱
    phone TEXT,                                 -- 电话
    whatsapp TEXT,                              -- WhatsApp
    telegram TEXT,                              -- Telegram
    social_links TEXT,                          -- 社交媒体链接（JSON）
    business_summary TEXT,                      -- 经营概况（自动提取）
    source_channel TEXT NOT NULL,               -- 来源渠道标签
    source_url TEXT,                            -- 来源页面 URL
    match_keyword TEXT,                         -- 匹配关键词
    domain TEXT,                                -- 域名（用于去重）
    confidence TEXT DEFAULT 'unknown',          -- 可信度：high/medium/low/unknown
    diligence_done INTEGER DEFAULT 0,           -- 是否已背调 0/1
    status TEXT DEFAULT 'new',                  -- new/contacted/ignored
    exported INTEGER DEFAULT 0,                 -- 是否已导出 0/1
    created_at TEXT DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (task_id) REFERENCES acquisition_tasks(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_leads_task ON leads(task_id);
CREATE INDEX IF NOT EXISTS idx_leads_domain ON leads(domain);
CREATE INDEX IF NOT EXISTS idx_leads_country ON leads(country);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);

-- ============================================================
-- 4. 背调结果
-- ============================================================
CREATE TABLE IF NOT EXISTS due_diligence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER NOT NULL UNIQUE,
    website_alive INTEGER DEFAULT 0,            -- 官网是否可访问 0/1
    website_title TEXT,                         -- 官网标题
    about_text TEXT,                            -- About 页面内容摘要
    products_found TEXT,                        -- 官网产品关键词
    email_count INTEGER DEFAULT 0,              -- 提取到的邮箱数
    phone_count INTEGER DEFAULT 0,              -- 提取到的电话数
    has_whatsapp INTEGER DEFAULT 0,             -- 是否有 WhatsApp
    has_product_page INTEGER DEFAULT 0,         -- 是否有产品页面
    has_contact_page INTEGER DEFAULT 0,         -- 是否有联系页面
    summary TEXT,                               -- 一句话背调总结
    checked_at TEXT DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE
);

-- ============================================================
-- 5. 开发信
-- ============================================================
CREATE TABLE IF NOT EXISTS outreach (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER,
    product_id INTEGER,
    language TEXT NOT NULL,                     -- en/ar/ru/fr/es/pt
    template_type TEXT DEFAULT 'first_contact', -- first_contact/quote/followup
    email_subject TEXT,
    email_body TEXT,
    whatsapp_msg TEXT,
    created_at TEXT DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE SET NULL,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
);

-- ============================================================
-- 6. 系统设置
-- ============================================================
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TEXT DEFAULT (datetime('now','localtime'))
);

-- ============================================================
-- 预置数据：黄页源
-- ============================================================
INSERT OR IGNORE INTO settings (key, value, description) VALUES
('yellow_pages_sources', 'europages.com|Europages|https://www.europages.com|Europe
kompass.com|Kompass|https://www.kompass.com|Global
tradekey.com|TradeKey|https://www.tradekey.com|Global
yellowpages.ae|UAE YellowPages|https://www.yellowpages.ae|Middle East
yellowpages.co.za|South Africa YellowPages|https://www.yellowpages.co.za|Africa
yellowpages.com.ng|Nigeria YellowPages|https://www.yellowpages.com.ng|Africa
exportersindia.com|Exporters India|https://www.exportersindia.com|South Asia
turkishexporter.net|Turkish Exporter|https://www.turkishexporter.net|Middle East
alibaba.com|Alibaba|https://www.alibaba.com|Global', '黄页源列表，格式: domain|name|url|region，每行一个');

-- 预置数据：城市列表
INSERT OR IGNORE INTO settings (key, value, description) VALUES
('cities', '中东|迪拜|Dubai
中东|阿布扎比|Abu Dhabi
中东|利雅得|Riyadh
中东|吉达|Jeddah
中东|多哈|Doha
中东|科威特城|Kuwait City
中东|马斯喀特|Muscat
中东|伊斯坦布尔|Istanbul
中东|德黑兰|Tehran
非洲|拉各斯|Lagos
非洲|内罗毕|Nairobi
非洲|开罗|Cairo
非洲|约翰内斯堡|Johannesburg
非洲|卡萨布兰卡|Casablanca
非洲|亚的斯亚贝巴|Addis Ababa
非洲|达累斯萨拉姆|Dar es Salaam
非洲|阿克拉|Accra
中亚|阿拉木图|Almaty
中亚|塔什干|Tashkent
中亚|阿什哈巴德|Ashgabat
中亚|比什凯克|Bishkek
中亚|杜尚别|Dushanbe
东南亚|雅加达|Jakarta
东南亚|曼谷|Bangkok
东南亚|胡志明市|Ho Chi Minh City
东南亚|马尼拉|Manila
东南亚|吉隆坡|Kuala Lumpur
东南亚|仰光|Yangon
东南亚|金边|Phnom Penh
南亚|达卡|Dhaka
南亚|卡拉奇|Karachi
南亚|拉合尔|Lahore
南亚|科伦坡|Colombo
南亚|加德满都|Kathmandu
南亚|吉大港|Chittagong
拉美|圣保罗|Sao Paulo
拉美|墨西哥城|Mexico City
拉美|布宜诺斯艾利斯|Buenos Aires
拉美|波哥大|Bogota
拉美|利马|Lima
拉美|圣地亚哥|Santiago
东欧|莫斯科|Moscow
东欧|明斯克|Minsk
东欧|基辅|Kyiv
东欧|华沙|Warsaw
东欧|布加勒斯特|Bucharest', '城市列表，格式: 区域|中文名|英文名，每行一个');

-- 预置数据：开发信模板
INSERT OR IGNORE INTO settings (key, value, description) VALUES
('outreach_templates', 'first_contact_en|Dear {contact_name}, I am writing from {company_name}. We are a leading manufacturer of {product_name_en}. Our {product_name_en} is widely used in {category} and we export to over 20 countries. Key specs: {specifications}. FOB Price: ${fob_price}/pc. MOQ: {moq}. We would love to explore cooperation with your company. Please let me know if you are interested. Best regards, {sender_name} {sender_email} {sender_phone}|first_contact_ar|{arabic_template_placeholder}|first_contact_ru|{russian_template_placeholder}|first_contact_fr|{french_template_placeholder}|quote_en|{quote_template_placeholder}|followup_en|{followup_template_placeholder}', '开发信模板，格式: 模板ID|内容，多个用|分隔');
