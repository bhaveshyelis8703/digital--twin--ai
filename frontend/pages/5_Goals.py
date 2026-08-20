"""
Digital Twin AI — Goals
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
    badge, insight_card,
)

st.set_page_config(page_title="Goals · Digital Twin AI", page_icon="🎯", layout="wide", initial_sidebar_state="expanded")
inject_theme()
bootstrap_session()
render_sidebar()
require_auth()

client = st.session_state.api_client
token  = st.session_state.token

_PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color="#94A3B8", size=12),
    margin=dict(l=0, r=0, t=10, b=0),
    xaxis=dict(gridcolor="rgba(37,99,235,.08)", linecolor="rgba(37,99,235,.15)", tickfont=dict(color="#64748B")),
    yaxis=dict(gridcolor="rgba(37,99,235,.08)", linecolor="rgba(37,99,235,.15)", tickfont=dict(color="#64748B")),
)

STATUSES = ["In Progress", "Not Started", "Completed", "On Hold"]

@st.cache_data(ttl=30, show_spinner=False)
def load_goals(tok):
    try:
        return client.get("/api/goals", token=tok) or []
    except Exception:
        return []

goals = load_goals(token)

page_header("Goals", "Define, track, and achieve your personal targets")

# ── KPIs ──────────────────────────────────────────────────────────────────────
completed_g  = [g for g in goals if g.get("status","").lower() == "completed"]
active_g     = [g for g in goals if g.get("status","").lower() not in ("completed","on hold")]
avg_pct      = (
    sum(min(g["current_value"]/g["target_value"]*100,100)
        for g in goals if g.get("target_value",0)>0)
    / len(goals) if goals else 0
)

metric_row([
    dict(icon="🎯", label="Total Goals",    value=str(len(goals)),
         sub="Defined",          accent="linear-gradient(90deg,#2563EB,#1D4ED8)"),
    dict(icon="⚡", label="Active",         value=str(len(active_g)),
         sub="In progress",      trend_up=len(active_g) > 0,
         accent="linear-gradient(90deg,#F59E0B,#D97706)"),
    dict(icon="✅", label="Completed",      value=str(len(completed_g)),
         sub="Achieved",         trend_up=len(completed_g) > 0,
         accent="linear-gradient(90deg,#10B981,#059669)"),
    dict(icon="📊", label="Avg Progress",   value=f"{avg_pct:.0f}%",
         sub="Overall",          trend_up=avg_pct >= 50,
         accent="linear-gradient(90deg,#8B5CF6,#7C3AED)"),
])

st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

# ── GOAL CARDS + PROGRESS ─────────────────────────────────────────────────────
if goals:
    section_header("📊", "Goal Progress", "Your current targets at a glance")

    _STATUS_COLOR = {
        "completed":   "#10B981",
        "in progress": "#2563EB",
        "not started": "#F59E0B",
        "on hold":     "#8B5CF6",
    }

    cols = st.columns(2, gap="large")
    for i, g in enumerate(sorted(goals, key=lambda x: x.get("target_date",""))):
        pct    = min(g["current_value"]/g["target_value"]*100, 100) if g.get("target_value",0) > 0 else 0
        status = g.get("status","")
        color  = _STATUS_COLOR.get(status.lower(), "#2563EB")
        days_left = ""
        try:
            td = datetime.fromisoformat(g["target_date"][:10])
            delta = (td - datetime.today()).days
            days_left = f"{delta} days left" if delta > 0 else "Deadline passed"
        except Exception:
            pass

        with cols[i % 2]:
            st.markdown(
                f"""
                <div style="
                    background:linear-gradient(135deg,rgba(13,17,28,.98),rgba(15,20,35,.98));
                    border:1px solid rgba(37,99,235,.15);border-radius:16px;
                    padding:1.25rem 1.5rem;margin-bottom:.75rem;position:relative;overflow:hidden
                ">
                    <div style="
                        position:absolute;top:0;left:0;right:0;height:3px;
                        background:linear-gradient(90deg,{color},{color}55)
                    "></div>
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:.75rem">
                        <div style="flex:1;min-width:0">
                            <div style="font-size:.95rem;font-weight:700;color:#F1F5F9;
                                        white-space:nowrap;overflow:hidden;text-overflow:ellipsis">
                                {g.get('name','')}</div>
                            <div style="font-size:.75rem;color:#64748B;margin-top:.2rem">
                                {g.get('description','')[:60]}{'…' if len(g.get('description',''))>60 else ''}</div>
                        </div>
                        <div style="margin-left:1rem;flex-shrink:0">{badge(status)}</div>
                    </div>
                    <div style="margin-bottom:.6rem">
                        <div style="display:flex;justify-content:space-between;
                                    font-size:.72rem;color:#64748B;margin-bottom:.3rem">
                            <span>{g.get('current_value',0):,.0f} / {g.get('target_value',0):,.0f}</span>
                            <span style="font-weight:600;color:{color}">{pct:.0f}%</span>
                        </div>
                        <div style="height:6px;background:rgba(30,41,59,.8);border-radius:99px;overflow:hidden">
                            <div style="height:100%;width:{pct:.1f}%;
                                        background:linear-gradient(90deg,{color},{color}88);
                                        border-radius:99px;transition:width .6s ease"></div>
                        </div>
                    </div>
                    <div style="font-size:.72rem;color:#475569">{days_left}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # overview bar chart
    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
    section_header("📈", "Progress Overview")
    fig = go.Figure(go.Bar(
        x=[g.get("name","")[:20] for g in goals],
        y=[min(g["current_value"]/g["target_value"]*100,100) if g.get("target_value",0)>0 else 0 for g in goals],
        marker=dict(
            color=[
                "#10B981" if g.get("status","").lower()=="completed" else
                "#2563EB" if g.get("status","").lower()=="in progress" else
                "#F59E0B" for g in goals
            ],
            opacity=0.85,
        ),
        text=[f"{min(g['current_value']/g['target_value']*100,100):.0f}%"
              if g.get("target_value",0)>0 else "0%" for g in goals],
        textposition="outside",
        textfont=dict(color="#94A3B8", size=11),
    ))
    fig.update_layout(**_PLOTLY_LAYOUT, height=220,
                      yaxis=dict(**_PLOTLY_LAYOUT["yaxis"], range=[0, 115]))
    st.plotly_chart(fig, use_container_width=True)

