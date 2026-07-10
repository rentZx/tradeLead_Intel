"""TradeLead Intel - 自定义 UI 样式模块 V3.0

提供全局 CSS 注入和 UI 辅助函数。
Design System: Precision Trade / 精准外贸 — 专业商务风。
"""

from __future__ import annotations

import streamlit as st

# ---------------------------------------------------------------------------
# 配色常量 (Precision Trade V3.0)
# ---------------------------------------------------------------------------
# 品牌主色
C_PRIMARY = "#0E7C7B"           # Teal 青蓝 — 现代、国际、精准
C_PRIMARY_DARK = "#0A5C5B"       # Teal 深色 — hover/active
C_PRIMARY_LIGHT = "#E6F4F4"      # Teal 浅底 — 背景衬色

# 品牌辅色
C_NAVY = "#1B2D45"              # 深海蓝 — 权威、信任、侧边栏底色
C_NAVY_LIGHT = "#243B5A"        # 浅海蓝 — hover 态
C_GOLD = "#B8860B"              # 金色 — 高价值/A 级专属点缀

# 表面色
C_BG = "#F5F3F0"                # 暖灰底色 — 减少数据密集场景的视觉疲劳
C_CARD = "#FFFFFF"              # 卡片底
C_BORDER = "#E2DDD6"            # 暖灰边框
C_BORDER_LIGHT = "#EDEAE5"      # 浅暖灰分割线

# 文字色
C_TEXT = "#1B2D45"              # 主文字 — 深海蓝
C_TEXT_MUTED = "#5A6B7F"        # 辅助文字 — 石板灰
C_TEXT_TERTIARY = "#8B9DB0"     # 三级文字

# 语义色
C_SUCCESS = "#0D8C5E"           # 成功 — 深绿
C_SUCCESS_BG = "#E8F5EF"
C_WARNING = "#C8781A"           # 警告 — 琥珀橙
C_WARNING_BG = "#FDF3E5"
C_DANGER = "#C0392B"            # 危险 — 低调红
C_DANGER_BG = "#FDF0ED"
C_INFO = "#2E6B9E"              # 信息 — 石板蓝
C_INFO_BG = "#EDF3F9"
C_PURPLE = "#6B46C1"            # 紫色 — 特殊指标

# 评级颜色
GRADE_COLORS = {
    "A": "#0D8C5E",
    "B": "#2E6B9E",
    "C": "#C8781A",
    "D": "#C0392B",
}

# 页面图标
PAGE_ICONS = {
    "首页仪表盘": "dashboard",
    "产品库": "box",
    "演示数据": "flask",
    "搜索任务": "search",
    "自动搜索": "rocket",
    "官网读取": "globe",
    "合规风险中心": "shield",
    "产品落地页/询盘": "file-text",
    "公司线索库": "building",
    "背调报告": "clipboard-check",
    "开发信生成器": "mail",
    "CRM跟进": "message-circle",
    "系统设置": "settings",
}

