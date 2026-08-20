"""
Digital Twin AI — Profile
"""
import os, sys
import streamlit as st

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from components.theme import inject_theme
from components.ui import (
    bootstrap_session, require_auth, render_sidebar,
    page_header, section_header, metric_row, empty_state,
)

st.set_page_config(page_title="Profile · Digital Twin AI", page_icon="👤", layout="wide", initial_sidebar_state="expanded")
inject_theme()
bootstrap_session()
render_sidebar()
require_auth()

client = st.session_state.api_client
token  = st.session_state.token

@st.cache_data(ttl=30, show_spinner=False)
def load_profile(tok):
    try:
        profile = client.get("/api/users/profile", token=tok)
        summary = client.get("/api/users/summary",  token=tok)
        return profile, summary
    except Exception:
        return {}, {}

profile, summary = load_profile(token)
name       = profile.get("name", "User")
email      = profile.get("email", "")
age        = profile.get("age", 0)
occupation = profile.get("occupation", "")
initials   = "".join(p[0].upper() for p in name.split()[:2])

page_header("My Profile", "Manage your identity and view your summary stats")

# ── HERO PROFILE CARD ─────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style="
        background:linear-gradient(135deg,rgba(13,17,28,.98),rgba(20,27,50,.98));
        border:1px solid rgba(37,99,235,.2);border-radius:20px;
        padding:2rem;margin-bottom:1.5rem;
        display:flex;align-items:center;gap:2rem;position:relative;overflow:hidden
    ">
        <div style="
            position:absolute;top:-40px;right:-40px;width:180px;height:180px;
            background:radial-gradient(circle,rgba(37,99,235,.08) 0%,transparent 70%);
            pointer-events:none
        "></div>
        <div style="
            width:80px;height:80px;flex-shrink:0;
            background:linear-gradient(135deg,#2563EB,#7C3AED);
            border-radius:50%;display:flex;align-items:center;justify-content:center;
            font-size:1.75rem;font-weight:800;color:#fff;
            box-shadow:0 0 30px rgba(37,99,235,.35)
        ">{initials}</div>
        <div style="flex:1;min-width:0">
            <div style="font-size:1.5rem;font-weight:800;color:#F1F5F9;letter-spacing:-.02em">{name}</div>
            <div style="font-size:.875rem;color:#64748B;margin-top:.2rem">{email}</div>
            <div style="display:flex;gap:.75rem;margin-top:.6rem;flex-wrap:wrap">
                <span class="badge badge-blue">{occupation}</span>
                <span class="badge badge-purple">Age {age}</span>
                <span class="badge badge-green">Active</span>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── SUMMARY KPIs ──────────────────────────────────────────────────────────────
metric_row([
    dict(icon="📁", label="Financial Records",
         value=str(summary.get("financial_record_count", 0)),
         sub="All time", accent="linear-gradient(90deg,#06B6D4,#0284C7)"),
    dict(icon="🎯", label="Active Goals",
         value=str(summary.get("active_goals", 0)),
         sub="In progress", accent="linear-gradient(90deg,#10B981,#059669)"),
    dict(icon="🔥", label="Habit Streak",
         value=str(summary.get("habit_streak", 0)),
         sub="Days", accent="linear-gradient(90deg,#F59E0B,#EF4444)"),
])

st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

# ── EDIT FORM ─────────────────────────────────────────────────────────────────
col_form, col_info = st.columns([1.2, 1], gap="large")

with col_form:
    section_header("✏️", "Edit Profile", "Update your personal details")
    with st.form("profile_form"):
        new_name       = st.text_input("Full Name",   value=name)
        new_age        = st.number_input("Age", min_value=13, max_value=100, value=int(age))
        new_occupation = st.text_input("Occupation",  value=occupation)
        save = st.form_submit_button("Save Changes", use_container_width=True)

    if save:
        if not new_name.strip():
            st.error("Name cannot be empty.")
        else:
            try:
                updated = client.put(
                    "/api/users/profile",
                    payload={"name": new_name.strip(),
                             "age": int(new_age),
                             "occupation": new_occupation.strip()},
                    token=token,
                )
                st.session_state.user = updated
                st.cache_data.clear()
                st.success("Profile updated successfully.")
                st.rerun()
            except Exception:
                st.error("Failed to update profile. Please try again.")

with col_info:
    section_header("🔒", "Account Security", "Your credentials and status")
    st.markdown(
        f"""
        <div style="background:rgba(13,17,28,.8);border:1px solid rgba(37,99,235,.15);
                    border-radius:16px;padding:1.5rem;display:flex;flex-direction:column;gap:1rem">
            <div>
                <div style="font-size:.7rem;font-weight:700;color:#64748B;
                            text-transform:uppercase;letter-spacing:.08em;margin-bottom:.3rem">Email</div>
                <div style="font-size:.9rem;color:#E2E8F0;font-family:'JetBrains Mono',monospace">{email}</div>
            </div>
            <div>
                <div style="font-size:.7rem;font-weight:700;color:#64748B;
                            text-transform:uppercase;letter-spacing:.08em;margin-bottom:.3rem">Account Status</div>
                <span class="badge badge-green">Active</span>
            </div>
            <div>
                <div style="font-size:.7rem;font-weight:700;color:#64748B;
                            text-transform:uppercase;letter-spacing:.08em;margin-bottom:.3rem">Occupation</div>
                <div style="font-size:.9rem;color:#E2E8F0">{occupation}</div>
            </div>
            <div>
                <div style="font-size:.7rem;font-weight:700;color:#64748B;
                            text-transform:uppercase;letter-spacing:.08em;margin-bottom:.3rem">Age</div>
                <div style="font-size:.9rem;color:#E2E8F0">{age} years old</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
