from __future__ import annotations

import json
from datetime import date

import pandas as pd
import streamlit as st

from src.compliance import (
    import_sanctions_csv,
    risk_pool_df,
    sanctions_entities_df,
    screen_companies,
    seed_enhanced_risk_keywords,
)
from src.db import execute, get_options, init_db, query_df, update
from src.demo_data import clear_demo_data, demo_counts, generate_demo_data
from src.due_diligence import build_due_diligence
from src.excel_io import export_table, import_companies, import_products, read_tabular
from src.landing_pages import (
    DEFAULT_PORT,
    convert_inquiry_to_crm,
    generate_landing_page,
    landing_page_url,
    start_inquiry_server,
)
from src.prompts import deterministic_keywords, generate_outreach
from src.risk import detect_risk_keywords, format_risk_hits
from src.scoring import calculate_score
from src.search import (
    create_search_task,
    generate_search_keywords,
    import_search_results_to_companies,
    log_task,
    run_search_provider,
    save_search_query,
    save_search_results,
    update_task_counts,
)
from src.ui_styles import (
    C_PRIMARY,
    C_PRIMARY_DARK,
    C_SUCCESS,
    C_SUCCESS_BG,
    C_WARNING,
    C_DANGER,
    C_DANGER_BG,
    C_INFO,
    C_PURPLE,
    C_TEXT_MUTED,
    C_BORDER,
    C_GOLD,
    GRADE_COLORS,
    inject_css,
    main_header,
    page_header,
    sidebar_group,
    sidebar_footer,
    metric_card,
    callout,
    grade_badge,
    grade_chip,
    status_badge,
    score_card,
)
from src.webpage_reader import companies_with_websites, read_company_website

APP_VERSION = "V3.0-RC1"

st.set_page_config(page_title="TradeLead Intel", page_icon="🌐", layout="wide")
init_db()


# ---------------------------------------------------------------------------
# 侧边栏导航配置
# ---------------------------------------------------------------------------
NAV_GROUPS = [
    ("概览", ["首页仪表盘"]),
    ("产品与线索", ["产品库", "公司线索库", "演示数据"]),
    ("搜索与采集", ["搜索任务", "自动搜索", "官网读取"]),
    ("风控与背调", ["合规风险中心", "背调报告"]),
    ("营销与跟进", ["落地页/询盘", "开发信生成器", "CRM跟进"]),
    ("系统", ["系统设置"]),
]

# 页面 -> (icon, color) 映射
PAGE_META = {
    "首页仪表盘": ("dashboard", C_PRIMARY),
    "产品库": ("box", C_PRIMARY),
    "公司线索库": ("building", C_PRIMARY),
    "演示数据": ("flask", C_PURPLE),
    "搜索任务": ("search", C_PRIMARY),
    "自动搜索": ("rocket", C_PRIMARY),
    "官网读取": ("globe", C_PRIMARY),
    "合规风险中心": ("shield", C_DANGER),
    "背调报告": ("clipboard-check", C_WARNING),
    "落地页/询盘": ("file-text", C_PRIMARY),
    "开发信生成器": ("mail", C_PRIMARY),
    "CRM跟进": ("message-circle", C_PRIMARY),
    "系统设置": ("settings", C_TEXT_MUTED),
}


def main() -> None:
    inject_css()
    main_header("TradeLead Intel", f"{APP_VERSION} ｜ 外贸线索情报系统 · 本地版")

    # ---- 侧边栏分组导航 ----
    if "current_page" not in st.session_state:
        st.session_state.current_page = "首页仪表盘"

    all_page_names: list[str] = []
    for _, pages in NAV_GROUPS:
        all_page_names.extend(pages)

    # 如果 session_state 中的页面不在列表中，重置为首页
    current = st.session_state.current_page
    if current not in all_page_names:
        current = "首页仪表盘"
        st.session_state.current_page = current

    # 渲染分组导航
    for group_title, pages in NAV_GROUPS:
        sidebar_group(group_title)
        for page_name in pages:
            is_active = page_name == current
            btn_type = "primary" if is_active else "secondary"
            if st.sidebar.button(
                page_name,
                key=f"nav_{page_name}",
                use_container_width=True,
                type=btn_type,
            ):
                st.session_state.current_page = page_name
                st.rerun()

    sidebar_footer(APP_VERSION)

    # ---- 页面路由 ----
    page = st.session_state.current_page
    if page == "首页仪表盘":
        dashboard_page()
    elif page == "产品库":
        products_page()
    elif page == "公司线索库":
        companies_page()
    elif page == "演示数据":
        demo_data_page()
    elif page == "搜索任务":
        tasks_page()
    elif page == "自动搜索":
        auto_search_page()
    elif page == "官网读取":
        webpage_reader_page()
    elif page == "合规风险中心":
        compliance_center_page()
    elif page == "背调报告":
        due_diligence_page()
    elif page == "落地页/询盘":
        landing_pages_page()
    elif page == "开发信生成器":
        outreach_page()
    elif page == "CRM跟进":
        crm_page()
    else:
        settings_page()