# ---------------------------------------------------------------------------
# 全局 CSS
# ---------------------------------------------------------------------------
GLOBAL_CSS = f"""
<style>
/* ============================================================
   TradeLead Intel V3.0 — Precision Trade Design System
   ============================================================ */

/* ==================== 全局重置 ==================== */
.stApp {{
    background: {C_BG};
}}

#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
header[data-testid="stHeader"] {{background: transparent;}}

/* ==================== 侧边栏 — 深海蓝基调 ==================== */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #0F1B2D 0%, {C_NAVY} 100%);
    border-right: 1px solid #1E3350;
}}

section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3,
section[data-testid="stSidebar"] .stMarkdown span {{
    color: #E8ECF1 !important;
}}

section[data-testid="stSidebar"] .stRadio > label {{
    color: #7A8EA8;
    font-size: 0.875rem;
    letter-spacing: 0.03em;
    font-weight: 700;
}}

/* 侧边栏导航项 */
section[data-testid="stSidebar"] [role="radiogroup"] label {{
    color: #A8B8CC !important;
    padding: 0.35rem 0.5rem;
    border-radius: 0.5rem;
    transition: all 0.15s;
    font-size: 0.8125rem;
}}

section[data-testid="stSidebar"] [role="radiogroup"] label:hover {{
    background: rgba(255,255,255,0.06);
    color: #FFFFFF !important;
}}

section[data-testid="stSidebar"] [role="radiogroup"] label[data-checked="true"] {{
    background: {C_PRIMARY};
    color: #FFFFFF !important;
    font-weight: 600;
    box-shadow: 0 2px 8px rgba(14,124,123,0.35);
}}

/* 侧边栏分组标题 */
.sidebar-group-title {{
    color: #7A8EA8;
    font-size: 0.875rem;
    letter-spacing: 0.03em;
    font-weight: 700;
    padding: 0.85rem 0 0.35rem 0;
    border-top: 1px solid rgba(74,94,122,0.18);
    margin-top: 0.5rem;
}}

/* 侧边栏导航按钮（button-based nav） */
section[data-testid="stSidebar"] .stButton > button {{
    background: transparent;
    color: #A8B8CC !important;
    border: 1px solid transparent;
    border-radius: 0.5rem;
    padding: 0.45rem 0.75rem;
    font-size: 0.8125rem;
    font-weight: 500;
    text-align: left;
    transition: all 0.15s;
    box-shadow: none;
}}

section[data-testid="stSidebar"] .stButton > button:hover {{
    background: rgba(255,255,255,0.06);
    color: #FFFFFF !important;
    border-color: rgba(255,255,255,0.06);
    transform: none;
    box-shadow: none;
}}

section[data-testid="stSidebar"] .stButton > button[kind="primary"],
section[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] {{
    background: {C_PRIMARY} !important;
    color: #FFFFFF !important;
    border: none;
    font-weight: 600;
    box-shadow: 0 2px 8px rgba(14,124,123,0.35);
}}

/* 侧边栏底部版本信息 */
.sidebar-footer {{
    color: #4A5E7A;
    font-size: 0.625rem;
    text-align: center;
    padding: 1rem 0 0.5rem 0;
    border-top: 1px solid rgba(74,94,122,0.18);
    margin-top: 1rem;
    letter-spacing: 0.03em;
}}

/* ==================== 标题区 ==================== */
.main-header {{
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.25rem;
}}

.main-header-icon {{
    width: 3rem;
    height: 3rem;
    background: linear-gradient(135deg, {C_PRIMARY} 0%, {C_PRIMARY_DARK} 100%);
    border-radius: 0.75rem;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    color: white;
    flex-shrink: 0;
    box-shadow: 0 4px 12px rgba(14,124,123,0.3);
}}

.main-header-text h1 {{
    margin: 0;
    font-size: 1.75rem;
    font-weight: 800;
    color: {C_TEXT};
    line-height: 1.2;
    letter-spacing: -0.02em;
}}

.main-header-text .subtitle {{
    color: {C_TEXT_MUTED};
    font-size: 0.8rem;
    margin-top: 0.15rem;
}}

/* ==================== 页面标题 ==================== */
.page-header {{
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 0;
    margin-bottom: 0.75rem;
    border-bottom: 2px solid {C_BORDER};
}}

.page-header-icon {{
    width: 2.25rem;
    height: 2.25rem;
    border-radius: 0.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.15rem;
    flex-shrink: 0;
}}

.page-header-title {{
    font-size: 1.375rem;
    font-weight: 700;
    color: {C_TEXT};
    margin: 0;
    letter-spacing: -0.02em;
}}

/* ==================== 指标卡片 V3 — 左侧色条引导 ==================== */
.metric-card {{
    background: {C_CARD};
    border: 1px solid {C_BORDER};
    border-radius: 0.75rem;
    padding: 1rem 1.25rem;
    box-shadow: 0 1px 2px rgba(27,45,69,0.04);
    transition: all 0.2s;
    position: relative;
    overflow: hidden;
}}

.metric-card:hover {{
    box-shadow: 0 2px 8px rgba(27,45,69,0.06), 0 1px 3px rgba(27,45,69,0.04);
    transform: translateY(-1px);
}}

.metric-card-accent {{
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 3px;
    border-radius: 0 0.375rem 0.375rem 0;
}}

.metric-card-label {{
    color: {C_TEXT_TERTIARY};
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    margin-bottom: 0.35rem;
}}

.metric-card-value {{
    font-size: 1.75rem;
    font-weight: 800;
    color: {C_TEXT};
    line-height: 1;
    font-variant-numeric: tabular-nums;
}}

.metric-card-delta {{
    font-size: 0.7rem;
    margin-top: 0.25rem;
}}

/* ==================== 评级徽章 ==================== */
.grade-badge {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 1.5rem;
    height: 1.5rem;
    border-radius: 0.375rem;
    font-weight: 800;
    font-size: 0.8rem;
    color: white;
    padding: 0 0.15rem;
}}

.grade-A {{ background: {GRADE_COLORS["A"]}; }}
.grade-B {{ background: {GRADE_COLORS["B"]}; }}
.grade-C {{ background: {GRADE_COLORS["C"]}; }}
.grade-D {{ background: {GRADE_COLORS["D"]}; }}

/* ==================== 评级分布芯片 ==================== */
.grade-chip {{
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.3rem 0.6rem;
    border-radius: 0.5rem;
    font-size: 0.8rem;
    font-weight: 600;
    border: 1px solid {C_BORDER};
    background: {C_CARD};
    transition: all 0.15s;
    cursor: pointer;
}}

.grade-chip:hover {{
    box-shadow: 0 1px 2px rgba(27,45,69,0.04);
    transform: translateY(-1px);
}}

.grade-chip-square {{
    min-width: 1.5rem;
    height: 1.5rem;
    border-radius: 0.35rem;
    color: #FFFFFF;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 0.8rem;
}}

/* ==================== 信息卡片 / callout ==================== */
.callout {{
    border-radius: 0.5rem;
    padding: 0.75rem 0.875rem;
    border-left: 3px solid;
    font-size: 0.8125rem;
    line-height: 1.5;
    margin-bottom: 0.5rem;
}}

.callout-info {{
    background: {C_INFO_BG};
    border-color: {C_INFO};
    color: #1C4B6E;
}}

.callout-warning {{
    background: {C_WARNING_BG};
    border-color: {C_WARNING};
    color: #7A4A10;
}}

.callout-danger {{
    background: {C_DANGER_BG};
    border-color: {C_DANGER};
    color: #7A1C1B;
}}

.callout-success {{
    background: {C_SUCCESS_BG};
    border-color: {C_SUCCESS};
    color: #0A5C3A;
}}

/* ==================== 按钮 ==================== */
.stButton > button {{
    border-radius: 0.5rem;
    font-weight: 600;
    transition: all 0.12s;
    border: 1px solid {C_BORDER};
}}

.stButton > button:hover {{
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(27,45,69,0.08);
}}

.stButton > button[kind="primary"] {{
    background: {C_PRIMARY} !important;
    border-color: {C_PRIMARY} !important;
}}

.stButton > button[kind="primary"]:hover {{
    background: {C_PRIMARY_DARK} !important;
    border-color: {C_PRIMARY_DARK} !important;
}}

.stButton > button:active {{
    transform: scale(0.98);
}}

/* ==================== 表格 ==================== */
.stDataFrame {{
    border-radius: 0.75rem;
    overflow: hidden;
    border: 1px solid {C_BORDER};
    box-shadow: 0 1px 2px rgba(27,45,69,0.04);
}}

.stDataFrame [data-testid="stDataFrameResizable"] {{
    border-radius: 0.75rem;
}}

.stDataFrame th {{
    background: {C_BG} !important;
    font-weight: 700 !important;
    font-size: 0.75rem !important;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    color: {C_TEXT_TERTIARY} !important;
}}

.stDataFrame tbody tr:hover {{
    background: #FAF9F7;
}}

/* ==================== 表单 & 输入 ==================== */
.stTextInput > div > input,
.stTextArea > div > textarea,
.stSelectbox [data-baseweb="select"] {{
    border-radius: 0.5rem;
    border-color: {C_BORDER} !important;
}}

.stTextInput > div > input:focus,
.stTextArea > div > textarea:focus {{
    border-color: {C_PRIMARY} !important;
    box-shadow: 0 0 0 3px rgba(14,124,123,0.1) !important;
}}

/* ==================== Expander ==================== */
.streamlit-expanderHeader {{
    font-weight: 600;
    font-size: 0.875rem;
    background: {C_CARD};
    border-radius: 0.625rem !important;
}}

details[data-testid="stExpander"] {{
    border: 1px solid {C_BORDER};
    border-radius: 0.625rem !important;
    overflow: hidden;
    margin-bottom: 0.75rem;
}}

/* ==================== Tabs ==================== */
.stTabs [data-baseweb="tab-list"] {{
    gap: 0.25rem;
    border-bottom: 2px solid {C_BORDER};
}}

.stTabs [data-baseweb="tab"] {{
    border-radius: 0.5rem 0.5rem 0 0;
    padding: 0.5rem 1rem;
    font-weight: 600;
    font-size: 0.85rem;
    color: {C_TEXT_TERTIARY};
    border-bottom: 2px solid transparent;
    transition: all 0.12s;
}}

.stTabs [data-baseweb="tab"]:hover {{
    background: {C_PRIMARY_LIGHT};
    color: {C_PRIMARY};
}}

.stTabs [aria-selected="true"] {{
    color: {C_PRIMARY} !important;
    border-bottom-color: {C_PRIMARY} !important;
}}

/* ==================== Divider ==================== */
hr {{
    border: none;
    border-top: 1px solid {C_BORDER};
    margin: 1rem 0;
}}

/* ==================== 评分条 ==================== */
.score-bar {{
    height: 0.5rem;
    border-radius: 0.25rem;
    background: {C_BORDER};
    overflow: hidden;
    margin-top: 0.25rem;
}}

.score-bar-fill {{
    height: 100%;
    border-radius: 0.25rem;
    transition: width 0.3s ease;
}}

/* ==================== 快速操作按钮 ==================== */
.quick-action-btn {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border: 1px solid {C_BORDER};
    border-radius: 0.5rem;
    background: {C_CARD};
    font-size: 0.8125rem;
    font-weight: 600;
    color: {C_TEXT};
    cursor: pointer;
    transition: all 0.15s;
}}

.quick-action-btn:hover {{
    border-color: {C_PRIMARY};
    background: {C_PRIMARY_LIGHT};
    color: {C_PRIMARY_DARK};
    box-shadow: 0 1px 2px rgba(27,45,69,0.04);
}}

.quick-action-btn:active {{
    transform: scale(0.98);
}}

/* ==================== 状态徽章 ==================== */
.badge-risk {{
    display: inline-flex;
    padding: 0.1rem 0.5rem;
    border-radius: 0.3rem;
    font-size: 0.7rem;
    font-weight: 600;
    color: {C_DANGER};
    background: {C_DANGER_BG};
    border: 1px solid #F5C6CB;
}}

.badge-clean {{
    display: inline-flex;
    padding: 0.1rem 0.5rem;
    border-radius: 0.3rem;
    font-size: 0.7rem;
    font-weight: 600;
    color: {C_SUCCESS};
    background: {C_SUCCESS_BG};
    border: 1px solid #B7DFC8;
}}

.badge-stage {{
    display: inline-flex;
    padding: 0.1rem 0.5rem;
    border-radius: 0.3rem;
    font-size: 0.7rem;
    font-weight: 600;
    color: {C_PRIMARY};
    background: {C_PRIMARY_LIGHT};
    border: 1px solid #B0D5D5;
}}

/* ==================== 响应式 ==================== */
@media (max-width: 768px) {{
    .main-header-text h1 {{
        font-size: 1.4rem;
    }}
    .metric-card-value {{
        font-size: 1.5rem;
    }}
}}

/* ==================== Streamlit 原生组件覆盖 ==================== */
[data-testid="stMetric"] {{
    background: {C_CARD};
    border: 1px solid {C_BORDER};
    border-radius: 0.625rem;
    padding: 0.875rem 1rem;
    box-shadow: 0 1px 2px rgba(27,45,69,0.04);
}}

[data-testid="stMetric"] label {{
    color: {C_TEXT_TERTIARY} !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}}

[data-testid="stMetric"] [data-testid="stMetricValue"] {{
    font-size: 1.75rem !important;
    font-weight: 800 !important;
    color: {C_TEXT} !important;
}}

.stCaption {{
    color: {C_TEXT_MUTED} !important;
    font-size: 0.8rem !important;
}}

h3 {{
    color: {C_TEXT} !important;
    font-weight: 700 !important;
}}

/* 评分展示卡片 */
.score-display-card {{
    background: {C_CARD};
    border: 1px solid {C_BORDER};
    border-radius: 0.75rem;
    padding: 1rem 1.25rem;
    text-align: center;
    box-shadow: 0 1px 2px rgba(27,45,69,0.04);
}}
</style>
"""


