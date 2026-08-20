"""
Digital Twin AI - Forecasting & Predictive Analytics (Milestone 2)
"""
import os, sys
from datetime import datetime, timedelta

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
    page_title="Forecasting - Digital Twin AI",
    page_icon="🔮",
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


def _api(path, method="get", payload=None, params=None):
    """API call — returns dict. On error returns {"error": msg, "status_code": N}."""
    try:
        if method == "get":
            url = path
            if params:
                url += "?" + "&".join(f"{k}={v}" for k, v in params.items())
            return client.get(url, token=token)
        return client.post(path, payload=payload, token=token)
    except Exception as exc:
        # Try to extract HTTP status and detail from the response
        msg = str(exc)
        try:
            body = exc.response.json()  # type: ignore[attr-defined]
            detail = body.get("detail", msg)
            code   = exc.response.status_code  # type: ignore[attr-defined]
            return {"error": detail, "status_code": code}
        except Exception:
            return {"error": msg}


def _show_error(data: dict, context: str = "") -> None:
    """Render a visible error card when an API call fails."""
    err = data.get("error", "Unknown error")
    code = data.get("status_code", "")
    code_str = f" (HTTP {code})" if code else ""
    st.markdown(
        '<div style="background:rgba(239,68,68,.08);border:1px solid rgba(239,68,68,.3);'
        'border-radius:12px;padding:1rem 1.25rem;margin:.5rem 0;">'
        '<div style="font-size:.75rem;font-weight:700;color:#EF4444;text-transform:uppercase;'
        f'letter-spacing:.08em;margin-bottom:.3rem;">API Error{code_str}</div>'
        f'<div style="font-size:.85rem;color:#FCA5A5;">{err}</div>'
        + (f'<div style="font-size:.72rem;color:#64748B;margin-top:.3rem;">{context}</div>' if context else "")
        + '</div>',
        unsafe_allow_html=True,
    )


page_header("Forecasting & Predictions",
            "AI-powered forecasts from your real data")

