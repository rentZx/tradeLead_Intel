"""
TradeLead Intel V3.0 — Main Application
======================================
面向外贸销售人员的获客工具，全部点选操作，零代码配置。
7 个页面，4 种免费获客渠道，1 键导出 Excel。
"""

from __future__ import annotations

import io
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

# ── Page config (must be first Streamlit call) ──────────────
st.set_page_config(
    page_title="TradeLead Intel",
    page_icon=":material/travel_explore:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Database init ──────────────────────────────────────────
from src.db_v3 import (
    init_db, add_product, get_products, get_product, delete_product,
    add_lead, get_leads, update_lead, count_leads,
    create_task, update_task, get_tasks,
    save_diligence, get_diligence,
    get_qualifications,
    save_outreach, get_outreach,
    export_leads_to_df,
    get_setting, set_setting, query,
)
from src.market_data import (
    get_regions, get_countries_for_region, get_cities_for_country,
    get_subregions_for_country, get_language_for_country,
    get_country_english_name, search_keywords_template,
)
from src.scraper import run_acquisition
from src.diligence import run_diligence, rate_confidence
from src.extractor import extract_contacts_from_html
from src.outreach_v3 import generate_outreach, generate_landing_page
from src.product_intelligence import analyze_product
from src.qualification import (
    backfill_missing_qualifications,
    evaluate_and_save,
)

# Initialize database on first run
if "db_initialized" not in st.session_state:
    init_db()
    backfill_missing_qualifications()
    st.session_state.db_initialized = True

def page_header(title: str, subtitle: str, icon: str) -> None:
    """Render a consistent workspace page header."""
    st.title(f":material/{icon}: {title}")
    st.caption(subtitle)


def section_header(title: str, subtitle: str = "") -> None:
    """Render a compact section heading with optional supporting copy."""
    st.subheader(title)
    if subtitle:
        st.caption(subtitle)


def csv_values(value: str | None) -> list[str]:
    """Split comma-delimited profile values for compact UI display."""
    return [item.strip() for item in (value or "").split(",") if item.strip()]


def render_profile_items(value: str | None, empty_text: str = "尚未配置") -> None:
    items = csv_values(value)
    if not items:
        st.caption(empty_text)
        return
    for item in items:
        st.markdown(f"- {item}")


@st.dialog("删除产品")
def confirm_product_delete(product_id: int, product_name: str) -> None:
    st.write(f"确定删除“{product_name}”吗？此操作无法撤销。")
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("取消", key=f"cancel_delete_{product_id}"):
            st.rerun()
        if st.button(
            "确认删除",
            key=f"confirm_delete_{product_id}",
            type="primary",
            icon=":material/delete:",
        ):
            delete_product(product_id)
            st.toast("产品已删除", icon=":material/check_circle:")
            st.rerun()

# ═══════════════════════════════════════════════════════════
#  Navigation
# ═══════════════════════════════════════════════════════════

PAGES = [
    ("首页", "业务总览", "home"),
    ("产品", "产品与买家画像", "inventory_2"),
    ("获客", "搜索与采集", "travel_explore"),
    ("线索库", "线索与资格判定", "patient_list"),
    ("开发信", "外联内容", "outgoing_mail"),
    ("落地页", "产品页面", "web"),
    ("设置", "系统设置", "settings"),
]

# Sidebar
with st.sidebar:
    st.markdown("## :material/travel_explore: TradeLead")
    st.caption("B2B 买家发现与外联工作台")
    st.space("small")

    current_page = st.session_state.get("page", "首页")

    for page_key, label, icon in PAGES:
        is_active = page_key == current_page
        btn_type = "primary" if is_active else "secondary"
        if st.button(
            label,
            key=f"nav_{page_key}",
            width="stretch",
            type=btn_type,
            icon=f":material/{icon}:",
        ):
            st.session_state.page = page_key
            st.rerun()

    st.space("medium")
    sidebar_stats = count_leads()
    sidebar_products = get_products()
    with st.container(border=True):
        st.markdown("**工作区状态**")
        st.caption(f"{len(sidebar_products)} 个产品 · {sidebar_stats['total']} 条线索")
        if sidebar_stats["total"]:
            st.caption(
                f"{sidebar_stats['new']} 条待处理 · "
                f"{sidebar_stats['contacted']} 条已联系"
            )
        else:
            st.caption("从添加产品开始建立获客流程")
    st.caption(f"TradeLead V3 · {datetime.now().strftime('%Y-%m-%d')}")

page = st.session_state.get("page", "首页")

# ═══════════════════════════════════════════════════════════
#  Page: 首页
# ═══════════════════════════════════════════════════════════
if page == "首页":
    stats = count_leads()
    products = get_products()
    page_header(
        "业务总览",
        "从产品解析、买家搜索、资格判定到开发信，集中管理外贸获客进度。",
        "space_dashboard",
    )

    with st.container(border=True):
        hero_left, hero_right = st.columns([1.35, 1], vertical_alignment="center")
        with hero_left:
            st.badge(
                "B2B buyer intelligence",
                color="blue",
                icon=":material/verified:",
            )
            st.header("把产品信息转化为可联系的海外买家")
            st.write(
                "系统会识别经销渠道与终端需求方，跨渠道收集公开商家资料，"
                "再根据产品匹配度筛出值得推广的客户。"
            )
        with hero_right:
            if products:
                product_names = [
                    f"{p['product_name_cn']}（{p['product_name_en']}）"
                    for p in products
                ]
                selected = st.selectbox(
                    "选择一个产品开始获客",
                    product_names,
                    key="quick_product",
                )
                if st.button(
                    "开始搜索买家",
                    width="stretch",
                    type="primary",
                    icon=":material/travel_explore:",
                ):
                    idx = product_names.index(selected)
                    st.session_state.acquisition_product_id = products[idx]["id"]
                    st.session_state.acquisition_product_name = products[idx]["product_name_cn"]
                    st.session_state.page = "获客"
                    st.rerun()
            else:
                st.markdown("**先建立第一个产品档案**")
                st.caption("输入产品名称后，系统会自动生成买家画像和搜索关键词。")
                if st.button(
                    "添加产品",
                    width="stretch",
                    type="primary",
                    icon=":material/add_circle:",
                ):
                    st.session_state.page = "产品"
                    st.rerun()

    with st.container(horizontal=True):
        st.metric("产品档案", len(products), border=True)
        st.metric("全部线索", stats["total"], border=True)
        st.metric("待处理", stats["new"], border=True)
        st.metric("高可信度", stats["high"], border=True)
        st.metric("已联系", stats["contacted"], border=True)

    section_header(
        "标准获客流程",
        "每一步都保留判断依据，方便业务人员复核和继续跟进。",
    )
    workflow_cols = st.columns(4)
    workflow_steps = [
        (
            "looks_one",
            "解析产品",
            "识别品类、英文关键词、经销渠道和终端需求方。",
        ),
        (
            "looks_two",
            "搜索市场",
            "按国家、行政区和城市组合免费及商业数据渠道。",
        ),
        (
            "looks_3",
            "筛选买家",
            "结合产品、渠道、需求信号和公开资料进行资格判定。",
        ),
        (
            "looks_4",
            "开展外联",
            "生成多语言邮件、WhatsApp 消息和产品落地页。",
        ),
    ]
    for column, (icon, title, description) in zip(workflow_cols, workflow_steps):
        with column.container(border=True, height="stretch"):
            st.markdown(f"### :material/{icon}: {title}")
            st.caption(description)

    if stats["total"] > 0:
        section_header("最近新增线索", "快速查看最新采集的商家和资料完整度。")
        recent = query(
            "SELECT company_name, country, city, source_channel, confidence, "
            "website, email, phone, created_at FROM leads "
            "ORDER BY created_at DESC LIMIT 8"
        )
        if recent:
            df = pd.DataFrame(recent)
            df.columns = [
                "公司名称", "国家", "城市", "来源", "可信度",
                "官网", "邮箱", "电话", "创建时间",
            ]
            st.dataframe(
                df,
                hide_index=True,
                column_config={
                    "公司名称": st.column_config.TextColumn(pinned=True),
                    "官网": st.column_config.LinkColumn(display_text="打开官网"),
                },
            )
            with st.container(horizontal=True, horizontal_alignment="right"):
                if st.button(
                    "查看全部线索",
                    icon=":material/arrow_forward:",
                    key="home_all_leads",
                ):
                    st.session_state.page = "线索库"
                    st.rerun()

# ═══════════════════════════════════════════════════════════
#  Page: 产品
# ═══════════════════════════════════════════════════════════
elif page == "产品":
    products = get_products()
    page_header(
        "产品与买家画像",
        "管理产品资料，并自动推导适合推广的经销渠道和终端需求方。",
        "inventory_2",
    )

    with st.container(horizontal=True):
        st.metric("产品总数", len(products), border=True)
        st.metric(
            "画像已生成",
            sum(bool(item.get("buyer_types")) for item in products),
            border=True,
        )
        st.metric(
            "含英文关键词",
            sum(bool(item.get("keywords_en")) for item in products),
            border=True,
        )

    tab1, tab2 = st.tabs(
        [":material/inventory_2: 产品目录", ":material/add_circle: 添加产品"]
    )

    with tab1:
        if not products:
            st.info(
                "还没有产品。切换到“添加产品”，系统会自动解析英文名称、"
                "关键词和买家画像。",
                icon=":material/info:",
            )
        else:
            for p in products:
                with st.container(border=True):
                    title_col, action_col = st.columns(
                        [5, 1], vertical_alignment="center"
                    )
                    with title_col:
                        st.subheader(p["product_name_cn"])
                        st.caption(p.get("product_name_en") or "英文名称待补充")
                        with st.container(horizontal=True):
                            if p.get("category"):
                                st.badge(p["category"], color="blue")
                            if p.get("sub_category"):
                                st.badge(p["sub_category"], color="gray")
                            if p.get("fob_price"):
                                st.badge(f"FOB ${p['fob_price']}", color="green")
                            if p.get("moq"):
                                st.badge(f"MOQ {p['moq']}", color="orange")
                    with action_col:
                        if st.button(
                            "删除",
                            key=f"del_{p['id']}",
                            icon=":material/delete:",
                            width="stretch",
                        ):
                            confirm_product_delete(
                                p["id"], p.get("product_name_cn") or "未命名产品"
                            )

                    profile_cols = st.columns(3)
                    with profile_cols[0].container(height="stretch"):
                        st.markdown("**:material/storefront: 经销渠道**")
                        render_profile_items(p.get("buyer_types"))
                    with profile_cols[1].container(height="stretch"):
                        st.markdown("**:material/factory: 终端需求方**")
                        render_profile_items(p.get("end_user_types"))
                    with profile_cols[2].container(height="stretch"):
                        st.markdown("**:material/block: 排除对象**")
                        render_profile_items(p.get("exclude_terms"), "无明确排除项")

                    if p.get("analysis_reasoning"):
                        with st.expander(
                            "查看画像判定依据",
                            icon=":material/psychology:",
                        ):
                            st.write(p["analysis_reasoning"])

    with tab2:
        section_header(
            "建立产品档案",
            "只需填写中文产品名；英文关键词和买家画像可由系统自动生成，也可人工覆盖。",
        )
        with st.form("add_product_form"):
            st.markdown("#### 基础信息")
            col1, col2 = st.columns(2)
            with col1:
                cn = st.text_input("中文产品名 *", placeholder="如：保温钉")
                category = st.text_input("品类（可留空自动识别）", placeholder="如：建筑五金")
                keywords = st.text_input("英文搜索关键词（可留空自动生成）", placeholder="如：insulation anchor, EIFS anchor")
                desc_cn = st.text_area("中文描述", placeholder="产品介绍...")
                spec = st.text_input("规格/型号", placeholder="如：IA-10×100")
                fob = st.number_input("FOB报价 (USD)", min_value=0.0, step=0.01, format="%.3f")
                images = st.file_uploader("产品图片（可多选）", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

            with col2:
                en = st.text_input("英文产品名（可留空自动生成）", placeholder="如：Insulation Anchor")
                sub_cat = st.text_input("子类目", placeholder="如：保温锚固件")
                desc_en = st.text_area("英文描述（用于开发信）", placeholder="Product description for outreach emails...")
                material = st.text_input("材质", placeholder="如：PP/PA6尼龙 + 镀锌钢")
                moq = st.text_input("起订量 (MOQ)", placeholder="如：10000 pcs")
                buyer_override = st.text_area(
                    "经销渠道类型（可留空自动生成）",
                    placeholder="例如 insulation materials distributor, building materials importer",
                )
                end_user_override = st.text_area(
                    "终端需求方类型（可留空自动生成）",
                    placeholder="例如 facade contractor, construction company",
                )
                exclude_override = st.text_input(
                    "排除词（可留空自动生成）",
                    placeholder="例如 nail salon, beauty",
                )

            submitted = st.form_submit_button(
                "保存并解析产品",
                width="stretch",
                type="primary",
                icon=":material/auto_awesome:",
            )
            if submitted:
                profile = analyze_product(
                    product_name_cn=cn,
                    product_name_en=en,
                    category=category,
                    sub_category=sub_cat,
                    description=f"{desc_cn} {desc_en}",
                    keywords_en=keywords,
                    buyer_types=buyer_override,
                    end_user_types=end_user_override,
                    exclude_terms=exclude_override,
                )
                if not cn:
                    st.error("中文产品名为必填项")
                elif not profile.product_name_en or not profile.keywords_en:
                    st.error("暂时无法自动识别该产品，请补充英文产品名或英文搜索关键词")
                else:
                    image_dir = Path("outputs/product_images")
                    image_dir.mkdir(parents=True, exist_ok=True)
                    saved_images = []
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    for index, uploaded in enumerate(images[:3]):
                        suffix = Path(uploaded.name).suffix.lower()
                        image_path = image_dir / f"{timestamp}_{index + 1}{suffix}"
                        image_path.write_bytes(uploaded.getvalue())
                        saved_images.append(str(image_path))
                    add_product({
                        "product_name_cn": cn,
                        "product_name_en": profile.product_name_en,
                        "category": profile.category,
                        "sub_category": profile.sub_category,
                        "keywords_en": ", ".join(profile.keywords_en),
                        "buyer_types": ", ".join(profile.buyer_types),
                        "end_user_types": ", ".join(profile.end_user_types),
                        "exclude_terms": ", ".join(profile.exclude_terms),
                        "analysis_reasoning": profile.reasoning,
                        "description_cn": desc_cn,
                        "description_en": desc_en,
                        "specifications": spec,
                        "material": material,
                        "fob_price": fob,
                        "moq": moq,
                        "image_paths": ",".join(saved_images),
                    })
                    st.success(
                        f"产品「{cn}」已识别为“{profile.category} / {profile.sub_category}”，"
                        f"生成 {len(profile.buyer_types)} 类目标客户。",
                        icon=":material/check_circle:",
                    )
                    st.rerun()

# ═══════════════════════════════════════════════════════════
#  Page: 获客
# ═══════════════════════════════════════════════════════════
elif page == "获客":
    page_header(
        "搜索与采集",
        "组合产品画像、目标市场和数据渠道，采集公开商家信息并自动去重。",
        "travel_explore",
    )

    products = get_products()
    if not products:
        st.warning(
            "请先建立产品档案，系统需要产品关键词和买家画像才能搜索。",
            icon=":material/warning:",
        )
        st.stop()

    # Step 1: Select product
    section_header("1. 选择产品", "搜索将围绕该产品的经销渠道与终端需求方展开。")
    product_names = [f"{p['product_name_cn']} ({p['product_name_en']})" for p in products]
    # Pre-select from quick action
    default_idx = 0
    if "acquisition_product_id" in st.session_state:
        for i, p in enumerate(products):
            if p["id"] == st.session_state.acquisition_product_id:
                default_idx = i
                break
    selected_prod = st.selectbox(
        "选择产品",
        product_names,
        index=default_idx,
        label_visibility="collapsed",
    )
    prod_idx = product_names.index(selected_prod)
    product = products[prod_idx]
    with st.container(border=True):
        profile_cols = st.columns(3)
        with profile_cols[0]:
            st.markdown("**:material/storefront: 经销渠道画像**")
            render_profile_items(product.get("buyer_types"))
        with profile_cols[1]:
            st.markdown("**:material/factory: 终端需求方画像**")
            render_profile_items(product.get("end_user_types"))
        with profile_cols[2]:
            st.markdown("**:material/block: 排除对象**")
            render_profile_items(product.get("exclude_terms"), "无明确排除项")
        if product.get("analysis_reasoning"):
            st.caption(f"判定依据：{product['analysis_reasoning']}")

    st.space("small")

    # Step 2: Select market
    section_header(
        "2. 选择目标市场",
        "行政区和城市均为可选；范围越小，结果越聚焦，但可能减少覆盖量。",
    )

    with st.container(border=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            region = st.selectbox("大区域", get_regions(), key="region")
        with col2:
            countries = get_countries_for_region(region)
            country_names = [c[1] for c in countries]
            selected_country = st.selectbox("国家", country_names, key="country")
        with col3:
            subregions = get_subregions_for_country(selected_country)
            subregion_labels = ["（不限州/省）"] + [
                f"{item_cn}（{item_en}）" for item_en, item_cn in subregions
            ] + ["其他（手工输入英文）"]
            selected_subregion = st.selectbox(
                "州/省/行政区（可选）",
                subregion_labels,
                key=f"subregion_{selected_country}",
            )
            subregion_en = ""
            if selected_subregion == "其他（手工输入英文）":
                subregion_en = st.text_input(
                    "行政区英文名",
                    placeholder="例如 Rayong Province",
                    key=f"custom_subregion_{selected_country}",
                ).strip()
            elif selected_subregion != "（不限州/省）":
                subregion_en = subregions[
                    subregion_labels.index(selected_subregion) - 1
                ][0]
        with col4:
            cities = get_cities_for_country(selected_country)
            city_options = ["（不限城市）"] + [
                f"{item_cn}（{item_en}）" for item_en, item_cn in cities
            ] + ["其他（手工输入英文）"]
            selected_city = st.selectbox(
                "城市（可选）",
                city_options,
                key=f"city_{selected_country}",
            )
            city_en = ""
            if selected_city == "其他（手工输入英文）":
                city_en = st.text_input(
                    "城市英文名",
                    placeholder="例如 Rayong",
                    key=f"custom_city_{selected_country}",
                ).strip()
            elif selected_city != "（不限城市）":
                city_en = cities[city_options.index(selected_city) - 1][0]

    st.space("small")

    # Step 3: Select search mode
    section_header(
        "3. 选择搜索渠道",
        "可同时运行多个渠道；结果会按公司、官网和联系方式自动去重。",
    )
    from src.scraper import configured_providers
    provider_status = configured_providers()
    provider_options = {
        "DuckDuckGo 免费网页搜索": "ddg",
        "公开黄页（按国家自动选择）": "yellow_pages",
        "OpenStreetMap 商家": "osm",
        "Brave Search API": "brave",
        "Google Places 商家搜索": "google_places",
        "SerpAPI 第三方搜索": "serpapi",
        "Foursquare Places 商家搜索": "foursquare",
        "OpenCorporates 企业注册": "opencorporates",
        "People Data Labs 企业库": "pdl",
    }
    default_channels = ["OpenStreetMap 商家"]
    if provider_status.get("ddg"):
        default_channels = [
            "DuckDuckGo 免费网页搜索",
            "公开黄页（按国家自动选择）",
            "OpenStreetMap 商家",
        ]
    with st.container(border=True):
        selected_labels = st.multiselect(
            "搜索渠道",
            list(provider_options),
            default=default_channels,
            help="免费渠道无需 API Key；商业渠道需先在环境变量中配置账号。",
        )
    channels = [provider_options[label] for label in selected_labels]
    if not channels:
        st.info("请至少选择一个搜索渠道", icon=":material/info:")

    channel_cols = st.columns(3)
    with channel_cols[0].container(border=True, height="stretch"):
        st.markdown("**网页与黄页**")
        if provider_status.get("ddg"):
            st.badge("可用", color="green", icon=":material/check:")
            st.caption("DuckDuckGo 与公开黄页发现")
        else:
            st.badge("受限", color="orange", icon=":material/warning:")
            st.caption("当前出口触发验证码，可改用其他渠道")
    with channel_cols[1].container(border=True, height="stretch"):
        st.markdown("**地图商家**")
        if provider_status.get("osm"):
            st.badge("可用", color="green", icon=":material/check:")
        else:
            st.badge("暂不可用", color="red", icon=":material/error:")
        st.caption("OpenStreetMap，无需 API Key")
    with channel_cols[2].container(border=True, height="stretch"):
        configured_paid = [
            name for name, key in [
                ("Brave", "brave"),
                ("Google Places", "google_places"),
                ("SerpAPI", "serpapi"),
                ("Foursquare", "foursquare"),
                ("OpenCorporates", "opencorporates"),
                ("PDL", "pdl"),
            ] if provider_status.get(key)
        ]
        st.markdown("**商业数据源**")
        if configured_paid:
            st.badge(
                f"已配置 {len(configured_paid)} 项",
                color="green",
                icon=":material/check:",
            )
            st.caption("、".join(configured_paid))
        else:
            st.badge("尚未配置", color="gray", icon=":material/key:")
            st.caption("购买账号后可在环境变量中启用")

    st.space("small")

    # Step 4: Search preview
    section_header(
        "4. 确认搜索关键词",
        "以下关键词由产品画像与目标地区自动组合，执行前可先检查方向是否正确。",
    )
    keyword_previews = search_keywords_template(
        product["keywords_en"], get_country_english_name(selected_country), city_en,
        product.get("category", ""), region, product.get("buyer_types", ""),
        product.get("end_user_types", ""),
        subregion_en=subregion_en,
    )
    with st.container(border=True):
        st.code("\n".join(keyword_previews[:8]), language=None)

    st.space("small")

    # Step 5: Execute
    section_header(
        "5. 执行采集",
        "搜索结果会直接保存到线索库，并自动进行产品匹配与买家资格判定。",
    )

    unavailable = [
        label for label, provider in provider_options.items()
        if provider in channels and not provider_status.get(provider, False)
    ]
    runnable_channels = [
        provider for provider in channels if provider_status.get(provider, False)
    ]
    if unavailable:
        st.warning(
            "以下渠道尚未配置或当前不可访问："
            + "、".join(unavailable)
            + "。其他已选渠道仍可继续执行。",
            icon=":material/warning:",
        )

    if st.button(
        "开始搜索并保存线索",
        width="stretch",
        type="primary",
        disabled=not runnable_channels,
        icon=":material/travel_explore:",
    ):
        if runnable_channels:
            with st.status(
                f"正在搜索 {selected_country} 的潜在买家",
                expanded=True,
            ) as search_status:
                st.write(f"产品：{product['product_name_en']}")
                st.write(
                    "范围："
                    + " / ".join(
                        value for value in [selected_country, subregion_en, city_en]
                        if value
                    )
                )
                st.write(f"渠道：{len(runnable_channels)} 个")
                try:
                    summary = run_acquisition(
                        product_id=product["id"],
                        product_keywords=product["keywords_en"],
                        region=region,
                        country_cn=selected_country,
                        city_en=city_en,
                        subregion_en=subregion_en,
                        channels=runnable_channels,
                        category=product.get("category", ""),
                        buyer_types=product.get("buyer_types", ""),
                        end_user_types=product.get("end_user_types", ""),
                        exclude_terms=product.get("exclude_terms", ""),
                    )
                    st.session_state.last_search_summary = summary
                    search_status.update(
                        label="搜索完成",
                        state="complete",
                        expanded=False,
                    )
                    st.success(
                        "搜索完成，结果已保存到线索库。",
                        icon=":material/check_circle:",
                    )
                    for ch, value in summary.items():
                        if ch.endswith("_error"):
                            st.error(f"{ch.removesuffix('_error')} 渠道失败：{value}")
                        else:
                            st.write(f"- {ch}: 找到 {value} 条线索")
                except RuntimeError as e:
                    search_status.update(
                        label="搜索未完成",
                        state="error",
                        expanded=True,
                    )
                    st.error(str(e))
                except Exception as e:
                    search_status.update(
                        label="搜索出现错误",
                        state="error",
                        expanded=True,
                    )
                    st.error(f"搜索出错：{e}")

    if st.session_state.get("last_search_summary") is not None:
        if st.button(
            "查看本次线索",
            key="go_to_leads_after_search",
            width="stretch",
            type="primary",
            icon=":material/arrow_forward:",
        ):
            st.session_state.page = "线索库"
            st.session_state.pop("last_search_summary", None)
            st.rerun()

# ═══════════════════════════════════════════════════════════
#  Page: 线索库
# ═══════════════════════════════════════════════════════════
elif page == "线索库":
    page_header(
        "线索与资格判定",
        "按照目标产品评估商家角色、匹配度和推广优先级，优先处理可联系的真实买家。",
        "patient_list",
    )

    all_leads = get_leads()
    qualification_products = get_products()
    product_label_map = {
        f"{item['product_name_cn']}（{item['product_name_en']}）": item["id"]
        for item in qualification_products
    }
    country_options = sorted({lead.get("country", "") for lead in all_leads if lead.get("country")})
    source_options = sorted({
        lead.get("source_channel", "") for lead in all_leads if lead.get("source_channel")
    })

    with st.expander(
        "筛选与视图",
        expanded=True,
        icon=":material/filter_list:",
    ):
        f1, f2, f3, f4 = st.columns(4)
        with f1:
            product_options = ["全部产品（取最高匹配）"] + list(product_label_map)
            selected_product_label = st.selectbox(
                "判定产品",
                product_options,
                index=1 if len(product_options) > 1 else 0,
                key="lead_qualification_product",
            )
        with f2:
            filter_verdict = st.selectbox(
                "推广资格",
                ["全部判定", "合格", "高潜", "待人工复核", "已淘汰", "尚未判定"],
                key="lead_filter_verdict",
            )
        with f3:
            filter_role = st.selectbox(
                "买家角色",
                ["全部角色", "经销/渠道客户", "终端需求方", "渠道兼终端", "角色待确认"],
                key="lead_filter_role",
            )
        with f4:
            filter_country = st.selectbox(
                "国家/地区", ["全部"] + country_options,
                key="lead_filter_country_select",
            )

        s1, s2, s3, s4 = st.columns(4)
        with s1:
            filter_status = st.selectbox(
                "跟进状态", ["全部", "新线索", "已联系", "已忽略"],
                key="lead_filter_status",
            )
        with s2:
            filter_source = st.selectbox(
                "线索来源", ["全部"] + source_options,
                key="lead_filter_source",
            )
        with s3:
            filter_confidence = st.selectbox(
                "资料可信度", ["全部", "高", "中", "低", "未知"],
                key="lead_filter_conf",
            )
        with s4:
            page_size = st.selectbox("每页", [10, 20, 50], key="lead_page_size")

        o1, o2, o3 = st.columns([2, 1, 1])
        with o1:
            valuable_only = st.checkbox(
                "只看有官网或联系方式",
                value=True,
                help="隐藏只有名称、没有官网/邮箱/电话/WhatsApp 的低价值目录记录",
            )
        with o2:
            view_mode = st.segmented_control(
                "展示方式", ["卡片", "表格"],
                default="卡片",
                key="lead_view_mode",
            )
        with o3:
            selected_product_id = product_label_map.get(selected_product_label)
            if st.button(
                "重新评估全部",
                width="stretch",
                disabled=not selected_product_id or not all_leads,
                help="使用现有公开资料重新计算，不产生 API 搜索费用",
                icon=":material/refresh:",
            ):
                with st.spinner("正在重新计算买家资格..."):
                    evaluated = sum(
                        bool(evaluate_and_save(lead["id"], selected_product_id))
                        for lead in all_leads
                    )
                st.success(f"已评估 {evaluated} 条线索")
                st.rerun()

    status_map = {"新线索": "new", "已联系": "contacted", "已忽略": "ignored"}
    confidence_map = {"高": "high", "中": "medium", "低": "low", "未知": "unknown"}
    verdict_map = {
        "合格": {"qualified"},
        "高潜": {"promising"},
        "待人工复核": {"review"},
        "已淘汰": {"rejected"},
        "尚未判定": {None},
    }
    role_map = {
        "经销/渠道客户": "channel_partner",
        "终端需求方": "end_user",
        "渠道兼终端": "mixed",
        "角色待确认": "unknown",
    }
    qualification_rows = get_qualifications(selected_product_id)
    qualification_by_lead: dict[int, dict] = {}
    for qualification in qualification_rows:
        lead_id = qualification["lead_id"]
        current = qualification_by_lead.get(lead_id)
        if (
            current is None
            or qualification.get("overall_score", 0) > current.get("overall_score", 0)
        ):
            qualification_by_lead[lead_id] = qualification
    for lead in all_leads:
        lead["_qualification"] = qualification_by_lead.get(lead["id"])

    leads = all_leads
    if filter_verdict != "全部判定":
        accepted_verdicts = verdict_map[filter_verdict]
        leads = [
            lead for lead in leads
            if (
                lead.get("_qualification", {}).get("verdict")
                if lead.get("_qualification") else None
            ) in accepted_verdicts
        ]
    if filter_role != "全部角色":
        leads = [
            lead for lead in leads
            if lead.get("_qualification")
            and lead["_qualification"].get("buyer_role") == role_map[filter_role]
        ]
    if filter_status != "全部":
        leads = [lead for lead in leads if lead.get("status") == status_map[filter_status]]
    if filter_confidence != "全部":
        leads = [
            lead for lead in leads
            if lead.get("confidence", "unknown") == confidence_map[filter_confidence]
        ]
    if filter_country != "全部":
        leads = [lead for lead in leads if lead.get("country") == filter_country]
    if filter_source != "全部":
        leads = [lead for lead in leads if lead.get("source_channel") == filter_source]
    if valuable_only:
        leads = [
            lead for lead in leads
            if any(lead.get(field) for field in ("website", "email", "phone", "whatsapp"))
        ]
    leads.sort(
        key=lambda lead: (
            lead.get("_qualification", {}).get("overall_score", -1)
            if lead.get("_qualification") else -1
        ),
        reverse=True,
    )

    contactable = sum(
        bool(lead.get("email") or lead.get("phone") or lead.get("whatsapp"))
        for lead in leads
    )
    qualified_count = sum(
        lead.get("_qualification", {}).get("verdict") == "qualified"
        for lead in leads if lead.get("_qualification")
    )
    promising_count = sum(
        lead.get("_qualification", {}).get("verdict") == "promising"
        for lead in leads if lead.get("_qualification")
    )
    with st.container(horizontal=True):
        st.metric("筛选结果", len(leads), border=True)
        st.metric("合格客户", qualified_count, border=True)
        st.metric("高潜客户", promising_count, border=True)
        st.metric("可直接联系", contactable, border=True)
        st.metric(
            "有官网",
            sum(bool(lead.get("website")) for lead in leads),
            border=True,
        )

    export_rows = [
        {
            "判定产品": (
                lead.get("_qualification", {}).get("product_name_cn", "")
                if lead.get("_qualification") else ""
            ),
            "公司名称": lead.get("company_name", ""),
            "国家": lead.get("country", ""),
            "州/省/行政区": lead.get("subregion", ""),
            "城市": lead.get("city", ""),
            "地址": lead.get("address", ""),
            "官网": lead.get("website", ""),
            "邮箱": lead.get("email", ""),
            "电话": lead.get("phone", ""),
            "WhatsApp": lead.get("whatsapp", ""),
            "公司简介": lead.get("business_summary", ""),
            "买家角色": (
                {
                    "channel_partner": "经销/渠道客户",
                    "end_user": "终端需求方",
                    "mixed": "渠道兼终端",
                    "unknown": "角色待确认",
                }.get(lead.get("_qualification", {}).get("buyer_role"), "")
                if lead.get("_qualification") else ""
            ),
            "推广资格": (
                {
                    "qualified": "合格",
                    "promising": "高潜",
                    "review": "待人工复核",
                    "rejected": "已淘汰",
                }.get(lead.get("_qualification", {}).get("verdict"), "")
                if lead.get("_qualification") else ""
            ),
            "综合评分": (
                lead.get("_qualification", {}).get("overall_score", "")
                if lead.get("_qualification") else ""
            ),
            "产品匹配": (
                lead.get("_qualification", {}).get("product_fit_score", "")
                if lead.get("_qualification") else ""
            ),
            "渠道匹配": (
                lead.get("_qualification", {}).get("channel_fit_score", "")
                if lead.get("_qualification") else ""
            ),
            "终端匹配": (
                lead.get("_qualification", {}).get("end_user_fit_score", "")
                if lead.get("_qualification") else ""
            ),
            "需求信号": (
                lead.get("_qualification", {}).get("demand_signal_score", "")
                if lead.get("_qualification") else ""
            ),
            "判定理由": (
                "；".join(json.loads(lead["_qualification"].get("reasons") or "[]"))
                if lead.get("_qualification") else ""
            ),
            "来源": lead.get("source_channel", ""),
            "来源网址": lead.get("source_url", ""),
            "可信度": lead.get("confidence", "unknown"),
            "状态": lead.get("status", "new"),
        }
        for lead in leads
    ]
    export_buffer = io.BytesIO()
    with pd.ExcelWriter(export_buffer, engine="openpyxl") as writer:
        pd.DataFrame(export_rows).to_excel(writer, index=False, sheet_name="线索")
    action_left, action_right = st.columns([3, 1])
    with action_left:
        st.caption("Excel 将导出当前筛选范围内的全部线索，不受分页影响。")
    with action_right:
        st.download_button(
            "导出当前结果",
            data=export_buffer.getvalue(),
            file_name=f"TradeLead_线索_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch",
            disabled=not leads,
            icon=":material/download:",
        )

    if not leads:
        st.info(
            "当前筛选条件下没有线索。可以放宽筛选，或前往“搜索与采集”继续搜索。",
            icon=":material/search_off:",
        )
    else:
        total_pages = max(1, (len(leads) + page_size - 1) // page_size)
        page_labels = [f"第 {index} 页" for index in range(1, total_pages + 1)]
        page_label = st.selectbox(
            "分页", page_labels, key="lead_page",
            label_visibility="collapsed",
        )
        current_page = page_labels.index(page_label) + 1
        start_index = (current_page - 1) * page_size
        page_leads = leads[start_index:start_index + page_size]
        st.caption(
            f"显示 {start_index + 1}–{min(start_index + page_size, len(leads))} / "
            f"{len(leads)} 条"
        )

        if view_mode == "表格":
            table_rows = [
                {
                    "公司": lead.get("company_name", ""),
                    "资格": {
                        "qualified": "合格",
                        "promising": "高潜",
                        "review": "复核",
                        "rejected": "淘汰",
                    }.get(
                        lead.get("_qualification", {}).get("verdict")
                        if lead.get("_qualification") else None,
                        "未判定",
                    ),
                    "角色": {
                        "channel_partner": "经销渠道",
                        "end_user": "终端需求",
                        "mixed": "渠道+终端",
                        "unknown": "待确认",
                    }.get(
                        lead.get("_qualification", {}).get("buyer_role")
                        if lead.get("_qualification") else None,
                        "未判定",
                    ),
                    "综合分": (
                        lead.get("_qualification", {}).get("overall_score", "")
                        if lead.get("_qualification") else ""
                    ),
                    "产品分": (
                        lead.get("_qualification", {}).get("product_fit_score", "")
                        if lead.get("_qualification") else ""
                    ),
                    "国家": lead.get("country", ""),
                    "州/省": lead.get("subregion", ""),
                    "城市": lead.get("city", ""),
                    "官网": lead.get("website", ""),
                    "邮箱": lead.get("email", ""),
                    "电话": lead.get("phone", ""),
                    "WhatsApp": lead.get("whatsapp", ""),
                    "可信度": {
                        "high": "高", "medium": "中", "low": "低", "unknown": "未知"
                    }.get(lead.get("confidence", "unknown"), "未知"),
                    "状态": {
                        "new": "新线索", "contacted": "已联系", "ignored": "已忽略"
                    }.get(lead.get("status", "new"), "新线索"),
                    "来源": lead.get("source_channel", ""),
                }
                for lead in page_leads
            ]
            st.dataframe(
                pd.DataFrame(table_rows),
                hide_index=True,
                column_config={
                    "官网": st.column_config.LinkColumn("官网", display_text="打开"),
                    "公司": st.column_config.TextColumn(
                        "公司", width="large", pinned=True
                    ),
                    "综合分": st.column_config.ProgressColumn(
                        "综合分", min_value=0, max_value=100
                    ),
                    "产品分": st.column_config.ProgressColumn(
                        "产品分", min_value=0, max_value=100
                    ),
                    "来源": st.column_config.TextColumn("来源", width="medium"),
                },
            )
        else:
            confidence_labels = {
                "high": "高可信", "medium": "中等",
                "low": "较低", "unknown": "待背调",
            }
            status_labels = {"new": "新线索", "contacted": "已联系", "ignored": "已忽略"}
            for lead in page_leads:
                qualification_data = lead.get("_qualification")
                with st.container(border=True):
                    title_col, badge_col = st.columns(
                        [4, 1.3], vertical_alignment="center"
                    )
                    with title_col:
                        st.subheader(lead.get("company_name", "未命名公司"))
                        location = " · ".join(
                            value for value in [
                                lead.get("country", ""),
                                lead.get("subregion", ""),
                                lead.get("city", ""),
                            ]
                            if value
                        )
                        st.caption(
                            f"{location or '地区未知'}　|　{lead.get('source_channel', '来源未知')}"
                        )
                    with badge_col:
                        verdict_key = (
                            qualification_data.get("verdict")
                            if qualification_data else None
                        )
                        verdict_label, verdict_color, verdict_icon = {
                            "qualified": (
                                "合格推广", "green", ":material/check_circle:"
                            ),
                            "promising": (
                                "高潜客户", "blue", ":material/trending_up:"
                            ),
                            "review": (
                                "人工复核", "orange", ":material/rule:"
                            ),
                            "rejected": (
                                "已淘汰", "red", ":material/block:"
                            ),
                        }.get(
                            verdict_key,
                            ("尚未判定", "gray", ":material/pending:"),
                        )
                        role_label = {
                            "channel_partner": "经销/渠道客户",
                            "end_user": "终端需求方",
                            "mixed": "渠道兼终端",
                            "unknown": "角色待确认",
                        }.get(
                            qualification_data.get("buyer_role")
                            if qualification_data else None,
                            "角色待确认",
                        )
                        st.badge(
                            verdict_label,
                            color=verdict_color,
                            icon=verdict_icon,
                        )
                        st.caption(role_label)

                    if qualification_data:
                        with st.container(horizontal=True):
                            st.metric(
                                "综合评分",
                                qualification_data.get("overall_score", 0),
                                border=True,
                            )
                            st.metric(
                                "产品匹配",
                                qualification_data.get("product_fit_score", 0),
                                border=True,
                            )
                            st.metric(
                                "渠道匹配",
                                qualification_data.get("channel_fit_score", 0),
                                border=True,
                            )
                            st.metric(
                                "终端匹配",
                                qualification_data.get("end_user_fit_score", 0),
                                border=True,
                            )
                            st.metric(
                                "需求信号",
                                qualification_data.get("demand_signal_score", 0),
                                border=True,
                            )

                    if lead.get("address"):
                        st.caption(f":material/location_on: {lead['address']}")

                    contact_cols = st.columns(4)
                    website = lead.get("website", "")
                    email = lead.get("email", "")
                    phone = lead.get("phone", "")
                    whatsapp = lead.get("whatsapp", "")
                    with contact_cols[0]:
                        st.caption("官网")
                        if website:
                            website_url = website if "://" in website else f"https://{website}"
                            st.link_button(
                                "访问官网",
                                website_url,
                                width="stretch",
                                icon=":material/language:",
                            )
                        else:
                            st.write("—")
                    with contact_cols[1]:
                        st.caption("邮箱")
                        if email:
                            primary_email = email.split(",")[0].strip()
                            st.link_button(
                                primary_email[:36],
                                f"mailto:{primary_email}",
                                width="stretch",
                                icon=":material/mail:",
                            )
                        else:
                            st.write("—")
                    with contact_cols[2]:
                        st.caption("电话")
                        st.write(phone[:40] if phone else "—")
                    with contact_cols[3]:
                        st.caption("WhatsApp")
                        if whatsapp:
                            primary_whatsapp = whatsapp.split(",")[0].strip()
                            if primary_whatsapp.startswith("http"):
                                whatsapp_url = primary_whatsapp
                            else:
                                digits = "".join(
                                    char for char in primary_whatsapp
                                    if char.isdigit()
                                )
                                whatsapp_url = f"https://wa.me/{digits}"
                            st.link_button(
                                "打开 WhatsApp",
                                whatsapp_url,
                                width="stretch",
                                icon=":material/chat:",
                            )
                        else:
                            st.write("—")

                    if lead.get("business_summary"):
                        st.markdown("**公司概况**")
                        st.write(lead["business_summary"][:700])

                    diligence_evidence = get_diligence(lead["id"])
                    with st.expander(
                        "买家资格判定证据",
                        icon=":material/fact_check:",
                    ):
                        if qualification_data:
                            st.caption(
                                "判定产品："
                                f"{qualification_data.get('product_name_cn', '')} "
                                f"({qualification_data.get('product_name_en', '')})"
                            )
                            for reason in json.loads(
                                qualification_data.get("reasons") or "[]"
                            ):
                                st.write(f"• {reason}")
                            for item in json.loads(
                                qualification_data.get("evidence") or "[]"
                            ):
                                matches = "、".join(item.get("matches", []))
                                st.write(
                                    f"**{item.get('category', '证据')}**：{matches} "
                                    f"（{item.get('source', '')}，{item.get('points', 0):+d}分）"
                                )
                            rejection_reasons = json.loads(
                                qualification_data.get("rejection_reasons") or "[]"
                            )
                            for reason in rejection_reasons:
                                st.error(reason)
                        else:
                            st.caption("尚未针对所选产品进行资格判定")

                    with st.expander(
                        "来源与官网背调详情",
                        icon=":material/manage_search:",
                    ):
                        st.write(f"匹配关键词：{lead.get('match_keyword') or '—'}")
                        if lead.get("source_url"):
                            st.markdown(f"[打开原始来源]({lead['source_url']})")
                        if diligence_evidence:
                            st.write(diligence_evidence.get("summary") or "已完成背调")
                            if diligence_evidence.get("products_found"):
                                st.write(
                                    f"网站产品关键词：{diligence_evidence['products_found']}"
                                )
                            if diligence_evidence.get("matched_product_terms"):
                                st.success(
                                    "目标产品命中："
                                    + diligence_evidence["matched_product_terms"]
                                )
                        else:
                            st.caption("尚未完成官网背调")

                    status_col, diligence_col, outreach_col = st.columns([2, 1, 1])
                    with status_col:
                        current_status = status_labels.get(lead.get("status", "new"), "新线索")
                        new_status = st.selectbox(
                            "跟进状态",
                            ["新线索", "已联系", "已忽略"],
                            index=["新线索", "已联系", "已忽略"].index(current_status),
                            key=f"status_{lead['id']}",
                        )
                        status_values = {
                            "新线索": "new", "已联系": "contacted", "已忽略": "ignored"
                        }
                        if status_values[new_status] != lead.get("status"):
                            update_lead(lead["id"], status=status_values[new_status])
                            st.rerun()
                    with diligence_col:
                        if st.button(
                            "重新背调" if lead.get("diligence_done") else "开始背调",
                            key=f"dd_{lead['id']}",
                            width="stretch",
                            disabled=not website,
                            icon=":material/manage_search:",
                        ):
                            with st.spinner("正在读取官网公开页面..."):
                                qualification_product_id = (
                                    selected_product_id
                                    or (
                                        qualification_data.get("product_id")
                                        if qualification_data else None
                                    )
                                )
                                diligence_product = (
                                    get_product(qualification_product_id)
                                    if qualification_product_id else None
                                )
                                target_keywords = ",".join(
                                    value for value in [
                                        diligence_product.get("product_name_en", "")
                                        if diligence_product else "",
                                        diligence_product.get("keywords_en", "")
                                        if diligence_product else "",
                                    ] if value
                                )
                                diligence = run_diligence(
                                    lead["id"],
                                    website,
                                    target_keywords=target_keywords,
                                )
                                confidence = rate_confidence(diligence)
                                save_diligence(diligence)
                                updates = {
                                    "confidence": confidence,
                                    "diligence_done": 1,
                                }
                                if diligence.get("emails"):
                                    updates["email"] = ", ".join(diligence["emails"])
                                if diligence.get("phones"):
                                    updates["phone"] = ", ".join(diligence["phones"])
                                if diligence.get("whatsapps"):
                                    updates["whatsapp"] = ", ".join(diligence["whatsapps"])
                                update_lead(lead["id"], **updates)
                                if qualification_product_id:
                                    evaluate_and_save(
                                        lead["id"], qualification_product_id
                                    )
                                st.rerun()
                    with outreach_col:
                        if st.button(
                            "生成开发信",
                            key=f"outreach_{lead['id']}",
                            width="stretch",
                            disabled=bool(
                                qualification_data
                                and qualification_data.get("verdict") == "rejected"
                            ),
                            help="已淘汰线索需重新评估后才能进入开发信流程",
                            icon=":material/outgoing_mail:",
                        ):
                            st.session_state.outreach_lead_id = lead["id"]
                            st.session_state.page = "开发信"
                            st.rerun()

# ═══════════════════════════════════════════════════════════
#  Page: 开发信
# ═══════════════════════════════════════════════════════════
elif page == "开发信":
    page_header(
        "外联内容",
        "根据产品、买家角色和目标市场生成可编辑的多语言邮件与 WhatsApp 消息。",
        "outgoing_mail",
    )

    products = get_products()
    leads = get_leads()

    if not products:
        st.warning("请先添加产品", icon=":material/warning:")
        st.stop()
    if not leads:
        st.warning("请先搜索客户", icon=":material/warning:")
        st.stop()

    with st.container(border=True):
        section_header("生成设置", "选择产品、目标客户、语言和联系场景。")
        col1, col2, col3 = st.columns(3)
        with col1:
            prod_names = [f"{p['product_name_cn']}" for p in products]
            sel_prod = st.selectbox(
                "选择产品", prod_names, key="outreach_product"
            )
            product = products[prod_names.index(sel_prod)]
        with col2:
            lead_names = [
                f"{lead['company_name']}（{lead.get('country', '')}）"
                for lead in leads
            ]
            requested_lead_id = st.session_state.pop("outreach_lead_id", None)
            if requested_lead_id:
                for index, candidate in enumerate(leads):
                    if candidate["id"] == requested_lead_id:
                        st.session_state["outreach_lead"] = lead_names[index]
                        break
            sel_lead = st.selectbox(
                "选择客户", lead_names, key="outreach_lead"
            )
            lead = leads[lead_names.index(sel_lead)]
        with col3:
            language = get_language_for_country(lead.get("country", ""))
            lang_options = {
                "en": "英语 English",
                "ar": "阿拉伯语 Arabic",
                "ru": "俄语 Russian",
                "fr": "法语 French",
                "es": "西班牙语 Spanish",
                "pt": "葡萄牙语 Portuguese",
            }
            sel_lang = st.selectbox(
                "语言",
                list(lang_options.values()),
                index=(
                    list(lang_options.keys()).index(language)
                    if language in lang_options else 0
                ),
                key="outreach_lang",
            )
            lang_key = {value: key for key, value in lang_options.items()}[sel_lang]

        template_type = st.segmented_control(
            "联系场景",
            ["初次联系", "报价推介", "跟进邮件"],
            default="初次联系",
            key="outreach_template",
        )
    type_map = {"初次联系": "first_contact", "报价推介": "quote", "跟进邮件": "followup"}

    if st.button(
        "生成外联内容",
        width="stretch",
        type="primary",
        icon=":material/auto_awesome:",
    ):
        result = generate_outreach(
            product=product,
            lead=lead,
            language=lang_key,
            template_type=type_map[template_type],
        )
        st.session_state.generated_outreach = {
            **result,
            "lead_id": lead["id"],
            "product_id": product["id"],
            "language": lang_key,
            "template_type": type_map[template_type],
        }
        for state_key in ("email_subject", "email_body", "wa_msg"):
            st.session_state.pop(state_key, None)

    generated = st.session_state.get("generated_outreach")
    generated_matches = (
        generated
        and generated.get("lead_id") == lead["id"]
        and generated.get("product_id") == product["id"]
    )
    if generated_matches:
        section_header(
            "编辑与保存",
            f"当前内容：{product['product_name_cn']} → {lead['company_name']}",
        )
        email_tab, whatsapp_tab = st.tabs(
            [":material/mail: 邮件", ":material/chat: WhatsApp"]
        )
        with email_tab:
            st.text_input(
                "邮件标题",
                generated["subject"],
                key="email_subject",
            )
            st.text_area(
                "邮件正文",
                generated["body"],
                height=320,
                key="email_body",
            )
        with whatsapp_tab:
            st.text_area(
                "WhatsApp 消息",
                generated["whatsapp"],
                height=180,
                key="wa_msg",
            )
            st.caption("消息可直接复制到 WhatsApp，发送前请核实称呼和产品参数。")

        with st.container(horizontal=True, horizontal_alignment="right"):
            if st.button(
                "保存开发信",
                type="primary",
                icon=":material/save:",
            ):
                save_outreach({
                    "lead_id": lead["id"],
                    "product_id": product["id"],
                    "language": generated["language"],
                    "template_type": generated["template_type"],
                    "email_subject": st.session_state.get(
                        "email_subject", generated["subject"]
                    ),
                    "email_body": st.session_state.get(
                        "email_body", generated["body"]
                    ),
                    "whatsapp_msg": st.session_state.get(
                        "wa_msg", generated["whatsapp"]
                    ),
                })
                st.toast(
                    "开发信已保存",
                    icon=":material/check_circle:",
                )
    elif generated:
        st.info(
            "产品或客户已切换，请重新生成对应的外联内容。",
            icon=":material/info:",
        )

# ═══════════════════════════════════════════════════════════
#  Page: 落地页
# ═══════════════════════════════════════════════════════════
elif page == "落地页":
    page_header(
        "产品落地页",
        "为指定产品生成可下载、可独立托管的多语言介绍页面。",
        "web",
    )

    products = get_products()
    if not products:
        st.warning("请先添加产品", icon=":material/warning:")
        st.stop()

    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            prod_names = [f"{p['product_name_cn']}" for p in products]
            sel_prod = st.selectbox("选择产品", prod_names, key="lp_product")
            product = products[prod_names.index(sel_prod)]
        with col2:
            lang_options = {
                "en": "英语",
                "ar": "阿拉伯语",
                "ru": "俄语",
                "fr": "法语",
                "es": "西班牙语",
                "pt": "葡萄牙语",
            }
            sel_lang = st.selectbox(
                "页面语言", list(lang_options.values()), key="lp_lang"
            )
            lang_key = {value: key for key, value in lang_options.items()}[sel_lang]
        st.caption(
            "页面将包含产品名称、主要描述、规格、报价和联系信息。"
        )

    if st.button(
        "生成落地页",
        width="stretch",
        type="primary",
        icon=":material/auto_awesome:",
    ):
        st.session_state.generated_landing_page = {
            "html": generate_landing_page(product, lang_key),
            "product_id": product["id"],
            "language": lang_key,
        }

    landing_page = st.session_state.get("generated_landing_page")
    if (
        landing_page
        and landing_page.get("product_id") == product["id"]
        and landing_page.get("language") == lang_key
    ):
        section_header(
            "页面预览",
            "这是下载文件的实际效果；建议发布前核对产品参数和联系信息。",
        )
        st.components.v1.html(
            landing_page["html"],
            height=620,
            scrolling=True,
        )

        st.download_button(
            label="下载 HTML 文件",
            data=landing_page["html"],
            file_name=f"{product['product_name_en'].replace(' ','_')}_landing_{lang_key}.html",
            mime="text/html",
            width="stretch",
            icon=":material/download:",
        )
        st.caption(
            "下载后可以托管到 GitHub Pages、Netlify 或企业服务器，再把链接发送给客户。"
        )
    elif landing_page:
        st.info(
            "产品或语言已切换，请重新生成对应页面。",
            icon=":material/info:",
        )

# ═══════════════════════════════════════════════════════════
#  Page: 设置
# ═══════════════════════════════════════════════════════════
elif page == "设置":
    page_header(
        "系统设置",
        "维护外联落款、搜索渠道状态，以及国内服务器的代理或海外网关配置。",
        "settings",
    )
    settings_section = st.segmented_control(
        "设置分类",
        ["发件人信息", "搜索渠道", "网络与代理"],
        default="发件人信息",
        key="settings_section",
        width="stretch",
    )

    if settings_section == "发件人信息":
        section_header(
            "外联落款",
            "这些信息会自动填入开发信和产品落地页，请使用真实可联系的业务资料。",
        )
        with st.form("sender_settings_form"):
            col1, col2 = st.columns(2)
            with col1:
                sender_name = st.text_input(
                    "联系人姓名",
                    value=get_setting("sender_name") or "",
                    key="set_name",
                )
                sender_email = st.text_input(
                    "业务邮箱",
                    value=get_setting("sender_email") or "",
                    key="set_email",
                )
            with col2:
                sender_company = st.text_input(
                    "公司名称",
                    value=get_setting("sender_company") or "",
                    key="set_company",
                )
                sender_phone = st.text_input(
                    "电话 / WhatsApp",
                    value=get_setting("sender_phone") or "",
                    key="set_phone",
                )
            save_sender = st.form_submit_button(
                "保存发件人信息",
                width="stretch",
                type="primary",
                icon=":material/save:",
            )
            if save_sender:
                set_setting("sender_name", sender_name)
                set_setting("sender_company", sender_company)
                set_setting("sender_email", sender_email)
                set_setting("sender_phone", sender_phone)
                st.toast("发件人信息已保存", icon=":material/check_circle:")

    elif settings_section == "搜索渠道":
        section_header(
            "渠道可用状态",
            "免费渠道可直接使用；商业渠道需购买账号并配置对应环境变量。",
        )
        from src.scraper import configured_providers, PROVIDER_LABELS
        settings_provider_status = configured_providers()
        channel_rows = [
            {
                "渠道": PROVIDER_LABELS[provider],
                "类型": (
                    "免费 / 公开"
                    if provider in {"ddg", "yellow_pages", "osm"}
                    else "商业 API"
                ),
                "状态": "可用" if ready else "未配置或不可访问",
            }
            for provider, ready in settings_provider_status.items()
        ]
        st.dataframe(
            pd.DataFrame(channel_rows),
            hide_index=True,
            column_config={
                "渠道": st.column_config.TextColumn(pinned=True, width="large"),
                "状态": st.column_config.TextColumn(width="medium"),
            },
        )

        section_header(
            "公开黄页来源",
            "系统会根据目标国家自动选择当地公开黄页，并补充全球 B2B 目录。",
        )
        default_sources = [
            ("https://europages.com", "Europages", "欧洲 B2B 目录"),
            ("https://kompass.com", "Kompass", "全球 B2B 数据库"),
            ("https://tradekey.com", "TradeKey", "进出口商目录"),
            ("https://yellowpages.ae", "UAE Yellow Pages", "阿联酋黄页"),
            ("https://yellowpages.co.za", "South Africa Yellow Pages", "南非黄页"),
            ("https://yellowpages.com.ng", "Nigeria Yellow Pages", "尼日利亚黄页"),
            ("https://exportersindia.com", "Exporters India", "印度出口商"),
            ("https://turkishexporter.net", "Turkish Exporter", "土耳其出口商"),
            ("https://alibaba.com", "Alibaba", "全球供应商目录"),
        ]
        st.dataframe(
            pd.DataFrame(
                default_sources,
                columns=["域名", "来源", "覆盖范围"],
            ),
            hide_index=True,
            column_config={
                "域名": st.column_config.LinkColumn(
                    display_text=r"https?://(?:www\.)?([^/]+)"
                ),
            },
        )

    elif settings_section == "网络与代理":
        section_header(
            "国内服务器网络方案",
            "代理适合临时直连；固定白名单海外网关更适合正式服务器部署。",
        )
        with st.container(border=True):
            st.markdown("**代理配置**")
            proxy_url = st.text_input(
                "代理地址",
                value=get_setting("proxy_url") or "",
                placeholder="http://user:pass@host:port 或 socks5://host:port",
                key="set_proxy",
            )
            st.caption("代理凭据只保存在本地设置库中，不会显示在页面状态列表。")
            with st.container(horizontal=True):
                if st.button(
                    "保存代理",
                    type="primary",
                    icon=":material/save:",
                ):
                    set_setting("proxy_url", proxy_url)
                    st.toast(
                        "代理设置已保存，重启服务后生效",
                        icon=":material/check_circle:",
                    )
                if st.button(
                    "测试当前网络",
                    icon=":material/network_check:",
                ):
                    from src.scraper import is_network_available
                    if is_network_available():
                        st.success(
                            "网络正常，可访问真实搜索服务。",
                            icon=":material/check_circle:",
                        )
                    else:
                        st.warning(
                            "当前无法直连海外搜索引擎。国内服务器可使用代理或海外 API 网关。",
                            icon=":material/warning:",
                        )

        with st.container(border=True):
            st.markdown("**海外 API 网关**")
            st.write(
                "商业搜索 API 可通过固定白名单网关转发。服务器只访问一个海外网关域名，"
                "由网关连接 Brave、Google Places、SerpAPI 等服务。"
            )
            gateway_configured = bool(os.getenv("TRADELEAD_API_GATEWAY_URL"))
            if gateway_configured:
                st.badge(
                    "网关已配置",
                    color="green",
                    icon=":material/check_circle:",
                )
            else:
                st.badge(
                    "网关尚未配置",
                    color="gray",
                    icon=":material/key:",
                )
            st.caption(
                "使用 TRADELEAD_API_GATEWAY_URL、TRADELEAD_API_GATEWAY_TOKEN "
                "和 TRADELEAD_GATEWAY_SERVICES 配置。"
            )

    with st.expander(
        "数据使用与合规说明",
        icon=":material/policy:",
    ):
        st.write(
            "本工具从公开网页和已授权数据源采集信息，仅供外贸业务参考。"
            "请遵守目标网站的使用条款和当地数据法规，合理控制请求频率；"
            "采集结果未经人工审核，联系前应核实公司身份与联系方式。"
        )
