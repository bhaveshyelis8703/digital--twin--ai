"""
Digital Twin AI — Study
"""
import os, sys
from datetime import datetime

import plotly.graph_objects as go
import streamlit as st

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from components.theme import inject_theme
from components.ui import (
    bootstrap_session, require_auth, render_sidebar,
    page_header, section_header, metric_row, empty_state, insight_card,
)

st.set_page_config(page_title="Study · Digital Twin AI", page_icon="📚", layout="wide", initial_sidebar_state="expanded")
inject_theme()
bootstrap_session()
render_sidebar()
require_auth()

client = st.session_state.api_client
token  = st.session_state.token

_PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color="#94A3B8", size=12),
    margin=dict(l=0, r=0, t=30, b=0),
    xaxis=dict(gridcolor="rgba(37,99,235,.08)", linecolor="rgba(37,99,235,.15)", tickfont=dict(color="#64748B")),
    yaxis=dict(gridcolor="rgba(37,99,235,.08)", linecolor="rgba(37,99,235,.15)", tickfont=dict(color="#64748B")),
)

@st.cache_data(ttl=30, show_spinner=False)
def load_study(tok):
    try:
        return client.get("/api/study", token=tok) or []
    except Exception:
        return []

sessions = load_study(token)

page_header("Study Tracker", "Monitor your academic performance and study habits")

# ── KPIs ──────────────────────────────────────────────────────────────────────
if sessions:
    total_hours  = sum(s.get("study_hours", 0) for s in sessions)
    avg_focus    = sum(s.get("focus_score", 0) for s in sessions) / len(sessions)
    avg_perf     = sum(s.get("performance_score", 0) for s in sessions) / len(sessions)
    avg_task     = sum(s.get("task_completion", 0) for s in sessions) / len(sessions)
    subjects     = len({s.get("subject") for s in sessions})
else:
    total_hours = avg_focus = avg_perf = avg_task = subjects = 0

metric_row([
    dict(icon="⏱️", label="Total Hours",      value=f"{total_hours:.1f}h",
         sub="Logged",            accent="linear-gradient(90deg,#2563EB,#1D4ED8)"),
    dict(icon="🎯", label="Avg Focus",        value=f"{avg_focus:.0f}/100",
         sub="Concentration",     trend_up=avg_focus >= 70,
         accent="linear-gradient(90deg,#7C3AED,#6D28D9)"),
    dict(icon="⭐", label="Avg Performance",  value=f"{avg_perf:.0f}/100",
         sub="Score",             trend_up=avg_perf >= 70,
         accent="linear-gradient(90deg,#F59E0B,#D97706)"),
    dict(icon="✅", label="Task Completion",  value=f"{avg_task:.0f}%",
         sub="Average",           trend_up=avg_task >= 70,
         accent="linear-gradient(90deg,#10B981,#059669)"),
    dict(icon="📖", label="Subjects",         value=str(subjects),
         sub="Unique",
         accent="linear-gradient(90deg,#06B6D4,#0284C7)"),
])

st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