else:
    empty_state("🎯", "No goals yet", "Add your first goal to start tracking progress.")

st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

# ── ADD / UPDATE ──────────────────────────────────────────────────────────────
col_add, col_update = st.columns(2, gap="large")

with col_add:
    section_header("➕", "Add Goal")
    with st.form("goal_form"):
        g_name   = st.text_input("Goal Name",   placeholder="Learn Machine Learning, Save $5000…")
        g_desc   = st.text_input("Description", placeholder="Short description of what you want to achieve")
        g_target = st.number_input("Target Value",  min_value=0.01, value=100.0)
        g_curr   = st.number_input("Current Value", min_value=0.0,  value=0.0)
        g_date   = st.date_input("Target Date", value=datetime.today())
        g_status = st.selectbox("Status", STATUSES)
        add_sub  = st.form_submit_button("Add Goal", use_container_width=True)

    if add_sub:
        errors = []
        if not g_name.strip(): errors.append("Name is required.")
        if not g_desc.strip(): errors.append("Description is required.")
        if errors:
            for e in errors: st.error(e)
        else:
            try:
                client.post(
                    "/api/goals",
                    payload={
                        "name":          g_name.strip(),
                        "description":   g_desc.strip(),
                        "target_value":  float(g_target),
                        "current_value": float(g_curr),
                        "target_date":   datetime.combine(g_date, datetime.min.time()).isoformat(),
                        "status":        g_status,
                    },
                    token=token,
                )
                st.success("Goal added.")
                st.cache_data.clear()
                st.rerun()
            except Exception:
                st.error("Failed to add goal.")

with col_update:
    section_header("✏️", "Update Progress")
    if goals:
        goal_map = {g["name"]: g for g in goals}
        sel_name = st.selectbox("Select Goal", list(goal_map.keys()))
        sel      = goal_map[sel_name]
        with st.form("update_goal_form"):
            new_val = st.number_input(
                "Current Value",
                min_value=0.0, max_value=float(sel["target_value"]),
                value=float(sel["current_value"]),
            )
            new_status = st.selectbox(
                "Status", STATUSES,
                index=STATUSES.index(sel["status"]) if sel["status"] in STATUSES else 0,
            )
            upd_sub = st.form_submit_button("Update Goal", use_container_width=True)

        if upd_sub:
            try:
                client.put(
                    f"/api/goals/{sel['id']}",
                    payload={"current_value": float(new_val), "status": new_status},
                    token=token,
                )
                st.success("Goal updated.")
                st.cache_data.clear()
                st.rerun()
            except Exception:
                st.error("Failed to update goal.")
    else:
        empty_state("✏️", "No goals to update", "Add a goal first.")
