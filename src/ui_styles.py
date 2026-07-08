"""TradeLead Intel - 自定义 UI 样式模块

提供全局 CSS 注入和 UI 辅助函数，让 Streamlit 应用告别默认丑皮肤。
"""

from __future__ import annotations

import streamlit as st

# ---------------------------------------------------------------------------
# 配色常量
# ---------------------------------------------------------------------------
C_PRIMARY = "#2563eb"
C_PRIMARY_DARK = "#1d4ed8"
C_PRIMARY_LIGHT = "#dbeafe"
C_BG = "#f8fafc"
C_CARD = "#ffffff"
C_BORDER = "#e2e8f0"
C_TEXT = "#1e293b"
C_TEXT_MUTED = "#64748b"
C_SUCCESS = "#16a34a"
C_SUCCESS_BG = "#dcfce7"
C_WARNING = "#d97706"
C_WARNING_BG = "#fef3c7"
C_DANGER = "#dc2626"
C_DANGER_BG = "#fee2e2"
C_INFO_BG = "#eff6ff"

# 评级颜色
GRADE_COLORS = {
    "A": "#16a34a",
    "B": "#2563eb",
    "C": "#d97706",
    "D": "#dc2626",
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
/* ==================== 全局重置 ==================== */
.stApp {{
    background: {C_BG};
}}

/* 隐藏默认 footer 和 hamburger 装饰 */
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}

/* ==================== 侧边栏 ==================== */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
    border-right: 1px solid #334155;
}}

section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3,
section[data-testid="stSidebar"] .stMarkdown span {{
    color: #e2e8f0 !important;
}}

section[data-testid="stSidebar"] .stRadio > label {{
    color: #94a3b8;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 600;
}}

/* 侧边栏导航项 */
section[data-testid="stSidebar"] [role="radiogroup"] label {{
    color: #cbd5e1 !important;
    padding: 0.35rem 0.5rem;
    border-radius: 0.5rem;
    transition: all 0.2s;
    font-size: 0.875rem;
}}

section[data-testid="stSidebar"] [role="radiogroup"] label:hover {{
    background: rgba(255,255,255,0.08);
    color: #ffffff !important;
}}

section[data-testid="stSidebar"] [role="radiogroup"] label[data-checked="true"] {{
    background: {C_PRIMARY};
    color: #ffffff !important;
    font-weight: 600;
}}

/* 侧边栏分组标题 */
.sidebar-group-title {{
    color: #64748b;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 700;
    padding: 0.75rem 0 0.25rem 0;
    border-top: 1px solid rgba(148,163,184,0.15);
    margin-top: 0.5rem;
}}

/* 侧边栏导航按钮（button-based nav） */
section[data-testid="stSidebar"] .stButton > button {{
    background: transparent;
    color: #cbd5e1 !important;
    border: 1px solid transparent;
    border-radius: 0.5rem;
    padding: 0.5rem 0.75rem;
    font-size: 0.85rem;
    font-weight: 500;
    text-align: left;
    transition: all 0.15s;
    box-shadow: none;
}}

section[data-testid="stSidebar"] .stButton > button:hover {{
    background: rgba(255,255,255,0.08);
    color: #ffffff !important;
    border-color: rgba(255,255,255,0.1);
    transform: none;
    box-shadow: none;
}}

/* 活跃导航项（primary 类型按钮） */
section[data-testid="stSidebar"] .stButton > button[kind="primary"],
section[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] {{
    background: {C_PRIMARY} !important;
    color: #ffffff !important;
    border: none;
    font-weight: 600;
    box-shadow: 0 2px 8px rgba(37,99,235,0.3);
}}

/* 侧边栏底部版本信息 */
.sidebar-footer {{
    color: #475569;
    font-size: 0.7rem;
    text-align: center;
    padding: 1rem 0 0.5rem 0;
    border-top: 1px solid rgba(148,163,184,0.15);
    margin-top: 1rem;
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
    box-shadow: 0 4px 12px rgba(37,99,235,0.3);
}}

.main-header-text h1 {{
    margin: 0;
    font-size: 1.75rem;
    font-weight: 800;
    color: {C_TEXT};
    line-height: 1.2;
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
    margin-bottom: 0.5rem;
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
    font-size: 1.25rem;
    font-weight: 700;
    color: {C_TEXT};
    margin: 0;
}}

/* ==================== 指标卡片 ==================== */
.metric-card {{
    background: {C_CARD};
    border: 1px solid {C_BORDER};
    border-radius: 0.75rem;
    padding: 1rem 1.25rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    transition: all 0.2s;
    position: relative;
    overflow: hidden;
}}

.metric-card:hover {{
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    transform: translateY(-2px);
}}

.metric-card-accent {{
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 4px;
    border-radius: 0.75rem 0 0 0.75rem;
}}

.metric-card-label {{
    color: {C_TEXT_MUTED};
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    margin-bottom: 0.35rem;
}}