def dashboard_page() -> None:
    icon, color = PAGE_META["首页仪表盘"]
    page_header(icon, "首页仪表盘", color)

    # ---- V3 指标卡片 ----
    metrics = [
        ("产品总数", "SELECT COUNT(*) AS n FROM products", C_PRIMARY),
        ("线索公司", "SELECT COUNT(*) AS n FROM companies", C_SUCCESS),
        ("已背调", "SELECT COUNT(*) AS n FROM due_diligence", C_PURPLE),
        ("A/B 优质客户", "SELECT COUNT(*) AS n FROM companies WHERE final_grade IN ('A','B')", C_GOLD),
        ("风险线索", "SELECT COUNT(*) AS n FROM companies WHERE risk_status NOT IN ('未筛查','未发现关键词风险') AND risk_status != ''", C_DANGER),
    ]
    cards_html = ""
    for label, sql, accent in metrics:
        val_df = query_df(sql)
        val = int(val_df.iloc[0]["n"]) if not val_df.empty else 0
        cards_html += f'<div style="flex:1;min-width:0;padding:0 0.4rem;">{metric_card(label, val, accent)}</div>'
    st.markdown(
        f'<div style="display:flex;gap:0.5rem;flex-wrap:wrap;margin-bottom:1.5rem;">{cards_html}</div>',
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.3, 1])

    with left:
        st.markdown("##### 最近公司线索")
        leads_df = query_df(
            """
            SELECT id, company_name, country, website, lead_status, final_grade, risk_status, created_at
            FROM companies ORDER BY id DESC LIMIT 10
            """
        )
        if not leads_df.empty:
            st.dataframe(leads_df, width="stretch", hide_index=True)
        else:
            st.caption("暂无公司线索，去「自动搜索」或「公司线索库」添加吧。")

        st.markdown("##### 评级分布")
        grade_df = query_df(
            """
            SELECT COALESCE(final_grade, '未评级') AS grade, COUNT(*) AS cnt
            FROM companies GROUP BY final_grade ORDER BY grade
            """
        )
        if not grade_df.empty:
            grade_html = '<div style="display:flex;gap:0.5rem;flex-wrap:wrap;">'
            total_rated = 0
            for _, row in grade_df.iterrows():
                g = str(row["grade"])
                cnt = int(row["cnt"])
                if g in GRADE_COLORS:
                    grade_html += grade_chip(g, cnt)
                    total_rated += cnt
            grade_html += "</div>"
            st.markdown(grade_html, unsafe_allow_html=True)
            st.caption(f"已评级 {total_rated} / 共 {len(leads_df) if not leads_df.empty else 0} 家公司")
        else:
            st.caption("暂无评级数据")

    with right:
        st.markdown("##### 合规提醒")
        callout(
            "涉及机床、工业设备、二手设备、高精度设备、数控设备、塑料机械时，"
            "请人工核查 HS 编码、技术参数、最终用途、最终用户和出口申报要求。",
            "info",
        )
        callout(
            "系统只辅助整理和判断。所有联系、报价、成交和合规决策必须由用户人工确认。",
            "warning",
        )

        st.markdown("##### 快速操作")
        col_a, col_b, col_c = st.columns(3)
        if col_a.button("产品库", use_container_width=True, key="qa_products"):
            st.session_state.current_page = "产品库"
            st.rerun()
        if col_b.button("搜索", use_container_width=True, key="qa_search"):
            st.session_state.current_page = "自动搜索"
            st.rerun()
        if col_c.button("背调", use_container_width=True, key="qa_dd"):
            st.session_state.current_page = "背调报告"
            st.rerun()
        col_d, col_e, col_f = st.columns(3)
        if col_d.button("线索库", use_container_width=True, key="qa_leads"):
            st.session_state.current_page = "公司线索库"
            st.rerun()
        if col_e.button("开发信", use_container_width=True, key="qa_outreach"):
            st.session_state.current_page = "开发信生成器"
            st.rerun()
        if col_f.button("CRM", use_container_width=True, key="qa_crm"):
            st.session_state.current_page = "CRM跟进"
            st.rerun()