# ---------------------------------------------------------------------------
# SVG 图标（内联，不依赖外部资源）
# ---------------------------------------------------------------------------
def _svg(icon: str, size: int = 20, color: str = "currentColor") -> str:
    """返回内联 SVG 图标 HTML。"""
    paths = {
        "dashboard": '<rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/>',
        "box": '<path d="M21 8l-9-5-9 5v8l9 5 9-5V8z"/><path d="M3 8l9 5 9-5"/><path d="M12 13v8"/>',
        "flask": '<path d="M9 3h6v4l5 11a2 2 0 01-2 3H6a2 2 0 01-2-3l5-11V3z"/><path d="M9 3h6"/>',
        "search": '<circle cx="11" cy="11" r="7"/><path d="M21 21l-5-5"/>',
        "rocket": '<path d="M5 13c0-5 4-9 7-9s7 4 7 9c0 3-2 5-4 6h-6c-2-1-4-3-4-6z"/><path d="M9 17v3M15 17v3"/><circle cx="12" cy="10" r="2"/>',
        "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3a14 14 0 010 18"/><path d="M12 3a14 14 0 000 18"/>',
        "shield": '<path d="M12 2l8 3v7c0 5-4 9-8 10-4-1-8-5-8-10V5l8-3z"/>',
        "file-text": '<path d="M14 3H6a2 2 0 00-2 2v14a2 2 0 002 2h12a2 2 0 002-2V9l-6-6z"/><path d="M14 3v6h6"/><path d="M8 13h8M8 17h6"/>',
        "building": '<rect x="4" y="3" width="16" height="18" rx="1"/><path d="M9 7h2M13 7h2M9 11h2M13 11h2M9 15h2M13 15h2"/>',
        "clipboard-check": '<path d="M9 3h6v3H9V3z"/><path d="M9 5H6a2 2 0 00-2 2v12a2 2 0 002 2h12a2 2 0 002-2V7a2 2 0 00-2-2h-3"/><path d="M9 14l2 2 4-4"/>',
        "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
        "message-circle": '<path d="M21 12a8 8 0 01-12 7l-5 1 1-5a8 8 0 1116-3z"/>',
        "settings": '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M5 5l2 2M17 17l2 2M2 12h3M19 12h3M5 19l2-2M17 7l2-2"/>',
        "check-circle": '<circle cx="12" cy="12" r="9"/><path d="M8 12l3 3 5-6"/>',
        "alert-triangle": '<path d="M12 3l9 16H3l9-16z"/><path d="M12 9v5M12 17h.01"/>',
        "info": '<circle cx="12" cy="12" r="9"/><path d="M12 8h.01M11 12h1v4h1"/>',
        "trending-up": '<path d="M3 17l6-6 4 4 7-7"/><path d="M14 7h6v6"/>',
        "database": '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v6c0 1.5 4 3 8 3s8-1.5 8-3V5"/><path d="M4 11v6c0 1.5 4 3 8 3s8-1.5 8-3v-6"/>',
    }
    d = paths.get(icon, paths["info"])
    return f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{d}</svg>'


