PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name_cn TEXT NOT NULL,
    product_name_en TEXT,
    product_name_ru TEXT,
    product_name_ar TEXT,
    product_name_fr TEXT,
    category TEXT,
    sub_category TEXT,
    description_cn TEXT,
    description_en TEXT,
    specifications TEXT,
    material TEXT,
    condition TEXT,
    model TEXT,
    brand TEXT,
    year TEXT,
    weight TEXT,
    dimensions TEXT,
    moq TEXT,
    purchase_price REAL,
    quote_price REAL,
    currency TEXT DEFAULT 'USD',
    supplier_name TEXT,
    supplier_contact TEXT,
    hs_code TEXT,
    export_control_note TEXT,
    compliance_status TEXT DEFAULT '待复核',
    image_urls TEXT,
    video_urls TEXT,
    status TEXT DEFAULT '在售',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS search_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_name TEXT NOT NULL,
    product_id INTEGER,
    target_region TEXT,
    target_countries TEXT,
    languages TEXT,
    keywords TEXT,
    source_type TEXT DEFAULT 'manual_import',
    status TEXT DEFAULT '待开始',
    discovered_company_count INTEGER DEFAULT 0,
    completed_dd_count INTEGER DEFAULT 0,
    grade_a_count INTEGER DEFAULT 0,
    grade_b_count INTEGER DEFAULT 0,
    grade_c_count INTEGER DEFAULT 0,
    grade_d_count INTEGER DEFAULT 0,
    risk_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    country TEXT,
    city TEXT,
    address TEXT,
    website TEXT,
    email TEXT,
    phone TEXT,
    whatsapp TEXT,
    telegram TEXT,
    contact_form_url TEXT,
    social_links TEXT,
    business_summary TEXT,
    source_url TEXT,
    source_type TEXT DEFAULT 'manual',
    related_product_id INTEGER,
    match_keywords TEXT,
    lead_status TEXT DEFAULT '待背调',
    final_grade TEXT,
    risk_status TEXT DEFAULT '未筛查',
    extraction_confidence REAL,
    company_name_confidence REAL,
    contact_confidence REAL,
    business_match_confidence REAL,
    duplicate_group_id TEXT,
    source_domain TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (related_product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS due_diligence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    authenticity_score INTEGER DEFAULT 0,
    business_match_score INTEGER DEFAULT 0,
    purchase_probability_score INTEGER DEFAULT 0,
    contactability_score INTEGER DEFAULT 0,
    risk_score INTEGER DEFAULT 0,
    final_score INTEGER DEFAULT 0,
    final_grade TEXT,
    risk_flags TEXT,
    evidence_summary TEXT,
    ai_report TEXT,
    recommendation TEXT,
    evidence_json TEXT,
    matched_keywords_json TEXT,
    confidence_score REAL,
    source_urls TEXT,
    manual_override_score INTEGER,
    manual_override_reason TEXT,
    review_status TEXT DEFAULT 'Pending',
    manual_review_status TEXT DEFAULT '待人工复核',
    reviewed_by TEXT,
    checked_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS search_queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER,
    product_id INTEGER,
    country TEXT,
    language TEXT,
    keyword TEXT NOT NULL,
    search_engine TEXT,
    result_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'Pending',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES search_tasks(id) ON DELETE SET NULL,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS search_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER,
    query_id INTEGER,
    title TEXT,
    url TEXT NOT NULL,
    snippet TEXT,
    domain TEXT,
    country_guess TEXT,
    language_guess TEXT,
    is_company_site INTEGER DEFAULT 0,
    is_duplicate INTEGER DEFAULT 0,
    imported_to_companies INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES search_tasks(id) ON DELETE SET NULL,
    FOREIGN KEY (query_id) REFERENCES search_queries(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS webpage_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER,
    url TEXT NOT NULL,
    page_type TEXT,
    http_status INTEGER,
    raw_title TEXT,
    extracted_text TEXT,
    extracted_emails TEXT,
    extracted_phones TEXT,
    extracted_social_links TEXT,
    fetch_status TEXT DEFAULT 'Pending',
    error_message TEXT,
    fetched_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS sanctions_entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    entity_name TEXT NOT NULL,
    aliases TEXT,
    country TEXT,
    address TEXT,
    entity_type TEXT,
    program TEXT,
    remarks TEXT,
    raw_data TEXT,
    imported_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS inquiries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,
    company_name TEXT,
    contact_name TEXT,
    country TEXT,
    email TEXT,
    whatsapp TEXT,
    telegram TEXT,
    product_interest TEXT,
    quantity TEXT,
    message TEXT,
    source_page TEXT,
    status TEXT DEFAULT 'New',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS task_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER,
    task_type TEXT NOT NULL,
    status TEXT DEFAULT 'Pending',
    message TEXT,
    error_detail TEXT,
    started_at TEXT DEFAULT CURRENT_TIMESTAMP,
    finished_at TEXT,
    FOREIGN KEY (task_id) REFERENCES search_tasks(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS outreach_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER,
    product_id INTEGER,
    language TEXT NOT NULL,
    channel TEXT DEFAULT 'email',
    email_subject TEXT,
    email_body TEXT,
    whatsapp_message TEXT,
    followup_1 TEXT,
    followup_2 TEXT,
    quote_followup TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    product_id INTEGER,
    contact_date TEXT,
    channel TEXT,
    content TEXT,
    customer_reply TEXT,
    result TEXT,
    next_followup_date TEXT,
    stage TEXT DEFAULT '未联系',
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS blacklist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    country TEXT,
    type TEXT,
    reason TEXT,
    source TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS risk_keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL,
    language TEXT DEFAULT 'mixed',
    category TEXT,
    risk_level TEXT DEFAULT 'high',
    description TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS schema_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    migration_name TEXT NOT NULL UNIQUE,
    applied_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_search_results_url_unique ON search_results(url);
CREATE INDEX IF NOT EXISTS idx_search_queries_task_id ON search_queries(task_id);
CREATE INDEX IF NOT EXISTS idx_search_queries_product_id ON search_queries(product_id);
CREATE INDEX IF NOT EXISTS idx_search_results_query_id ON search_results(query_id);
CREATE INDEX IF NOT EXISTS idx_search_results_domain ON search_results(domain);
CREATE INDEX IF NOT EXISTS idx_webpage_snapshots_company_id ON webpage_snapshots(company_id);
CREATE INDEX IF NOT EXISTS idx_webpage_snapshots_url ON webpage_snapshots(url);
CREATE INDEX IF NOT EXISTS idx_sanctions_entities_name ON sanctions_entities(entity_name);
CREATE INDEX IF NOT EXISTS idx_inquiries_product_id ON inquiries(product_id);
CREATE INDEX IF NOT EXISTS idx_inquiries_status ON inquiries(status);
CREATE INDEX IF NOT EXISTS idx_task_logs_task_id ON task_logs(task_id);
CREATE INDEX IF NOT EXISTS idx_task_logs_task_type ON task_logs(task_type);
