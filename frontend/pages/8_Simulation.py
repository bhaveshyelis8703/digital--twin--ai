"""Digital Twin AI - Simulation Engine (Milestone 3)"""
import os, sys
from datetime import datetime
import plotly.graph_objects as go
import streamlit as st

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from components.theme import inject_theme
from components.ui import (
    bootstrap_session, empty_state, insight_card, metric_row,
    page_header, progress_bar, render_sidebar, require_auth, section_header,
)

st.set_page_config(
    page_title="Simulation - Digital Twin AI",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_theme()
bootstrap_session()
render_sidebar()
require_auth()

client = st.session_state.api_client
token  = st.session_state.token

_PL = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color="#94A3B8", size=12),
    margin=dict(l=0, r=0, t=30, b=0),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#94A3B8")),
    xaxis=dict(gridcolor="rgba(37,99,235,.08)", linecolor="rgba(37,99,235,.15)",
               tickfont=dict(color="#64748B")),
    yaxis=dict(gridcolor="rgba(37,99,235,.08)", linecolor="rgba(37,99,235,.15)",
               tickfont=dict(color="#64748B")),
)
_COLORS = ["#2563EB","#7C3AED","#10B981","#F59E0B","#EF4444","#06B6D4","#EC4899","#14B8A6"]


def _api(path, method="get", payload=None):
    try:
        if method == "get":
            return client.get(path, token=token)
        return client.post(path, payload=payload, token=token)
    except Exception as e:
        return {"error": str(e)}