# ---------------------------------------------------------------------------
# UI 辅助函数
# ---------------------------------------------------------------------------
def inject_css() -> None:
    """在页面顶部注入全局自定义 CSS。"""
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def main_header(title: str, subtitle: str = "") -> None:
    """渲染主标题区（带渐变图标方块）。"""
    st.markdown(
        f"""<div class="main-header">
    <div class="main-header-icon">
        {_svg("trending-up", 28, "#ffffff")}
    </div>
    <div class="main-header-text">
        <h1>{title}</h1>
        <div class="subtitle">{subtitle}</div>
    </div>
</div>""",
        unsafe_allow_html=True,
    )


def page_header(icon: str, title: str, color: str = C_PRIMARY) -> None:
    """渲染页面标题（带小图标方块）。"""
    bg = color + "1a"  # 10% opacity
    st.markdown(
        f"""<div class="page-header">
    <div class="page-header-icon" style="background:{bg};color:{color};">
        {_svg(icon, 18, color)}
    </div>
    <span class="page-header-title">{title}</span>
</div>""",
        unsafe_allow_html=True,
    )


def sidebar_group(title: str) -> None:
    """在侧边栏渲染分组标题。"""
    st.sidebar.markdown(f'<div class="sidebar-group-title">{title}</div>', unsafe_allow_html=True)


