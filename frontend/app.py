"""
Digital Twin AI — Home Dashboard
"""
import os
import sys

import streamlit as st

# ── path bootstrap ────────────────────────────────────────────────────────────
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from components.theme import inject_theme
from components.ui import (
    bootstrap_session,
    compute_scores,
    empty_state,
    generate_insights,
    insight_card,
    metric_row,
    page_header,
    progress_bar,
    render_sidebar,
    require_auth,
    section_header,
)

st.set_page_config(
    page_title="Digital Twin AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_theme()
bootstrap_session()
render_sidebar()
require_auth()

# ── fetch all data ────────────────────────────────────────────────────────────
client = st.session_state.api_client
token  = st.session_state.token
user   = st.session_state.user or {}

@st.cache_data(ttl=60, show_spinner=False)
def load_dashboard_data(tok: str):
    try:
        study    = client.get("/api/study",            token=tok) or []
        habits   = client.get("/api/habits",           token=tok) or []
        fitness  = client.get("/api/fitness",          token=tok) or []
        goals    = client.get("/api/goals",            token=tok) or []
        fin      = client.get("/api/financial/records",token=tok) or []
        summary  = client.get("/api/users/summary",    token=tok) or {}
        fin_sum  = client.get("/api/financial/summary",token=tok) or {}
    except Exception:
        study = habits = fitness = goals = fin = []
        summary = fin_sum = {}
    return study, habits, fitness, goals, fin, summary, fin_sum

study, habits, fitness, goals, fin, summary, fin_sum = load_dashboard_data(token)
scores, overall = compute_scores(study, habits, fitness, goals, fin)
name = user.get("name", "User")

# ── PAGE HEADER ───────────────────────────────────────────────────────────────
page_header(
    "Command Center",
    f"Your Digital Twin is active · {len(study)} study sessions · "
    f"{len(habits)} habits · {len(goals)} goals",
)

# ── KPI CARDS ─────────────────────────────────────────────────────────────────
total_income   = fin_sum.get("total_income", 0)
total_expenses = fin_sum.get("total_expenses", 0)
net_savings    = fin_sum.get("net_savings", 0)
habit_streak   = summary.get("habit_streak", 0)
active_goals   = summary.get("active_goals", 0)
total_cal      = sum(f.get("calories_burned", 0) for f in fitness)

metric_row([
    dict(icon="🎯", label="Twin Alignment",   value=f"{overall:.0f}%",
         sub="Overall score",  trend="Live",     trend_up=overall >= 60,
         accent="linear-gradient(90deg,#2563EB,#7C3AED)"),
    dict(icon="🔥", label="Habit Streak",     value=str(habit_streak),
         sub="Days",           trend=f"{len(habits)} habits",  trend_up=habit_streak > 0,
         accent="linear-gradient(90deg,#F59E0B,#EF4444)"),
    dict(icon="🎯", label="Active Goals",     value=str(active_goals),
         sub="In progress",    trend=f"{len(goals)} total",    trend_up=active_goals > 0,
         accent="linear-gradient(90deg,#10B981,#059669)"),
    dict(icon="💰", label="Net Savings",      value=f"${net_savings:,.0f}",
         sub="All time",       trend="Income vs Expenses",     trend_up=net_savings >= 0,
         accent="linear-gradient(90deg,#06B6D4,#0284C7)"),
    dict(icon="🏃", label="Calories Burned",  value=f"{total_cal:,.0f}",
         sub="Total",          trend=f"{len(fitness)} sessions", trend_up=len(fitness) > 0,
         accent="linear-gradient(90deg,#8B5CF6,#7C3AED)"),
])

st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

# ── TWIN VISUALIZATION + DOMAIN SCORES ───────────────────────────────────────
col_twin, col_scores = st.columns([1, 1], gap="large")

with col_twin:
    section_header("🧠", "Your Digital Twin", "Live alignment across all domains")

    # ── Digital Twin widget rendered inline (bypasses import cache) ──────────
    _initials = "".join(p[0].upper() for p in name.split()[:2]) if name else "DT"
    _node_defs = [
        ("📚", "Study"), ("💰", "Finance"), ("🔥", "Habits"),
        ("🏃", "Fitness"), ("🎯", "Goals"), ("📊", "Analytics"),
    ]
    def _node(ic, k):
        sc = int(scores.get(k, 0))
        return (
            f'<div style="background:rgba(13,17,28,.9);border:1px solid rgba(37,99,235,.2);'
            f'border-radius:12px;padding:.75rem 1rem;text-align:center;">'
            f'<div style="font-size:1.4rem;">{ic}</div>'
            f'<div style="font-size:.7rem;font-weight:600;color:#64748B;text-transform:uppercase;'
            f'letter-spacing:.08em;margin-top:.2rem;">{k}</div>'
            f'<div style="font-size:1.1rem;font-weight:700;color:#60A5FA;">{sc}</div>'
            f'</div>'
        )
    _top = (
        '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:.75rem;margin-bottom:.75rem;">'
        + "".join(_node(ic, k) for ic, k in _node_defs[:3])
        + "</div>"
    )
    _bot = (
        '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:.75rem;margin-top:.75rem;">'
        + "".join(_node(ic, k) for ic, k in _node_defs[3:])
        + "</div>"
    )
    _twin_html = (
        '<div style="background:linear-gradient(135deg,rgba(13,17,28,.98),rgba(20,27,50,.98));'
        'border:1px solid rgba(37,99,235,.2);border-radius:20px;padding:2rem;text-align:center;">'
        + _top
        + '<div style="text-align:center;padding:1.25rem 0 1rem;">'
        + '<div style="width:100px;height:100px;margin:0 auto .75rem;'
        'background:linear-gradient(135deg,rgba(37,99,235,.3),rgba(139,92,246,.3));'
        'border:2px solid rgba(37,99,235,.5);border-radius:50%;'
        'display:flex;align-items:center;justify-content:center;'
        'font-size:1.75rem;font-weight:800;color:#fff;'
        'box-shadow:0 0 40px rgba(37,99,235,.2);">'
        + _initials
        + "</div>"
        + '<div style="font-size:1.1rem;font-weight:700;color:#F1F5F9;margin-bottom:.25rem;">'
        + name + "&#39;s Digital Twin"
        + "</div>"
        + '<div style="font-size:2.5rem;font-weight:800;color:#60A5FA;line-height:1.1;">'
        + f"{overall:.0f}%"
        + "</div>"
        + '<div style="font-size:.8rem;color:#64748B;margin-top:.2rem;">Overall Alignment Score</div>'
        + "</div>"
        + _bot
        + "</div>"
    )
    st.markdown(_twin_html, unsafe_allow_html=True)

with col_scores:
    section_header("📈", "Domain Performance", "Score breakdown by life area")
    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    domain_cfg = [
        ("📚", "Study",    "#2563EB"),
        ("💰", "Finance",  "#06B6D4"),
        ("🔥", "Habits",   "#F59E0B"),
        ("🏃", "Fitness",  "#10B981"),
        ("🎯", "Goals",    "#8B5CF6"),
    ]
    for icon, key, color in domain_cfg:
        sc = scores.get(key, 0)
        progress_bar(
            f"{icon} {key}",
            sc,
            100,
            color=f"linear-gradient(90deg,{color},{color}aa)",
        )
        st.markdown("<div style='height:.25rem'></div>", unsafe_allow_html=True)

st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

# ── AI INSIGHTS ───────────────────────────────────────────────────────────────
section_header("🤖", "AI Insights", "Derived from your real data")

insights = generate_insights(study, habits, fitness, goals, fin)
if insights:
    cols = st.columns(2)
    for i, ins in enumerate(insights):
        with cols[i % 2]:
            insight_card(ins["type"], ins["text"], ins.get("footer", ""))
else:
    empty_state("🤖", "No insights yet", "Add data across domains to generate AI insights.")

st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

# ── RECENT ACTIVITY SUMMARY ───────────────────────────────────────────────────
section_header("⚡", "Recent Activity", "Latest entries across all domains")

col_a, col_b, col_c = st.columns(3)

with col_a:
    st.markdown(
        "<div style='font-size:.75rem;font-weight:700;color:#64748B;"
        "text-transform:uppercase;letter-spacing:.08em;margin-bottom:.5rem'>"
        "📚 Last Study Sessions</div>",
        unsafe_allow_html=True,
    )
    if study:
        for s in study[:3]:
            st.markdown(
                f"""
                <div style="background:rgba(13,17,28,.8);border:1px solid rgba(37,99,235,.12);
                            border-radius:10px;padding:.65rem 1rem;margin-bottom:.4rem">
                    <div style="font-size:.8rem;font-weight:600;color:#E2E8F0">{s.get('subject','—')}</div>
                    <div style="font-size:.72rem;color:#64748B;margin-top:.15rem">
                        {s.get('study_hours',0):.1f}h · Focus {s.get('focus_score',0):.0f}/100
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        empty_state("📚", "No sessions yet")

with col_b:
    st.markdown(
        "<div style='font-size:.75rem;font-weight:700;color:#64748B;"
        "text-transform:uppercase;letter-spacing:.08em;margin-bottom:.5rem'>"
        "🎯 Active Goals</div>",
        unsafe_allow_html=True,
    )
    active_g = [g for g in goals if g.get("status", "").lower() != "completed"]
    if active_g:
        for g in active_g[:3]:
            pct = min(g["current_value"] / g["target_value"] * 100, 100) if g.get("target_value") else 0
            st.markdown(
                f"""
                <div style="background:rgba(13,17,28,.8);border:1px solid rgba(37,99,235,.12);
                            border-radius:10px;padding:.65rem 1rem;margin-bottom:.4rem">
                    <div style="font-size:.8rem;font-weight:600;color:#E2E8F0">{g.get('name','—')}</div>
                    <div style="height:4px;background:rgba(30,41,59,.8);border-radius:99px;
                                margin:.4rem 0;overflow:hidden">
                        <div style="height:100%;width:{pct:.0f}%;
                                    background:linear-gradient(90deg,#2563EB,#7C3AED);
                                    border-radius:99px"></div>
                    </div>
                    <div style="font-size:.72rem;color:#64748B">{pct:.0f}% complete</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        empty_state("🎯", "No active goals")

with col_c:
    st.markdown(
        "<div style='font-size:.75rem;font-weight:700;color:#64748B;"
        "text-transform:uppercase;letter-spacing:.08em;margin-bottom:.5rem'>"
        "💰 Recent Transactions</div>",
        unsafe_allow_html=True,
    )
    if fin:
        for f in fin[:3]:
            color = "#10B981" if f.get("record_type") == "income" else "#EF4444"
            sign  = "+" if f.get("record_type") == "income" else "-"
            st.markdown(
                f"""
                <div style="background:rgba(13,17,28,.8);border:1px solid rgba(37,99,235,.12);
                            border-radius:10px;padding:.65rem 1rem;margin-bottom:.4rem;
                            display:flex;justify-content:space-between;align-items:center">
                    <div>
                        <div style="font-size:.8rem;font-weight:600;color:#E2E8F0">
                            {f.get('description','—')[:28]}</div>
                        <div style="font-size:.72rem;color:#64748B">{f.get('category','')}</div>
                    </div>
                    <div style="font-size:.9rem;font-weight:700;color:{color}">
                        {sign}${f.get('amount',0):,.0f}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        empty_state("💰", "No transactions yet")
