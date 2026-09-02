"""
Reusable UI building blocks for Digital Twin AI.
All st.markdown calls use single-line string concatenation — no multiline
triple-quoted HTML — to avoid Streamlit's markdown parser treating indented
HTML as code blocks and rendering it as plain text.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime

import streamlit as st

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from utils.api_client import APIClient  # noqa: E402


# ═══════════════════════════════════════════════════════════════════════════════
#  SESSION BOOTSTRAP
# ═══════════════════════════════════════════════════════════════════════════════

def bootstrap_session() -> None:
    if "api_client" not in st.session_state:
        st.session_state.api_client = APIClient(
            os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
        )
    if "token" not in st.session_state:
        st.session_state.token = None
    if "user" not in st.session_state:
        st.session_state.user = None
    if "theme" not in st.session_state:
        st.session_state.theme = "dark"


def require_auth() -> None:
    bootstrap_session()
    if not st.session_state.get("token"):
        is_light = st.session_state.get("theme", "dark") == "light"
        bg   = "linear-gradient(135deg,#FFFFFF,#F0F5FF)" if is_light else "linear-gradient(135deg,rgba(13,17,28,.98),rgba(20,27,50,.98))"
        bdr  = "rgba(37,99,235,.2)"
        head = "#0F172A" if is_light else "#F1F5F9"
        sub  = "#64748B"
        st.markdown(
            f'<div style="text-align:center;padding:4rem 2rem;background:{bg};'
            f'border:1px solid {bdr};border-radius:20px;margin-top:3rem;">'
            '<div style="font-size:3rem;margin-bottom:1rem;">🔐</div>'
            f'<div style="font-size:1.3rem;font-weight:700;color:{head};margin-bottom:.5rem;">Authentication Required</div>'
            f'<div style="font-size:.875rem;color:{sub};">Please log in to access your Digital Twin dashboard.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.stop()


# ═══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════

def render_sidebar() -> None:
    bootstrap_session()
    is_light = st.session_state.get("theme", "dark") == "light"
    text_muted   = "#64748B"
    nav_label_c  = "#334155" if is_light else "#4B5563"

    with st.sidebar:
        # ── Logo / brand ────────────────────────────────────────────────────
        logo_title_c = "#0F172A" if is_light else "#F1F5F9"
        logo_sub_c   = "#2563EB"
        st.markdown(
            '<div style="padding:1.2rem .75rem .8rem;'
            'border-bottom:1px solid rgba(37,99,235,.1);margin-bottom:.35rem;">'
            '<div style="display:flex;align-items:center;gap:.6rem;overflow:hidden;">'
            '<div style="width:36px;height:36px;flex-shrink:0;'
            'background:linear-gradient(135deg,#2563EB,#7C3AED);'
            'border-radius:9px;display:flex;align-items:center;justify-content:center;'
            'font-size:1.1rem;box-shadow:0 3px 10px rgba(37,99,235,.35);">🧠</div>'
            f'<div style="overflow:hidden;white-space:nowrap;">'
            f'<div style="font-size:.88rem;font-weight:800;color:{logo_title_c};letter-spacing:-.02em;">Digital Twin</div>'
            f'<div style="font-size:.55rem;color:{logo_sub_c};font-weight:700;'
            f'text-transform:uppercase;letter-spacing:.14em;">AI Platform · v4.0</div>'
            f'</div></div></div>',
            unsafe_allow_html=True,
        )

        # ── Nav links ────────────────────────────────────────────────────────
        st.markdown(
            f'<div style="padding:.3rem .75rem .15rem;font-size:.56rem;font-weight:700;'
            f'color:{nav_label_c};text-transform:uppercase;letter-spacing:.14em;'
            f'white-space:nowrap;overflow:hidden;">Menu</div>',
            unsafe_allow_html=True,
        )
        nav = [
            ("app.py",                    "🏠", "Dashboard"),
            ("pages/1_Profile.py",        "👤", "Profile"),
            ("pages/2_Financial.py",      "💰", "Finance"),
            ("pages/3_Study.py",          "📚", "Study"),
            ("pages/4_Habits_Fitness.py", "🔥", "Habits & Fitness"),
            ("pages/5_Goals.py",          "🎯", "Goals"),
            ("pages/6_Analytics.py",      "📊", "Analytics"),
            ("pages/7_Forecasting.py",    "🔮", "Forecasting"),
            ("pages/8_Simulation.py",     "🧬", "Simulation"),
            ("pages/9_Chat.py",           "🤖", "AI Chat"),
            ("pages/10_Dashboard.py",     "📈", "Full Dashboard"),
            ("pages/11_Reports.py",       "📄", "Reports"),
        ]
        for page, icon, label in nav:
            st.page_link(page, label=f"{icon}  {label}")

        # ── spacer ───────────────────────────────────────────────────────────
        st.markdown("<div style='flex:1'></div>", unsafe_allow_html=True)

        # ── Sign out ─────────────────────────────────────────────────────────
        if st.session_state.get("token"):
            st.markdown(
                '<div style="padding:.35rem .75rem 0;white-space:nowrap;overflow:hidden;">'
                f'<div style="font-size:.56rem;font-weight:700;color:{nav_label_c};'
                f'text-transform:uppercase;letter-spacing:.14em;margin-bottom:.3rem;">Account</div>'
                '</div>',
                unsafe_allow_html=True,
            )
            if st.button("⏻  Sign Out", use_container_width=True, key="sidebar_logout"):
                st.session_state.token = None
                st.session_state.user  = None
                st.rerun()

        st.markdown(
            '<div class="version-footer">v4.0</div>',
            unsafe_allow_html=True,
        )


def render_topbar(page_name: str = "") -> None:
    """
    Render the horizontal topbar: brand | page name || user pill + theme toggle.
    Call this once per page right after render_sidebar().
    """
    bootstrap_session()
    is_light = st.session_state.get("theme", "dark") == "light"
    user     = st.session_state.get("user") or {}
    name     = user.get("name", "")
    initials = "".join(p[0].upper() for p in name.split()[:2]) if name else "DT"

    # theme toggle — rendered as a clickable Streamlit button overlaid on the pill
    knob_icon   = "☀️" if not is_light else "🌙"
    next_theme  = "light" if not is_light else "dark"
    toggle_tip  = "Switch to Light" if not is_light else "Switch to Dark"

    text_primary = "#0F172A" if is_light else "#F1F5F9"
    text_muted   = "#64748B"
    border       = "rgba(37,99,235,.14)"
    accent_glow  = "rgba(37,99,235,.12)" if is_light else "rgba(37,99,235,.18)"
    topbar_bg    = "rgba(255,255,255,0.95)" if is_light else "rgba(6,8,15,0.95)"
    badge_c      = "#2563EB"

    # Static topbar HTML (brand + breadcrumb + user pill)
    st.markdown(
        f'<div class="dt-topbar">'
        # left: brand
        f'<div class="dt-topbar-left">'
        f'<div class="dt-topbar-brand">'
        f'<div class="tb-icon">🧠</div>'
        f'<span style="color:{text_primary};">Digital Twin</span>'
        f'</div>'
        + (
            f'<div class="dt-topbar-divider"></div>'
            f'<span class="dt-topbar-page">{page_name}</span>'
            if page_name else ""
        ) +
        f'<div class="dt-badge">v4.0</div>'
        f'</div>'
        # right: user pill + theme toggle
        f'<div class="dt-topbar-right">'
        + (
            f'<div class="dt-user-pill">'
            f'<div class="dt-user-avatar">{initials}</div>'
            f'<span class="dt-user-name">{name}</span>'
            f'</div>'
            if name else ""
        ) +
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Theme toggle button — floats over the topbar right side
    # We inject it as a Streamlit button and use CSS to position it
    col_space, col_btn = st.columns([0.92, 0.08], gap="small")
    with col_btn:
        if st.button(knob_icon, key="topbar_theme", help=toggle_tip):
            st.session_state.theme = next_theme
            st.rerun()

    # Move the button up into the topbar with CSS
    st.markdown(
        '<style>'
        '[data-testid="stHorizontalBlock"]:has(button[title="' + toggle_tip + '"]) {'
        '  margin-top: -56px !important;'
        '  margin-bottom: 0 !important;'
        '  position: relative; z-index: 300;'
        '}'
        '[data-testid="stHorizontalBlock"]:has(button[title="' + toggle_tip + '"]) [data-testid="stColumn"]:first-child {'
        '  visibility: hidden;'
        '}'
        '[data-testid="stHorizontalBlock"]:has(button[title="' + toggle_tip + '"]) button {'
        '  background: ' + accent_glow + ' !important;'
        '  border: 1px solid ' + border + ' !important;'
        '  border-radius: 10px !important;'
        '  box-shadow: none !important;'
        '  font-size: 1rem !important;'
        '  padding: .3rem !important;'
        '  height: 36px !important;'
        '  min-height: 36px !important;'
        '}'
        '</style>',
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE HEADER
# ═══════════════════════════════════════════════════════════════════════════════

def page_header(title: str, subtitle: str = "", greeting: str = "") -> None:
    hour = datetime.now().hour
    if not greeting:
        time_word = "Morning" if hour < 12 else "Afternoon" if hour < 17 else "Evening"
        user = st.session_state.get("user")
        name = user.get("name", "").split()[0] if user else ""
        greeting = f"Good {time_word}{', ' + name if name else ''} 👋"

    st.markdown(
        '<div class="page-header">'
        + f'<div class="ph-greeting">{greeting}</div>'
        + f'<div class="ph-title">{title}</div>'
        + (f'<div class="ph-sub">{subtitle}</div>' if subtitle else "")
        + "</div>",
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  METRIC CARDS
# ═══════════════════════════════════════════════════════════════════════════════

def metric_card(
    icon: str,
    label: str,
    value: str,
    sub: str = "",
    trend: str = "",
    trend_up: bool = True,
    accent: str = "linear-gradient(90deg,#2563EB,#7C3AED)",
) -> str:
    trend_html = ""
    if trend:
        cls = "mc-trend-up" if trend_up else "mc-trend-down"
        arrow = "↑" if trend_up else "↓"
        trend_html = f'<div class="{cls}">{arrow} {trend}</div>'
    return (
        f'<div class="metric-card" style="--accent:{accent};">'
        + f'<span class="mc-icon">{icon}</span>'
        + f'<div class="mc-label">{label}</div>'
        + f'<div class="mc-value">{value}</div>'
        + (f'<div class="mc-sub">{sub}</div>' if sub else "")
        + trend_html
        + "</div>"
    )


def metric_row(cards: list[dict]) -> None:
    cols = st.columns(len(cards))
    for col, card in zip(cols, cards):
        with col:
            st.markdown(metric_card(**card), unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION HEADER
# ═══════════════════════════════════════════════════════════════════════════════

def section_header(icon: str, title: str, subtitle: str = "") -> None:
    sub_html = f'<div class="sh-subtitle">{subtitle}</div>' if subtitle else ""
    st.markdown(
        '<div class="section-header">'
        + f'<div class="sh-icon">{icon}</div>'
        + f'<div><div class="sh-title">{title}</div>{sub_html}</div>'
        + "</div>",
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  INSIGHT CARD
# ═══════════════════════════════════════════════════════════════════════════════

_INSIGHT_COLORS = {
    "tip":        "#2563EB",
    "warning":    "#F59E0B",
    "success":    "#10B981",
    "prediction": "#7C3AED",
    "info":       "#06B6D4",
}


def insight_card(type_: str, text: str, footer: str = "") -> None:
    color = _INSIGHT_COLORS.get(type_, "#2563EB")
    labels = {
        "tip": "💡 Insight", "warning": "⚠️ Attention",
        "success": "✅ Achievement", "prediction": "🔮 Prediction", "info": "ℹ️ Info",
    }
    label = labels.get(type_, type_.title())
    st.markdown(
        f'<div class="insight-card" style="--insight-color:{color};">'
        + f'<div class="ic-type">{label}</div>'
        + f'<div class="ic-text">{text}</div>'
        + (f'<div class="ic-footer">{footer}</div>' if footer else "")
        + "</div>",
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  PROGRESS BAR
# ═══════════════════════════════════════════════════════════════════════════════

def progress_bar(
    label: str,
    value: float,
    max_val: float = 100,
    color: str = "linear-gradient(90deg,#2563EB,#7C3AED)",
) -> None:
    pct = min(value / max_val * 100, 100) if max_val else 0
    st.markdown(
        '<div class="progress-wrap">'
        + f'<div class="progress-label"><span>{label}</span><span>{pct:.0f}%</span></div>'
        + '<div class="progress-bar-bg">'
        + f'<div class="progress-bar-fill" style="width:{pct:.1f}%;--bar-color:{color};"></div>'
        + "</div></div>",
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  BADGE
# ═══════════════════════════════════════════════════════════════════════════════

_STATUS_BADGE = {
    "completed":   "badge-green",
    "in progress": "badge-blue",
    "not started": "badge-yellow",
    "on hold":     "badge-purple",
    "income":      "badge-green",
    "expense":     "badge-red",
}


def badge(text: str) -> str:
    cls = _STATUS_BADGE.get(text.lower(), "badge-blue")
    return f'<span class="badge {cls}">{text}</span>'


# ═══════════════════════════════════════════════════════════════════════════════
#  EMPTY STATE
# ═══════════════════════════════════════════════════════════════════════════════

def empty_state(icon: str, title: str, subtitle: str = "") -> None:
    is_light = st.session_state.get("theme", "dark") == "light"
    bg  = "rgba(248,250,255,.7)"     if is_light else "rgba(13,17,28,.6)"
    bdr = "rgba(37,99,235,.18)"
    tc  = "#475569"                  if is_light else "#94A3B8"
    sc  = "#64748B"
    st.markdown(
        f'<div style="text-align:center;padding:3rem 2rem;background:{bg};'
        f'border:1px dashed {bdr};border-radius:16px;margin:1rem 0;">'
        + f'<div style="font-size:2.5rem;margin-bottom:.75rem;">{icon}</div>'
        + f'<div style="font-size:1rem;font-weight:600;color:{tc};margin-bottom:.35rem;">{title}</div>'
        + (f'<div style="font-size:.8rem;color:{sc};">{subtitle}</div>' if subtitle else "")
        + "</div>",
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  TWIN VISUALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

def twin_visualization(name: str, scores: dict[str, float], overall: float) -> None:
    is_light = st.session_state.get("theme", "dark") == "light"
    node_bg   = "#F8FAFF"              if is_light else "rgba(13,17,28,.9)"
    node_bdr  = "rgba(37,99,235,.16)" if is_light else "rgba(37,99,235,.2)"
    node_lbl  = "#64748B"
    node_sc   = "#1D4ED8"             if is_light else "#60A5FA"
    core_bg   = "linear-gradient(135deg,rgba(37,99,235,.2),rgba(139,92,246,.2))" if is_light else "linear-gradient(135deg,rgba(37,99,235,.3),rgba(139,92,246,.3))"
    wrap_bg   = "linear-gradient(135deg,#FFFFFF,#F0F5FF)" if is_light else "linear-gradient(135deg,rgba(13,17,28,.98),rgba(20,27,50,.98))"
    wrap_bdr  = "rgba(37,99,235,.16)" if is_light else "rgba(37,99,235,.2)"
    name_c    = "#0F172A"             if is_light else "#F1F5F9"
    score_c   = "#1D4ED8"             if is_light else "#60A5FA"
    sub_c     = "#64748B"

    node_defs = [
        ("📚", "Study"), ("💰", "Finance"), ("🔥", "Habits"),
        ("🏃", "Fitness"), ("🎯", "Goals"), ("📊", "Analytics"),
    ]

    def _node(ic: str, k: str) -> str:
        sc = int(scores.get(k, 0))
        return (
            f'<div style="background:{node_bg};border:1px solid {node_bdr};'
            'border-radius:12px;padding:.75rem 1rem;text-align:center;">'
            + f'<div style="font-size:1.4rem;">{ic}</div>'
            + f'<div style="font-size:.7rem;font-weight:600;color:{node_lbl};text-transform:uppercase;letter-spacing:.08em;margin-top:.2rem;">{k}</div>'
            + f'<div style="font-size:1.1rem;font-weight:700;color:{node_sc};">{sc}</div>'
            + "</div>"
        )

    top = (
        '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:.75rem;margin-bottom:.75rem;">'
        + "".join(_node(ic, k) for ic, k in node_defs[:3])
        + "</div>"
    )
    bot = (
        '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:.75rem;margin-top:.75rem;">'
        + "".join(_node(ic, k) for ic, k in node_defs[3:])
        + "</div>"
    )
    initials = "".join(p[0].upper() for p in name.split()[:2]) if name else "DT"

    html = (
        f'<div style="background:{wrap_bg};'
        f'border:1px solid {wrap_bdr};border-radius:20px;padding:2rem;text-align:center;">'
        + top
        + '<div style="padding:1.25rem 0 1rem;">'
        + f'<div style="width:100px;height:100px;margin:0 auto .75rem;'
        f'background:{core_bg};'
        'border:2px solid rgba(37,99,235,.5);border-radius:50%;'
        'display:flex;align-items:center;justify-content:center;'
        f'font-size:1.75rem;font-weight:800;color:#fff;box-shadow:0 0 40px rgba(37,99,235,.2);">{initials}</div>'
        + f'<div style="font-size:1.1rem;font-weight:700;color:{name_c};margin-bottom:.25rem;">{name}\'s Digital Twin</div>'
        + f'<div style="font-size:2.5rem;font-weight:800;color:{score_c};line-height:1.1;">{overall:.0f}%</div>'
        + f'<div style="font-size:.8rem;color:{sub_c};margin-top:.2rem;">Overall Alignment Score</div>'
        + "</div>"
        + bot
        + "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  AI INSIGHTS GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════

def generate_insights(
    study: list[dict],
    habits: list[dict],
    fitness: list[dict],
    goals: list[dict],
    financial: list[dict],
) -> list[dict[str, str]]:
    insights: list[dict[str, str]] = []

    if study:
        avg_focus = sum(s["focus_score"] for s in study) / len(study)
        if avg_focus >= 80:
            insights.append({"type": "success", "text": f"Your average focus score is {avg_focus:.0f}/100 — excellent concentration levels.", "footer": "Based on study sessions"})
        elif avg_focus < 60:
            insights.append({"type": "warning", "text": f"Your average focus score is {avg_focus:.0f}/100. Consider shorter, more focused sessions.", "footer": "Based on study sessions"})
        avg_hours = sum(s["study_hours"] for s in study) / len(study)
        insights.append({"type": "tip", "text": f"You study an average of {avg_hours:.1f} hours per session across {len(study)} recorded sessions.", "footer": "Study analytics"})
    else:
        insights.append({"type": "info", "text": "Start logging study sessions to unlock AI-powered study insights.", "footer": "No data yet"})

    if habits:
        completed = sum(1 for h in habits if h.get("completed"))
        pct = completed / len(habits) * 100
        if pct >= 70:
            insights.append({"type": "success", "text": f"{pct:.0f}% of your habits are completed — strong consistency!", "footer": "Habit tracker"})
        else:
            insights.append({"type": "warning", "text": f"Only {pct:.0f}% of habits completed. Focus on your top priority habits first.", "footer": "Habit tracker"})
        best_streak = max((h.get("streak", 0) for h in habits), default=0)
        if best_streak > 0:
            insights.append({"type": "tip", "text": f"Your best current habit streak is {best_streak} days. Keep it going!", "footer": "Streak data"})
    else:
        insights.append({"type": "info", "text": "Add habits to track your daily consistency and build streaks.", "footer": "No data yet"})

    if fitness:
        total_cal = sum(f.get("calories_burned", 0) for f in fitness)
        total_dur = sum(f.get("duration", 0) for f in fitness)
        insights.append({"type": "tip", "text": f"You've burned {total_cal:.0f} calories across {len(fitness)} fitness sessions ({total_dur:.0f} total minutes).", "footer": "Fitness tracker"})
    else:
        insights.append({"type": "info", "text": "Log fitness activities to track your health and calorie progress.", "footer": "No data yet"})

    if goals:
        active = [g for g in goals if g.get("status", "").lower() not in ("completed",)]
        completed_goals = len(goals) - len(active)
        if completed_goals > 0:
            insights.append({"type": "success", "text": f"You've completed {completed_goals} goal(s). Great progress!", "footer": "Goals tracker"})
        if active:
            avg_pct = sum(
                min(g["current_value"] / g["target_value"] * 100, 100)
                for g in active if g.get("target_value", 0) > 0
            ) / len(active) if active else 0
            insights.append({"type": "prediction", "text": f"Your active goals are {avg_pct:.0f}% complete on average. Keep pushing!", "footer": "Goal predictions"})
    else:
        insights.append({"type": "info", "text": "Define goals to get AI-powered progress predictions.", "footer": "No data yet"})

    if financial:
        income = sum(f["amount"] for f in financial if f.get("record_type") == "income")
        expenses = sum(f["amount"] for f in financial if f.get("record_type") == "expense")
        net = income - expenses
        if net > 0:
            insights.append({"type": "success", "text": f"Net savings: ${net:,.2f}. You're spending less than you earn — healthy financial behavior.", "footer": "Finance analytics"})
        elif net < 0:
            insights.append({"type": "warning", "text": f"Net savings: ${net:,.2f}. Your expenses exceed income. Review your spending categories.", "footer": "Finance analytics"})

    return insights[:6]


# ═══════════════════════════════════════════════════════════════════════════════
#  SCORE CALCULATOR
# ═══════════════════════════════════════════════════════════════════════════════

def compute_scores(
    study: list[dict],
    habits: list[dict],
    fitness: list[dict],
    goals: list[dict],
    financial: list[dict],
) -> tuple[dict[str, float], float]:
    scores: dict[str, float] = {}

    scores["Study"] = (
        sum(s["performance_score"] for s in study) / len(study) if study else 0
    )
    scores["Habits"] = (
        sum(1 for h in habits if h.get("completed")) / len(habits) * 100 if habits else 0
    )
    scores["Fitness"] = min(len(fitness) * 10, 100) if fitness else 0

    if goals:
        scores["Goals"] = sum(
            min(g["current_value"] / g["target_value"] * 100, 100)
            for g in goals if g.get("target_value", 0) > 0
        ) / len(goals)
    else:
        scores["Goals"] = 0

    if financial:
        income = sum(f["amount"] for f in financial if f.get("record_type") == "income")
        expenses = sum(f["amount"] for f in financial if f.get("record_type") == "expense")
        scores["Finance"] = min((income / expenses * 70) if expenses > 0 else 70, 100)
    else:
        scores["Finance"] = 0

    scores["Analytics"] = 75 if any(scores.values()) else 0

    overall = sum(scores.values()) / len(scores) if scores else 0
    return scores, overall
