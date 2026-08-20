"""Digital Twin AI - Finance"""
import os, sys
from collections import defaultdict
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from components.theme import inject_theme
from components.ui import (
    badge, bootstrap_session, empty_state, metric_row,
    page_header, render_sidebar, require_auth, section_header,
)

st.set_page_config(page_title="Finance - Digital Twin AI", page_icon="💰",
                   layout="wide", initial_sidebar_state="expanded")
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
_C = ["#2563EB","#7C3AED","#10B981","#F59E0B","#EF4444","#06B6D4","#EC4899","#14B8A6"]


@st.cache_data(ttl=30, show_spinner=False)
def load_finance(tok):
    try:
        records = client.get("/api/financial/records", token=tok) or []
        summary = client.get("/api/financial/summary", token=tok) or {}
    except Exception:
        records, summary = [], {}
    return records, summary


records, summary = load_finance(token)
page_header("Finance", "Track income, expenses, and your net savings")

# KPIs
monthly_trend = summary.get("monthly_trend", 0)
metric_row([
    dict(icon="💚", label="Total Income", value=f"${summary.get('total_income',0):,.0f}",
         sub="All time", trend_up=True, accent="linear-gradient(90deg,#10B981,#059669)"),
    dict(icon="🔴", label="Total Expenses", value=f"${summary.get('total_expenses',0):,.0f}",
         sub="All time", trend_up=False, accent="linear-gradient(90deg,#EF4444,#DC2626)"),
    dict(icon="💰", label="Net Savings", value=f"${summary.get('net_savings',0):,.0f}",
         sub="Income minus Expenses", trend_up=summary.get("net_savings",0) >= 0,
         accent="linear-gradient(90deg,#06B6D4,#0284C7)"),
    dict(icon="📈", label="Monthly Trend", value=f"${monthly_trend:,.0f}",
         sub="Current month net", trend_up=monthly_trend >= 0,
         accent="linear-gradient(90deg,#8B5CF6,#7C3AED)"),
    dict(icon="📋", label="Total Records", value=str(len(records)),
         sub="Logged entries", accent="linear-gradient(90deg,#F59E0B,#D97706)"),
])
st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

