"""
Digital Twin AI — Analytics
"""
import os, sys
from collections import Counter

import plotly.graph_objects as go
import streamlit as st

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from components.theme import inject_theme
from components.ui import (
    bootstrap_session, require_auth, render_sidebar,
    page_header, section_header, metric_row, empty_state,
)

st.set_page_config(page_title="Analytics · Digital Twin AI", page_icon="📊", layout="wide", initial_sidebar_state="expanded")
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
def load_logs(tok):
    try:
        return client.get("/api/analytics/activity-log", token=tok) or []
    except Exception:
        return []

logs = load_logs(token)

page_header("Analytics", "API activity log — every request with latency breakdown")

if not logs:
    empty_state("📊", "No activity recorded yet",
                "Interact with the app to populate your analytics dashboard.")
    st.stop()

# ── KPIs ──────────────────────────────────────────────────────────────────────
total   = len(logs)
avg_ms  = sum(r["response_time_ms"] for r in logs) / total
max_ms  = max(r["response_time_ms"] for r in logs)
min_ms  = min(r["response_time_ms"] for r in logs)
methods = Counter(r["method"] for r in logs)
gets    = methods.get("GET",  0)
posts   = methods.get("POST", 0)

metric_row([
    dict(icon="📡", label="Total Requests", value=str(total),
         sub="All time", accent="linear-gradient(90deg,#2563EB,#1D4ED8)"),
    dict(icon="⚡", label="Avg Latency",    value=f"{avg_ms:.1f} ms",
         sub="Response time", trend_up=avg_ms < 100,
         accent="linear-gradient(90deg,#10B981,#059669)"),
    dict(icon="🔴", label="Peak Latency",   value=f"{max_ms:.0f} ms",
         sub="Slowest request", trend_up=False,
         accent="linear-gradient(90deg,#EF4444,#DC2626)"),
    dict(icon="🟢", label="Fastest",        value=f"{min_ms:.0f} ms",
         sub="Best response",
         accent="linear-gradient(90deg,#06B6D4,#0284C7)"),
    dict(icon="📥", label="GET / POST",     value=f"{gets} / {posts}",
         sub="Request methods",
         accent="linear-gradient(90deg,#8B5CF6,#7C3AED)"),
])

st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

# ── LATENCY OVER TIME ─────────────────────────────────────────────────────────
col_lat, col_end = st.columns([1.6, 1], gap="large")

with col_lat:
    section_header("📈", "Response Time Over Time", "Latency per request (ms)")
    sorted_logs = sorted(logs, key=lambda x: x.get("timestamp",""))
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[r["timestamp"][:19].replace("T"," ") for r in sorted_logs],
        y=[r["response_time_ms"] for r in sorted_logs],
        mode="lines+markers", name="Latency (ms)",
        line=dict(color="#2563EB", width=1.5),
        marker=dict(size=4, color="#2563EB"),
        fill="tozeroy", fillcolor="rgba(37,99,235,.06)",
    ))
    # moving average line
    window = 5
    if len(sorted_logs) >= window:
        ma = [
            sum(sorted_logs[i-window+1:i+1][j]["response_time_ms"] for j in range(window)) / window
            for i in range(window-1, len(sorted_logs))
        ]
        fig.add_trace(go.Scatter(
            x=[r["timestamp"][:19].replace("T"," ") for r in sorted_logs[window-1:]],
            y=ma,
            mode="lines", name=f"{window}-req avg",
            line=dict(color="#7C3AED", width=2, dash="dot"),
        ))
    fig.update_layout(**_PLOTLY_LAYOUT, height=280,
                      legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#94A3B8")))
    st.plotly_chart(fig, use_container_width=True)

with col_end:
    section_header("🗂️", "Requests by Endpoint")
    ep_counts: dict = {}
    for r in logs:
        ep = r["endpoint"]
        ep_counts[ep] = ep_counts.get(ep, 0) + 1
    sorted_ep = sorted(ep_counts.items(), key=lambda x: x[1], reverse=True)[:12]
    fig2 = go.Figure(go.Bar(
        x=[v for _, v in sorted_ep],
        y=[k.replace("/api/","") for k, _ in sorted_ep],
        orientation="h",
        marker_color="#2563EB", opacity=0.85,
        text=[str(v) for _, v in sorted_ep],
        textposition="outside",
        textfont=dict(color="#64748B", size=10),
    ))
    fig2.update_layout(
        **_PLOTLY_LAYOUT, height=280,
        yaxis=dict(**_PLOTLY_LAYOUT["yaxis"], categoryorder="total ascending"),
    )
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

# ── METHOD BREAKDOWN + LATENCY HISTOGRAM ─────────────────────────────────────
col_meth, col_hist = st.columns(2, gap="large")

with col_meth:
    section_header("🔵", "Requests by Method")
    fig3 = go.Figure(go.Pie(
        labels=list(methods.keys()),
        values=list(methods.values()),
        hole=0.55,
        marker=dict(colors=["#2563EB","#10B981","#F59E0B","#EF4444"]),
        textfont=dict(color="#E2E8F0", size=11),
    ))
    fig3.update_layout(**_PLOTLY_LAYOUT, height=240,
                       showlegend=True,
                       legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#94A3B8")))
    st.plotly_chart(fig3, use_container_width=True)

with col_hist:
    section_header("📉", "Latency Distribution")
    ms_vals = [r["response_time_ms"] for r in logs]
    fig4 = go.Figure(go.Histogram(
        x=ms_vals, nbinsx=20,
        marker_color="#7C3AED", opacity=0.85,
    ))
    fig4.update_layout(**_PLOTLY_LAYOUT, height=240,
                       xaxis=dict(**_PLOTLY_LAYOUT["xaxis"], title="ms"),
                       yaxis=dict(**_PLOTLY_LAYOUT["yaxis"], title="Count"))
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

# ── FULL LOG TABLE ────────────────────────────────────────────────────────────
with st.expander("📋  Full Activity Log", expanded=False):
    section_header("📋", "Raw Log", f"{total} entries")
    for r in sorted(logs, key=lambda x: x.get("timestamp",""), reverse=True)[:50]:
        ms    = r.get("response_time_ms", 0)
        color = "#10B981" if ms < 50 else "#F59E0B" if ms < 200 else "#EF4444"
        st.markdown(
            f"""
            <div style="
                background:rgba(13,17,28,.7);border:1px solid rgba(37,99,235,.08);
                border-radius:10px;padding:.6rem 1rem;margin-bottom:.3rem;
                display:flex;justify-content:space-between;align-items:center;font-family:'JetBrains Mono',monospace
            ">
                <div style="flex:1;min-width:0">
                    <span style="font-size:.72rem;color:{color};font-weight:700;margin-right:.75rem">
                        {r.get('method','')}</span>
                    <span style="font-size:.78rem;color:#94A3B8;
                                 white-space:nowrap;overflow:hidden;text-overflow:ellipsis">
                        {r.get('endpoint','')}</span>
                </div>
                <div style="text-align:right;margin-left:1rem;flex-shrink:0">
                    <span style="font-size:.8rem;font-weight:600;color:{color}">{ms:.1f} ms</span>
                    <div style="font-size:.65rem;color:#475569">{r.get('timestamp','')[:19]}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