.metric-card-value {{
    font-size: 2rem;
    font-weight: 800;
    color: {C_TEXT};
    line-height: 1;
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
    width: 2rem;
    height: 2rem;
    border-radius: 0.5rem;
    font-weight: 800;
    font-size: 1.1rem;
    color: white;
}}

.grade-A {{ background: {C_SUCCESS}; }}
.grade-B {{ background: {C_PRIMARY}; }}
.grade-C {{ background: {C_WARNING}; }}
.grade-D {{ background: {C_DANGER}; }}

/* ==================== 信息卡片 / callout ==================== */
.callout {{
    border-radius: 0.625rem;
    padding: 0.875rem 1rem;
    border-left: 4px solid;
    font-size: 0.85rem;
    line-height: 1.5;
    margin-bottom: 0.5rem;
}}

.callout-info {{
    background: {C_INFO_BG};
    border-color: {C_PRIMARY};
    color: #1e3a5f;
}}

.callout-warning {{
    background: {C_WARNING_BG};
    border-color: {C_WARNING};
    color: #78350f;
}}

.callout-danger {{
    background: {C_DANGER_BG};
    border-color: {C_DANGER};
    color: #7f1d1d;
}}

.callout-success {{
    background: {C_SUCCESS_BG};
    border-color: {C_SUCCESS};
    color: #14532d;
}}

/* ==================== 按钮 ==================== */
.stButton > button {{
    border-radius: 0.5rem;
    font-weight: 600;
    transition: all 0.15s;
    border: 1px solid {C_BORDER};
}}

.stButton > button:hover {{
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}}

/* ==================== 表格 ==================== */
.stDataFrame {{
    border-radius: 0.625rem;
    overflow: hidden;
    border: 1px solid {C_BORDER};
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}}

.stDataFrame [data-testid="stDataFrameResizable"] {{
    border-radius: 0.625rem;
}}

/* 表头 */
.stDataFrame th {{
    background: #f8fafc !important;
    font-weight: 700 !important;
    font-size: 0.75rem !important;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    color: {C_TEXT_MUTED} !important;
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
    box-shadow: 0 0 0 3px {C_PRIMARY_LIGHT} !important;
}}

/* ==================== Expander ==================== */
.streamlit-expanderHeader {{
    font-weight: 600;
    font-size: 0.9rem;
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
    color: {C_TEXT_MUTED};
    border-bottom: 3px solid transparent;
    transition: all 0.15s;
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
/* Metric 元素 */
[data-testid="stMetric"] {{
    background: {C_CARD};
    border: 1px solid {C_BORDER};
    border-radius: 0.625rem;
    padding: 0.875rem 1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}}

[data-testid="stMetric"] label {{
    color: {C_TEXT_MUTED} !important;
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

/* caption */
.stCaption {{
    color: {C_TEXT_MUTED} !important;
    font-size: 0.8rem !important;
}}

/* subheader */
h3 {{
    color: {C_TEXT} !important;
    font-weight: 700 !important;
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
        f"""
        <div class="main-header">
            <div class="main-header-icon">
                {_svg("trending-up", 28, "#ffffff")}
            </div>
            <div class="main-header-text">
                <h1>{title}</h1>
                <div class="subtitle">{subtitle}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_header(icon: str, title: str, color: str = C_PRIMARY) -> None:
    """渲染页面标题（带小图标方块）。"""
    bg = color + "1a"  # 10% opacity
    st.markdown(
        f"""
        <div class="page-header">
            <div class="page-header-icon" style="background:{bg};color:{color};">
                {_svg(icon, 18, color)}
            </div>
            <span class="page-header-title">{title}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar_group(title: str) -> None:
    """在侧边栏渲染分组标题。"""
    st.markdown(f'<div class="sidebar-group-title">{title}</div>', unsafe_allow_html=True)


def sidebar_footer(version: str) -> None:
    """在侧边栏底部渲染版本信息。"""
    st.markdown(
        f'<div class="sidebar-footer">TradeLead Intel<br>{version}<br>本地版 · 数据不出域</div>',
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str | int, accent_color: str = C_PRIMARY, delta: str = "") -> str:
    """返回指标卡片的 HTML 字符串。"""
    delta_html = f'<div class="metric-card-delta" style="color:{accent_color};">{delta}</div>' if delta else ""
    return f"""
    <div class="metric-card">
        <div class="metric-card-accent" style="background:{accent_color};"></div>
        <div class="metric-card-label">{label}</div>
        <div class="metric-card-value">{value}</div>
        {delta_html}
    </div>
    """


def callout(text: str, kind: str = "info") -> None:
    """渲染带左侧色条的提示框。kind: info / warning / danger / success"""
    st.markdown(f'<div class="callout callout-{kind}">{text}</div>', unsafe_allow_html=True)


def grade_badge(grade: str) -> str:
    """返回评级徽章 HTML。"""
    color = GRADE_COLORS.get(grade, C_TEXT_MUTED)
    return f'<span class="grade-badge grade-{grade}" style="background:{color};">{grade}</span>'