def sidebar_footer(version: str) -> None:
    """在侧边栏底部渲染版本信息。"""
    st.sidebar.markdown(
        f'<div class="sidebar-footer">TradeLead Intel<br>{version}<br>本地版 · 数据不出域</div>',
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str | int, accent_color: str = C_PRIMARY, delta: str = "") -> str:
    """返回指标卡片的 HTML 字符串。

    注意：返回紧凑的单行 HTML，不能有前导换行或缩进，
    否则 Streamlit markdown 解析器会将其当作代码块渲染为纯文本。
    """
    delta_html = f'<div class="metric-card-delta" style="color:{accent_color};">{delta}</div>' if delta else ""
    return (
        f'<div class="metric-card">'
        f'<div class="metric-card-accent" style="background:{accent_color};"></div>'
        f'<div class="metric-card-label">{label}</div>'
        f'<div class="metric-card-value">{value}</div>'
        f'{delta_html}'
        f'</div>'
    )


def callout(text: str, kind: str = "info") -> None:
    """渲染带左侧色条的提示框。kind: info / warning / danger / success"""
    st.markdown(f'<div class="callout callout-{kind}">{text}</div>', unsafe_allow_html=True)


def grade_badge(grade: str) -> str:
    """返回评级徽章 HTML（V3 圆角方块）。"""
    color = GRADE_COLORS.get(grade, C_TEXT_MUTED)
    return (
        f'<span class="grade-badge grade-{grade}" style="background:{color};">{grade}</span>'
    )