def _render_result(result: dict):
    """Render a simulation result: KPIs + bar chart + recommendations."""
    if not result or "error" in result:
        st.error(result.get("error", "Simulation failed."))
        return

    conf = result.get("confidence_score", 0)
    st.markdown(
        '<div style="background:rgba(37,99,235,.08);border:1px solid rgba(37,99,235,.2);'
        'border-radius:12px;padding:.75rem 1.25rem;margin-bottom:1rem;display:flex;'
        'align-items:center;justify-content:space-between;">'
        f'<span style="color:#94A3B8;font-size:.8rem;">Simulation: '
        f'<b style="color:#E2E8F0;">{result.get("simulation_type","").replace("_"," ").title()}</b></span>'
        f'<span style="color:#10B981;font-size:.85rem;font-weight:700;">'
        f'Confidence: {conf*100:.0f}%</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    cur  = result.get("current_state", {})
    fut  = result.get("future_state",  {})
    diff = result.get("difference",    {})

    numeric_keys = [k for k in set(cur) | set(fut)
                    if isinstance(cur.get(k, fut.get(k)), (int, float))][:6]

    if numeric_keys:
        cols = st.columns(min(len(numeric_keys), 3))
        for i, k in enumerate(numeric_keys[:3]):
            c_val = cur.get(k, 0)
            f_val = fut.get(k, 0)
            d_val = diff.get(k, 0)
            with cols[i]:
                up = d_val >= 0
                label = k.replace("_", " ").title()
                if isinstance(f_val, float):
                    f_str = f"{f_val:,.2f}" if abs(f_val) < 1_000_000 else f"{f_val:,.0f}"
                else:
                    f_str = str(f_val)
                st.markdown(
                    f'<div style="background:rgba(13,17,28,.9);border:1px solid rgba(37,99,235,.15);'
                    f'border-radius:12px;padding:1rem;text-align:center;">'
                    f'<div style="font-size:.7rem;color:#64748B;text-transform:uppercase;'
                    f'letter-spacing:.08em;margin-bottom:.4rem;">{label}</div>'
                    f'<div style="font-size:1.5rem;font-weight:800;color:#F1F5F9;">{f_str}</div>'
                    f'<div style="font-size:.78rem;color:{"#10B981" if up else "#EF4444"};margin-top:.25rem;">'
                    f'{"+" if up else ""}{d_val:+,.2f} vs current</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        # Bar chart: current vs future for all numeric keys
        if len(numeric_keys) >= 2:
            st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)
            cur_vals = [float(cur.get(k, 0)) for k in numeric_keys]
            fut_vals = [float(fut.get(k, 0)) for k in numeric_keys]
            labels   = [k.replace("_"," ").title() for k in numeric_keys]
            fig = go.Figure()
            fig.add_trace(go.Bar(name="Current", x=labels, y=cur_vals,
                                 marker_color="#2563EB", opacity=0.85))
            fig.add_trace(go.Bar(name="Projected", x=labels, y=fut_vals,
                                 marker_color="#10B981", opacity=0.85))
            fig.update_layout(**_PL, height=260, barmode="group",
                              title="Current vs Projected")
            st.plotly_chart(fig, use_container_width=True)

    recs = result.get("recommendations", [])
    if recs:
        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
        section_header("💡", "Recommendations")
        for r in recs:
            insight_card("tip", r)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE HEADER + TWIN SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

page_header("Simulation Engine", "Run what-if scenarios across all life domains")

with st.spinner("Loading Digital Twin…"):
    summary = _api("/api/digital-twin/summary")

if summary and "error" not in summary:
    overall = summary.get("overall_score", 0)
    risk    = summary.get("risk_level", "medium")
    risk_color = {"low": "#10B981", "medium": "#F59E0B", "high": "#EF4444"}.get(risk, "#F59E0B")

    metric_row([
        dict(icon="🧬", label="Twin Alignment",  value=f"{overall:.0f}%",
             sub="Overall score", trend_up=overall >= 60,
             accent="linear-gradient(90deg,#2563EB,#7C3AED)"),
        dict(icon="📚", label="Study Score",     value=f"{summary.get('study_score',0):.0f}",
             sub="/ 100", trend_up=summary.get("study_score",0) >= 60,
             accent="linear-gradient(90deg,#7C3AED,#6D28D9)"),
        dict(icon="💰", label="Finance Score",   value=f"{summary.get('financial_score',0):.0f}",
             sub="/ 100", trend_up=summary.get("financial_score",0) >= 60,
             accent="linear-gradient(90deg,#06B6D4,#0284C7)"),
        dict(icon="🔥", label="Habits Score",    value=f"{summary.get('habits_score',0):.0f}",
             sub="/ 100", trend_up=summary.get("habits_score",0) >= 60,
             accent="linear-gradient(90deg,#F59E0B,#D97706)"),
        dict(icon="🏃", label="Fitness Score",   value=f"{summary.get('fitness_score',0):.0f}",
             sub="/ 100", trend_up=summary.get("fitness_score",0) >= 60,
             accent="linear-gradient(90deg,#10B981,#059669)"),
    ])

    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
    insight_card("warning" if risk == "high" else "tip",
                 f"Risk Level: **{risk.upper()}** — {summary.get('top_insight','')}",
                 "Digital Twin Analysis")
else:
    st.warning("Could not load Digital Twin summary. Make sure the backend is running.")

st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════════════════

tab_fin, tab_study, tab_hab, tab_fit, tab_cmp, tab_rec, tab_risk = st.tabs([
    "  💰 Financial  ",
    "  📚 Study  ",
    "  🔥 Habits  ",
    "  🏃 Fitness  ",
    "  🔀 Compare  ",
    "  💡 Recommendations  ",
    "  ⚠️ Risk  ",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — FINANCIAL SIMULATION
# ═══════════════════════════════════════════════════════════════════════════════

with tab_fin:
    section_header("💰", "Financial Simulation", "Model savings, purchases, investments and loans")

    fin_sub = st.radio(
        "Simulation Type",
        ["Savings Increase", "Major Purchase", "Expense Reduction",
         "Investment Growth", "Loan Impact"],
        horizontal=True, key="fin_sub",
    )
    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
    col_params, col_result = st.columns([1, 1.5], gap="large")

    with col_params:
        if fin_sub == "Savings Increase":
            section_header("💾", "Parameters")
            monthly_inc = st.slider("Extra Monthly Savings ($)", 50, 5000, 200, 50)
            horizon_m   = st.slider("Horizon (months)", 1, 60, 12)
            if st.button("Run Simulation", key="fin_sav", use_container_width=True):
                with st.spinner("Simulating…"):
                    r = _api("/api/simulation/financial", "post",
                             {"sim_type": "savings_increase",
                              "monthly_increase": monthly_inc,
                              "horizon_months": horizon_m})
                    st.session_state["fin_result"] = r

            # Savings projection chart
            months_range = list(range(1, horizon_m + 1))
            base = summary.get("financial_score", 0) * 100 if summary and "error" not in summary else 0
            proj = [base + monthly_inc * i for i in months_range]
            fig = go.Figure(go.Scatter(
                x=months_range, y=proj, mode="lines+markers", name="Projected Savings",
                line=dict(color="#10B981", width=2), fill="tozeroy",
                fillcolor="rgba(16,185,129,.07)",
            ))
            fig.update_layout(**_PL, height=200, title="Savings Projection")
            st.plotly_chart(fig, use_container_width=True)

        elif fin_sub == "Major Purchase":
            section_header("🛍️", "Parameters")
            purchase_amt = st.number_input("Purchase Amount ($)", 100.0, 1_000_000.0, 5000.0, 100.0)
            pur_month    = st.slider("Purchase in Month", 1, 24, 3)
            horizon_m    = st.slider("Horizon (months)", 1, 60, 12)
            if st.button("Run Simulation", key="fin_pur", use_container_width=True):
                with st.spinner("Simulating…"):
                    r = _api("/api/simulation/financial", "post",
                             {"sim_type": "major_purchase",
                              "purchase_amount": purchase_amt,
                              "purchase_month": pur_month,
                              "horizon_months": horizon_m})
                    st.session_state["fin_result"] = r

        elif fin_sub == "Expense Reduction":
            section_header("✂️", "Parameters")
            red_pct  = st.slider("Reduce Expenses By (%)", 1, 50, 10)
            horizon_m = st.slider("Horizon (months)", 1, 60, 12)
            if st.button("Run Simulation", key="fin_exp", use_container_width=True):
                with st.spinner("Simulating…"):
                    r = _api("/api/simulation/financial", "post",
                             {"sim_type": "expense_reduction",
                              "reduction_pct": red_pct,
                              "horizon_months": horizon_m})
                    st.session_state["fin_result"] = r

        elif fin_sub == "Investment Growth":
            section_header("📈", "Parameters")
            init_amt   = st.number_input("Initial Investment ($)", 100.0, 1_000_000.0, 10000.0, 500.0)
            monthly_ct = st.number_input("Monthly Contribution ($)", 0.0, 50000.0, 500.0, 50.0)
            ann_ret    = st.slider("Annual Return (%)", 1.0, 30.0, 8.0, 0.5)
            horizon_m  = st.slider("Horizon (months)", 12, 120, 36)
            if st.button("Run Simulation", key="fin_inv", use_container_width=True):
                with st.spinner("Simulating…"):
                    r = _api("/api/simulation/financial", "post",
                             {"sim_type": "investment_growth",
                              "initial_amount": init_amt,
                              "monthly_contribution": monthly_ct,
                              "annual_return_pct": ann_ret,
                              "horizon_months": horizon_m})
                    st.session_state["fin_result"] = r

            # Investment growth chart
            import math
            mr = ann_ret / 100 / 12
            months_range = list(range(1, horizon_m + 1))
            fv_vals = [
                init_amt * (1 + mr) ** m + (monthly_ct * (((1 + mr) ** m - 1) / mr) if mr > 0 else monthly_ct * m)
                for m in months_range
            ]
            fig2 = go.Figure(go.Scatter(
                x=months_range, y=fv_vals, mode="lines", name="Portfolio Value",
                line=dict(color="#2563EB", width=2), fill="tozeroy",
                fillcolor="rgba(37,99,235,.07)",
            ))
            fig2.update_layout(**_PL, height=200, title="Investment Growth Projection")
            st.plotly_chart(fig2, use_container_width=True)

        else:  # Loan Impact
            section_header("🏦", "Parameters")
            loan_amt  = st.number_input("Loan Amount ($)", 1000.0, 10_000_000.0, 50000.0, 1000.0)
            ann_int   = st.slider("Annual Interest Rate (%)", 1.0, 36.0, 10.0, 0.5)
            tenure    = st.slider("Tenure (months)", 6, 360, 60)
            if st.button("Run Simulation", key="fin_loan", use_container_width=True):
                with st.spinner("Simulating…"):
                    r = _api("/api/simulation/financial", "post",
                             {"sim_type": "loan_impact",
                              "loan_amount": loan_amt,
                              "annual_interest_pct": ann_int,
                              "tenure_months": tenure})
                    st.session_state["fin_result"] = r

            # EMI breakdown chart
            r_m = ann_int / 100 / 12
            emi = (loan_amt * r_m * (1 + r_m) ** tenure) / ((1 + r_m) ** tenure - 1) if r_m > 0 else loan_amt / tenure
            principal_share = [loan_amt / tenure] * tenure
            interest_share  = [emi - p for p in principal_share]
            fig3 = go.Figure()
            fig3.add_trace(go.Bar(name="Principal", x=list(range(1,tenure+1)),
                                  y=principal_share, marker_color="#2563EB", opacity=0.85))
            fig3.add_trace(go.Bar(name="Interest", x=list(range(1,tenure+1)),
                                  y=interest_share, marker_color="#EF4444", opacity=0.85))
            fig3.update_layout(**_PL, height=200, barmode="stack", title="EMI Breakdown")
            st.plotly_chart(fig3, use_container_width=True)

    with col_result:
        section_header("📊", "Simulation Result")
        if "fin_result" in st.session_state:
            _render_result(st.session_state["fin_result"])
        else:
            empty_state("💰", "Run a simulation", "Set parameters and click Run Simulation.")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — STUDY SIMULATION
# ═══════════════════════════════════════════════════════════════════════════════

with tab_study:
    section_header("📚", "Study Simulation", "Model performance improvements and exam preparation")
    stu_sub = st.radio(
        "Simulation Type",
        ["Extra Study Hours", "Exam Preparation", "Subject Improvement"],
        horizontal=True, key="stu_sub",
    )
    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
    cs1, cs2 = st.columns([1, 1.5], gap="large")

    with cs1:
        if stu_sub == "Extra Study Hours":
            section_header("⏱️", "Parameters")
            extra_h = st.slider("Extra Hours / Day", 0.5, 8.0, 1.0, 0.5)
            hw = st.slider("Horizon (weeks)", 1, 52, 8)
            if st.button("Run Simulation", key="stu_hrs", use_container_width=True):
                with st.spinner("Simulating…"):
                    r = _api("/api/simulation/study", "post",
                             {"sim_type": "extra_hours",
                              "extra_hours_per_day": extra_h,
                              "horizon_weeks": hw})
                    st.session_state["stu_result"] = r
            weeks = list(range(1, hw + 1))
            base_perf = summary.get("study_score", 50) if summary and "error" not in summary else 50
            proj_perf = [min(100, base_perf + extra_h * 0.4 * w) for w in weeks]
            fig = go.Figure(go.Scatter(x=weeks, y=proj_perf, mode="lines+markers",
                                       line=dict(color="#7C3AED", width=2),
                                       fill="tozeroy", fillcolor="rgba(124,58,237,.07)"))
            fig.update_layout(**_PL, height=200, title="Performance Projection",
                              xaxis_title="Weeks", yaxis_title="Performance Score")
            st.plotly_chart(fig, use_container_width=True)

        elif stu_sub == "Exam Preparation":
            section_header("🎓", "Parameters")
            subj     = st.text_input("Subject", value="Mathematics")
            days_ex  = st.slider("Days Until Exam", 7, 180, 30)
            tgt_sc   = st.slider("Target Score", 50, 100, 80)
            if st.button("Run Simulation", key="stu_exam", use_container_width=True):
                with st.spinner("Simulating…"):
                    r = _api("/api/simulation/study", "post",
                             {"sim_type": "exam_prep",
                              "subject": subj,
                              "days_until_exam": days_ex,
                              "target_score": tgt_sc})
                    st.session_state["stu_result"] = r

        else:  # Subject Improvement
            section_header("📖", "Parameters")
            subj2    = st.text_input("Subject", value="Python", key="subj2")
            tgt_prf  = st.slider("Target Performance", 50, 100, 80, key="tgt_prf")
            hw2      = st.slider("Horizon (weeks)", 1, 52, 8, key="hw2")
            if st.button("Run Simulation", key="stu_subj", use_container_width=True):
                with st.spinner("Simulating…"):
                    r = _api("/api/simulation/study", "post",
                             {"sim_type": "subject_improvement",
                              "subject": subj2,
                              "target_performance": tgt_prf,
                              "horizon_weeks": hw2})
                    st.session_state["stu_result"] = r

    with cs2:
        section_header("📊", "Simulation Result")
        if "stu_result" in st.session_state:
            _render_result(st.session_state["stu_result"])
        else:
            empty_state("📚", "Run a simulation", "Set parameters and click Run Simulation.")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — HABIT SIMULATION
# ═══════════════════════════════════════════════════════════════════════════════

with tab_hab:
    section_header("🔥", "Habit Simulation", "Model new habits, removals and focus improvements")
    hab_sub = st.radio(
        "Simulation Type",
        ["New Habit", "Remove Habit", "Productivity Change"],
        horizontal=True, key="hab_sub",
    )
    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
    ch1, ch2 = st.columns([1, 1.5], gap="large")

    with ch1:
        if hab_sub == "New Habit":
            section_header("➕", "Parameters")
            hname   = st.text_input("Habit Name", value="Morning Meditation")
            hfreq   = st.selectbox("Frequency", ["daily", "weekly", "3x weekly"])
            hhw     = st.slider("Horizon (weeks)", 1, 52, 8, key="hhw")
            if st.button("Run Simulation", key="hab_new", use_container_width=True):
                with st.spinner("Simulating…"):
                    r = _api("/api/simulation/habits", "post",
                             {"sim_type": "new_habit",
                              "habit_name": hname,
                              "target_frequency": hfreq,
                              "horizon_weeks": hhw})
                    st.session_state["hab_result"] = r
            weeks = list(range(1, hhw + 1))
            streak_proj = [min(w * 0.65 * 7, hhw * 7) for w in weeks]
            fig = go.Figure(go.Scatter(x=weeks, y=streak_proj, mode="lines+markers",
                                       line=dict(color="#F59E0B", width=2),
                                       fill="tozeroy", fillcolor="rgba(245,158,11,.07)"))
            fig.update_layout(**_PL, height=200, title="Projected Streak Growth")
            st.plotly_chart(fig, use_container_width=True)

        elif hab_sub == "Remove Habit":
            section_header("➖", "Parameters")
            hrname = st.text_input("Habit to Remove", value="Late Night Scrolling")
            hrhw   = st.slider("Horizon (weeks)", 1, 52, 4, key="hrhw")
            if st.button("Run Simulation", key="hab_rem", use_container_width=True):
                with st.spinner("Simulating…"):
                    r = _api("/api/simulation/habits", "post",
                             {"sim_type": "remove_habit",
                              "habit_name": hrname,
                              "horizon_weeks": hrhw})
                    st.session_state["hab_result"] = r

        else:  # Productivity Change
            section_header("🎯", "Parameters")
            focus_imp = st.slider("Focus Improvement (%)", -20, 100, 20, key="focus_imp")
            phw       = st.slider("Horizon (weeks)", 1, 52, 8, key="phw")
            if st.button("Run Simulation", key="hab_prod", use_container_width=True):
                with st.spinner("Simulating…"):
                    r = _api("/api/simulation/habits", "post",
                             {"sim_type": "productivity",
                              "focus_improvement_pct": focus_imp,
                              "horizon_weeks": phw})
                    st.session_state["hab_result"] = r

    with ch2:
        section_header("📊", "Simulation Result")
        if "hab_result" in st.session_state:
            _render_result(st.session_state["hab_result"])
        else:
            empty_state("🔥", "Run a simulation", "Set parameters and click Run Simulation.")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — FITNESS SIMULATION
# ═══════════════════════════════════════════════════════════════════════════════

with tab_fit:
    section_header("🏃", "Fitness Simulation", "Model workout plans, calorie burns and goal timelines")
    fit_sub = st.radio(
        "Simulation Type",
        ["Workout Plan", "Weight Loss", "Goal Completion"],
        horizontal=True, key="fit_sub",
    )
    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
    cf1, cf2 = st.columns([1, 1.5], gap="large")

    with cf1:
        if fit_sub == "Workout Plan":
            section_header("🏋️", "Parameters")
            spw     = st.slider("Sessions / Week", 1, 7, 3)
            dur_min = st.slider("Session Duration (min)", 20, 120, 45)
            act_type = st.selectbox("Activity", ["Running", "Cycling", "HIIT", "Yoga",
                                                  "Weight Training", "Swimming", "Mixed"])
            fhw     = st.slider("Horizon (weeks)", 1, 52, 8, key="fhw")
            if st.button("Run Simulation", key="fit_wkt", use_container_width=True):
                with st.spinner("Simulating…"):
                    r = _api("/api/simulation/fitness", "post",
                             {"sim_type": "workout_plan",
                              "sessions_per_week": spw,
                              "session_duration_minutes": float(dur_min),
                              "activity_type": act_type,
                              "horizon_weeks": fhw})
                    st.session_state["fit_result"] = r
            weeks  = list(range(1, fhw + 1))
            cal_pw = spw * dur_min * 7
            total_cal_proj = [cal_pw * w for w in weeks]
            fig = go.Figure(go.Bar(x=weeks, y=[cal_pw] * fhw,
                                   name="Weekly Burn", marker_color="#10B981", opacity=0.85))
            fig.add_trace(go.Scatter(x=weeks, y=total_cal_proj, mode="lines",
                                     name="Cumulative", line=dict(color="#F59E0B", width=2),
                                     yaxis="y2"))
            fig.update_layout(**_PL, height=220, title="Calorie Burn Projection",
                              yaxis2=dict(overlaying="y", side="right",
                                         showgrid=False, tickfont=dict(color="#F59E0B")))
            st.plotly_chart(fig, use_container_width=True)

        elif fit_sub == "Weight Loss":
            section_header("⚖️", "Parameters")
            twc  = st.slider("Target Weekly Calories Burned", 500, 5000, 1500, 100)
            wlhw = st.slider("Horizon (weeks)", 4, 52, 12, key="wlhw")
            if st.button("Run Simulation", key="fit_wl", use_container_width=True):
                with st.spinner("Simulating…"):
                    r = _api("/api/simulation/fitness", "post",
                             {"sim_type": "weight_loss",
                              "target_weekly_calories": float(twc),
                              "horizon_weeks": wlhw})
                    st.session_state["fit_result"] = r
            weeks = list(range(1, wlhw + 1))
            kg_loss_proj = [twc * w / 7700 for w in weeks]
            fig2 = go.Figure(go.Scatter(x=weeks, y=kg_loss_proj, mode="lines+markers",
                                        line=dict(color="#EF4444", width=2),
                                        fill="tozeroy", fillcolor="rgba(239,68,68,.07)"))
            fig2.update_layout(**_PL, height=220, title="Projected Weight Loss (kg)",
                               yaxis_title="kg")
            st.plotly_chart(fig2, use_container_width=True)

        else:  # Goal Completion
            section_header("🎯", "Parameters")
            gname = st.text_input("Goal Name", value="Run 5km")
            gchw  = st.slider("Horizon (weeks)", 1, 52, 8, key="gchw")
            if st.button("Run Simulation", key="fit_gc", use_container_width=True):
                with st.spinner("Simulating…"):
                    r = _api("/api/simulation/fitness", "post",
                             {"sim_type": "goal_completion",
                              "goal_name": gname,
                              "horizon_weeks": gchw})
                    st.session_state["fit_result"] = r

    with cf2:
        section_header("📊", "Simulation Result")
        if "fit_result" in st.session_state:
            _render_result(st.session_state["fit_result"])
        else:
            empty_state("🏃", "Run a simulation", "Set parameters and click Run Simulation.")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 — SCENARIO COMPARISON
# ═══════════════════════════════════════════════════════════════════════════════

with tab_cmp:
    section_header("🔀", "Scenario Comparison", "Compare two what-if paths head-to-head")
    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    cmp_col1, cmp_col2 = st.columns(2, gap="large")

    SIM_TYPES = {
        "Save More ($200/mo)":        ("financial.savings_increase",    {"monthly_increase": 200,  "horizon_months": 12}),
        "Cut Expenses 15%":           ("financial.expense_reduction",   {"reduction_pct": 15,      "horizon_months": 12}),
        "Invest $5000 @ 8%":          ("financial.investment_growth",   {"initial_amount": 5000,   "monthly_contribution": 200, "annual_return_pct": 8, "horizon_months": 24}),
        "Study 1h Extra / Day":       ("study.extra_hours",             {"extra_hours_per_day": 1, "horizon_weeks": 16}),
        "Study 2h Extra / Day":       ("study.extra_hours",             {"extra_hours_per_day": 2, "horizon_weeks": 16}),
        "Add Morning Habit":          ("habit.new_habit",               {"habit_name": "Morning Exercise", "horizon_weeks": 8}),
        "Boost Focus 20%":            ("habit.productivity",            {"focus_improvement_pct": 20, "horizon_weeks": 8}),
        "Workout 3x / Week":          ("fitness.workout_plan",          {"sessions_per_week": 3,   "session_duration_minutes": 45, "activity_type": "Mixed", "horizon_weeks": 8}),
        "Workout 5x / Week":          ("fitness.workout_plan",          {"sessions_per_week": 5,   "session_duration_minutes": 45, "activity_type": "Mixed", "horizon_weeks": 8}),
    }

    with cmp_col1:
        st.markdown('<div style="font-size:.8rem;font-weight:700;color:#60A5FA;'
                    'text-transform:uppercase;letter-spacing:.08em;margin-bottom:.5rem;">'
                    'Scenario A</div>', unsafe_allow_html=True)
        sc_a_name = st.selectbox("Choose Scenario A", list(SIM_TYPES.keys()), index=0, key="sc_a")
        st.caption(f"Type: `{SIM_TYPES[sc_a_name][0]}`")

    with cmp_col2:
        st.markdown('<div style="font-size:.8rem;font-weight:700;color:#A78BFA;'
                    'text-transform:uppercase;letter-spacing:.08em;margin-bottom:.5rem;">'
                    'Scenario B</div>', unsafe_allow_html=True)
        sc_b_name = st.selectbox("Choose Scenario B", list(SIM_TYPES.keys()), index=3, key="sc_b")
        st.caption(f"Type: `{SIM_TYPES[sc_b_name][0]}`")

    cmp_horizon = st.slider("Comparison Horizon (months)", 3, 24, 12, key="cmp_hor")

    if st.button("Compare Scenarios", use_container_width=True, key="cmp_run"):
        a_type, a_params = SIM_TYPES[sc_a_name]
        b_type, b_params = SIM_TYPES[sc_b_name]
        payload = {
            "scenario_a": {"name": sc_a_name, "sim_type": a_type,
                           "description": sc_a_name, "parameters": a_params},
            "scenario_b": {"name": sc_b_name, "sim_type": b_type,
                           "description": sc_b_name, "parameters": b_params},
            "horizon_months": cmp_horizon,
            "domains": ["financial", "study", "habits", "fitness"],
        }
        with st.spinner("Comparing scenarios…"):
            cmp_r = _api("/api/scenarios/compare", "post", payload)
            st.session_state["cmp_result"] = cmp_r

    if "cmp_result" in st.session_state:
        cr = st.session_state["cmp_result"]
        if "error" in cr:
            st.error(cr["error"])
        else:
            winner = cr.get("overall_winner", "tie")
            winner_name = cr.get("scenario_a_name") if winner == "A" else (
                cr.get("scenario_b_name") if winner == "B" else "Tie")
            st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)
            insight_card(
                "success" if winner != "tie" else "info",
                f"Overall Winner: **{winner_name}** — {cr.get('recommendation','')}",
                f"Confidence: {cr.get('confidence',0)*100:.0f}%",
            )
            st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

            impacts = cr.get("domain_impacts", [])
            if impacts:
                domains  = [i["domain"].title() for i in impacts]
                scores_a = [i["scenario_a_score"] for i in impacts]
                scores_b = [i["scenario_b_score"] for i in impacts]
                fig = go.Figure()
                fig.add_trace(go.Bar(name=cr.get("scenario_a_name","A"),
                                     x=domains, y=scores_a,
                                     marker_color="#2563EB", opacity=0.85))
                fig.add_trace(go.Bar(name=cr.get("scenario_b_name","B"),
                                     x=domains, y=scores_b,
                                     marker_color="#7C3AED", opacity=0.85))
                fig.update_layout(**_PL, height=280, barmode="group",
                                  title="Domain Impact Comparison")
                st.plotly_chart(fig, use_container_width=True)

                # radar chart
                fig_r = go.Figure(go.Scatterpolar(
                    r=scores_a + [scores_a[0]], theta=domains + [domains[0]],
                    fill="toself", name=cr.get("scenario_a_name","A"),
                    line=dict(color="#2563EB"),
                ))
                fig_r.add_trace(go.Scatterpolar(
                    r=scores_b + [scores_b[0]], theta=domains + [domains[0]],
                    fill="toself", name=cr.get("scenario_b_name","B"),
                    line=dict(color="#7C3AED"),
                ))
                fig_r.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    polar=dict(bgcolor="rgba(13,17,28,.8)",
                               radialaxis=dict(visible=True, color="#64748B"),
                               angularaxis=dict(color="#64748B")),
                    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#94A3B8")),
                    height=300, title="Radar: Domain Coverage",
                    font=dict(family="Inter", color="#94A3B8"),
                )
                st.plotly_chart(fig_r, use_container_width=True)

                # risk comparison
                ra = cr.get("scenario_a_risk", 0)
                rb = cr.get("scenario_b_risk", 0)
                rc1, rc2 = st.columns(2)
                with rc1:
                    st.markdown(
                        f'<div style="background:rgba(13,17,28,.9);border:1px solid rgba(37,99,235,.15);'
                        f'border-radius:12px;padding:1rem;text-align:center;">'
                        f'<div style="font-size:.7rem;color:#64748B;text-transform:uppercase;">Risk Score A</div>'
                        f'<div style="font-size:2rem;font-weight:800;color:{"#10B981" if ra<30 else "#F59E0B" if ra<60 else "#EF4444"};">{ra:.0f}</div>'
                        f'<div style="font-size:.75rem;color:#64748B;">{"Low" if ra<30 else "Medium" if ra<60 else "High"} risk</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                with rc2:
                    st.markdown(
                        f'<div style="background:rgba(13,17,28,.9);border:1px solid rgba(37,99,235,.15);'
                        f'border-radius:12px;padding:1rem;text-align:center;">'
                        f'<div style="font-size:.7rem;color:#64748B;text-transform:uppercase;">Risk Score B</div>'
                        f'<div style="font-size:2rem;font-weight:800;color:{"#10B981" if rb<30 else "#F59E0B" if rb<60 else "#EF4444"};">{rb:.0f}</div>'
                        f'<div style="font-size:.75rem;color:#64748B;">{"Low" if rb<30 else "Medium" if rb<60 else "High"} risk</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
    else:
        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
        with st.spinner("Loading best path recommendation…"):
            best = _api("/api/scenarios/best-path")
        if best and "error" not in best:
            section_header("🏆", "Recommended Best Path")
            insight_card("prediction",
                         f"**{best.get('recommended_path','')}** — {best.get('path_description','')}",
                         f"Expected gain: +{best.get('expected_score_gain',0):.1f} pts over "
                         f"{best.get('horizon_months',6)} months")
            for action in best.get("top_actions", [])[:3]:
                insight_card("tip", action)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 6 — RECOMMENDATIONS
# ═══════════════════════════════════════════════════════════════════════════════

with tab_rec:
    section_header("💡", "AI Recommendations", "Prioritised action plan derived from your real data")

    if st.button("Generate Recommendations", use_container_width=True, key="gen_recs"):
        with st.spinner("Generating AI recommendations…"):
            rec_data = _api("/api/digital-twin/recommendations", "post", {})
            st.session_state["rec_data"] = rec_data
    elif "rec_data" not in st.session_state:
        with st.spinner("Loading recommendations…"):
            st.session_state["rec_data"] = _api("/api/digital-twin/recommendations", "post", {})

    rd = st.session_state.get("rec_data", {})
    if rd and "error" not in rd:
        health_score = rd.get("overall_health_score", 0)
        st.markdown(
            f'<div style="background:rgba(37,99,235,.08);border:1px solid rgba(37,99,235,.2);'
            f'border-radius:12px;padding:.75rem 1.5rem;margin-bottom:1rem;'
            f'display:flex;align-items:center;justify-content:space-between;">'
            f'<span style="color:#94A3B8;">Overall Health Score</span>'
            f'<span style="font-size:1.5rem;font-weight:800;color:#60A5FA;">'
            f'{health_score:.0f} / 100</span></div>',
            unsafe_allow_html=True,
        )

        recs = rd.get("recommendations", [])
        if recs:
            # Domain filter
            domains = list({r["domain"] for r in recs})
            sel_dom = st.multiselect("Filter by domain", domains, default=domains, key="rec_dom")
            filtered_recs = [r for r in recs if r["domain"] in sel_dom]

            for rec in filtered_recs:
                pri_color = {"high": "#EF4444", "medium": "#F59E0B", "low": "#10B981"}.get(
                    rec.get("priority", "low"), "#64748B")
                imp_color = {"high": "#EF4444", "medium": "#F59E0B", "low": "#10B981"}.get(
                    rec.get("impact", "low"), "#64748B")
                conf_pct = rec.get("confidence", 0.5) * 100

                st.markdown(
                    '<div style="background:rgba(13,17,28,.9);border:1px solid rgba(37,99,235,.12);'
                    'border-radius:14px;padding:1.25rem 1.5rem;margin-bottom:.75rem;">'
                    '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.5rem;">'
                    f'<div style="font-size:1rem;font-weight:700;color:#F1F5F9;">{rec.get("title","")}</div>'
                    '<div style="display:flex;gap:.5rem;flex-shrink:0;">'
                    f'<span style="background:rgba(37,99,235,.1);border:1px solid rgba(37,99,235,.2);'
                    f'border-radius:99px;padding:2px 8px;font-size:.68rem;font-weight:700;'
                    f'color:#64748B;text-transform:uppercase;">{rec.get("domain","").upper()}</span>'
                    f'<span style="background:rgba(0,0,0,.2);border-radius:99px;padding:2px 8px;'
                    f'font-size:.68rem;font-weight:700;color:{pri_color};">'
                    f'P: {rec.get("priority","").upper()}</span>'
                    f'<span style="background:rgba(0,0,0,.2);border-radius:99px;padding:2px 8px;'
                    f'font-size:.68rem;font-weight:700;color:{imp_color};">'
                    f'I: {rec.get("impact","").upper()}</span>'
                    '</div></div>'
                    f'<div style="font-size:.85rem;color:#CBD5E1;margin-bottom:.75rem;">{rec.get("description","")}</div>',
                    unsafe_allow_html=True,
                )

                steps = rec.get("action_steps", [])
                if steps:
                    for i, step in enumerate(steps, 1):
                        st.markdown(
                            f'<div style="display:flex;gap:.5rem;margin-bottom:.25rem;">'
                            f'<span style="color:#2563EB;font-weight:700;font-size:.8rem;'
                            f'flex-shrink:0;">{i}.</span>'
                            f'<span style="font-size:.8rem;color:#94A3B8;">{step}</span></div>',
                            unsafe_allow_html=True,
                        )

                progress_bar(f"Confidence", conf_pct, 100,
                             f"linear-gradient(90deg,{pri_color},{pri_color}88)")
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            empty_state("💡", "No recommendations yet", "Add data across domains to unlock AI insights.")
    else:
        empty_state("💡", "Loading…", "Generating recommendations from your data.")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 7 — RISK ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

with tab_risk:
    section_header("⚠️", "Risk Analysis", "Current risk exposure across all life domains")

    if st.button("Refresh Risk Analysis", use_container_width=True, key="risk_refresh"):
        with st.spinner("Analysing risks…"):
            st.session_state["risk_data"] = _api("/api/digital-twin/risk")
    elif "risk_data" not in st.session_state:
        with st.spinner("Loading risk analysis…"):
            st.session_state["risk_data"] = _api("/api/digital-twin/risk")

    risk_d = st.session_state.get("risk_data", {})

    if risk_d and "error" not in risk_d:
        ors = risk_d.get("overall_risk_score", 0)
        rl  = risk_d.get("risk_level", "medium")
        safe = risk_d.get("safe_to_proceed", True)

        rl_color = {"low": "#10B981", "medium": "#F59E0B", "high": "#EF4444"}.get(rl, "#F59E0B")

        rc1, rc2, rc3 = st.columns(3)
        with rc1:
            st.markdown(
                f'<div style="background:rgba(13,17,28,.9);border:1px solid rgba(37,99,235,.15);'
                f'border-radius:12px;padding:1.25rem;text-align:center;">'
                f'<div style="font-size:.7rem;color:#64748B;text-transform:uppercase;letter-spacing:.08em;">Overall Risk</div>'
                f'<div style="font-size:2.5rem;font-weight:800;color:{rl_color};">{ors:.0f}</div>'
                f'<div style="font-size:.8rem;color:{rl_color};font-weight:600;">'
                f'{rl.upper()} RISK</div></div>',
                unsafe_allow_html=True,
            )
        with rc2:
            st.markdown(
                f'<div style="background:rgba(13,17,28,.9);border:1px solid rgba(37,99,235,.15);'
                f'border-radius:12px;padding:1.25rem;text-align:center;">'
                f'<div style="font-size:.7rem;color:#64748B;text-transform:uppercase;letter-spacing:.08em;">Safe to Proceed</div>'
                f'<div style="font-size:2.5rem;font-weight:800;color:{"#10B981" if safe else "#EF4444"};">{"✓" if safe else "✗"}</div>'
                f'<div style="font-size:.8rem;color:{"#10B981" if safe else "#EF4444"};font-weight:600;">'
                f'{"PROCEED" if safe else "REVIEW FIRST"}</div></div>',
                unsafe_allow_html=True,
            )
        with rc3:
            factors = risk_d.get("risk_factors", [])
            high_count = sum(1 for f in factors if f.get("severity") in ("high","critical"))
            st.markdown(
                f'<div style="background:rgba(13,17,28,.9);border:1px solid rgba(37,99,235,.15);'
                f'border-radius:12px;padding:1.25rem;text-align:center;">'
                f'<div style="font-size:.7rem;color:#64748B;text-transform:uppercase;letter-spacing:.08em;">High Risk Factors</div>'
                f'<div style="font-size:2.5rem;font-weight:800;color:{"#EF4444" if high_count>0 else "#10B981"};">{high_count}</div>'
                f'<div style="font-size:.8rem;color:#64748B;">of {len(factors)} total</div></div>',
                unsafe_allow_html=True,
            )

        # Risk heatmap by domain
        if factors:
            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
            section_header("🗺️", "Risk Heatmap")
            dom_risk = {}
            for f in factors:
                sev = {"low": 25, "medium": 50, "high": 75, "critical": 100}.get(f.get("severity","low"), 25)
                dom = f.get("domain","unknown")
                dom_risk[dom] = max(dom_risk.get(dom, 0), sev)
            all_domains = ["financial", "study", "habits", "fitness", "goals"]
            risk_vals   = [dom_risk.get(d, 5) for d in all_domains]
            risk_colors = ["#10B981" if v < 30 else "#F59E0B" if v < 60 else "#EF4444" for v in risk_vals]
            fig_h = go.Figure(go.Bar(
                x=all_domains, y=risk_vals,
                marker_color=risk_colors, opacity=0.85,
                text=[f"{v}" for v in risk_vals],
                textposition="outside", textfont=dict(color="#94A3B8", size=11),
            ))
            fig_h.update_layout(**_PL, height=260, yaxis=dict(**_PL["yaxis"], range=[0, 110]),
                                title="Risk Score by Domain (0=safe, 100=critical)")
            st.plotly_chart(fig_h, use_container_width=True)

            # Risk factor cards
            st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
            section_header("🔍", "Risk Factor Details")
            for f in factors:
                sev = f.get("severity", "low")
                sev_color = {"low":"#10B981","medium":"#F59E0B","high":"#EF4444","critical":"#EF4444"}.get(sev,"#64748B")
                card_type = "warning" if sev in ("medium","high") else ("success" if sev == "low" else "warning")
                insight_card(
                    card_type,
                    f"**[{f.get('domain','').upper()} / {sev.upper()}]** {f.get('description','')} "
                    f"— *Mitigation: {f.get('mitigation','')}*",
                    f"Probability: {f.get('probability',0)*100:.0f}%",
                )
    else:
        empty_state("⚠️", "Loading risk analysis…", "Analysing your data.")