def products_page() -> None:
    icon, color = PAGE_META["产品库"]
    page_header(icon, "产品资料库", color)
    with st.expander("➕ 新增产品", expanded=True):
        with st.form("product_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            product_name_cn = c1.text_input("中文产品名 *")
            product_name_en = c2.text_input("英文产品名")
            category = c3.selectbox("品类", ["塑料小件制品", "普通二手机床", "塑料机械和辅机", "再生塑料", "谨慎品类", "其他"])
            sub_category = c1.text_input("子类目")
            condition = c2.selectbox("状态/成色", ["在售", "暂缺", "已下架", "待确认", "二手", "全新"])
            status = c3.selectbox("产品状态", ["在售", "暂缺", "已下架", "待确认"])
            description_cn = st.text_area("中文描述")
            specifications = st.text_area("规格参数")
            c4, c5, c6 = st.columns(3)
            model = c4.text_input("型号")
            brand = c5.text_input("品牌")
            material = c6.text_input("材质")
            purchase_price = c4.number_input("拿货价", min_value=0.0, value=0.0)
            quote_price = c5.number_input("建议报价", min_value=0.0, value=0.0)
            currency = c6.selectbox("币种", ["USD", "CNY", "EUR"])
            supplier_name = c4.text_input("供应商")
            supplier_contact = c5.text_input("供应商联系方式")
            hs_code = c6.text_input("HS编码")
            export_control_note = st.text_area("出口管制/认证备注")
            image_urls = st.text_area("图片链接，每行一个")
            video_urls = st.text_area("视频链接，每行一个")
            submitted = st.form_submit_button("保存产品")
        if submitted:
            if not product_name_cn:
                st.error("请填写中文产品名。")
            else:
                execute(
                    """
                    INSERT INTO products (
                        product_name_cn, product_name_en, category, sub_category, description_cn,
                        specifications, material, condition, model, brand, purchase_price, quote_price,
                        currency, supplier_name, supplier_contact, hs_code, export_control_note,
                        image_urls, video_urls, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        product_name_cn,
                        product_name_en,
                        category,
                        sub_category,
                        description_cn,
                        specifications,
                        material,
                        condition,
                        model,
                        brand,
                        purchase_price,
                        quote_price,
                        currency,
                        supplier_name,
                        supplier_contact,
                        hs_code,
                        export_control_note,
                        image_urls,
                        video_urls,
                        status,
                    ),
                )
                st.success("产品已保存。")

    import_export_block("products")
    st.dataframe(query_df("SELECT * FROM products ORDER BY id DESC"), width="stretch", hide_index=True)


def demo_data_page() -> None:
    icon, color = PAGE_META["演示数据"]
    page_header(icon, "演示数据", color)
    st.caption("生成的数据均带有 DEMO_DATA / demo 标记，并明确注明「演示数据，不可用于真实联系」。清空按钮只删除演示数据，不影响真实数据。")
    counts = demo_counts()
    cols = st.columns(5)
    for col, (label, value) in zip(cols, counts.items()):
        col.metric(label, value)

    callout(
        "演示公司和询盘中的邮箱、电话、WhatsApp、Telegram 均为测试数据，不可用于真实联系。",
        "warning",
    )
    c1, c2 = st.columns(2)
    if c1.button("生成演示数据", type="primary", use_container_width=True):
        stats = generate_demo_data()
        st.success(
            f"演示数据已生成：产品 {stats['products']} 条，公司 {stats['companies']} 条，"
            f"风险名单 {stats['sanctions_entities']} 条，询盘 {stats['inquiries']} 条，CRM跟进 {stats['interactions']} 条。"
        )
    if c2.button("清空演示数据", use_container_width=True):
        deleted = clear_demo_data()
        st.success(
            f"已清空演示数据：产品 {deleted['products']} 条，公司 {deleted['companies']} 条，"
            f"风险名单 {deleted['sanctions_entities']} 条，询盘 {deleted['inquiries']} 条，CRM跟进 {deleted['interactions']} 条。"
        )

    st.markdown("**演示公司预览**")
    st.dataframe(
        query_df(
            """
            SELECT id, company_name, country, website, email, business_summary, source_type, risk_status
            FROM companies
            WHERE source_type = 'demo'
            ORDER BY id DESC
            LIMIT 50
            """
        ),
        width="stretch",
        hide_index=True,
    )


def tasks_page() -> None:
    icon, color = PAGE_META["搜索任务"]
    page_header(icon, "搜索任务管理", color)
    products = get_options("products")
    with st.form("task_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        task_name = c1.text_input("任务名称 *")
        product_label = c2.selectbox("绑定产品", list(products.keys()) or ["请先新增产品"])
        target_region = c1.text_input("目标区域", value="中亚/中东/非洲")
        target_countries = c2.text_input("目标国家，逗号分隔", value="哈萨克斯坦, 乌兹别克斯坦, 俄罗斯")
        languages = c1.multiselect("语言", ["英语", "俄语", "阿语", "法语"], default=["英语", "俄语"])
        source_type = c2.selectbox("来源方式", ["manual_import", "search_api_later", "public_web_text"])
        if products and product_label in products:
            product = query_df("SELECT product_name_cn, product_name_en FROM products WHERE id = ?", (products[product_label],)).iloc[0]
            product_name = product["product_name_en"] or product["product_name_cn"]
        else:
            product_name = ""
        keywords = deterministic_keywords(product_name, target_countries)
        st.code(json.dumps(keywords, ensure_ascii=False, indent=2), language="json")
        submitted = st.form_submit_button("创建任务")
    if submitted and products:
        execute(
            """
            INSERT INTO search_tasks(task_name, product_id, target_region, target_countries, languages, keywords, source_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (task_name, products[product_label], target_region, target_countries, ",".join(languages), json.dumps(keywords, ensure_ascii=False), source_type),
        )
        st.success("搜索任务已创建。")

    st.dataframe(query_df("SELECT * FROM search_tasks ORDER BY id DESC"), width="stretch", hide_index=True)


def auto_search_page() -> None:
    icon, color = PAGE_META["自动搜索"]
    page_header(icon, "自动搜索", color)
    st.caption("根据产品、国家和语言生成关键词，通过配置的搜索 API 获取结果，保存到 V2.0 search_queries/search_results。")
    products = get_options("products")
    if not products:
        callout("请先在产品库新增至少一个产品。", "info")
        return

    with st.form("auto_search_form"):
        c1, c2, c3 = st.columns(3)
        product_label = c1.selectbox("产品", list(products.keys()))
        countries_text = c2.text_input("国家，逗号分隔", value="哈萨克斯坦, 乌兹别克斯坦, 俄罗斯")
        languages = c3.multiselect("语言", ["英语", "俄语", "阿语", "法语"], default=["英语", "俄语"])
        provider_label = c1.selectbox("搜索 API", ["Mock", "SerpAPI", "Bing", "Google_CSE"])
        limit = c2.number_input("每个关键词最多结果数", min_value=1, max_value=10, value=5, step=1)
        api_key = c3.text_input("API Key（可留空读取环境变量）", type="password")
        endpoint = c1.text_input("Bing Endpoint（可选）", value="")
        cse_id = c2.text_input("Google CSE ID（Google_CSE 使用）", value="")
        run_button = st.form_submit_button("生成关键词并执行搜索", type="primary")

    product_id = products[product_label]
    product = query_df("SELECT * FROM products WHERE id = ?", (product_id,)).iloc[0].to_dict()
    countries = [item.strip() for item in countries_text.replace("，", ",").split(",") if item.strip()]
    keyword_rows = generate_search_keywords(product, countries, languages)

    st.markdown("**将要执行的关键词**")
    st.dataframe(pd.DataFrame(keyword_rows), width="stretch", hide_index=True)

    if run_button:
        if not countries:
            st.error("请至少填写一个目标国家。")
            return
        if not languages:
            st.error("请至少选择一种语言。")
            return
        task_id = create_search_task(product_id, product.get("product_name_cn", ""), countries, languages, provider_label)
        total_inserted = 0
        total_duplicate_url = 0
        total_duplicate_domain = 0
        progress = st.progress(0, text="开始搜索...")
        for index, row in enumerate(keyword_rows, start=1):
            query_id = save_search_query(task_id, product_id, row, provider_label)
            try:
                results = run_search_provider(
                    provider_label,
                    row["keyword"],
                    row["country"],
                    row["language"],
                    api_key=api_key,
                    endpoint=endpoint,
                    cse_id=cse_id,
                    limit=int(limit),
                )
                stats = save_search_results(task_id, query_id, results)
                update(
                    "UPDATE search_queries SET result_count = ?, status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (len(results), "Completed", query_id),
                )
                log_task(task_id, "auto_search", "Completed", f"{row['keyword']} returned {len(results)} results")
                total_inserted += stats["inserted"]
                total_duplicate_url += stats["duplicate_url"]
                total_duplicate_domain += stats["duplicate_domain"]
            except Exception as exc:
                update(
                    "UPDATE search_queries SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    ("Failed", query_id),
                )
                log_task(task_id, "auto_search", "Failed", f"{row['keyword']} failed", str(exc))
                st.error(f"关键词失败：{row['keyword']}；{exc}")
            progress.progress(index / max(1, len(keyword_rows)), text=f"已处理 {index}/{len(keyword_rows)}")
        update_task_counts(task_id)
        st.success(
            f"搜索完成。新增 {total_inserted} 条结果，跳过 URL 重复 {total_duplicate_url} 条，标记域名重复 {total_duplicate_domain} 条。"
        )

    st.divider()
    st.markdown("**搜索结果**")
    task_options = get_options("search_tasks", "task_name")
    selected_task_id = None
    if task_options:
        selected_task_label = st.selectbox("查看任务", list(task_options.keys()))
        selected_task_id = task_options[selected_task_label]
    import_product_id = product_id
    if selected_task_id:
        task_product_df = query_df("SELECT product_id FROM search_tasks WHERE id = ?", (selected_task_id,))
        if not task_product_df.empty and task_product_df.iloc[0]["product_id"]:
            import_product_id = int(task_product_df.iloc[0]["product_id"])
    show_duplicates = st.checkbox("显示重复域名结果", value=False)
    where = "1 = 1"
    params: tuple = ()
    if selected_task_id:
        where += " AND task_id = ?"
        params = (selected_task_id,)
    if not show_duplicates:
        where += " AND is_duplicate = 0"
    results_df = query_df(
        f"""
        SELECT id, title, url, domain, snippet, country_guess, language_guess,
               is_company_site, is_duplicate, imported_to_companies, created_at
        FROM search_results
        WHERE {where}
        ORDER BY id DESC
        LIMIT 300
        """,
        params,
    )
    st.dataframe(results_df, width="stretch", hide_index=True)

    eligible_ids = [
        int(row.id)
        for row in results_df.itertuples(index=False)
        if int(row.is_company_site or 0) == 1 and int(row.is_duplicate or 0) == 0 and int(row.imported_to_companies or 0) == 0
    ]
    if st.button("一键导入当前未重复公司站点到线索库", disabled=not eligible_ids, type="primary"):
        stats = import_search_results_to_companies(import_product_id, eligible_ids)
        st.success(f"已导入 {stats['imported']} 条，已存在跳过 {stats['skipped_existing']} 条。")


def webpage_reader_page() -> None:
    icon, color = PAGE_META["官网读取"]
    page_header(icon, "官网读取", color)
    st.caption("批量读取公司官网公开页面，提取正文、邮箱、电话、WhatsApp、Telegram 和社交媒体链接，保存到 webpage_snapshots。")

    only_not_read = st.checkbox("只显示尚未读取过官网的公司", value=True)
    company_rows = companies_with_websites(only_not_read=only_not_read)
    if not company_rows:
        callout("暂无可读取官网的公司线索。请先在公司线索库录入 website，或从自动搜索结果导入公司。", "info")
        snapshots_df = query_df(
            """
            SELECT id, company_id, url, page_type, http_status, fetch_status, error_message, fetched_at
            FROM webpage_snapshots
            ORDER BY id DESC
            LIMIT 200
            """
        )
        st.dataframe(snapshots_df, width="stretch", hide_index=True)
        return

    labels = {f"{row['company_name']} - {row['website']} (#{row['id']})": int(row["id"]) for row in company_rows}
    selected_labels = st.multiselect("选择要读取的公司", list(labels.keys()), default=list(labels.keys())[: min(5, len(labels))])
    c1, c2, c3 = st.columns(3)
    max_pages = c1.number_input("每家公司最多读取页面数", min_value=1, max_value=9, value=4, step=1)
    timeout = c2.number_input("单页超时秒数", min_value=5, max_value=60, value=15, step=5)
    run_button = c3.button("开始批量读取", disabled=not selected_labels, type="primary")

    preview_df = query_df(
        """
        SELECT id, company_name, website, email, phone, whatsapp, telegram, updated_at
        FROM companies
        WHERE website IS NOT NULL AND website != ''
        ORDER BY id DESC
        LIMIT 200
        """
    )
    st.markdown("**公司官网列表**")
    st.dataframe(preview_df, width="stretch", hide_index=True)

    if run_button:
        company_ids = [labels[label] for label in selected_labels]
        progress = st.progress(0, text="开始读取官网...")
        total_success = 0
        total_failed = 0
        for index, company_id in enumerate(company_ids, start=1):
            company_name = next(label for label, value in labels.items() if value == company_id)
            try:
                stats = read_company_website(company_id, max_pages=int(max_pages), timeout=int(timeout))
                total_success += stats["success"]
                total_failed += stats["failed"]
                log_task(None, "webpage_reader", "Completed", f"{company_name}: success={stats['success']}, failed={stats['failed']}")
            except Exception as exc:
                total_failed += 1
                log_task(None, "webpage_reader", "Failed", f"{company_name}: read failed", str(exc))
                st.error(f"{company_name} 读取失败：{exc}")
            progress.progress(index / max(1, len(company_ids)), text=f"已处理 {index}/{len(company_ids)}")
        st.success(f"官网读取完成。成功页面 {total_success} 个，失败页面 {total_failed} 个。")

    st.divider()
    st.markdown("**网页快照与读取状态**")
    status_filter = st.selectbox("读取状态", ["全部", "Success", "Failed", "Pending"])
    where = "1 = 1"
    params: tuple = ()
    if status_filter != "全部":
        where = "fetch_status = ?"
        params = (status_filter,)
    snapshots_df = query_df(
        f"""
        SELECT ws.id, ws.company_id, c.company_name, ws.url, ws.page_type, ws.http_status,
               ws.fetch_status, ws.error_message, ws.raw_title, ws.extracted_emails,
               ws.extracted_phones, ws.extracted_social_links, ws.fetched_at
        FROM webpage_snapshots ws
        LEFT JOIN companies c ON c.id = ws.company_id
        WHERE {where}
        ORDER BY ws.id DESC
        LIMIT 300
        """,
        params,
    )
    st.dataframe(snapshots_df, width="stretch", hide_index=True)


def compliance_center_page() -> None:
    icon, color = PAGE_META["合规风险中心"]
    page_header(icon, "合规风险中心", color)
    st.caption("导入制裁名单 CSV，使用 rapidfuzz 对公司名称做模糊匹配，并将高风险客户自动标记为风险池。")

    # ---- 指标卡片 ----
    metrics = [
        ("制裁实体", "SELECT COUNT(*) AS n FROM sanctions_entities", C_DANGER),
        ("风险关键词", "SELECT COUNT(*) AS n FROM risk_keywords", C_WARNING),
        ("公司线索", "SELECT COUNT(*) AS n FROM companies", C_PRIMARY),
        ("风险池客户", None, C_DANGER),
    ]
    cols = st.columns(4)
    for i, (label, sql, accent) in enumerate(metrics):
        if sql:
            val = int(query_df(sql).iloc[0]["n"])
        else:
            val = len(risk_pool_df())
        cols[i].metric(label, val)

    tab1, tab2, tab3 = st.tabs(["📋 制裁名单导入", "🔍 风险筛查", "⚠️ 风险池"])

    with tab1:
        uploaded = st.file_uploader("上传制裁名单 CSV", type=["csv"], key="sanctions_csv")
        source_default = st.text_input("名单来源", value="CSV")
        if uploaded is not None:
            try:
                sanctions_df = pd.read_csv(uploaded)
                st.dataframe(sanctions_df.head(50), width="stretch", hide_index=True)
                if st.button("导入制裁名单", type="primary"):
                    count = import_sanctions_csv(sanctions_df, source_default=source_default)
                    st.success(f"已导入 {count} 条制裁实体。")
            except Exception as exc:
                st.error(f"CSV 读取失败：{exc}")
        st.markdown("**已导入制裁实体**")
        st.dataframe(sanctions_entities_df(), width="stretch", hide_index=True)

    with tab2:
        left, right = st.columns([1, 1])
        if left.button("增强风险关键词库"):
            inserted = seed_enhanced_risk_keywords()
            st.success(f"已新增 {inserted} 条风险关键词。")
        threshold = right.slider("制裁名单模糊匹配阈值", min_value=70, max_value=100, value=88, step=1)
        include_keyword_screen = st.checkbox("同时使用高风险关键词筛查公司资料", value=True)
        callout("高风险命中只代表需要人工复核；系统不提供规避制裁、出口管制或报关监管的方案。", "danger")
        if st.button("执行合规筛查", type="primary"):
            stats = screen_companies(threshold=int(threshold), include_keyword_screen=include_keyword_screen)
            st.success(
                f"筛查完成：公司 {stats['screened']} 家，制裁模糊命中 {stats['sanctions_matches']} 条，"
                f"关键词标记 {stats['keyword_flagged']} 家，风险池当前 {stats['risk_pool']} 家。"
            )
        st.markdown("**最近合规日志**")
        logs_df = query_df(
            """
            SELECT id, task_type, status, message, error_detail, started_at, finished_at
            FROM task_logs
            WHERE task_type IN ('compliance_import', 'compliance_screen')
            ORDER BY id DESC
            LIMIT 100
            """
        )
        st.dataframe(logs_df, width="stretch", hide_index=True)

    with tab3:
        st.markdown("**风险池客户**")
        pool_df = risk_pool_df()
        st.dataframe(pool_df, width="stretch", hide_index=True)
        if not pool_df.empty:
            st.download_button(
                "导出风险池 CSV",
                pool_df.to_csv(index=False).encode("utf-8-sig"),
                "risk_pool.csv",
                "text/csv",
            )


def landing_pages_page() -> None:
    icon, color = PAGE_META["落地页/询盘"]
    page_header(icon, "产品落地页与询盘管理", color)
    st.caption("选择产品和语言生成静态 HTML 产品页；页面询盘表单提交后写入 inquiries，并可转入 CRM。")

    products = get_options("products")
    tab1, tab2 = st.tabs(["📄 产品落地页", "📨 询盘管理"])

    with tab1:
        if not products:
            callout("请先在产品库新增产品。", "info")
        else:
            c1, c2, c3 = st.columns(3)
            product_label = c1.selectbox("产品", list(products.keys()))
            language = c2.selectbox("语言", ["英语", "俄语", "阿语", "法语"])
            port = c3.number_input("询盘服务端口", min_value=8000, max_value=9999, value=DEFAULT_PORT, step=1)
            product_id = products[product_label]
            product = query_df("SELECT * FROM products WHERE id = ?", (product_id,)).iloc[0].to_dict()
            c1_btn, c2_btn = st.columns(2)
            if c1_btn.button("启动询盘接收服务", use_container_width=True):
                url = start_inquiry_server(int(port))
                st.success(f"询盘接收服务已启动：{url}")
            if c2_btn.button("生成静态HTML产品页", type="primary", use_container_width=True):
                start_inquiry_server(int(port))
                path = generate_landing_page(product, language, int(port))
                url = landing_page_url(path, int(port))
                st.success("产品落地页已生成。")
                st.markdown(f"[🔗 打开产品页]({url})")
                st.code(str(path), language="text")
            st.markdown("**产品页预览数据**")
            st.json(
                {
                    "product_id": product_id,
                    "product_name_cn": product.get("product_name_cn"),
                    "product_name_en": product.get("product_name_en"),
                    "category": product.get("category"),
                    "specifications": product.get("specifications"),
                    "image_urls": product.get("image_urls"),
                }
            )

    with tab2:
        c1, c2 = st.columns([1, 1])
        status_filter = c1.selectbox("询盘状态", ["全部", "New", "Reviewed", "Replied", "Quoted", "Converted", "Closed"])
        product_filter = c2.selectbox("产品筛选", ["全部"] + list(products.keys()))
        where = "1 = 1"
        params: list = []
        if status_filter != "全部":
            where += " AND i.status = ?"
            params.append(status_filter)
        if product_filter != "全部":
            where += " AND i.product_id = ?"
            params.append(products[product_filter])
        inquiries_df = query_df(
            f"""
            SELECT i.id, i.product_id, p.product_name_cn, i.company_name, i.contact_name,
                   i.country, i.email, i.whatsapp, i.telegram, i.product_interest,
                   i.quantity, i.message, i.source_page, i.status, i.created_at
            FROM inquiries i
            LEFT JOIN products p ON p.id = i.product_id
            WHERE {where}
            ORDER BY i.id DESC
            LIMIT 500
            """,
            tuple(params),
        )
        st.dataframe(inquiries_df, width="stretch", hide_index=True)
        if not inquiries_df.empty:
            inquiry_options = {f"#{row.id} {row.company_name or row.contact_name or row.email}": int(row.id) for row in inquiries_df.itertuples(index=False)}
            selected = st.selectbox("选择询盘", list(inquiry_options.keys()))
            col_a, col_b, col_c = st.columns(3)
            new_status = col_a.selectbox("更新状态", ["New", "Reviewed", "Replied", "Quoted", "Converted", "Closed"])
            if col_b.button("保存状态", use_container_width=True):
                update("UPDATE inquiries SET status = ? WHERE id = ?", (new_status, inquiry_options[selected]))
                st.success("询盘状态已更新。")
            if col_c.button("转入CRM", type="primary", use_container_width=True):
                company_id = convert_inquiry_to_crm(inquiry_options[selected])
                st.success(f"已转入 CRM，公司ID：{company_id}")
        st.download_button(
            "📥 导出询盘 CSV",
            inquiries_df.to_csv(index=False).encode("utf-8-sig"),
            "inquiries.csv",
            "text/csv",
            disabled=inquiries_df.empty,
        )


def companies_page() -> None:
    icon, color = PAGE_META["公司线索库"]
    page_header(icon, "候选公司线索库", color)
    products = get_options("products")
    with st.expander("➕ 手动录入公司", expanded=True):
        with st.form("company_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            company_name = c1.text_input("公司名称 *")
            country = c2.text_input("国家")
            city = c3.text_input("城市")
            website = c1.text_input("官网")
            email = c2.text_input("邮箱")
            whatsapp = c3.text_input("WhatsApp")
            product_label = st.selectbox("关联产品", list(products.keys()) or ["不关联"])
            business_summary = st.text_area("业务摘要")
            source_url = st.text_input("来源URL")
            match_keywords = st.text_input("匹配关键词")
            submitted = st.form_submit_button("保存线索", type="primary")
        if submitted:
            if not company_name:
                st.error("请填写公司名称。")
            else:
                product_id = products.get(product_label)
                execute(
                    """
                    INSERT INTO companies(company_name, country, city, website, email, whatsapp, business_summary, source_url, related_product_id, match_keywords)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (company_name, country, city, website, email, whatsapp, business_summary, source_url, product_id, match_keywords),
                )
                st.success("公司线索已保存。")

    import_export_block("companies")
    st.dataframe(query_df("SELECT * FROM companies ORDER BY id DESC"), width="stretch", hide_index=True)


def due_diligence_page() -> None:
    icon, color = PAGE_META["背调报告"]
    page_header(icon, "公司背调与客户评分", color)
    companies = get_options("companies", "company_name")
    if not companies:
        callout("请先录入候选公司。", "info")
        return

    company_label = st.selectbox("选择公司", list(companies.keys()))
    company_id = companies[company_label]
    company = query_df("SELECT * FROM companies WHERE id = ?", (company_id,)).iloc[0].to_dict()
    product = {}
    if company.get("related_product_id"):
        df = query_df("SELECT * FROM products WHERE id = ?", (company["related_product_id"],))
        product = df.iloc[0].to_dict() if not df.empty else {}

    snapshot_df = query_df(
        """
        SELECT url, page_type, fetch_status, error_message, fetched_at
        FROM webpage_snapshots
        WHERE company_id = ?
        ORDER BY id DESC
        LIMIT 20
        """,
        (company_id,),
    )
    if snapshot_df.empty:
        callout("还没有官网读取快照。建议先到「官网读取」页面读取公开网页，背调报告会更有证据链。", "info")
    else:
        with st.expander("已读取网页快照", expanded=False):
            st.dataframe(snapshot_df, width="stretch", hide_index=True)

    public_text = st.text_area("补充公开资料文本", value=company.get("business_summary") or "", height=140)
    hits = detect_risk_keywords(" ".join([public_text, str(company), str(product)]))
    diligence = build_due_diligence(company, product, public_text, hits)
    suggested = diligence["score"]
    c1, c2, c3, c4 = st.columns(4)
    business_match = c1.slider("业务匹配度 /30", 0, 30, int(suggested["business_match_score"]))
    purchase_probability = c2.slider("采购可能性 /20", 0, 20, int(suggested["purchase_probability_score"]))
    authenticity = c3.slider("真实性 /20", 0, 20, int(suggested["authenticity_score"]))
    contactability = c4.slider("联系可达性 /15", 0, 15, int(suggested["contactability_score"]))

    score = calculate_score(business_match, purchase_probability, authenticity, contactability, hits)
    if (
        business_match != suggested["business_match_score"]
        or purchase_probability != suggested["purchase_probability_score"]
        or authenticity != suggested["authenticity_score"]
        or contactability != suggested["contactability_score"]
    ):
        diligence = build_due_diligence(
            company,
            product,
            public_text,
            hits,
            score_override={
                "business_match_score": business_match,
                "purchase_probability_score": purchase_probability,
                "authenticity_score": authenticity,
                "contactability_score": contactability,
            },
        )
    st.markdown("**⚠️ 风险命中**")
    st.code(format_risk_hits(hits))

    # ---- V3 评分展示 ----
    grade = score["final_grade"]
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(
            score_card(
                final_score=int(score["final_score"]),
                grade=grade,
                business_match=int(score["business_match_score"]),
                purchase_probability=int(score["purchase_probability_score"]),
                authenticity=int(score["authenticity_score"]),
                contactability=int(score["contactability_score"]),
                risk_score=int(score["risk_score"]),
            ),
            unsafe_allow_html=True,
        )
    m2.metric("风险扣分", score["risk_score"])
    m3.metric("整体置信度", diligence["confidence_score"])

    evidence_df = pd.DataFrame(diligence["evidence"])
    st.markdown("**分项评分理由与证据链**")
    st.dataframe(evidence_df, width="stretch", hide_index=True)

    evidence_summary = st.text_area("证据摘要", value=diligence["summary"], height=160)
    matched_keywords_json = json.dumps(diligence["matched_keywords"], ensure_ascii=False, indent=2)
    st.text_area("命中关键词 JSON", value=matched_keywords_json, height=160)
    st.text_area("来源URL", value="\n".join(diligence["source_urls"]), height=100)
    ai_report = st.text_area("背调报告草稿", value=diligence["report"], height=360)
    recommendation = st.selectbox("建议", ["优先开发", "可跟进", "暂缓", "人工合规复核", "拉黑/不开发"])
    if st.button("保存背调报告", type="primary"):
        execute(
            """
            INSERT INTO due_diligence (
                company_id, authenticity_score, business_match_score, purchase_probability_score,
                contactability_score, risk_score, final_score, final_grade, risk_flags,
                evidence_summary, ai_report, recommendation, evidence_json, matched_keywords_json,
                confidence_score, source_urls, review_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                company_id,
                score["authenticity_score"],
                score["business_match_score"],
                score["purchase_probability_score"],
                score["contactability_score"],
                score["risk_score"],
                score["final_score"],
                score["final_grade"],
                format_risk_hits(hits),
                evidence_summary,
                ai_report,
                recommendation,
                json.dumps(diligence["evidence"], ensure_ascii=False),
                matched_keywords_json,
                diligence["confidence_score"],
                json.dumps(diligence["source_urls"], ensure_ascii=False),
                "Pending",
            ),
        )
        update(
            "UPDATE companies SET final_grade = ?, risk_status = ?, lead_status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (score["final_grade"], "有风险命中" if hits else "未发现关键词风险", "已背调", company_id),
        )
        st.success("背调报告已保存。")

    st.dataframe(
        query_df("SELECT * FROM due_diligence WHERE company_id = ? ORDER BY id DESC", (company_id,)),
        width="stretch",
        hide_index=True,
    )


def outreach_page() -> None:
    icon, color = PAGE_META["开发信生成器"]
    page_header(icon, "开发信与联系话术生成器", color)
    companies = get_options("companies", "company_name")
    products = get_options("products")
    if not companies or not products:
        callout("请先录入产品和公司。", "info")
        return
    c1, c2, c3 = st.columns(3)
    company_label = c1.selectbox("客户", list(companies.keys()))
    product_label = c2.selectbox("产品", list(products.keys()))
    language = c3.selectbox("语言", ["英语", "俄语", "阿语", "法语"])
    company_name = company_label.rsplit(" (#", 1)[0]
    product_name = product_label.rsplit(" (#", 1)[0]
    draft = generate_outreach(language, company_name, product_name)
    subject = st.text_input("邮件标题", value=draft["email_subject"])
    body = st.text_area("邮件正文", value=draft["email_body"], height=240)
    whatsapp = st.text_area("WhatsApp开场白", value=draft["whatsapp_message"], height=80)
    followup_1 = st.text_area("第一次跟进", value=draft["followup_1"], height=80)
    followup_2 = st.text_area("第二次跟进", value=draft["followup_2"], height=80)
    quote_followup = st.text_area("报价后跟进", value=draft["quote_followup"], height=80)
    callout("以上内容仅为草稿。发送前请人工确认客户身份、产品信息、出口合规和目标市场邮件规则。", "warning")
    if st.button("保存话术", type="primary"):
        execute(
            """
            INSERT INTO outreach_templates(company_id, product_id, language, channel, email_subject, email_body, whatsapp_message, followup_1, followup_2, quote_followup)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (companies[company_label], products[product_label], language, "email/whatsapp", subject, body, whatsapp, followup_1, followup_2, quote_followup),
        )
        st.success("话术已保存。")
    st.dataframe(query_df("SELECT * FROM outreach_templates ORDER BY id DESC"), width="stretch", hide_index=True)


def crm_page() -> None:
    icon, color = PAGE_META["CRM跟进"]
    page_header(icon, "CRM跟进管理", color)
    companies = get_options("companies", "company_name")
    products = get_options("products")
    if not companies:
        callout("请先录入公司线索。", "info")
        return
    with st.form("interaction_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        company_label = c1.selectbox("公司", list(companies.keys()))
        product_label = c2.selectbox("产品", list(products.keys()) or ["不关联"])
        contact_date = c3.date_input("联系日期", value=date.today())
        channel = c1.selectbox("渠道", ["Email", "WhatsApp", "电话", "表单", "Telegram", "其他"])
        stage = c2.selectbox("阶段", ["未联系", "已联系", "已回复", "有意向", "报价中", "暂缓", "成交", "不匹配"])
        next_followup_date = c3.date_input("下次跟进", value=date.today())
        content = st.text_area("联系内容")
        customer_reply = st.text_area("客户回复")
        result = st.text_input("结果")
        notes = st.text_area("备注")
        submitted = st.form_submit_button("保存跟进", type="primary")
    if submitted:
        execute(
            """
            INSERT INTO interactions(company_id, product_id, contact_date, channel, content, customer_reply, result, next_followup_date, stage, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                companies[company_label],
                products.get(product_label),
                str(contact_date),
                channel,
                content,
                customer_reply,
                result,
                str(next_followup_date),
                stage,
                notes,
            ),
        )
        update("UPDATE companies SET lead_status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (stage, companies[company_label]))
        st.success("跟进记录已保存。")

    st.dataframe(query_df("SELECT * FROM interactions ORDER BY id DESC"), width="stretch", hide_index=True)
    st.download_button("导出跟进记录 Excel", export_table("interactions"), "interactions.xlsx")


def settings_page() -> None:
    icon, color = PAGE_META["系统设置"]
    page_header(icon, "系统设置", color)
    tab1, tab2 = st.tabs(["⚠️ 风险关键词", "🚫 黑名单"])
    with tab1:
        with st.form("risk_keyword_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            keyword = c1.text_input("关键词")
            language = c2.text_input("语言", value="mixed")
            risk_level = c3.selectbox("等级", ["critical", "high", "medium", "low"])
            category = c1.text_input("分类")
            description = c2.text_input("说明")
            if st.form_submit_button("新增风险关键词"):
                execute(
                    "INSERT INTO risk_keywords(keyword, language, category, risk_level, description) VALUES (?, ?, ?, ?, ?)",
                    (keyword, language, category, risk_level, description),
                )
                st.success("已新增风险关键词。")
        st.dataframe(query_df("SELECT * FROM risk_keywords ORDER BY id DESC"), width="stretch", hide_index=True)
    with tab2:
        with st.form("blacklist_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            name = c1.text_input("名称/域名/邮箱/电话")
            country = c2.text_input("国家")
            item_type = c3.selectbox("类型", ["company", "person", "domain", "email", "phone"])
            reason = st.text_area("原因")
            source = st.text_input("来源")
            if st.form_submit_button("加入黑名单"):
                execute(
                    "INSERT INTO blacklist(name, country, type, reason, source) VALUES (?, ?, ?, ?, ?)",
                    (name, country, item_type, reason, source),
                )
                st.success("已加入黑名单。")
        st.dataframe(query_df("SELECT * FROM blacklist ORDER BY id DESC"), width="stretch", hide_index=True)


def import_export_block(table: str) -> None:
    with st.expander("📥 导入 / 导出"):
        uploaded = st.file_uploader(f"导入 {table} CSV/Excel", type=["csv", "xlsx"], key=f"upload_{table}")
        if uploaded and st.button(f"确认导入 {table}", key=f"import_{table}"):
            df = read_tabular(uploaded)
            count = import_products(df) if table == "products" else import_companies(df)
            st.success(f"已导入 {count} 条记录。")
        st.download_button(f"📤 导出 {table} Excel", export_table(table), f"{table}.xlsx", key=f"export_{table}")


if __name__ == "__main__":
    main()
