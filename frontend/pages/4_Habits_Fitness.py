"""
Digital Twin AI — Habits & Fitness
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
    page_header, section_header, metric_row, empty_state,
    progress_bar, badge, insight_card,
)

st.set_page_config(page_title="Habits & Fitness · Digital Twin AI", page_icon="🔥", layout="wide", initial_sidebar_state="expanded")
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
def load_data(tok):
    try:
        habits  = client.get("/api/habits",  token=tok) or []
        fitness = client.get("/api/fitness", token=tok) or []
    except Exception:
        habits = fitness = []
    return habits, fitness

habits, fitness = load_data(token)

page_header("Habits & Fitness", "Build consistency and track your physical activity")

# ── KPIs ──────────────────────────────────────────────────────────────────────
completed_habits = sum(1 for h in habits if h.get("completed"))
habit_rate       = (completed_habits / len(habits) * 100) if habits else 0
best_streak      = max((h.get("streak", 0) for h in habits), default=0)
total_cal        = sum(f.get("calories_burned", 0) for f in fitness)
total_dur        = sum(f.get("duration", 0) for f in fitness)

metric_row([
    dict(icon="🔥", label="Habits Total",     value=str(len(habits)),
         sub="Tracked",         accent="linear-gradient(90deg,#F59E0B,#D97706)"),
    dict(icon="✅", label="Completion Rate",  value=f"{habit_rate:.0f}%",
         sub="Habits done",     trend_up=habit_rate >= 60,
         accent="linear-gradient(90deg,#10B981,#059669)"),
    dict(icon="⚡", label="Best Streak",      value=str(best_streak),
         sub="Days",
         accent="linear-gradient(90deg,#EF4444,#DC2626)"),
    dict(icon="🏃", label="Fitness Sessions", value=str(len(fitness)),
         sub="Logged",
         accent="linear-gradient(90deg,#2563EB,#1D4ED8)"),
    dict(icon="🔥", label="Calories Burned",  value=f"{total_cal:,.0f}",
         sub=f"{total_dur:.0f} min total",   trend_up=total_cal > 0,
         accent="linear-gradient(90deg,#8B5CF6,#7C3AED)"),
])

st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
#  HABITS
# ══════════════════════════════════════════════════════════════════
section_header("🔥", "Habit Tracker", "Build consistent daily routines")

col_hadd, col_hlist = st.columns([1, 1.6], gap="large")

with col_hadd:
    st.markdown("<div style='font-size:.8rem;color:#64748B;margin-bottom:.75rem'>Log a new habit</div>",
                unsafe_allow_html=True)
    with st.form("habit_form"):
        habit_name     = st.text_input("Habit Name", placeholder="Morning workout, Reading…")
        target_freq    = st.text_input("Target Frequency", placeholder="daily, weekly, 3x/week")
        completed_chk  = st.checkbox("Completed today")
        submitted_h    = st.form_submit_button("Add Habit", use_container_width=True)

    if submitted_h:
        if not habit_name.strip() or not target_freq.strip():
            st.error("Habit name and frequency are required.")
        else:
            try:
                client.post(
                    "/api/habits",
                    payload={
                        "name":             habit_name.strip(),
                        "target_frequency": target_freq.strip(),
                        "completed":        completed_chk,
                        "streak":           1 if completed_chk else 0,
                    },
                    token=token,
                )
                st.success("Habit added.")
                st.cache_data.clear()
                st.rerun()
            except Exception:
                st.error("Failed to add habit.")

with col_hlist:
    if habits:
        for h in habits:
            streak    = h.get("streak", 0)
            done      = h.get("completed", False)
            dot_color = "#10B981" if done else "#EF4444"
            st.markdown(
                f"""
                <div style="
                    background:rgba(13,17,28,.8);border:1px solid rgba(37,99,235,.1);
                    border-radius:12px;padding:.85rem 1.1rem;margin-bottom:.4rem;
                    display:flex;justify-content:space-between;align-items:center
                ">
                    <div style="display:flex;align-items:center;gap:.75rem;flex:1;min-width:0">
                        <div style="width:10px;height:10px;border-radius:50%;
                                    background:{dot_color};flex-shrink:0"></div>
                        <div style="min-width:0">
                            <div style="font-size:.85rem;font-weight:600;color:#E2E8F0;
                                        white-space:nowrap;overflow:hidden;text-overflow:ellipsis">
                                {h.get('name','')}</div>
                            <div style="font-size:.72rem;color:#64748B;margin-top:.1rem">
                                {h.get('target_frequency','')}
                            </div>
                        </div>
                    </div>
                    <div style="text-align:right;flex-shrink:0;margin-left:1rem">
                        <div style="font-size:.9rem;font-weight:700;color:#F59E0B">🔥 {streak}</div>
                        <div style="font-size:.68rem;color:#64748B">streak</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        empty_state("🔥", "No habits yet", "Add your first habit above.")