# ── CHARTS ────────────────────────────────────────────────────────────────────
if sessions:
    col_line, col_bar = st.columns(2, gap="large")
    sorted_s = sorted(sessions, key=lambda x: x.get("study_date", ""))

    with col_line:
        section_header("📈", "Study Hours Over Time")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[s["study_date"][:10] for s in sorted_s],
            y=[s["study_hours"] for s in sorted_s],
            mode="lines+markers", name="Hours",
            line=dict(color="#2563EB", width=2),
            marker=dict(size=6, color="#2563EB"),
            fill="tozeroy", fillcolor="rgba(37,99,235,.08)",
        ))
        fig.update_layout(**_PLOTLY_LAYOUT, height=240)
        st.plotly_chart(fig, use_container_width=True)

    with col_bar:
        section_header("🎯", "Focus vs Performance vs Completion")
        fig2 = go.Figure()
        dates = [s["study_date"][:10] for s in sorted_s[-10:]]
        fig2.add_trace(go.Bar(x=dates, y=[s["focus_score"] for s in sorted_s[-10:]],
                              name="Focus", marker_color="#2563EB", opacity=0.85))
        fig2.add_trace(go.Bar(x=dates, y=[s["performance_score"] for s in sorted_s[-10:]],
                              name="Performance", marker_color="#7C3AED", opacity=0.85))
        fig2.add_trace(go.Bar(x=dates, y=[s["task_completion"] for s in sorted_s[-10:]],
                              name="Completion", marker_color="#10B981", opacity=0.85))
        fig2.update_layout(**_PLOTLY_LAYOUT, height=240, barmode="group",
                           legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#94A3B8")))
        st.plotly_chart(fig2, use_container_width=True)

st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

# ── ADD SESSION + RECENT ──────────────────────────────────────────────────────
col_form, col_list = st.columns([1, 1.5], gap="large")

with col_form:
    section_header("➕", "Log Session", "Record a new study session")
    with st.form("study_form"):
        subject       = st.text_input("Subject", placeholder="Mathematics, Python, History…")
        study_date    = st.date_input("Date", value=datetime.today())
        study_hours   = st.number_input("Hours Studied", min_value=0.5, max_value=16.0, value=1.0, step=0.5)
        focus_score   = st.slider("Focus Score",       0, 100, 80)
        task_comp     = st.slider("Task Completion %", 0, 100, 80)
        perf_score    = st.slider("Performance Score", 0, 100, 80)
        submitted     = st.form_submit_button("Log Session", use_container_width=True)

    if submitted:
        if not subject.strip():
            st.error("Subject is required.")
        else:
            try:
                client.post(
                    "/api/study",
                    payload={
                        "subject":           subject.strip(),
                        "study_date":        datetime.combine(study_date, datetime.min.time()).isoformat(),
                        "study_hours":       float(study_hours),
                        "focus_score":       float(focus_score),
                        "task_completion":   float(task_comp),
                        "performance_score": float(perf_score),
                    },
                    token=token,
                )
                st.success("Session logged.")
                st.cache_data.clear()
                st.rerun()
            except Exception:
                st.error("Failed to log session.")

with col_list:
    section_header("📋", "Recent Sessions", f"{len(sessions)} total")
    if sessions:
        for s in sorted(sessions, key=lambda x: x.get("study_date",""), reverse=True)[:10]:
            perf  = s.get("performance_score", 0)
            color = "#10B981" if perf >= 75 else "#F59E0B" if perf >= 50 else "#EF4444"
            st.markdown(
                f"""
                <div style="
                    background:rgba(13,17,28,.8);border:1px solid rgba(37,99,235,.1);
                    border-radius:12px;padding:.85rem 1.1rem;margin-bottom:.4rem;
                    display:flex;justify-content:space-between;align-items:center
                ">
                    <div style="flex:1;min-width:0">
                        <div style="font-size:.85rem;font-weight:600;color:#E2E8F0">{s.get('subject','')}</div>
                        <div style="font-size:.72rem;color:#64748B;margin-top:.15rem">
                            {s.get('study_date','')[:10]} · {s.get('study_hours',0):.1f}h ·
                            Focus {s.get('focus_score',0):.0f} · Task {s.get('task_completion',0):.0f}%
                        </div>
                    </div>
                    <div style="text-align:right;margin-left:1rem;flex-shrink:0">
                        <div style="font-size:1.1rem;font-weight:700;color:{color}">{perf:.0f}</div>
                        <div style="font-size:.68rem;color:#64748B">perf</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        empty_state("📚", "No sessions yet", "Log your first study session to see insights.")

# ── AI INSIGHTS ───────────────────────────────────────────────────────────────
if sessions:
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    section_header("🤖", "Study Insights", "AI-derived from your sessions")
    avg_f = sum(s.get("focus_score", 0) for s in sessions) / len(sessions)
    avg_p = sum(s.get("performance_score", 0) for s in sessions) / len(sessions)
    col1, col2 = st.columns(2)
    with col1:
        t = "tip" if avg_f >= 70 else "warning"
        insight_card(t, f"Average focus score: {avg_f:.0f}/100. "
                     + ("Great concentration!" if avg_f >= 70 else "Try Pomodoro technique for better focus."),
                     "Focus analytics")
    with col2:
        t = "success" if avg_p >= 75 else "tip"
        insight_card(t, f"Average performance: {avg_p:.0f}/100 across {len(sessions)} sessions. "
                     + ("Excellent work!" if avg_p >= 75 else "Review weaker subjects more frequently."),
                     "Performance analytics")