# ── model status banner ───────────────────────────────────────────────────────
with st.expander("ℹ️  Model Status — click to expand", expanded=False):
    st.markdown(
        '<div style="font-size:.85rem;color:#94A3B8;line-height:1.7;">'
        '<b style="color:#60A5FA;">How forecasting works</b><br>'
        '1. <b>User-specific models</b> give the best accuracy — run '
        '<code>python train_user_models.py --user-id YOUR_ID</code> once to train them.<br>'
        '2. If no user model exists, the <b>global model</b> (trained on 500 synthetic users) '
        'is used as a fallback.<br>'
        '3. If neither exists, a <b>deterministic linear-trend estimate</b> is shown — '
        'still useful but less accurate.<br>'
        'All three modes return real data and are shown with a confidence band.'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:.25rem'></div>", unsafe_allow_html=True)

st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

tab_fin, tab_cashflow, tab_study, tab_habit = st.tabs([
    "  💰 Financial  ",
    "  💵 Cash Flow  ",
    "  📚 Study  ",
    "  🔥 Habits  ",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — FINANCIAL FORECASTING
# ══════════════════════════════════════════════════════════════════════════════
with tab_fin:
    section_header("💰", "Financial Forecasting", "Prophet · XGBoost · ARIMA")

    period_map = {"6 Months": 6, "1 Year": 12, "3 Years": 36}
    sel_period = st.radio("Forecast Period", list(period_map.keys()),
                          horizontal=True, key="fin_period")
    months = period_map[sel_period]

    with st.spinner("Running AI savings forecast…"):
        savings_data = _api("/api/forecasting/savings", params={"months": months})

    forecast = savings_data.get("forecast", [])

    if "error" in savings_data:
        _show_error(savings_data, "GET /api/forecasting/savings")
    elif not forecast:
        empty_state("💰", "No financial data yet",
                    "Add income and expense records to generate AI forecasts.")
    else:
        dates = [f["date"] for f in forecast]
        pred  = [f["predicted_savings"] for f in forecast]
        lower = [f["lower_bound"] for f in forecast]
        upper = [f["upper_bound"] for f in forecast]

        total_pred = sum(pred)
        final_pred = pred[-1] if pred else 0
        first_pred = pred[0]  if pred else 0
        growth_pct = ((final_pred - first_pred) / abs(first_pred) * 100
                      if first_pred != 0 else 0)

        metric_row([
            dict(icon="💰", label="Projected Total Savings",
                 value=f"${total_pred:,.0f}",
                 sub=f"Over {months} months",
                 accent="linear-gradient(90deg,#10B981,#059669)"),
            dict(icon="📈", label="End-Period Savings",
                 value=f"${final_pred:,.0f}",
                 sub="Projected",
                 trend=f"{growth_pct:+.1f}% growth",
                 trend_up=growth_pct >= 0,
                 accent="linear-gradient(90deg,#2563EB,#1D4ED8)"),
            dict(icon="📅", label="Monthly Average",
                 value=f"${total_pred/max(months,1):,.0f}",
                 sub="Per month",
                 accent="linear-gradient(90deg,#8B5CF6,#7C3AED)"),
        ])

        st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)
        section_header("📈", "Savings Projection with Confidence Band")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates + dates[::-1], y=upper + lower[::-1],
            fill="toself", fillcolor="rgba(37,99,235,.08)",
            line=dict(color="rgba(0,0,0,0)"), name="80% Confidence Band",
            showlegend=True,
        ))
        fig.add_trace(go.Scatter(
            x=dates, y=pred, mode="lines+markers",
            line=dict(color="#2563EB", width=2.5),
            marker=dict(size=5, color="#2563EB"),
            name="Projected Savings",
        ))
        fig.update_layout(**_PL, height=320)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    col_exp, col_sim = st.columns(2, gap="large")

    with col_exp:
        section_header("🛒", "Expense Forecast by Category")
        categories = ["Food", "Transport", "Housing", "Entertainment",
                      "Healthcare", "Education", "Shopping", "Utilities", "Fitness"]
        cat = st.selectbox("Category", categories, key="exp_cat")

        with st.spinner("Forecasting expenses…"):
            exp_data = _api("/api/forecasting/expenses",
                            params={"category": cat, "months": 6})
        exp_fc = exp_data.get("forecast", [])

        if "error" in exp_data:
            _show_error(exp_data, "GET /api/forecasting/expenses")
        elif not exp_fc:
            empty_state("🛒", "No expense data", "Add expense records first.")
        else:
            fig2 = go.Figure(go.Bar(
                x=[e["date"] for e in exp_fc],
                y=[e["predicted_expense"] for e in exp_fc],
                marker_color="#F59E0B", opacity=0.85,
                text=[f"${e['predicted_expense']:,.0f}" for e in exp_fc],
                textposition="outside",
                textfont=dict(color="#94A3B8", size=10),
            ))
            fig2.update_layout(**_PL, height=260,
                               yaxis=dict(**_PL["yaxis"], range=[0, max(e["predicted_expense"] for e in exp_fc) * 1.25]))
            st.plotly_chart(fig2, use_container_width=True)

    with col_sim:
        section_header("🎛️", "Savings Rate What-If")
        st.markdown(
            '<div style="font-size:.8rem;color:#64748B;margin-bottom:.5rem;">'
            'What if I save X% more per month?</div>',
            unsafe_allow_html=True,
        )
        rate = st.slider("Extra savings rate", 0.0, 0.5, 0.05, 0.01,
                         format="%.0f%%", key="sim_rate")

        with st.spinner("Running scenario…"):
            sim_data = _api("/api/forecasting/scenario", method="post",
                            payload={"savings_rate_change": rate, "months": 12})

        if "error" in sim_data:
            _show_error(sim_data, "POST /api/forecasting/scenario")
        elif "monthly_projection" in sim_data:
            proj = sim_data["monthly_projection"]
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(
                x=[p["date"] for p in proj],
                y=[p["base_savings"] for p in proj],
                mode="lines", name="Base trajectory",
                line=dict(color="#64748B", width=1.5, dash="dot"),
            ))
            fig3.add_trace(go.Scatter(
                x=[p["date"] for p in proj],
                y=[p["adjusted_savings"] for p in proj],
                mode="lines+markers", name="With extra savings",
                line=dict(color="#10B981", width=2),
                marker=dict(size=4),
                fill="tonexty", fillcolor="rgba(16,185,129,.07)",
            ))
            fig3.update_layout(**_PL, height=260)
            st.plotly_chart(fig3, use_container_width=True)
            extra = sim_data.get("total_extra_1yr", 0)
            epm   = sim_data.get("extra_per_month", 0)
            st.markdown(
                f'<div style="background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.2);'
                f'border-radius:10px;padding:.75rem 1rem;margin-top:.5rem;">'
                f'<div style="font-size:.8rem;color:#34D399;font-weight:700;">'
                f'+${epm:,.0f}/month → +${extra:,.0f} extra saved over 1 year</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            empty_state("🎛️", "Add financial data to run scenario.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — CASH FLOW FORECAST  (new tab, was missing)
# ══════════════════════════════════════════════════════════════════════════════
with tab_cashflow:
    section_header("💵", "Net Cash Flow Forecast", "ARIMA time-series model")

    cf_period_map = {"3 Months": 3, "6 Months": 6, "1 Year": 12}
    cf_sel = st.radio("Forecast Horizon", list(cf_period_map.keys()),
                      horizontal=True, key="cf_period")
    cf_months = cf_period_map[cf_sel]

    with st.spinner("Running ARIMA cash flow forecast…"):
        cf_data = _api("/api/forecasting/cashflow", params={"months": cf_months})

    cf_fc = cf_data.get("forecast", [])

    if "error" in cf_data:
        _show_error(cf_data, "GET /api/forecasting/cashflow")
    elif not cf_fc:
        empty_state("💵", "No cash flow data",
                    "Add financial records to generate cash flow forecasts.")
    else:
        cf_vals   = [f["predicted_cashflow"] for f in cf_fc]
        cf_dates  = [f["date"] for f in cf_fc]
        cf_total  = sum(cf_vals)
        cf_avg    = cf_total / max(len(cf_vals), 1)
        positive_months = sum(1 for v in cf_vals if v >= 0)

        metric_row([
            dict(icon="💵", label="Projected Net Cash",
                 value=f"${cf_total:,.0f}",
                 sub=f"Over {cf_months} months",
                 trend_up=cf_total >= 0,
                 accent="linear-gradient(90deg,#06B6D4,#0284C7)"),
            dict(icon="📊", label="Avg Monthly",
                 value=f"${cf_avg:,.0f}",
                 sub="Per month",
                 trend_up=cf_avg >= 0,
                 accent="linear-gradient(90deg,#2563EB,#1D4ED8)"),
            dict(icon="✅", label="Positive Months",
                 value=f"{positive_months}/{cf_months}",
                 sub="Cash positive",
                 trend_up=positive_months >= cf_months // 2,
                 accent="linear-gradient(90deg,#10B981,#059669)"),
        ])

        st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)
        section_header("📈", "Monthly Cash Flow Projection")

        colors = ["#10B981" if v >= 0 else "#EF4444" for v in cf_vals]
        fig_cf = go.Figure()
        fig_cf.add_trace(go.Bar(
            x=cf_dates, y=cf_vals,
            marker_color=colors, opacity=0.85,
            text=[f"${v:,.0f}" for v in cf_vals],
            textposition="outside",
            textfont=dict(color="#94A3B8", size=10),
            name="Net Cash Flow",
        ))
        # zero line
        fig_cf.add_hline(y=0, line_dash="dot",
                         line_color="rgba(100,116,139,.4)", line_width=1)
        fig_cf.update_layout(**_PL, height=320)
        st.plotly_chart(fig_cf, use_container_width=True)

        # running cumulative
        section_header("📉", "Cumulative Cash Position")
        cumulative = []
        running = 0.0
        for v in cf_vals:
            running += v
            cumulative.append(running)

        fig_cum = go.Figure(go.Scatter(
            x=cf_dates, y=cumulative,
            mode="lines+markers",
            line=dict(color="#7C3AED", width=2),
            marker=dict(size=5,
                        color=["#10B981" if v >= 0 else "#EF4444" for v in cumulative]),
            fill="tozeroy",
            fillcolor="rgba(124,58,237,.06)",
            name="Cumulative Cash",
        ))
        fig_cum.add_hline(y=0, line_dash="dot",
                          line_color="rgba(100,116,139,.4)", line_width=1)
        fig_cum.update_layout(**_PL, height=240)
        st.plotly_chart(fig_cum, use_container_width=True)

        # insight
        final_cum = cumulative[-1] if cumulative else 0
        if final_cum >= 0:
            insight_card("success",
                         f"Projected cumulative cash position is ${final_cum:,.0f} — positive trajectory.",
                         "ARIMA forecast")
        else:
            insight_card("warning",
                         f"Projected cumulative cash position is ${final_cum:,.0f}. "
                         "Review your spending to avoid a cash shortfall.",
                         "ARIMA forecast")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — STUDY & PRODUCTIVITY