# ── CHART ROW 1: line chart + expense donut ───────────────────────────────────
if records:
    c1, c2 = st.columns([1.6, 1], gap="large")
    with c1:
        section_header("📈", "Income vs Expenses Over Time")
        inc_s = sorted([r for r in records if r["record_type"] == "income"],  key=lambda x: x["date"])
        exp_s = sorted([r for r in records if r["record_type"] == "expense"], key=lambda x: x["date"])
        fig = go.Figure()
        if inc_s:
            fig.add_trace(go.Scatter(
                x=[r["date"][:10] for r in inc_s], y=[r["amount"] for r in inc_s],
                mode="lines+markers", name="Income",
                line=dict(color="#10B981", width=2), marker=dict(size=5, color="#10B981"),
                fill="tozeroy", fillcolor="rgba(16,185,129,.07)",
            ))
        if exp_s:
            fig.add_trace(go.Scatter(
                x=[r["date"][:10] for r in exp_s], y=[r["amount"] for r in exp_s],
                mode="lines+markers", name="Expenses",
                line=dict(color="#EF4444", width=2), marker=dict(size=5, color="#EF4444"),
                fill="tozeroy", fillcolor="rgba(239,68,68,.07)",
            ))
        fig.update_layout(**_PL, height=260)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        section_header("🍕", "Spending by Category")
        exp_recs = [r for r in records if r["record_type"] == "expense"]
        if exp_recs:
            cats = defaultdict(float)
            for r in exp_recs:
                cats[r["category"]] += r["amount"]
            fig2 = go.Figure(go.Pie(
                labels=list(cats.keys()), values=list(cats.values()),
                hole=0.55, marker=dict(colors=_C),
                textfont=dict(color="#E2E8F0", size=11),
            ))
            fig2.update_layout(**_PL, height=260, showlegend=True,
                               legend=dict(orientation="v", x=1.05, y=0.5))
            st.plotly_chart(fig2, use_container_width=True)
        else:
            empty_state("🍕", "No expense records yet")

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # ── CHART ROW 2: monthly bar + income donut ───────────────────────────────
    c3, c4 = st.columns([1.6, 1], gap="large")
    with c3:
        section_header("📊", "Monthly Income vs Expenses")
        m_inc, m_exp = defaultdict(float), defaultdict(float)
        for r in records:
            try:
                mo = r["date"][:7]
            except Exception:
                continue
            if r["record_type"] == "income":
                m_inc[mo] += r["amount"]
            else:
                m_exp[mo] += r["amount"]
        months = sorted(set(list(m_inc.keys()) + list(m_exp.keys())))
        if months:
            fig3 = go.Figure()
            fig3.add_trace(go.Bar(x=months, y=[m_inc.get(m, 0) for m in months],
                                  name="Income", marker_color="#10B981", opacity=0.85))
            fig3.add_trace(go.Bar(x=months, y=[m_exp.get(m, 0) for m in months],
                                  name="Expenses", marker_color="#EF4444", opacity=0.85))
            fig3.update_layout(**_PL, height=260, barmode="group")
            st.plotly_chart(fig3, use_container_width=True)

    with c4:
        section_header("💚", "Income by Category")
        inc_recs = [r for r in records if r["record_type"] == "income"]
        if inc_recs:
            inc_cats = defaultdict(float)
            for r in inc_recs:
                inc_cats[r["category"]] += r["amount"]
            fig4 = go.Figure(go.Pie(
                labels=list(inc_cats.keys()), values=list(inc_cats.values()),
                hole=0.55, marker=dict(colors=_C),
                textfont=dict(color="#E2E8F0", size=11),
            ))
            fig4.update_layout(**_PL, height=260, showlegend=True,
                               legend=dict(orientation="v", x=1.05, y=0.5))
            st.plotly_chart(fig4, use_container_width=True)
        else:
            empty_state("💚", "No income records yet")

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # ── CHART ROW 3: recurring frequency bar ─────────────────────────────────
    section_header("🔄", "Recurring Frequency Breakdown")
    freq = defaultdict(float)
    for r in records:
        freq[r.get("recurring_frequency", "unknown")] += r["amount"]
    if freq:
        fig5 = go.Figure(go.Bar(
            x=list(freq.keys()), y=list(freq.values()),
            marker=dict(color=_C[:len(freq)], opacity=0.85),
            text=[f"${v:,.0f}" for v in freq.values()],
            textposition="outside", textfont=dict(color="#94A3B8", size=11),
        ))
        fig5.update_layout(**_PL, height=220)
        st.plotly_chart(fig5, use_container_width=True)

st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

# ── FILTER BAR ────────────────────────────────────────────────────────────────
section_header("🔍", "Filter and Manage Records")
fc1, fc2, fc3, fc4 = st.columns([1, 1, 1, 1], gap="small")
with fc1:
    filter_type = st.selectbox("Type", ["All", "income", "expense"], key="f_type")
with fc2:
    all_cats = sorted({r.get("category", "") for r in records if r.get("category")})
    filter_cat = st.selectbox("Category", ["All"] + all_cats, key="f_cat")
with fc3:
    filter_desc = st.text_input("Search description", placeholder="keyword...", key="f_desc")
with fc4:
    st.markdown("<div style='height:1.65rem'></div>", unsafe_allow_html=True)
    if st.button("Clear Filters", use_container_width=True):
        for k in ("f_type", "f_cat", "f_desc"):
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()

filtered = list(records)
if filter_type != "All":
    filtered = [r for r in filtered if r["record_type"] == filter_type]
if filter_cat != "All":
    filtered = [r for r in filtered if r.get("category") == filter_cat]
if filter_desc.strip():
    kw = filter_desc.strip().lower()
    filtered = [r for r in filtered if kw in r.get("description", "").lower()]

st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

