"""
Digital Twin AI — Reports & PDF Export (Milestone 4)
Generate and download personalised PDF reports with real data.
Period comparison view.
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
    bootstrap_session, empty_state, insight_card, metric_row,
    page_header, render_sidebar, render_topbar, require_auth, section_header,
)

st.set_page_config(
    page_title="Reports · Digital Twin AI",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_theme()
bootstrap_session()
render_sidebar()
render_topbar("Reports")
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

txt_c  = "#0F172A" if is_light else "#F1F5F9"
bdr_c  = "rgba(37,99,235,.14)"
card_bg = "#FFFFFF" if is_light else "rgba(13,17,28,.9)"
muted  = "#64748B"


def _api(path, params=None, method="get", payload=None):
    try:
        if method == "post":
            return client.post(path, payload=payload or {}, token=token)
        url = path + ("?" + "&".join(f"{k}={v}" for k, v in (params or {}).items()) if params else "")
        return client.get(url, token=token)
    except Exception as e:
        return {"error": str(e)}


page_header("Reports & PDF Export", "Generate personalised reports and compare periods")

# ══════════════════════════════════════════════════════════════════════════════
# REPORT GENERATOR SECTION
# ══════════════════════════════════════════════════════════════════════════════
section_header("📄", "Generate PDF Report", "Download your full digital twin report")

REPORT_TYPES = {
    "Full Report":       ("full",            "📊", "Complete report: financial, goals, study, productivity, recommendations & risk"),
    "Financial Report":  ("financial",       "💰", "Income, expenses, savings rate, 12-month projection"),
    "Goals Report":      ("goals",           "🎯", "Goal progress, timeline, completion probabilities"),
    "Study Report":      ("study",           "📚", "Study hours, performance trends, productivity metrics"),
    "Recommendations":   ("recommendations", "💡", "Top 5 personalised action items with steps"),
}

rc1, rc2 = st.columns([1.2, 1], gap="large")

with rc1:
    section_header("🗂️", "Select Report Type")
    selected_label = st.radio(
        "Report type", list(REPORT_TYPES.keys()),
        key="report_type_sel", label_visibility="collapsed",
    )
    rtype, ricon, rdesc = REPORT_TYPES[selected_label]

    st.markdown(
        f'<div style="background:{card_bg};border:1px solid {bdr_c};border-radius:12px;'
        f'padding:.85rem 1.1rem;margin:.5rem 0;">'
        f'<div style="font-size:.95rem;font-weight:700;color:{txt_c};">{ricon} {selected_label}</div>'
        f'<div style="font-size:.8rem;color:{muted};margin-top:.3rem;">{rdesc}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if st.button(f"⬇️  Generate & Download {selected_label}", use_container_width=True, key="gen_report"):
        with st.spinner("Generating PDF report… this may take a few seconds"):
            try:
                pdf_bytes = client.get_bytes(
                    f"/api/reports/generate?type={rtype}", token=token, timeout=30
                )
                fname = f"digital_twin_{rtype}_{datetime.utcnow().strftime('%Y%m%d')}.pdf"
                st.download_button(
                    label=f"📥  Click to download {fname}",
                    data=pdf_bytes,
                    file_name=fname,
                    mime="application/pdf",
                    use_container_width=True,
                )
                st.success("Report generated! Click the download button above.")
            except Exception as exc:
                st.error(f"Could not generate report: {exc}")

with rc2:
    section_header("📋", "Report Preview")
    # Load live data for preview
    twin   = _api("/api/digital-twin/summary")
    risk   = _api("/api/digital-twin/risk")
    recs_d = _api("/api/digital-twin/recommendations", method="post")

    if "error" not in twin:
        metric_row([
            dict(icon="🧬", label="Alignment",   value=f"{twin.get('overall_score',0):.0f}%",
                 sub="Overall", accent="linear-gradient(90deg,#2563EB,#7C3AED)"),
            dict(icon="⚠️", label="Risk",         value=risk.get("risk_level","?").upper(),
                 sub=f"Score {risk.get('overall_risk_score',0):.0f}", trend_up=False,
                 accent="linear-gradient(90deg,#EF4444,#DC2626)"),
        ])
        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    recs = recs_d.get("recommendations", [])[:3]
    for r in recs:
        pri_c = {"high": "#EF4444", "medium": "#F59E0B", "low": "#10B981"}.get(r.get("priority","low"), "#64748B")
        st.markdown(
            f'<div style="background:{card_bg};border-left:3px solid {pri_c};border:1px solid {bdr_c};'
            f'border-left:3px solid {pri_c};border-radius:0 10px 10px 0;'
            f'padding:.65rem 1rem;margin-bottom:.4rem;">'
            f'<div style="font-size:.8rem;font-weight:600;color:{txt_c};">{r.get("title","")}</div>'
            f'<div style="font-size:.7rem;color:{muted};">{r.get("domain","").upper()} · {r.get("priority","").upper()}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PERIOD COMPARISON SECTION
# ══════════════════════════════════════════════════════════════════════════════
section_header("📅", "Period Comparison", "Compare two time periods side-by-side")

cc1, cc2, cc3 = st.columns([1, 1, 1], gap="small")
with cc1:
    period_a = st.selectbox("Earlier Period", ["1M", "3M", "6M", "1Y"], index=0, key="pa")
with cc2:
    period_b = st.selectbox("Later Period",   ["1M", "3M", "6M", "1Y"], index=3, key="pb")
with cc3:
    st.markdown("<div style='height:1.65rem'></div>", unsafe_allow_html=True)
    run_comp = st.button("Compare Periods", use_container_width=True, key="run_comp")

if run_comp or "comp_data" in st.session_state:
    if run_comp:
        with st.spinner("Comparing periods…"):
            comp = _api(f"/api/reports/comparison?period_a={period_a}&period_b={period_b}")
            st.session_state["comp_data"] = comp

    comp = st.session_state.get("comp_data", {})

    if "error" in comp:
        st.error(f"Comparison failed: {comp['error']}")
    else:
        pa_label = comp.get("period_a", {}).get("label", period_a)
        pb_label = comp.get("period_b", {}).get("label", period_b)

        st.markdown(
            f'<div style="background:{card_bg};border:1px solid {bdr_c};border-radius:14px;'
            f'padding:1rem 1.5rem;margin:.75rem 0;">'
            f'<div style="font-size:.85rem;font-weight:700;color:{txt_c};">'
            f'Comparing {pa_label} vs {pb_label}</div></div>',
            unsafe_allow_html=True,
        )

        # Build comparison cards for each domain
        domains = [
            ("financial", "💰", "Financial", ["income", "expenses", "net"]),
            ("study",     "📚", "Study",     ["sessions", "avg_hours", "avg_performance"]),
            ("fitness",   "🏃", "Fitness",   ["sessions", "avg_calories"]),
            ("habits",    "🔥", "Habits",    ["completion_rate"]),
        ]

        comp_cols = st.columns(4, gap="small")
        for ci, (dom, icon, label, keys) in enumerate(domains):
            dom_data = comp.get(dom, {})
            a_data   = dom_data.get("period_a", {})
            b_data   = dom_data.get("period_b", {})
            delta_d  = dom_data.get("delta", {})

            with comp_cols[ci]:
                st.markdown(
                    f'<div style="background:{card_bg};border:1px solid {bdr_c};'
                    f'border-radius:12px;padding:.9rem 1rem;height:100%;">'
                    f'<div style="font-size:.85rem;font-weight:700;color:{txt_c};margin-bottom:.5rem;">'
                    f'{icon} {label}</div>',
                    unsafe_allow_html=True,
                )
                for k in keys:
                    av = a_data.get(k, 0)
                    bv = b_data.get(k, 0)
                    d  = delta_d.get(k, {})
                    chg = d.get("change", 0) if d else 0
                    pct = d.get("pct", 0) if d else 0
                    improved = d.get("improved", False) if d else False
                    chg_color = "#10B981" if improved else "#EF4444"
                    arrow = "↑" if improved else "↓"
                    st.markdown(
                        f'<div style="margin-bottom:.35rem;">'
                        f'<div style="font-size:.68rem;color:{muted};text-transform:uppercase;">{k.replace("_"," ")}</div>'
                        f'<div style="font-size:.82rem;color:{txt_c};">'
                        f'{av:.1f} → {bv:.1f} '
                        f'<span style="color:{chg_color};font-weight:700;">{arrow} {abs(pct):.0f}%</span>'
                        f'</div></div>',
                        unsafe_allow_html=True,
                    )
                st.markdown('</div>', unsafe_allow_html=True)

        # Radar chart: domain scores comparison (using twin scores)
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        section_header("📊", "Visual Comparison")
        twin_now = _api("/api/digital-twin/summary")
        if "error" not in twin_now:
            domains_r = ["Study", "Finance", "Habits", "Fitness", "Goals"]
            scores_r  = [
                twin_now.get("study_score",    0),
                twin_now.get("financial_score", 0),
                twin_now.get("habits_score",   0),
                twin_now.get("fitness_score",  0),
                twin_now.get("goals_score",    0),
            ]
            fig_r = go.Figure()
            fig_r.add_trace(go.Scatterpolar(
                r=scores_r + [scores_r[0]], theta=domains_r + [domains_r[0]],
                fill="toself", name="Current State",
                line=dict(color="#2563EB", width=2),
                fillcolor="rgba(37,99,235,.1)",
            ))
            fig_r.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                polar=dict(
                    bgcolor="rgba(13,17,28,.4)",
                    radialaxis=dict(visible=True, range=[0, 100], color="#64748B"),
                    angularaxis=dict(color="#64748B"),
                ),
                title=dict(text="Current Domain Scores", font=dict(color="#E2E8F0", size=13)),
                height=300,
                font=dict(family="Inter", color="#94A3B8"),
            )
            st.plotly_chart(fig_r, use_container_width=True)

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