# ══════════════════════════════════════════════════════════════════════════════
with tab_study:
    section_header("📚", "Study & Productivity Predictions", "RandomForest · Linear Regression")

    col_r, col_e = st.columns(2, gap="large")

    with col_r:
        section_header("🎯", "Exam Readiness")
        with st.spinner("Calculating…"):
            readiness = _api("/api/study/exam-readiness")
        if "error" in readiness:
            _show_error(readiness, "GET /api/study/exam-readiness")
        elif "score" in readiness:
            score = readiness["score"]
            color = "#10B981" if score >= 80 else "#F59E0B" if score >= 60 else "#EF4444"
            st.markdown(
                '<div style="background:rgba(13,17,28,.9);border:1px solid rgba(37,99,235,.2);'
                f'border-radius:16px;padding:1.5rem;text-align:center;margin-bottom:.75rem;">'
                f'<div style="font-size:3rem;font-weight:800;color:{color};">{score:.0f}</div>'
                '<div style="font-size:.8rem;color:#64748B;margin-top:.25rem;">/ 100</div>'
                f'<div style="font-size:1rem;font-weight:600;color:{color};margin-top:.5rem;">'
                f'{readiness.get("interpretation","")}</div></div>',
                unsafe_allow_html=True,
            )
            for label, val in readiness.get("breakdown", {}).items():
                progress_bar(label.replace("_", " ").title(), val, 100)
        else:
            empty_state("🎯", "No study data yet", "Log study sessions to see readiness score.")

    with col_e:
        section_header("📈", "Performance Prediction")
        with st.spinner("Predicting…"):
            perf = _api("/api/study/performance-prediction")
        if "error" in perf:
            _show_error(perf, "GET /api/study/performance-prediction")
        elif perf.get("predicted_score") is not None:
            ps    = perf["predicted_score"]
            color = "#10B981" if ps >= 75 else "#F59E0B" if ps >= 55 else "#EF4444"
            st.markdown(
                '<div style="background:rgba(13,17,28,.9);border:1px solid rgba(37,99,235,.2);'
                f'border-radius:16px;padding:1.5rem;text-align:center;">'
                f'<div style="font-size:3rem;font-weight:800;color:{color};">{ps:.0f}</div>'
                '<div style="font-size:.8rem;color:#64748B;">Predicted Score / 100</div>'
                f'<div style="font-size:.8rem;color:#475569;margin-top:.5rem;">'
                f'Source: {perf.get("source","heuristic")}</div></div>',
                unsafe_allow_html=True,
            )
        else:
            empty_state("📈", "No study history", "Log sessions to get predictions.")

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    section_header("📉", "Study Hours Trend")
    with st.spinner("Loading trend…"):
        trend = _api("/api/study/trend")

    if "error" in trend:
        _show_error(trend, "GET /api/study/trend")
    elif trend.get("weekly_data"):
        wd = trend["weekly_data"]
        fig4 = go.Figure(go.Scatter(
            x=[w["date"] for w in wd], y=[w["hours"] for w in wd],
            mode="lines+markers", name="Weekly Hours",
            line=dict(color="#2563EB", width=2),
            marker=dict(size=5),
            fill="tozeroy", fillcolor="rgba(37,99,235,.07)",
        ))
        fig4.update_layout(**_PL, height=220)
        st.plotly_chart(fig4, use_container_width=True)
        t   = trend.get("trend", "stable")
        col = "#10B981" if t == "improving" else "#EF4444" if t == "declining" else "#F59E0B"
        st.markdown(
            f'<div style="font-size:.85rem;color:{col};font-weight:600;">'
            f'Trend: {t.upper()} · {trend.get("description","")}</div>',
            unsafe_allow_html=True,
        )
    else:
        empty_state("📉", "Not enough data for trend analysis",
                    "Log at least 3 study sessions across different weeks.")

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    section_header("📅", "Optimal Study Plan Generator")
    with st.form("plan_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            target_score = st.number_input("Target Score", 0.0, 100.0, 85.0)
        with c2:
            exam_date = st.date_input("Exam Date",
                                      value=datetime.today() + timedelta(days=30))
        with c3:
            subject = st.text_input("Subject", "General")
        plan_sub = st.form_submit_button("Generate Plan", use_container_width=True)

    if plan_sub:
        with st.spinner("Generating…"):
            plan = _api("/api/study/optimal-plan", method="post", payload={
                "target_score": float(target_score),
                "exam_date":    exam_date.isoformat(),
                "subject":      subject,
            })
        if "error" in plan:
            _show_error(plan, "POST /api/study/optimal-plan")
        else:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Daily Hours",    plan.get("recommended_daily_hours", "—"))
            c2.metric("Sessions/Day",   plan.get("sessions_per_day", "—"))
            c3.metric("Session Length", f"{plan.get('session_length_hours','—')}h")
            c4.metric("Feasibility",    plan.get("feasibility", "—"))

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — HABIT PREDICTIONS
# ══════════════════════════════════════════════════════════════════════════════
with tab_habit:
    section_header("🔥", "Habit Predictions", "AI Consistency · Productivity Index")

    col_a, col_b = st.columns(2, gap="large")

    with col_a:
        section_header("📊", "Productivity Index")
        with st.spinner("Calculating…"):
            prod = _api("/api/habits/productivity-index")
        if "error" in prod:
            _show_error(prod, "GET /api/habits/productivity-index")
        elif "productivity_index" in prod:
            pi    = prod["productivity_index"]
            color = "#10B981" if pi >= 75 else "#F59E0B" if pi >= 55 else "#EF4444"
            st.markdown(
                '<div style="background:rgba(13,17,28,.9);border:1px solid rgba(37,99,235,.2);'
                f'border-radius:16px;padding:1.5rem;text-align:center;margin-bottom:.75rem;">'
                f'<div style="font-size:3rem;font-weight:800;color:{color};">{pi:.0f}</div>'
                '<div style="font-size:.8rem;color:#64748B;">Productivity Index / 100</div>'
                f'<div style="font-size:.9rem;font-weight:600;color:{color};margin-top:.35rem;">'
                f'{prod.get("interpretation","")}</div></div>',
                unsafe_allow_html=True,
            )
            for k, label in {
                "study_task_completion": "Study Task Completion",
                "habit_consistency":     "Habit Consistency",
                "fitness_frequency":     "Fitness Frequency",
                "financial_discipline":  "Financial Discipline",
            }.items():
                if k in prod.get("components", {}):
                    progress_bar(label, prod["components"][k], 100)
        else:
            empty_state("📊", "Add data to calculate productivity index")

    with col_b:
        section_header("🔍", "Habit Analysis")
        with st.spinner("Analysing…"):
            analysis = _api("/api/habits/analysis")
        if "error" in analysis:
            _show_error(analysis, "GET /api/habits/analysis")
        elif "score" in analysis:
            sc    = analysis["score"]
            color = "#10B981" if sc >= 70 else "#F59E0B" if sc >= 50 else "#EF4444"
            st.markdown(
                '<div style="background:rgba(13,17,28,.9);border:1px solid rgba(37,99,235,.2);'
                f'border-radius:16px;padding:1.25rem 1.5rem;margin-bottom:.75rem;">'
                f'<div style="font-size:1.75rem;font-weight:800;color:{color};">{sc:.0f}/100</div>'
                '<div style="font-size:.75rem;color:#64748B;">Consistency Score</div>'
                f'<div style="margin-top:.5rem;font-size:.8rem;color:#94A3B8;">'
                f'{analysis.get("completed_habits",0)} of {analysis.get("total_habits",0)} '
                f'habits completed · Avg streak: {analysis.get("avg_streak",0):.0f} days'
                '</div></div>',
                unsafe_allow_html=True,
            )
            if analysis.get("at_risk_habits"):
                insight_card("warning",
                             f"At-risk habits: {', '.join(analysis['at_risk_habits'][:3])}",
                             "Completion rate < 60%")
            if analysis.get("strong_habits"):
                insight_card("success",
                             f"Strong habits: {', '.join(analysis['strong_habits'][:3])}",
                             "Streak >= 7 days")
        else:
            empty_state("🔍", "No habit data yet", "Add habits to get analysis.")

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    section_header("📈", "4-Week Productivity Forecast")
    with st.spinner("Forecasting…"):
        pt = _api("/api/habits/trend")

    if "error" in pt:
        _show_error(pt, "GET /api/habits/trend")
    elif pt.get("forecast"):
        hist = pt.get("historical", [])
        fc   = pt.get("forecast", [])
        fig5 = go.Figure()
        if hist:
            fig5.add_trace(go.Scatter(
                x=[h["week"] for h in hist], y=[h["index"] for h in hist],
                mode="lines+markers", name="Historical",
                line=dict(color="#2563EB", width=2), marker=dict(size=5),
            ))
        if fc:
            fig5.add_trace(go.Scatter(
                x=[f["week"] for f in fc], y=[f["predicted_index"] for f in fc],
                mode="lines+markers", name="Forecast",
                line=dict(color="#7C3AED", width=2, dash="dash"),
                marker=dict(size=6, symbol="diamond"),
            ))
        fig5.update_layout(**_PL, height=250)
        st.plotly_chart(fig5, use_container_width=True)
        t   = pt.get("trend", "stable")
        col = "#10B981" if t == "improving" else "#EF4444" if t == "declining" else "#F59E0B"
        st.markdown(
            f'<div style="font-size:.85rem;color:{col};font-weight:600;">'
            f'Trend: {t.upper()}</div>',
            unsafe_allow_html=True,
        )
    else:
        empty_state("📈", "Not enough data for trend forecast",
                    "Keep logging habits and study sessions.")

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    section_header("⚠️", "Anomaly Detection")
    with st.spinner("Scanning…"):
        anom = _api("/api/habits/anomalies")

    if "error" in anom:
        _show_error(anom, "GET /api/habits/anomalies")
    else:
        anomalies = anom.get("anomalies", [])
        if anomalies:
            for a in anomalies:
                atype = a.get("type", "unusual")
                insight_card(
                    "warning" if atype == "low_activity" else "info",
                    f"Week of {a.get('week','?')}: {atype.replace('_',' ').title()} — "
                    f"Study: {a.get('study_hours',0):.1f}h · "
                    f"Fitness: {a.get('fitness_mins',0):.0f} min",
                    "Isolation Forest detection",
                )
        else:
            insight_card("success",
                         "No anomalous weeks detected — your patterns look consistent.",
                         "Anomaly detection")
