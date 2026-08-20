"""
Digital Twin AI — Login & Registration
"""
import os
import sys

import streamlit as st

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from components.theme import inject_theme
from components.ui import bootstrap_session
from utils.api_client import APIClient

st.set_page_config(
    page_title="Sign In · Digital Twin AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_theme()
bootstrap_session()

if st.session_state.get("token"):
    st.switch_page("app.py")

# ── FULL PAGE LAYOUT ──────────────────────────────────────────────────────────
left, center, right = st.columns([1, 1.4, 1])

with center:
    # Hero logo
    st.markdown(
        """
        <div class="login-container">
            <div class="login-logo">
                <span class="ll-icon">🧠</span>
                <div class="ll-title">Digital Twin AI</div>
                <div class="ll-sub">Your intelligent personal command center</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    tab_login, tab_register = st.tabs(["  Sign In  ", "  Create Account  "])

    # ── LOGIN ─────────────────────────────────────────────────────────────────
    with tab_login:
        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
        with st.form("login_form"):
            email    = st.text_input("Email Address", placeholder="you@example.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Sign In →", use_container_width=True)

        if submitted:
            if not email.strip() or not password:
                st.error("Please enter your email and password.")
            else:
                with st.spinner("Authenticating…"):
                    try:
                        response = st.session_state.api_client.post_form(
                            "/api/auth/login",
                            data={"username": email.strip(), "password": password},
                        )
                        st.session_state.token = response.get("access_token")
                        profile = st.session_state.api_client.get(
                            "/api/users/profile",
                            token=st.session_state.token,
                        )
                        st.session_state.user = profile
                        st.success(f"Welcome back, {profile.get('name','').split()[0]}!")
                        st.rerun()
                    except Exception as exc:
                        detail = "Incorrect email or password."
                        try:
                            body = exc.response.json()  # type: ignore[attr-defined]
                            if isinstance(body.get("detail"), str):
                                detail = body["detail"]
                        except Exception:
                            pass
                        st.error(detail)

    # ── REGISTER ─────────────────────────────────────────────────────────────
    with tab_register:
        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
        with st.form("register_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name", placeholder="Bhavesh Sharma")
            with col2:
                age  = st.number_input("Age", min_value=13, max_value=100, value=25)
            reg_email    = st.text_input("Email Address", placeholder="you@example.com")
            reg_password = st.text_input(
                "Password (min 8 characters)", type="password", placeholder="••••••••"
            )
            occupation   = st.text_input("Occupation", placeholder="Student / Engineer / Designer…")
            submitted_reg = st.form_submit_button("Create Account →", use_container_width=True)

        if submitted_reg:
            errors = []
            if not name.strip():        errors.append("Full name is required.")
            if not reg_email.strip():   errors.append("Email is required.")
            if len(reg_password) < 8:   errors.append("Password must be at least 8 characters.")
            if not occupation.strip():  errors.append("Occupation is required.")

            if errors:
                for e in errors:
                    st.error(e)
            else:
                with st.spinner("Creating your Digital Twin…"):
                    try:
                        st.session_state.api_client.post(
                            "/api/auth/register",
                            payload={
                                "name":       name.strip(),
                                "email":      reg_email.strip(),
                                "password":   reg_password,
                                "age":        int(age),
                                "occupation": occupation.strip(),
                            },
                        )
                        st.success("Account created! Switch to Sign In to log in.")
                    except Exception as exc:
                        detail = "Registration failed."
                        try:
                            body = exc.response.json()  # type: ignore[attr-defined]
                            msgs = [d.get("msg", "") for d in body.get("detail", [])]
                            if msgs:
                                detail = "; ".join(msgs)
                            elif isinstance(body.get("detail"), str):
                                detail = body["detail"]
                        except Exception:
                            pass
                        st.error(detail)

    st.markdown("</div>", unsafe_allow_html=True)

    # bottom tagline
    st.markdown(
        """
        <div style="text-align:center;margin-top:1.5rem;font-size:.75rem;color:#334155">
            Powered by AI · Your data stays private · Built for high performers
        </div>
        """,
        unsafe_allow_html=True,
    )
