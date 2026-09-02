"""
Digital Twin AI — Enhanced Dashboard (Milestone 4)
Period-controlled charts: Savings, Productivity, Fitness, Study, KPIs, Recommendations.
All data pulled from real backend APIs.
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
    compute_scores, page_header, render_sidebar, render_topbar, require_auth, section_header,
)

st.set_page_config(
    page_title="Dashboard · Digital Twin AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_theme()
bootstrap_session()
render_sidebar()
render_topbar("Dashboard")
require_auth()

client = st.session_state.api_client
token  = st.session_state.token
is_light = st.session_state.get("theme", "dark") == "light"

_PL = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color="#94A3B8", size=12),
    margin=dict(l=0, r=0, t=36, b=0),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#94A3B8")),
    xaxis=dict(gridcolor="rgba(37,99,235,.07)", linecolor="rgba(37,99,235,.12)",
               tickfont=dict(color="#64748B")),
    yaxis=dict(gridcolor="rgba(37,99,235,.07)", linecolor="rgba(37,99,235,.12)",
               tickfont=dict(color="#64748B")),
)


# ── helpers ────────────────────────────────────────────────────────────────────
def _api(path, params=None, method="get", payload=None):
    try:
        if method == "post":
            return client.post(path, payload=payload, token=token) or {}
        url = path + ("?" + "&".join(f"{k}={v}" for k, v in (params or {}).items()) if params else "")
        return client.get(url, token=token) or {}
    except Exception as e:
        return {"error": str(e)}


def _period_months(period: str) -> int:
    return {"1W": 1, "1M": 1, "3M": 3, "6M": 6, "1Y": 12, "All": 12}.get(period, 12)


def _cutoff(period: str) -> datetime:
    days = {"1W": 7, "1M": 30, "3M": 90, "6M": 180, "1Y": 365}
    if period == "All":
        return datetime.min
    return datetime.utcnow() - timedelta(days=days.get(period, 365))


def _filter_by_date(records: list, date_field: str, period: str) -> list:
    cutoff = _cutoff(period)
    out = []
    for r in records:
        try:
            dt = datetime.fromisoformat(str(r.get(date_field, ""))[:19])
            if dt >= cutoff:
                out.append(r)
        except Exception:
            out.append(r)
    return out


# ══════════════════════════════════════════════════════════════════════════════
# PAGE HEADER + PERIOD SELECTOR
# ══════════════════════════════════════════════════════════════════════════════
page_header("Your Digital Twin Dashboard", "Unified view of your financial, productivity & wellness data")

h1, h2 = st.columns([3, 1], gap="small")
with h1:
    period = st.radio(
        "Period", ["1W", "1M", "3M", "6M", "1Y", "All"],
        horizontal=True, key="dash_period", index=2,
    )
with h2:
    last_updated = datetime.utcnow().strftime("%d %b %Y %H:%M")
    st.markdown(
        f'<div style="text-align:right;padding-top:.5rem;">'
        f'<span style="font-size:.72rem;color:#64748B;">Last updated: {last_updated} UTC</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
    if st.button("🔄 Refresh", key="dash_refresh"):
        st.cache_data.clear()
        st.rerun()

months = _period_months(period)

# ── load all data ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)
def load_all(tok, period_key):
    def g(path, params=None):
        try:
            url = path + ("?" + "&".join(f"{k}={v}" for k, v in (params or {}).items()) if params else "")
            return client.get(url, token=tok) or {}
        except Exception:
            return {}
    def p(path, payload):
        try:
            return client.post(path, payload=payload, token=tok) or {}
        except Exception:
            return {}

    months_n = _period_months(period_key)
    return {
        "twin":       g("/api/digital-twin/summary"),
        "risk":       g("/api/digital-twin/risk"),
        "savings":    g("/api/forecasting/savings", {"months": months_n}),
        "cashflow":   g("/api/forecasting/cashflow", {"months": months_n}),
        "fin_recs":   g("/api/financial/records"),
        "fin_sum":    g("/api/financial/summary"),
        "study":      g("/api/study"),
        "habits":     g("/api/habits"),
        "fitness":    g("/api/fitness"),
        "goals":      g("/api/goals"),
        "recs":       p("/api/digital-twin/recommendations", {}),
        "prod":       g("/api/habits/productivity-index"),
        "trend":      g("/api/study/trend"),
    }

data = load_all(token, period)

twin     = data.get("twin", {})
risk     = data.get("risk", {})
savings  = data.get("savings", {})
cashflow = data.get("cashflow", {})
fin_recs = data.get("fin_recs", []) or []
fin_sum  = data.get("fin_sum", {})
study    = data.get("study", []) or []
habits   = data.get("habits", []) or []
fitness  = data.get("fitness", []) or []
goals    = data.get("goals", []) or []
recs_d   = data.get("recs", {})
prod     = data.get("prod", {})
trend    = data.get("trend", {})

# Apply period filter
fin_recs_f = _filter_by_date(fin_recs, "date", period)
study_f    = _filter_by_date(study,    "study_date", period)
fitness_f  = _filter_by_date(fitness,  "activity_date", period)
habits_f   = _filter_by_date(habits,   "created_at", period)
goals_f    = _filter_by_date(goals,    "created_at", period)

# Recalculate local domain scores from the same period shown in the charts.
period_scores, period_overall = compute_scores(
    study_f, habits_f, fitness_f, goals_f, fin_recs_f
)

# ══════════════════════════════════════════════════════════════════════════════
# KPI ROW
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

overall_score  = period_overall
financial_sc   = period_scores.get("Finance", 0)
habits_sc      = period_scores.get("Habits", 0)
fitness_sc     = period_scores.get("Fitness", 0)
study_sc       = period_scores.get("Study", 0)
goals_sc       = period_scores.get("Goals", 0)
risk_level     = risk.get("risk_level", "unknown")
risk_score_v   = risk.get("overall_risk_score", 0)

total_income   = sum(r.get("amount", 0) for r in fin_recs_f if r.get("record_type") == "income")
total_exp      = sum(r.get("amount", 0) for r in fin_recs_f if r.get("record_type") == "expense")
net_savings    = total_income - total_exp
prod_idx       = prod.get("productivity_index", 0)
active_goals   = sum(1 for g in goals_f if g.get("status", "").lower() not in ("completed",))
completed_goals = sum(1 for g in goals_f if g.get("status", "").lower() == "completed")

metric_row([
    dict(icon="🧬", label="Twin Alignment",   value=f"{overall_score:.0f}%",
         sub="Overall score", trend_up=overall_score >= 60,
         accent="linear-gradient(90deg,#2563EB,#7C3AED)"),
    dict(icon="💰", label="Financial Health", value=f"{financial_sc:.0f}/100",
         sub=f"Net ${net_savings:,.0f}", trend_up=net_savings >= 0,
         accent="linear-gradient(90deg,#10B981,#059669)"),
    dict(icon="🧠", label="Productivity",     value=f"{prod_idx:.0f}/100",
         sub=prod.get("interpretation", ""),
         trend_up=prod_idx >= 60,
         accent="linear-gradient(90deg,#7C3AED,#6D28D9)"),
    dict(icon="🎯", label="Goal Achievement", value=f"{completed_goals}/{len(goals)}",
         sub=f"{active_goals} active", trend_up=completed_goals > 0,
         accent="linear-gradient(90deg,#F59E0B,#D97706)"),
    dict(icon="⚠️", label="Risk Level",      value=risk_level.upper(),
         sub=f"Score {risk_score_v:.0f}/100",
         trend_up=risk_score_v < 40,
         accent="linear-gradient(90deg,#EF4444,#DC2626)"),
])

st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# CHART ROW 1 — Savings Projection + Productivity
# ══════════════════════════════════════════════════════════════════════════════
section_header("📈", "Financial & Productivity", f"{period} view")
cr1, cr2 = st.columns(2, gap="large")

with cr1:
    fc = savings.get("forecast", [])
    if fc:
        dates = [f["date"] for f in fc]
        pred  = [f["predicted_savings"] for f in fc]
        lower = [f["lower_bound"] for f in fc]
        upper = [f["upper_bound"] for f in fc]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates + dates[::-1], y=upper + lower[::-1],
            fill="toself", fillcolor="rgba(37,99,235,.07)",
            line=dict(color="rgba(0,0,0,0)"), name="80% CI", showlegend=True,
        ))
        fig.add_trace(go.Scatter(
            x=dates, y=pred, mode="lines+markers",
            line=dict(color="#2563EB", width=2.5),
            marker=dict(size=4, color="#2563EB"),
            name="Projected Savings",
        ))
        # Annotate max
        if pred:
            max_i = pred.index(max(pred))
            fig.add_annotation(
                x=dates[max_i], y=max(pred),
                text=f"Peak: ${max(pred):,.0f}",
                showarrow=True, arrowhead=2,
                font=dict(color="#10B981", size=11),
                arrowcolor="#10B981",
            )
        fig.update_layout(
            **_PL, height=300,
            title=dict(text="💰 Savings Projection", font=dict(color="#E2E8F0", size=13)),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        empty_state("💰", "No forecast data", "Add financial records to generate projections.")

with cr2:
    # Productivity components radar
    comps = prod.get("components", {})
    if comps:
        labels = [k.replace("_", " ").title() for k in comps]
        values = list(comps.values())
        fig2 = go.Figure(go.Scatterpolar(
            r=values + [values[0]],
            theta=labels + [labels[0]],
            fill="toself",
            line=dict(color="#7C3AED", width=2),
            fillcolor="rgba(124,58,237,.12)",
            name="Productivity",
        ))
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            polar=dict(
                bgcolor="rgba(13,17,28,.5)",
                radialaxis=dict(visible=True, range=[0, 100], color="#64748B", tickfont=dict(size=9)),
                angularaxis=dict(color="#64748B"),
            ),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#94A3B8")),
            title=dict(text="🧠 Productivity Components", font=dict(color="#E2E8F0", size=13)),
            height=300,
            font=dict(family="Inter", color="#94A3B8"),
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        # Fallback: domain scores bar
        domain_scores = {
            "Study": study_sc, "Finance": financial_sc, "Habits": habits_sc,
            "Fitness": fitness_sc, "Goals": goals_sc,
        }
        colors = ["#2563EB","#10B981","#F59E0B","#EF4444","#8B5CF6"]
        fig2 = go.Figure(go.Bar(
            x=list(domain_scores.keys()),
            y=list(domain_scores.values()),
            marker_color=colors, opacity=0.88,
            text=[f"{v:.0f}" for v in domain_scores.values()],
            textposition="outside", textfont=dict(color="#94A3B8", size=11),
        ))
        domain_layout = _PL.copy()
        domain_layout["yaxis"] = {**_PL.get("yaxis", {}), "range": [0, 115]}
        fig2.update_layout(
            **domain_layout, height=300,
            title=dict(text="📊 Domain Scores", font=dict(color="#E2E8F0", size=13)),
        )
        st.plotly_chart(fig2, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# CHART ROW 2 — Fitness Activity + Study Hours
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)
section_header("🏃", "Activity & Learning", f"{period} view")
cr3, cr4 = st.columns(2, gap="large")

with cr3:
    if fitness_f:
        sorted_f = sorted(fitness_f, key=lambda x: x.get("activity_date", ""))
        dates_f  = [r["activity_date"][:10] for r in sorted_f]
        cals     = [r.get("calories_burned", 0) for r in sorted_f]
        durs     = [r.get("duration", 0) for r in sorted_f]

        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            x=dates_f, y=cals, name="Calories Burned",
            marker_color="#10B981", opacity=0.82,
        ))
        fig3.add_trace(go.Scatter(
            x=dates_f, y=durs, mode="lines+markers",
            name="Duration (min)", line=dict(color="#F59E0B", width=2),
            marker=dict(size=4), yaxis="y2",
        ))
        fig3.update_layout(
            **_PL, height=280,
            yaxis2=dict(overlaying="y", side="right", showgrid=False,
                        tickfont=dict(color="#F59E0B")),
            title=dict(text="🏃 Fitness Activity", font=dict(color="#E2E8F0", size=13)),
        )
        st.plotly_chart(fig3, use_container_width=True)
    else:
        empty_state("🏃", f"No fitness data in {period}", "Log activities to see charts.")

with cr4:
    if study_f:
        sorted_s = sorted(study_f, key=lambda x: x.get("study_date", ""))
        dates_s  = [r["study_date"][:10] for r in sorted_s]
        hrs_s    = [r.get("study_hours", 0) for r in sorted_s]
        perf_s   = [r.get("performance_score", 0) for r in sorted_s]

        fig4 = go.Figure()
        fig4.add_trace(go.Bar(
            x=dates_s, y=hrs_s, name="Study Hours",
            marker_color="#2563EB", opacity=0.82,
        ))
        fig4.add_trace(go.Scatter(
            x=dates_s, y=perf_s, mode="lines+markers",
            name="Performance", line=dict(color="#7C3AED", width=2),
            marker=dict(size=5), yaxis="y2",
        ))
        fig4.update_layout(
            **_PL, height=280,
            yaxis2=dict(overlaying="y", side="right", showgrid=False,
                        tickfont=dict(color="#7C3AED"), range=[0, 110]),
            title=dict(text="📚 Study Hours & Performance", font=dict(color="#E2E8F0", size=13)),
        )
        st.plotly_chart(fig4, use_container_width=True)
    else:
        empty_state("📚", f"No study data in {period}", "Log study sessions to see trends.")

# ══════════════════════════════════════════════════════════════════════════════
# CHART ROW 3 — Cash Flow + Goals Progress
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)
section_header("💵", "Cash Flow & Goals", f"{period} view")
cr5, cr6 = st.columns(2, gap="large")

with cr5:
    cf_fc = cashflow.get("forecast", [])
    if cf_fc:
        cf_dates = [f["date"] for f in cf_fc]
        cf_vals  = [f["predicted_cashflow"] for f in cf_fc]
        colors   = ["#10B981" if v >= 0 else "#EF4444" for v in cf_vals]
        fig5 = go.Figure(go.Bar(
            x=cf_dates, y=cf_vals, marker_color=colors, opacity=0.85,
            text=[f"${v:,.0f}" for v in cf_vals],
            textposition="outside", textfont=dict(color="#94A3B8", size=9),
        ))
        fig5.add_hline(y=0, line_dash="dot", line_color="rgba(100,116,139,.4)")
        fig5.update_layout(
            **_PL, height=260,
            title=dict(text="💵 Monthly Cash Flow", font=dict(color="#E2E8F0", size=13)),
        )
        st.plotly_chart(fig5, use_container_width=True)
    else:
        empty_state("💵", "No cash flow data", "Add financial records to see projections.")

with cr6:
    if goals:
        g_names = [g.get("name", "?")[:22] for g in goals[:8]]
        g_pct   = [
            min(g.get("current_value", 0) / g.get("target_value", 1) * 100, 100)
            for g in goals[:8]
        ]
        g_colors = [
            "#10B981" if p >= 80 else "#F59E0B" if p >= 40 else "#EF4444"
            for p in g_pct
        ]
        fig6 = go.Figure(go.Bar(
            x=g_pct, y=g_names, orientation="h",
            marker_color=g_colors, opacity=0.88,
            text=[f"{p:.0f}%" for p in g_pct],
            textposition="outside", textfont=dict(color="#94A3B8", size=10),
        ))
        goals_layout = _PL.copy()
        goals_layout["xaxis"] = {**_PL.get("xaxis", {}), "range": [0, 115], "title": "Progress %"}
        goals_layout["yaxis"] = {**_PL.get("yaxis", {}), "categoryorder": "total ascending"}
        fig6.update_layout(
            **goals_layout, height=260,
            title=dict(text="🎯 Goal Progress", font=dict(color="#E2E8F0", size=13)),
        )
        st.plotly_chart(fig6, use_container_width=True)
    else:
        empty_state("🎯", "No goals defined", "Add goals to track progress.")

# ══════════════════════════════════════════════════════════════════════════════
# AI RECOMMENDATIONS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
section_header("🤖", "AI Recommendations", "Top 5 personalised actions")
recs_list = recs_d.get("recommendations", [])
if recs_list:
    cols_rec = st.columns(min(len(recs_list[:5]), 3), gap="large")
    for i, rec in enumerate(recs_list[:5]):
        with cols_rec[i % 3]:
            pri  = rec.get("priority", "low")
            dom  = rec.get("domain", "general")
            titl = rec.get("title", "")
            desc = rec.get("description", "")[:160]
            pri_color = {"high": "#EF4444", "medium": "#F59E0B", "low": "#10B981"}.get(pri, "#64748B")
            dom_icon  = {"financial": "💰", "study": "📚", "habits": "🔥",
                         "fitness": "🏃", "goals": "🎯"}.get(dom, "💡")
            st.markdown(
                f'<div style="background:{"rgba(13,17,28,.9)" if not is_light else "#FFFFFF"};'
                f'border:1px solid rgba(37,99,235,.15);border-radius:14px;padding:1rem 1.1rem;'
                f'height:100%;border-top:3px solid {pri_color};">'
                f'<div style="font-size:.68rem;font-weight:700;color:{pri_color};'
                f'text-transform:uppercase;letter-spacing:.1em;margin-bottom:.35rem;">'
                f'{dom_icon} {dom.upper()} · {pri.upper()}</div>'
                f'<div style="font-size:.88rem;font-weight:700;color:{"#0F172A" if is_light else "#F1F5F9"};'
                f'margin-bottom:.4rem;">{titl}</div>'
                f'<div style="font-size:.78rem;color:#94A3B8;line-height:1.55;">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
else:
    empty_state("🤖", "No recommendations yet", "Add data across domains to generate AI insights.")

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
