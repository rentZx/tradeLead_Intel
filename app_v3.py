"""
TradeLead Intel V3.0 — Main Application
======================================
面向外贸销售人员的获客工具，全部点选操作，零代码配置。
7 个页面，4 种免费获客渠道，1 键导出 Excel。
"""

from __future__ import annotations

import io
import os
import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

# ── Page config (must be first Streamlit call) ──────────────
st.set_page_config(
    page_title="TradeLead Intel V3",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Database init ──────────────────────────────────────────
from src.db_v3 import (
    init_db, add_product, get_products, get_product, delete_product,
    add_lead, get_leads, update_lead, count_leads,
    create_task, update_task, get_tasks,
    save_diligence, get_diligence,
    save_outreach, get_outreach,
    export_leads_to_df,
    get_setting, set_setting, query,
)
from src.market_data import (
    get_regions, get_countries_for_region, get_cities_for_country,
    get_language_for_country, search_keywords_template,
)
from src.scraper import (
    scrape_google_search, scrape_yellow_pages, run_acquisition,
)
from src.diligence import run_diligence, rate_confidence
from src.extractor import extract_contacts_from_html
from src.outreach_v3 import generate_outreach, generate_landing_page

# Initialize database on first run
if "db_initialized" not in st.session_state:
    init_db()
    st.session_state.db_initialized = True

# ── CSS (minimal, only what's needed for visual polish) ───
def _inject_css():
    st.markdown("""
    <style>
    /* Clean card style */
    .card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 18px 20px;
        margin-bottom: 12px;
    }
    .card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.06); }

    /* Stats */
    .stat-big {
        font-size: 2rem;
        font-weight: 700;
        color: #2563eb;
        line-height: 1.2;
    }
    .stat-label {
        font-size: 0.8rem;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Badge */
    .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-high { background: #dcfce7; color: #166534; }
    .badge-medium { background: #fef3c7; color: #92400e; }
    .badge-low { background: #fee2e2; color: #991b1b; }
    .badge-unknown { background: #f1f5f9; color: #475569; }

    /* Channel tag */
    .channel-tag {
        display: inline-block;
        padding: 1px 8px;
        border-radius: 6px;
        font-size: 0.7rem;
        background: #eff6ff;
        color: #1d4ed8;
    }

    /* Hide Streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

_inject_css()

# ═══════════════════════════════════════════════════════════
#  Navigation
# ═══════════════════════════════════════════════════════════

PAGES = {
    "🏠 首页": "首页",
    "📦 产品": "产品",
    "🔍 获客": "获客",
    "📋 线索库": "线索库",
    "✉️ 开发信": "开发信",
    "📄 落地页": "落地页",
    "⚙️ 设置": "设置",
}

# Sidebar
with st.sidebar:
    st.markdown("## 🌍 TradeLead V3")
    st.caption("外贸获客 · 免费 · 零配置")

    current_page = st.session_state.get("page", "首页")

    for label, page_key in PAGES.items():
        is_active = page_key == current_page
        btn_type = "primary" if is_active else "secondary"
        if st.button(label, key=f"nav_{page_key}", use_container_width=True, type=btn_type):
            st.session_state.page = page_key
            st.rerun()

    st.divider()
    st.caption("目标市场：中东 · 非洲 · 中亚 · 东南亚 · 南亚 · 拉美 · 东欧")
    st.caption(f"v3.0 · {datetime.now().strftime('%Y-%m-%d')}")

page = st.session_state.get("page", "首页")

# ═══════════════════════════════════════════════════════════
#  Page: 首页
# ═══════════════════════════════════════════════════════════
if page == "首页":
    st.title("TradeLead Intel V3")
    st.caption("输入产品，选目标市场，自动找到潜在客户 → 导出表格，一键生成开发信")

    stats = count_leads()
    products = get_products()

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("产品数", len(products))
    with col2:
        st.metric("线索总数", stats["total"])
    with col3:
        st.metric("新线索", stats["new"])
    with col4:
        st.metric("高可信度", stats["high"])
    with col5:
        st.metric("已联系", stats["contacted"])

    st.divider()

    if not products:
        st.info("👋 还没有产品，去「📦 产品」页面添加第一个产品开始获客吧！")
        if st.button("开始添加产品 →", use_container_width=True, type="primary"):
            st.session_state.page = "产品"
            st.rerun()
    else:
        st.subheader("快速开始")
        product_names = [f"{p['product_name_cn']} ({p['product_name_en']})" for p in products]
        selected = st.selectbox("选择产品", product_names, key="quick_product")
        if st.button("🚀 为这个产品搜索客户", use_container_width=True, type="primary"):
            idx = product_names.index(selected)
            st.session_state.acquisition_product_id = products[idx]["id"]
            st.session_state.acquisition_product_name = products[idx]["product_name_cn"]
            st.session_state.page = "获客"
            st.rerun()

    # Recent leads
    if stats["total"] > 0:
        st.divider()
        st.subheader("最新线索")
        recent = query("SELECT company_name, country, city, source_channel, confidence, created_at FROM leads ORDER BY created_at DESC LIMIT 10")
        if recent:
            df = pd.DataFrame(recent)
            df.columns = ["公司名", "国家", "城市", "来源", "可信度", "时间"]
            st.dataframe(df, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════
#  Page: 产品
# ═══════════════════════════════════════════════════════════
elif page == "产品":
    st.title("📦 产品库")

    tab1, tab2 = st.tabs(["产品列表", "添加产品"])

    with tab1:
        products = get_products()
        if not products:
            st.info("还没有产品，切换到「添加产品」标签添加第一个产品")
        else:
            for p in products:
                with st.container():
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"**{p['product_name_cn']}** — {p['product_name_en']}")
                        st.caption(f"{p.get('category','')} · {p.get('sub_category','')} · FOB ${p.get('fob_price','-')}/pc · MOQ {p.get('moq','-')}")
                    with col2:
                        if st.button("🗑️ 删除", key=f"del_{p['id']}"):
                            delete_product(p["id"])
                            st.rerun()
                    st.divider()

    with tab2:
        st.subheader("添加新产品")
        with st.form("add_product_form"):
            col1, col2 = st.columns(2)
            with col1:
                cn = st.text_input("中文产品名 *", placeholder="如：保温钉")
                category = st.text_input("品类", placeholder="如：建筑五金")
                keywords = st.text_input("英文搜索关键词 *（逗号分隔）", placeholder="如：insulation anchor, EIFS anchor, wall anchor")
                desc_cn = st.text_area("中文描述", placeholder="产品介绍...")
                spec = st.text_input("规格/型号", placeholder="如：IA-10×100")
                fob = st.number_input("FOB报价 (USD)", min_value=0.0, step=0.01, format="%.3f")
                images = st.file_uploader("产品图片（可多选）", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

            with col2:
                en = st.text_input("英文产品名 *", placeholder="如：Insulation Anchor")
                sub_cat = st.text_input("子类目", placeholder="如：保温锚固件")
                desc_en = st.text_area("英文描述（用于开发信）", placeholder="Product description for outreach emails...")
                material = st.text_input("材质", placeholder="如：PP/PA6尼龙 + 镀锌钢")
                moq = st.text_input("起订量 (MOQ)", placeholder="如：10000 pcs")

            submitted = st.form_submit_button("✅ 添加产品", use_container_width=True, type="primary")
            if submitted:
                if not cn or not en or not keywords:
                    st.error("中文名、英文名、搜索关键词为必填项")
                else:
                    add_product({
                        "product_name_cn": cn,
                        "product_name_en": en,
                        "category": category,
                        "sub_category": sub_cat,
                        "keywords_en": keywords,
                        "description_cn": desc_cn,
                        "description_en": desc_en,
                        "specifications": spec,
                        "material": material,
                        "fob_price": fob,
                        "moq": moq,
                    })
                    st.success(f"产品「{cn}」已添加！")
                    st.rerun()

# ═══════════════════════════════════════════════════════════
#  Page: 获客
# ═══════════════════════════════════════════════════════════
elif page == "获客":
    st.title("🔍 获客搜索")

    products = get_products()
    if not products:
        st.warning("请先去「📦 产品」页面添加产品")
        st.stop()

    # Step 1: Select product
    st.subheader("① 选择产品")
    product_names = [f"{p['product_name_cn']} ({p['product_name_en']})" for p in products]
    # Pre-select from quick action
    default_idx = 0
    if "acquisition_product_id" in st.session_state:
        for i, p in enumerate(products):
            if p["id"] == st.session_state.acquisition_product_id:
                default_idx = i
                break
    selected_prod = st.selectbox("", product_names, index=default_idx, label_visibility="collapsed")
    prod_idx = product_names.index(selected_prod)
    product = products[prod_idx]

    st.divider()

    # Step 2: Select market
    st.subheader("② 选择目标市场")

    col1, col2, col3 = st.columns(3)
    with col1:
        region = st.selectbox("大区域", get_regions(), key="region")
    with col2:
        countries = get_countries_for_region(region)
        country_names = [c[1] for c in countries]
        selected_country = st.selectbox("国家", country_names, key="country")
    with col3:
        cities = get_cities_for_country(selected_country)
        city_options = ["（不限城市）"] + [c[1] for c in cities]
        selected_city = st.selectbox("城市（可选）", city_options, key="city")
        city_en = ""
        if selected_city != "（不限城市）":
            for c in cities:
                if c[1] == selected_city:
                    city_en = c[0]
                    break

    st.divider()

    # Step 3: Select channels
    st.subheader("③ 选择获客渠道")

    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        use_yellowpages = st.checkbox("📒 黄页采集", value=True)
        if use_yellowpages:
            yp_sources = st.multiselect(
                "黄页来源",
                ["europages.com", "kompass.com", "tradekey.com", "yellowpages.ae",
                 "yellowpages.com.ng", "exportersindia.com", "alibaba.com"],
                default=["tradekey.com", "europages.com"],
            )
    with col_b:
        use_google = st.checkbox("🔍 Google搜索", value=True)
    with col_c:
        use_whois = st.checkbox("🌐 WHOIS反查", value=False)
        if use_whois:
            st.caption("对搜索到的域名进行WHOIS查询")
    with col_d:
        use_maps = st.checkbox("📍 Google Maps", value=False)
        if use_maps:
            st.caption("需要配置 Google API Key（免费额度）")

    st.divider()

    # Step 4: Search preview
    st.subheader("④ 搜索关键词预览")
    keyword_previews = search_keywords_template(product["keywords_en"], selected_country, city_en)
    for kw in keyword_previews[:8]:
        st.code(kw, language=None)

    st.divider()

    # Step 5: Execute
    st.subheader("⑤ 开始获客")
    st.caption("系统会自动排队搜索，请耐心等待（约需 2-5 分钟）")

    channels = []
    if use_yellowpages:
        channels.append("yellow_pages")
    if use_google:
        channels.append("google_search")
    if use_whois:
        channels.append("whois")
    if use_maps:
        channels.append("google_maps")

    if st.button("🚀 开始搜索", use_container_width=True, type="primary", disabled=not channels):
        if not channels:
            st.error("请至少选择一个获客渠道")
        else:
            with st.spinner(f"正在搜索... 产品: {product['product_name_en']} | 市场: {selected_country} {city_en}"):
                try:
                    summary = run_acquisition(
                        product_id=product["id"],
                        product_keywords=product["keywords_en"],
                        region=region,
                        country_cn=selected_country,
                        city_en=city_en,
                        channels=channels,
                        yellow_page_sources=yp_sources if use_yellowpages else None,
                    )
                    st.success("✅ 搜索完成！")
                    for ch, count in summary.items():
                        st.write(f"- {ch}: 找到 {count} 条线索")
                    st.info("转到「📋 线索库」页面查看结果")
                    if st.button("查看线索 →", use_container_width=True):
                        st.session_state.page = "线索库"
                        st.rerun()
                except Exception as e:
                    st.error(f"搜索过程出错：{e}")

# ═══════════════════════════════════════════════════════════
#  Page: 线索库
# ═══════════════════════════════════════════════════════════
elif page == "线索库":
    st.title("📋 线索库")

    # Filters
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        filter_status = st.selectbox("状态", ["全部", "新线索", "已联系", "已忽略"], key="lead_filter_status")
    with col2:
        filter_confidence = st.selectbox("可信度", ["全部", "高", "中", "低", "未知"], key="lead_filter_conf")
    with col3:
        filter_country = st.text_input("国家筛选（可选）", key="lead_filter_country")
    with col4:
        # Export
        if st.button("📥 导出 Excel", use_container_width=True, type="primary"):
            df = export_leads_to_df()
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="线索")
            st.download_button(
                label="⬇️ 下载 Excel",
                data=output.getvalue(),
                file_name=f"TradeLead_线索_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    # Build query params
    status_map = {"新线索": "new", "已联系": "contacted", "已忽略": "ignored"}
    conf_map = {"高": "high", "中": "medium", "低": "low", "未知": "unknown"}
    s = status_map.get(filter_status)
    c = conf_map.get(filter_confidence)
    country = filter_country if filter_country else None

    leads = get_leads(status=s, confidence=c, country=country)

    if not leads:
        st.info("还没有线索。去「🔍 获客」页面搜索客户吧！")
    else:
        st.caption(f"共 {len(leads)} 条线索")

        for lead in leads:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    conf_badge = {
                        "high": "🟢 高", "medium": "🟡 中",
                        "low": "🔴 低", "unknown": "⚪ 未知",
                    }.get(lead.get("confidence", "unknown"), "⚪ 未知")
                    st.markdown(f"**{lead['company_name']}**")
                    st.caption(f"{lead.get('country','')} {lead.get('city','')} · {conf_badge} · {lead.get('source_channel','')}")
                    if lead.get("website"):
                        st.caption(f"🔗 {lead['website']}")
                with col2:
                    if lead.get("email"):
                        st.caption(f"📧 {lead['email'][:40]}")
                    if lead.get("phone"):
                        st.caption(f"📞 {lead['phone'][:30]}")
                with col3:
                    status_label = {"new": "新", "contacted": "已联系", "ignored": "已忽略"}.get(lead.get("status", "new"), "新")
                    new_status = st.selectbox("状态", ["新", "已联系", "已忽略"],
                                              index=["新", "已联系", "已忽略"].index(status_label),
                                              key=f"status_{lead['id']}", label_visibility="collapsed")
                    status_rev = {"新": "new", "已联系": "contacted", "已忽略": "ignored"}
                    if status_rev[new_status] != lead.get("status"):
                        update_lead(lead["id"], status=status_rev[new_status])
                        st.rerun()
                with col4:
                    if st.button("🔍 背调", key=f"dd_{lead['id']}"):
                        with st.spinner("正在背调..."):
                            website = lead.get("website", "")
                            if not website:
                                st.warning("该公司没有网址，无法背调")
                            else:
                                diligence = run_diligence(lead["id"], website)
                                confidence = rate_confidence(diligence)
                                save_diligence(diligence)
                                update_lead(lead["id"], confidence=confidence, diligence_done=1)
                                st.success(f"背调完成 — 可信度: {confidence}")
                                st.rerun()
                st.divider()

# ═══════════════════════════════════════════════════════════
#  Page: 开发信
# ═══════════════════════════════════════════════════════════
elif page == "开发信":
    st.title("✉️ 开发信生成器")

    products = get_products()
    leads = get_leads()

    if not products:
        st.warning("请先添加产品")
        st.stop()
    if not leads:
        st.warning("请先搜索客户")
        st.stop()

    col1, col2, col3 = st.columns(3)
    with col1:
        prod_names = [f"{p['product_name_cn']}" for p in products]
        sel_prod = st.selectbox("选择产品", prod_names, key="outreach_product")
        product = products[prod_names.index(sel_prod)]
    with col2:
        lead_names = [f"{l['company_name']} ({l.get('country','')})" for l in leads]
        sel_lead = st.selectbox("选择客户", lead_names, key="outreach_lead")
        lead = leads[lead_names.index(sel_lead)]
    with col3:
        language = get_language_for_country(lead.get("country", ""))
        lang_options = {"en": "英语 English", "ar": "阿拉伯语 Arabic", "ru": "俄语 Russian",
                        "fr": "法语 French", "es": "西班牙语 Spanish", "pt": "葡萄牙语 Portuguese"}
        sel_lang = st.selectbox("语言", list(lang_options.values()),
                                index=list(lang_options.keys()).index(language) if language in lang_options else 0,
                                key="outreach_lang")
        lang_key = {v: k for k, v in lang_options.items()}[sel_lang]

    template_type = st.radio("模板类型", ["初次联系", "报价推介", "跟进邮件"], horizontal=True,
                             key="outreach_template")
    type_map = {"初次联系": "first_contact", "报价推介": "quote", "跟进邮件": "followup"}

    if st.button("📝 生成开发信", use_container_width=True, type="primary"):
        result = generate_outreach(
            product=product,
            lead=lead,
            language=lang_key,
            template_type=type_map[template_type],
        )

        st.divider()
        st.subheader("📧 邮件")
        st.text_input("邮件标题", result["subject"], key="email_subject")
        st.text_area("邮件正文", result["body"], height=300, key="email_body")
        st.button("📋 复制邮件正文", key="copy_email", on_click=lambda: st.write("已复制！"))  # Simplified

        st.divider()
        st.subheader("💬 WhatsApp")
        st.text_area("WhatsApp 消息", result["whatsapp"], height=100, key="wa_msg")
        st.button("📋 复制 WhatsApp", key="copy_wa")

        if st.button("💾 保存开发信", use_container_width=True):
            save_outreach({
                "lead_id": lead["id"],
                "product_id": product["id"],
                "language": lang_key,
                "template_type": type_map[template_type],
                "email_subject": result["subject"],
                "email_body": result["body"],
                "whatsapp_msg": result["whatsapp"],
            })
            st.success("开发信已保存！")

# ═══════════════════════════════════════════════════════════
#  Page: 落地页
# ═══════════════════════════════════════════════════════════
elif page == "落地页":
    st.title("📄 产品落地页")

    products = get_products()
    if not products:
        st.warning("请先添加产品")
        st.stop()

    col1, col2 = st.columns(2)
    with col1:
        prod_names = [f"{p['product_name_cn']}" for p in products]
        sel_prod = st.selectbox("选择产品", prod_names, key="lp_product")
        product = products[prod_names.index(sel_prod)]
    with col2:
        lang_options = {"en": "英语", "ar": "阿拉伯语", "ru": "俄语",
                        "fr": "法语", "es": "西班牙语", "pt": "葡萄牙语"}
        sel_lang = st.selectbox("页面语言", list(lang_options.values()), key="lp_lang")
        lang_key = {v: k for k, v in lang_options.items()}[sel_lang]

    if st.button("🎨 生成落地页", use_container_width=True, type="primary"):
        html = generate_landing_page(product, lang_key)
        st.divider()
        st.subheader("预览")
        st.components.v1.html(html, height=600, scrolling=True)

        st.divider()
        st.download_button(
            label="⬇️ 下载 HTML 文件",
            data=html,
            file_name=f"{product['product_name_en'].replace(' ','_')}_landing_{lang_key}.html",
            mime="text/html",
            use_container_width=True,
        )
        st.caption("下载后可以托管到 GitHub Pages 或 Netlify（免费），然后把链接发给客户")

# ═══════════════════════════════════════════════════════════
#  Page: 设置
# ═══════════════════════════════════════════════════════════
elif page == "设置":
    st.title("⚙️ 设置")

    st.subheader("发件人信息（用于开发信落款）")
    col1, col2, col3 = st.columns(3)
    with col1:
        sender_name = st.text_input("你的名字", value=get_setting("sender_name") or "", key="set_name")
    with col2:
        sender_company = st.text_input("公司名称", value=get_setting("sender_company") or "", key="set_company")
    with col3:
        sender_email = st.text_input("邮箱", value=get_setting("sender_email") or "", key="set_email")

    sender_phone = st.text_input("电话/WhatsApp", value=get_setting("sender_phone") or "", key="set_phone")

    if st.button("💾 保存设置", use_container_width=True, type="primary"):
        set_setting("sender_name", sender_name)
        set_setting("sender_company", sender_company)
        set_setting("sender_email", sender_email)
        set_setting("sender_phone", sender_phone)
        st.success("设置已保存！")

    st.divider()

    st.subheader("黄页源管理")
    st.caption("勾选要使用的黄页网站（获客时会从这些网站搜索客户）")
    default_sources = [
        ("europages.com", "Europages（欧洲B2B目录）"),
        ("kompass.com", "Kompass（全球B2B数据库）"),
        ("tradekey.com", "TradeKey（进出口商目录）"),
        ("yellowpages.ae", "阿联酋黄页"),
        ("yellowpages.co.za", "南非黄页"),
        ("yellowpages.com.ng", "尼日利亚黄页"),
        ("exportersindia.com", "Exporters India（印度出口商）"),
        ("turkishexporter.net", "Turkish Exporter（土耳其出口商）"),
        ("alibaba.com", "Alibaba（全球供应商）"),
    ]
    for src, label in default_sources:
        st.checkbox(label, value=True, key=f"src_{src}")

    st.divider()
    st.subheader("⚠️ 免责声明")
    st.caption(
        "本工具从公开网页采集信息，仅供外贸业务参考。"
        "请遵守目标网站的使用条款，合理控制请求频率。"
        "系统已内置 2-5 秒随机延迟和 User-Agent 轮换，防止被封。"
        "所有采集结果未经人工审核，请自行核实客户信息。"
    )