# ── CSV EXPORT ────────────────────────────────────────────────────────────────
if filtered:
    rows_ex = [{"ID": r["id"], "Type": r["record_type"], "Amount": r["amount"],
                "Description": r.get("description",""), "Category": r.get("category",""),
                "Date": r["date"][:10] if r.get("date") else "",
                "Frequency": r.get("recurring_frequency",""),
                "Goal Impact": r.get("goal_impact") or ""} for r in filtered]
    csv_bytes = pd.DataFrame(rows_ex).to_csv(index=False).encode("utf-8")
    st.download_button(
        label=f"Export {len(filtered)} records to CSV",
        data=csv_bytes,
        file_name=f"finance_{datetime.today().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )

st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)

# ── EDIT / DELETE SESSION STATE ───────────────────────────────────────────────
if "edit_rec_id" not in st.session_state:
    st.session_state.edit_rec_id = None
if "del_confirm_id" not in st.session_state:
    st.session_state.del_confirm_id = None

# ── ADD / EDIT FORM  +  RECORDS TABLE ────────────────────────────────────────
col_form, col_table = st.columns([1, 1.6], gap="large")

with col_form:
    editing  = st.session_state.edit_rec_id is not None
    edit_rec = next((r for r in records if r["id"] == st.session_state.edit_rec_id), None) if editing else None

    if editing and edit_rec:
        section_header("✏️", "Edit Record", f"ID #{edit_rec['id']}")
        if st.button("Cancel Edit"):
            st.session_state.edit_rec_id = None
            st.rerun()
    else:
        section_header("➕", "Add Record", "Log a new income or expense")

    with st.form(f"fin_form_{st.session_state.edit_rec_id or 'new'}"):
        def_type = edit_rec["record_type"] if edit_rec else "income"
        record_type = st.selectbox("Type", ["income", "expense"],
                                   index=0 if def_type == "income" else 1)
        amount = st.number_input("Amount ($)", min_value=0.01, format="%.2f",
                                 value=float(edit_rec["amount"]) if edit_rec else 0.01)
        description = st.text_input("Description",
                                    value=edit_rec.get("description", "") if edit_rec else "",
                                    placeholder="Salary, Rent, Groceries...")
        try:
            def_date = datetime.fromisoformat(edit_rec["date"][:10]).date() if edit_rec else datetime.today().date()
        except Exception:
            def_date = datetime.today().date()
        date = st.date_input("Date", value=def_date)
        category = st.text_input("Category",
                                 value=edit_rec.get("category", "") if edit_rec else "",
                                 placeholder="Food, Transport, Housing...")
        rec_freq = st.text_input("Recurring Frequency",
                                 value=edit_rec.get("recurring_frequency", "") if edit_rec else "",
                                 placeholder="monthly, weekly, once")
        goal_impact = st.text_input("Goal Impact (optional)",
                                    value=edit_rec.get("goal_impact") or "" if edit_rec else "",
                                    placeholder="Emergency fund, Holiday savings...")
        submitted = st.form_submit_button(
            "Save Changes" if editing else "Add Record",
            use_container_width=True,
        )

    if submitted:
        errs = []
        if not description.strip(): errs.append("Description is required.")
        if not category.strip():    errs.append("Category is required.")
        if not rec_freq.strip():    errs.append("Recurring frequency is required.")
        if errs:
            for e in errs:
                st.error(e)
        else:
            payload = {
                "record_type":         record_type,
                "amount":              float(amount),
                "description":         description.strip(),
                "date":                datetime.combine(date, datetime.min.time()).isoformat(),
                "category":            category.strip(),
                "recurring_frequency": rec_freq.strip(),
                "goal_impact":         goal_impact.strip() or None,
            }
            try:
                if editing and edit_rec:
                    client.put(f"/api/financial/records/{edit_rec['id']}",
                               payload=payload, token=token)
                    st.success("Record updated.")
                    st.session_state.edit_rec_id = None
                else:
                    client.post("/api/financial/records", payload=payload, token=token)
                    st.success("Record added.")
                st.cache_data.clear()
                st.rerun()
            except Exception:
                st.error("Failed to save. Please try again.")