def grade_chip(grade: str, count: int) -> str:
    """返回评级分布芯片 HTML（带色块 + 数量）。"""
    color = GRADE_COLORS.get(grade, C_TEXT_MUTED)
    labels = {"A": "优质", "B": "良好", "C": "可跟进", "D": "不建议"}
    label = labels.get(grade, grade)
    return (
        f'<div class="grade-chip">'
        f'<div class="grade-chip-square" style="background:{color};">{grade}</div>'
        f'<span style="color:{C_TEXT};min-width:2rem;">{label}</span>'
        f'<span style="font-weight:800;color:{C_TEXT};font-variant-numeric:tabular-nums;min-width:1rem;text-align:right;">{count}</span>'
        f'</div>'
    )


def status_badge(label: str, kind: str = "stage") -> str:
    """返回状态徽章 HTML。
    kind: 'risk' / 'clean' / 'stage'
    """
    return f'<span class="badge-{kind}">{label}</span>'


def score_card(
    final_score: int,
    grade: str,
    business_match: int = 0,
    purchase_probability: int = 0,
    authenticity: int = 0,
    contactability: int = 0,
    risk_score: int = 0,
) -> str:
    """返回 V3 评分展示卡片 HTML（含环形分数 + 分项进度条）。"""
    grade_color = GRADE_COLORS.get(grade, C_TEXT_MUTED)

    bars = [
        ("业务匹配度 /30", business_match, 30, C_SUCCESS),
        ("采购可能性 /20", purchase_probability, 20, C_PRIMARY),
        ("真实性 /20", authenticity, 20, C_INFO),
        ("联系可达性 /15", contactability, 15, C_PURPLE),
    ]
    bar_html = ""
    for label, val, total, bar_color in bars:
        pct = (val / total * 100) if total > 0 else 0
        bar_html += (
            f'<div style="display:flex;align-items:center;justify-content:space-between;'
            f'gap:0.5rem;font-size:0.75rem;color:{C_TEXT_MUTED};margin-bottom:0.2rem;">'
            f'<span style="min-width:5rem;">{label}</span>'
            f'<div class="score-bar" style="flex:1;min-width:60px;"><div class="score-bar-fill" '
            f'style="width:{pct}%;background:{bar_color};"></div></div>'
            f'<span style="min-width:2rem;text-align:right;font-variant-numeric:tabular-nums;font-weight:600;">{val}</span>'
            f'</div>'
        )

    risk_html = ""
    if risk_score > 0:
        risk_html += (
            f'<div style="display:flex;align-items:center;justify-content:space-between;'
            f'gap:0.5rem;font-size:0.75rem;color:{C_DANGER};margin-top:0.25rem;">'
            f'<span style="min-width:5rem;font-weight:600;">⚠️ 风险扣分</span>'
            f'<span style="flex:1;"></span>'
            f'<span style="text-align:right;font-weight:700;">-{risk_score}</span>'
            f'</div>'
        )

    return (
        f'<div class="score-display-card">'
        f'<div style="display:flex;align-items:center;gap:1rem;margin-bottom:0.75rem;">'
        f'<div style="width:3.5rem;height:3.5rem;border-radius:50%;display:flex;flex-direction:column;'
        f'align-items:center;justify-content:center;border:3px solid {grade_color};'
        f'background:{grade_color}0D;flex-shrink:0;">'
        f'<span style="font-size:1.25rem;font-weight:800;color:{grade_color};line-height:1;">{final_score}</span>'
        f'<span style="font-size:0.55rem;text-transform:uppercase;color:{grade_color};'
        f'font-weight:700;letter-spacing:0.03em;">{grade}级</span>'
        f'</div>'
        f'<div style="font-size:0.75rem;font-weight:600;color:{C_TEXT};">'
        f'<span style="background:{grade_color};color:white;padding:0.15rem 0.6rem;'
        f'border-radius:0.3rem;font-size:0.7rem;">评级 {grade}</span>'
        f'</div>'
        f'</div>'
        f'{bar_html}'
        f'{risk_html}'
        f'</div>'
    )
