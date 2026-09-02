"""
backend/app/services/report_service.py

Milestone 4 — PDF Report Generation using fpdf2.

Generates personalised reports with real user data:
  - Financial summary
  - Savings projections
  - Goals
  - Study & productivity
  - Top recommendations

Returns bytes (in-memory PDF) ready for HTTP response.
"""
from __future__ import annotations

import logging
import sys
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_BACKEND = Path(__file__).resolve().parents[2]
_ROOT    = _BACKEND.parent
for _p in [str(_ROOT), str(_BACKEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _load_user_data(user_id: int) -> dict[str, Any]:
    """Gather all data needed for the report from existing services."""
    from app.services.digital_twin_service import (
        get_current_twin, generate_recommendations, generate_risk_analysis,
    )
    from app.services.forecasting_service import generate_savings_projection
    from app.core.database import SessionLocal
    from app.models.user import User

    data: dict[str, Any] = {}

    # Profile
    try:
        db = SessionLocal()
        u  = db.query(User).filter(User.id == user_id).first()
        if u:
            data["profile"] = {
                "name": u.name, "age": u.age, "email": u.email,
                "occupation": u.occupation,
            }
        db.close()
    except Exception as exc:
        logger.warning("report profile error: %s", exc)

    # Twin state
    try:
        state = get_current_twin(user_id)
        data["twin"]      = state
        data["financial"] = state.get("financial", {})
        data["study"]     = state.get("study", {})
        data["habits"]    = state.get("habits", {})
        data["fitness"]   = state.get("fitness", {})
        data["goals"]     = state.get("goals", [])
        data["productivity_score"] = state.get("productivity_score", 0)
    except Exception as exc:
        logger.warning("report twin error: %s", exc)

    # Recommendations
    try:
        recs_data    = generate_recommendations(user_id)
        data["recommendations"] = recs_data.get("recommendations", [])[:5]
    except Exception as exc:
        logger.warning("report recs error: %s", exc)

    # Risk
    try:
        data["risk"] = generate_risk_analysis(user_id)
    except Exception as exc:
        logger.warning("report risk error: %s", exc)

    # Savings forecast
    try:
        data["savings_forecast"] = generate_savings_projection(user_id, 12)
    except Exception as exc:
        logger.warning("report forecast error: %s", exc)

    return data


def generate_pdf_report(user_id: int, report_type: str = "full") -> bytes:
    """
    Generate a PDF report and return its bytes.

    Args:
        user_id:     Authenticated user ID.
        report_type: "full" | "financial" | "goals" | "study" | "recommendations"

    Returns:
        bytes — PDF file content.
    """
    try:
        from fpdf import FPDF
        from fpdf.enums import XPos, YPos
        _NL  = {"new_x": XPos.LMARGIN, "new_y": YPos.NEXT}   # replaces ln=True
        _CONT = {"new_x": XPos.RIGHT,  "new_y": YPos.TOP}    # replaces ln=False
    except ImportError:
        raise RuntimeError("fpdf2 is not installed. Run: pip install fpdf2")

    data = _load_user_data(user_id)
    profile   = data.get("profile", {})
    financial = data.get("financial", {})
    study     = data.get("study", {})
    habits    = data.get("habits", {})
    fitness   = data.get("fitness", {})
    goals     = data.get("goals", [])
    recs      = data.get("recommendations", [])
    risk      = data.get("risk", {})
    savings_fc = data.get("savings_forecast", [])
    prod_score = data.get("productivity_score", 0)

    name       = profile.get("name", "User")
    occupation = profile.get("occupation", "")
    generated  = datetime.utcnow().strftime("%d %B %Y at %H:%M UTC")

    # ── PDF setup ──────────────────────────────────────────────────────────────
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # ── helper functions ───────────────────────────────────────────────────────
    BLUE  = (37, 99, 235)
    DARK  = (15, 23, 42)
    GRAY  = (100, 116, 139)
    GREEN = (16, 185, 129)
    RED   = (239, 68, 68)
    AMBER = (245, 158, 11)
    WHITE = (255, 255, 255)

    def _pdf_text(value):
        """Keep dynamic content compatible with the built-in Helvetica font."""
        return str(value).encode("latin-1", "replace").decode("latin-1")

    def h1(text):
        pdf.set_font("Helvetica", "B", 22)
        pdf.set_text_color(*BLUE)
        pdf.cell(0, 12, _pdf_text(text), **_NL)
        pdf.ln(2)

    def h2(text):
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(*DARK)
        x, y = pdf.get_x(), pdf.get_y()
        pdf.set_fill_color(*BLUE)
        pdf.rect(x, y + 1, 3, 8, "F")
        pdf.set_x(x + 5)
        pdf.cell(0, 10, _pdf_text(text), **_NL)
        pdf.ln(1)

    def body(text):
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*GRAY)
        pdf.multi_cell(0, 6, _pdf_text(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(1)

    def kv(key, value, highlight=False):
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*DARK)
        pdf.cell(68, 7, _pdf_text(key) + ":", **_CONT)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*GREEN if highlight else DARK)
        pdf.cell(0, 7, _pdf_text(value), **_NL)

    def divider():
        pdf.set_draw_color(*BLUE)
        pdf.set_line_width(0.3)
        pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 170, pdf.get_y())
        pdf.ln(4)

    def small_table(headers: list, rows: list):
        col_w = 170 // len(headers)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(37, 99, 235)
        pdf.set_text_color(*WHITE)
        for h in headers:
            pdf.cell(col_w, 7, _pdf_text(h), border=1, fill=True, align="C")
        pdf.ln()
        pdf.set_font("Helvetica", "", 9)
        for i, row in enumerate(rows):
            pdf.set_fill_color(240, 245, 255) if i % 2 == 0 else pdf.set_fill_color(*WHITE)
            pdf.set_text_color(*DARK)
            for cell in row:
                pdf.cell(col_w, 6, _pdf_text(cell)[:30], border=1, fill=True)
            pdf.ln()
        pdf.ln(3)

    # ══════════════════════════════════════════════════════════════════════════
    # COVER / HEADER
    # ══════════════════════════════════════════════════════════════════════════
    pdf.set_fill_color(37, 99, 235)
    pdf.rect(0, 0, 210, 40, "F")
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(*WHITE)
    pdf.set_xy(10, 10)
    pdf.cell(0, 10, "Digital Twin AI", **_NL)
    pdf.set_font("Helvetica", "", 12)
    pdf.set_xy(10, 22)
    pdf.cell(0, 8, "Personal Financial & Productivity Report", **_NL)
    pdf.ln(20)

    # User info block
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*DARK)
    pdf.cell(0, 9, f"Report for: {name}", **_NL)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*GRAY)
    pdf.cell(0, 6, f"Occupation: {occupation}  |  Generated: {generated}", **_NL)
    pdf.ln(4)
    divider()

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 1 — EXECUTIVE SUMMARY
    # ══════════════════════════════════════════════════════════════════════════
    h2("Executive Summary")
    kv("Overall Alignment Score", f"{prod_score:.0f} / 100")
    kv("Risk Level", risk.get("risk_level", "Unknown").upper(),
       highlight=risk.get("risk_level") == "low")
    kv("Risk Score",  f"{risk.get('overall_risk_score', 0):.0f} / 100")
    kv("Active Goals", str(sum(1 for g in goals if g.get("status","").lower() not in ("completed",))))
    kv("Completed Goals", str(sum(1 for g in goals if g.get("status","").lower() == "completed")))
    pdf.ln(2)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 2 — FINANCIAL SUMMARY
    # ══════════════════════════════════════════════════════════════════════════
    if report_type in ("full", "financial"):
        h2("Financial Summary")
        inc  = financial.get("total_income", 0)
        exp  = financial.get("total_expenses", 0)
        net  = financial.get("net_savings", 0)
        rate = financial.get("savings_rate", 0)
        mInc = financial.get("monthly_avg_income", 0)
        mExp = financial.get("monthly_avg_expenses", 0)
        top  = financial.get("top_expense_category", "N/A")

        kv("Total Income (all time)",    f"${inc:,.2f}")
        kv("Total Expenses (all time)",  f"${exp:,.2f}")
        kv("Net Savings",                f"${net:,.2f}", highlight=net > 0)
        kv("Savings Rate",               f"{rate*100:.1f}%",  highlight=rate >= 0.1)
        kv("Monthly Avg Income",         f"${mInc:,.2f}")
        kv("Monthly Avg Expenses",       f"${mExp:,.2f}")
        kv("Top Expense Category",       top)
        pdf.ln(3)

        # 12-month savings forecast table
        if savings_fc:
            h2("12-Month Savings Projection")
            body("Forecast generated by Prophet ML model trained on your transaction history.")
            fc_rows = [
                [f["date"], f"${f['predicted_savings']:,.0f}",
                 f"${f['lower_bound']:,.0f}", f"${f['upper_bound']:,.0f}"]
                for f in savings_fc[:12]
            ]
            small_table(["Date", "Projected", "Lower 80%", "Upper 80%"], fc_rows)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 3 — GOALS
    # ══════════════════════════════════════════════════════════════════════════
    if report_type in ("full", "goals") and goals:
        h2("Goal Achievement Forecast")
        g_rows = []
        for g in goals[:10]:
            target = g.get("target_value", 1)
            curr   = g.get("current_value", 0)
            pct    = min(curr / target * 100, 100) if target else 0
            days_r = g.get("days_remaining", 0)
            on_tr  = "Yes" if g.get("on_track") else "No"
            g_rows.append([
                g.get("name", "?")[:28],
                f"{pct:.0f}%",
                g.get("status", "?"),
                f"{days_r}d",
                on_tr,
            ])
        small_table(["Goal", "Progress", "Status", "Days Left", "On Track"], g_rows)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 4 — STUDY & PRODUCTIVITY
    # ══════════════════════════════════════════════════════════════════════════
    if report_type in ("full", "study"):
        h2("Study & Productivity")
        kv("Avg Study Hours / Session", f"{study.get('avg_study_hours', 0):.1f}h")
        kv("Avg Focus Score",           f"{study.get('avg_focus_score', 0):.0f}/100")
        kv("Avg Performance Score",     f"{study.get('avg_performance_score', 0):.0f}/100")
        kv("Total Sessions Logged",     str(study.get("total_sessions", 0)))
        kv("Habit Completion Rate",     f"{habits.get('completion_rate', 0)*100:.0f}%")
        kv("Best Streak",               f"{habits.get('best_streak', 0)} days")
        kv("Fitness Sessions / Week",   f"{fitness.get('sessions_per_week', 0):.1f}")
        kv("Avg Calories / Session",    f"{fitness.get('avg_calories', 0):.0f} kcal")
        pdf.ln(3)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 5 — RECOMMENDATIONS
    # ══════════════════════════════════════════════════════════════════════════
    if report_type in ("full", "recommendations") and recs:
        h2("Personalised Recommendations")
        for i, r in enumerate(recs[:5], 1):
            pri   = r.get("priority", "low").upper()
            dom   = r.get("domain", "").upper()
            title = r.get("title", "")
            desc  = r.get("description", "")[:200]
            steps = r.get("action_steps", [])

            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*DARK)
            pdf.cell(0, 7, _pdf_text(f"{i}. [{dom} | {pri}] {title}"), **_NL)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*GRAY)
            pdf.multi_cell(0, 5.5, _pdf_text(desc), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            if steps:
                pdf.set_font("Helvetica", "I", 9)
                pdf.multi_cell(0, 5.5, _pdf_text("Action: " + str(steps[0])), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(2)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 6 — RISK ANALYSIS
    # ══════════════════════════════════════════════════════════════════════════
    if report_type == "full":
        risk_factors = risk.get("risk_factors", [])
        if risk_factors:
            h2("Risk Analysis")
            for f in risk_factors[:6]:
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(*RED if f.get("severity") in ("high","critical") else AMBER)
                sev = f.get("severity", "").upper()
                dom = f.get("domain", "").upper()
                pdf.cell(0, 7, _pdf_text(f"[{dom} | {sev}] {f.get('description', '')}"), **_NL)
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(*GRAY)
                pdf.multi_cell(0, 5.5, _pdf_text("Mitigation: " + str(f.get("mitigation", ""))), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.ln(1)

    # ══════════════════════════════════════════════════════════════════════════
    # FOOTER
    # ══════════════════════════════════════════════════════════════════════════
    pdf.set_y(-18)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*GRAY)
    pdf.cell(0, 6,
             f"Digital Twin AI · Confidential · Generated {generated} · "
             f"This report is for informational purposes only.",
             align="C", **_NL)

    # Return bytes
    return bytes(pdf.output())