st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
#  FITNESS
# ══════════════════════════════════════════════════════════════════
section_header("🏃", "Fitness Tracker", "Log workouts and monitor calories")

col_fadd, col_fchart = st.columns([1, 1.6], gap="large")

with col_fadd:
    st.markdown("<div style='font-size:.8rem;color:#64748B;margin-bottom:.75rem'>Log a workout</div>",
                unsafe_allow_html=True)
    with st.form("fitness_form"):
        activity_type = st.text_input("Activity Type", placeholder="Running, Cycling, Swimming…")
        act_date      = st.date_input("Date", value=datetime.today())
        duration      = st.number_input("Duration (minutes)", min_value=1.0, value=30.0, step=5.0)
        calories      = st.number_input("Calories Burned",    min_value=1.0, value=250.0, step=10.0)
        submitted_f   = st.form_submit_button("Log Activity", use_container_width=True)

    if submitted_f:
        if not activity_type.strip():
            st.error("Activity type is required.")
        else:
            try:
                client.post(
                    "/api/fitness",
                    payload={
                        "activity_type": activity_type.strip(),
                        "duration":      float(duration),
                        "calories_burned": float(calories),
                        "activity_date": datetime.combine(act_date, datetime.min.time()).isoformat(),
                    },
                    token=token,
                )
                st.success("Activity logged.")
                st.cache_data.clear()
                st.rerun()
            except Exception:
                st.error("Failed to log activity.")

with col_fchart:
    if fitness:
        sorted_f = sorted(fitness, key=lambda x: x.get("activity_date", ""))
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=[f["activity_date"][:10] for f in sorted_f],
            y=[f["calories_burned"] for f in sorted_f],
            name="Calories", marker_color="#EF4444", opacity=0.85,
        ))
        fig.add_trace(go.Scatter(
            x=[f["activity_date"][:10] for f in sorted_f],
            y=[f["duration"] for f in sorted_f],
            name="Duration (min)", mode="lines+markers",
            line=dict(color="#2563EB", width=2),
            marker=dict(size=5), yaxis="y2",
        ))
        fig.update_layout(
            **_PLOTLY_LAYOUT, height=260,
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#94A3B8")),
            yaxis2=dict(overlaying="y", side="right",
                        gridcolor="rgba(0,0,0,0)",
                        tickfont=dict(color="#64748B")),
        )
        st.plotly_chart(fig, use_container_width=True)

        # activity type breakdown
        type_totals: dict = {}
        for f in fitness:
            t = f.get("activity_type", "Other")
            type_totals[t] = type_totals.get(t, 0) + f.get("calories_burned", 0)
        section_header("📊", "Calories by Activity Type")
        fig2 = go.Figure(go.Bar(
            x=list(type_totals.keys()),
            y=list(type_totals.values()),
            marker_color="#7C3AED", opacity=0.85,
        ))
        fig2.update_layout(**_PLOTLY_LAYOUT, height=200)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        empty_state("🏃", "No fitness activities yet", "Log your first workout above.")