with col_table:
    PAGE_SIZE   = 15
    total       = len(filtered)
    total_pages = max(1, -(-total // PAGE_SIZE))

    if "fin_page" not in st.session_state:
        st.session_state.fin_page = 1
    st.session_state.fin_page = min(st.session_state.fin_page, total_pages)

    section_header(
        "📋", "Records",
        f"Showing {min(PAGE_SIZE * st.session_state.fin_page, total)} of {total}  |  "
        f"Page {st.session_state.fin_page} of {total_pages}",
    )

    if filtered:
        start        = (st.session_state.fin_page - 1) * PAGE_SIZE
        page_records = filtered[start: start + PAGE_SIZE]

        for r in page_records:
            rc   = "#10B981" if r["record_type"] == "income" else "#EF4444"
            sign = "+" if r["record_type"] == "income" else "-"
            ds   = r["date"][:10] if r.get("date") else ""
            gtag = f" · Goal: {r['goal_impact']}" if r.get("goal_impact") else ""

            st.markdown(
                '<div style="background:rgba(13,17,28,.8);border:1px solid rgba(37,99,235,.1);'
                'border-radius:12px;padding:.8rem 1.1rem;margin-bottom:.3rem;">'
                '<div style="display:flex;justify-content:space-between;align-items:center;">'
                '<div style="flex:1;min-width:0;">'
                f'<div style="font-size:.85rem;font-weight:600;color:#E2E8F0;white-space:nowrap;'
                f'overflow:hidden;text-overflow:ellipsis;">{r.get("description","")}</div>'
                f'<div style="font-size:.72rem;color:#64748B;margin-top:.15rem;">'
                f'{r.get("category","")} · {ds} · {r.get("recurring_frequency","")}{gtag}</div>'
                '</div>'
                '<div style="text-align:right;margin-left:1rem;flex-shrink:0;">'
                f'<div style="font-size:1rem;font-weight:700;color:{rc};">{sign}${r.get("amount",0):,.2f}</div>'
                + badge(r.get("record_type", ""))
                + '</div></div></div>',
                unsafe_allow_html=True,
            )

            b1, b2 = st.columns(2, gap="small")
            with b1:
                if st.button("Edit", key=f"e_{r['id']}", use_container_width=True):
                    st.session_state.edit_rec_id    = r["id"]
                    st.session_state.del_confirm_id = None
                    st.rerun()
            with b2:
                if st.session_state.del_confirm_id == r["id"]:
                    st.warning(f"Delete '{r.get('description','')}'?")
                    y_col, n_col = st.columns(2)
                    with y_col:
                        if st.button("Yes, delete", key=f"dy_{r['id']}", use_container_width=True):
                            try:
                                client.delete(f"/api/financial/records/{r['id']}", token=token)
                                st.success("Deleted.")
                                st.session_state.del_confirm_id = None
                                st.cache_data.clear()
                                st.rerun()
                            except Exception:
                                st.error("Delete failed.")
                    with n_col:
                        if st.button("Cancel", key=f"dn_{r['id']}", use_container_width=True):
                            st.session_state.del_confirm_id = None
                            st.rerun()
                else:
                    if st.button("Delete", key=f"d_{r['id']}", use_container_width=True):
                        st.session_state.del_confirm_id = r["id"]
                        st.rerun()

            st.markdown("<div style='height:.15rem'></div>", unsafe_allow_html=True)

        # pagination controls
        if total_pages > 1:
            st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
            p1, p2, p3 = st.columns([1, 2, 1])
            with p1:
                if st.button("Prev", disabled=st.session_state.fin_page <= 1,
                             use_container_width=True, key="fp"):
                    st.session_state.fin_page -= 1
                    st.rerun()
            with p2:
                st.markdown(
                    f'<div style="text-align:center;color:#64748B;font-size:.8rem;padding-top:.4rem;">'
                    f'Page {st.session_state.fin_page} of {total_pages}</div>',
                    unsafe_allow_html=True,
                )
            with p3:
                if st.button("Next", disabled=st.session_state.fin_page >= total_pages,
                             use_container_width=True, key="fn"):
                    st.session_state.fin_page += 1
                    st.rerun()
    else:
        empty_state("💰", "No matching records", "Try adjusting your filters.")
