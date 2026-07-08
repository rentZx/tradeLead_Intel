PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    migration_name TEXT NOT NULL UNIQUE,
    applied_at TEXT DEFAULT CURRENT_TIMESTAMP
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

INSERT OR IGNORE INTO schema_migrations(migration_name)
VALUES ('001_v2_database_upgrade');
