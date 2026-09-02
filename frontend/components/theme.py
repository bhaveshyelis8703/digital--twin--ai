"""
Shared CSS theme for Digital Twin AI  v3.0
Layout: slim icon-rail sidebar (64px default, 220px on hover) + top navigation bar.
Supports Dark (default) and Light mode.
"""
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# SHARED CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
_FONT = "@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');"
_RAIL = "64px"
_RAIL_OPEN = "220px"
_TOPBAR_H = "56px"

def _build_css(dark: bool) -> str:
    # ── token sets ────────────────────────────────────────────────────────────
    if dark:
        bg_base       = "#05070D"
        bg_surface    = "#0C0F1A"
        bg_card       = "rgba(11,15,26,0.96)"
        bg_sidebar    = "linear-gradient(180deg,#06080F 0%,#080B18 100%)"
        bg_topbar     = "rgba(6,8,15,0.95)"
        border        = "rgba(37,99,235,0.14)"
        border_hover  = "rgba(37,99,235,0.42)"
        accent        = "#2563EB"
        accent_glow   = "rgba(37,99,235,0.22)"
        accent_light  = "#60A5FA"
        text_primary  = "#F1F5F9"
        text_secondary= "#CBD5E1"
        text_muted    = "#64748B"
        text_label    = "#94A3B8"
        input_bg      = "rgba(8,11,18,0.92)"
        shadow_card   = "0 4px 24px rgba(0,0,0,0.4)"
        shadow_hover  = "0 12px 40px rgba(37,99,235,0.18)"
        card_grad     = "linear-gradient(145deg,rgba(10,14,24,0.97),rgba(13,18,34,0.97))"
        page_hdr_grad = "linear-gradient(135deg,rgba(8,11,20,0.99),rgba(14,19,42,0.99))"
        insight_bg    = "rgba(10,13,22,0.92)"
        progress_track= "rgba(30,41,59,0.75)"
        tab_list_bg   = "rgba(8,11,20,.7)"
        expander_bg   = "rgba(10,13,22,.75)"
        df_th_bg      = "rgba(8,11,20,.92)"
        scrollbar_thumb="#1E3A5F"
        nav_icon_bg   = "rgba(37,99,235,0.08)"
        nav_active_bg = "linear-gradient(135deg,rgba(37,99,235,0.24),rgba(124,58,237,0.16))"
        login_bg      = "linear-gradient(135deg,rgba(8,11,20,.99),rgba(14,19,42,.99))"
        login_title   = "#60A5FA"
    else:
        bg_base       = "#F0F4FF"
        bg_surface    = "#FFFFFF"
        bg_card       = "rgba(255,255,255,0.97)"
        bg_sidebar    = "linear-gradient(180deg,#EBF0FF 0%,#E4ECFF 100%)"
        bg_topbar     = "rgba(255,255,255,0.95)"
        border        = "rgba(37,99,235,0.14)"
        border_hover  = "rgba(37,99,235,0.40)"
        accent        = "#2563EB"
        accent_glow   = "rgba(37,99,235,0.12)"
        accent_light  = "#1D4ED8"
        text_primary  = "#0F172A"
        text_secondary= "#1E293B"
        text_muted    = "#64748B"
        text_label    = "#475569"
        input_bg      = "rgba(248,250,255,0.95)"
        shadow_card   = "0 2px 16px rgba(37,99,235,0.07)"
        shadow_hover  = "0 8px 32px rgba(37,99,235,0.14)"
        card_grad     = "linear-gradient(145deg,#FFFFFF,#F8FAFF)"
        page_hdr_grad = "linear-gradient(135deg,#FFFFFF,#F0F5FF)"
        insight_bg    = "#FFFFFF"
        progress_track= "rgba(37,99,235,0.1)"
        tab_list_bg   = "rgba(235,240,255,0.9)"
        expander_bg   = "#FFFFFF"
        df_th_bg      = "#EEF3FF"
        scrollbar_thumb="#BFCFFF"
        nav_icon_bg   = "rgba(37,99,235,0.07)"
        nav_active_bg = "linear-gradient(135deg,rgba(37,99,235,0.15),rgba(124,58,237,0.10))"
        login_bg      = "linear-gradient(135deg,#FFFFFF,#F0F5FF)"
        login_title   = "#2563EB"

    return f"""<style>
{_FONT}

/* ═══════════════════════ BASE ═══════════════════════ */
:root {{
  --bg-base:{bg_base};--bg-surface:{bg_surface};--bg-card:{bg_card};
  --border:{border};--border-hover:{border_hover};
  --accent:{accent};--accent-glow:{accent_glow};--accent-light:{accent_light};
  --text-primary:{text_primary};--text-secondary:{text_secondary};
  --text-muted:{text_muted};--text-label:{text_label};
  --input-bg:{input_bg};--shadow-card:{shadow_card};--shadow-hover:{shadow_hover};
  --radius-card:16px;--radius-input:10px;--transition:all 0.22s ease;
  --rail:{_RAIL};--rail-open:{_RAIL_OPEN};--topbar:{_TOPBAR_H};
}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
html,body,[data-testid="stAppViewContainer"],[data-testid="stApp"]{{
  background:{bg_base}!important;font-family:'Inter',sans-serif!important;color:{text_primary}!important;
}}
#MainMenu,footer,header{{visibility:hidden!important;}}
[data-testid="stDecoration"]{{display:none!important;}}
.stDeployButton{{display:none!important;}}
::-webkit-scrollbar{{width:4px;height:4px;}}
::-webkit-scrollbar-track{{background:{bg_surface};}}
::-webkit-scrollbar-thumb{{background:{scrollbar_thumb};border-radius:4px;}}
::-webkit-scrollbar-thumb:hover{{background:{accent};}}

/* ═══════════════════════ SIDEBAR RAIL ═══════════════════════ */
/* Collapse the sidebar to a slim rail by default */
[data-testid="stSidebar"] {{
  background:{bg_sidebar}!important;
  border-right:1px solid {border}!important;
  min-width:{_RAIL}!important;
  max-width:{_RAIL}!important;
  width:{_RAIL}!important;
  overflow:hidden!important;
  transition:min-width .28s cubic-bezier(.4,0,.2,1),
             max-width .28s cubic-bezier(.4,0,.2,1),
             box-shadow .28s ease!important;
  box-shadow:2px 0 20px rgba(0,0,0,0.25)!important;
  z-index:100!important;
}}
[data-testid="stSidebar"]:hover {{
  min-width:{_RAIL_OPEN}!important;
  max-width:{_RAIL_OPEN}!important;
  box-shadow:4px 0 32px rgba(37,99,235,0.18)!important;
}}
[data-testid="stSidebar"]>div:first-child{{padding:0!important;}}

/* Hide the Streamlit collapse button — we use hover instead */
[data-testid="stSidebarCollapseButton"]{{display:none!important;}}
[data-testid="collapsedControl"]{{display:none!important;}}

/* Nav links: show only icon when collapsed, icon+label when expanded */
[data-testid="stSidebarNavLink"]{{
  color:{text_label}!important;
  border-radius:10px!important;
  margin:2px 6px!important;
  padding:10px 10px!important;
  transition:{_RAIL}!important;
  font-size:.875rem!important;
  font-weight:500!important;
  white-space:nowrap!important;
  overflow:hidden!important;
  display:flex!important;
  align-items:center!important;
  gap:.7rem!important;
  min-height:40px!important;
}}
[data-testid="stSidebarNavLink"] span:last-child{{
  opacity:0;transition:opacity .18s ease;
}}
[data-testid="stSidebar"]:hover [data-testid="stSidebarNavLink"] span:last-child{{
  opacity:1;
}}
[data-testid="stSidebarNavLink"]:hover{{
  background:{accent_glow}!important;color:{accent_light}!important;
}}
[data-testid="stSidebarNavLink"][aria-current="page"]{{
  background:{nav_active_bg}!important;
  color:{accent_light}!important;
  border-left:3px solid {accent}!important;
  font-weight:600!important;
}}

/* Page links inside sidebar (st.page_link) */
[data-testid="stSidebar"] a[data-testid="stPageLink"]{{
  color:{text_label}!important;
  border-radius:10px!important;
  margin:1px 6px!important;
  padding:9px 10px!important;
  font-size:.875rem!important;font-weight:500!important;
  white-space:nowrap!important;overflow:hidden!important;
  display:flex!important;align-items:center!important;gap:.7rem!important;
  transition:var(--transition)!important;
  min-height:38px!important;
}}
[data-testid="stSidebar"] a[data-testid="stPageLink"]:hover{{
  background:{accent_glow}!important;color:{accent_light}!important;
}}
[data-testid="stSidebar"] a[data-testid="stPageLink"][aria-current="page"]{{
  background:{nav_active_bg}!important;
  color:{accent_light}!important;
  border-left:3px solid {accent}!important;
  font-weight:600!important;
}}

/* ═══════════════════════ TOPBAR ═══════════════════════ */
.dt-topbar {{
  position:sticky;top:0;z-index:200;
  background:{bg_topbar};
  backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);
  border-bottom:1px solid {border};
  padding:.75rem 1.75rem;
  display:flex;align-items:center;justify-content:space-between;
  margin-bottom:1.5rem;
  box-shadow:0 2px 20px rgba(0,0,0,.12);
}}
.dt-topbar-left{{display:flex;align-items:center;gap:1rem;}}
.dt-topbar-brand{{
  display:flex;align-items:center;gap:.6rem;
  font-size:.95rem;font-weight:800;color:{text_primary};letter-spacing:-.02em;
}}
.dt-topbar-brand .tb-icon{{
  width:32px;height:32px;
  background:linear-gradient(135deg,#2563EB,#7C3AED);
  border-radius:8px;
  display:flex;align-items:center;justify-content:center;
  font-size:1rem;flex-shrink:0;
  box-shadow:0 2px 10px rgba(37,99,235,.35);
}}
.dt-topbar-divider{{width:1px;height:20px;background:{border};margin:0 .25rem;}}
.dt-topbar-page{{
  font-size:.82rem;font-weight:600;color:{text_muted};letter-spacing:.01em;
}}
.dt-topbar-right{{display:flex;align-items:center;gap:.75rem;}}
.dt-user-pill{{
  display:flex;align-items:center;gap:.5rem;
  background:{accent_glow};border:1px solid {border};
  border-radius:99px;padding:.3rem .75rem .3rem .3rem;
  cursor:default;
}}
.dt-user-avatar{{
  width:28px;height:28px;
  background:linear-gradient(135deg,#2563EB,#7C3AED);
  border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  font-size:.7rem;font-weight:700;color:#fff;flex-shrink:0;
}}
.dt-user-name{{font-size:.78rem;font-weight:600;color:{text_primary};max-width:100px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}}
.dt-theme-btn{{
  width:34px;height:34px;
  background:{accent_glow};border:1px solid {border};
  border-radius:10px;display:flex;align-items:center;justify-content:center;
  font-size:1rem;cursor:pointer;transition:var(--transition);
  flex-shrink:0;
}}
.dt-theme-btn:hover{{background:{border_hover};transform:scale(1.08);}}
.dt-badge{{
  font-size:.65rem;font-weight:700;color:{accent};
  background:{accent_glow};border:1px solid {border};
  border-radius:6px;padding:2px 7px;letter-spacing:.06em;text-transform:uppercase;
}}

/* Main content: push down to clear topbar, push left to clear rail */
[data-testid="stMainBlockContainer"],.main .block-container{{
  padding:.25rem 2.25rem 2.5rem!important;
  max-width:1440px!important;
}}

/* ═══════════════════════ TYPOGRAPHY ═══════════════════════ */
h1,h2,h3,h4,h5,h6{{font-family:'Inter',sans-serif!important;letter-spacing:-.02em!important;}}
h1{{color:{text_primary}!important;font-weight:800!important;font-size:1.875rem!important;}}
h2{{color:{text_secondary}!important;font-weight:700!important;font-size:1.4rem!important;}}
h3{{color:{text_secondary}!important;font-weight:600!important;font-size:1.1rem!important;}}
p,li{{color:{text_label}!important;line-height:1.65!important;}}
.twin-container p,.twin-container div{{color:inherit;}}

/* ═══════════════════════ METRIC CARDS ═══════════════════════ */
.metric-card{{
  background:{card_grad};border:1px solid {border};border-radius:var(--radius-card);
  padding:1.3rem 1.6rem;position:relative;overflow:hidden;
  transition:var(--transition);box-shadow:{shadow_card};
}}
.metric-card::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:var(--accent,linear-gradient(90deg,#2563EB,#7C3AED));}}
.metric-card::after{{content:'';position:absolute;top:-30px;right:-30px;width:100px;height:100px;background:radial-gradient(circle,{accent_glow} 0%,transparent 70%);pointer-events:none;}}
.metric-card:hover{{border-color:{border_hover};transform:translateY(-3px);box-shadow:{shadow_hover};}}
.metric-card .mc-icon{{font-size:1.8rem;margin-bottom:.5rem;display:block;}}
.metric-card .mc-label{{font-size:.7rem;font-weight:700;color:{text_muted};text-transform:uppercase;letter-spacing:.1em;margin-bottom:.3rem;}}
.metric-card .mc-value{{font-size:2rem;font-weight:800;color:{text_primary};letter-spacing:-.03em;line-height:1;}}
.metric-card .mc-sub{{font-size:.78rem;color:{text_muted};margin-top:.3rem;}}
.metric-card .mc-trend-up{{color:#10B981!important;font-size:.78rem;font-weight:600;}}
.metric-card .mc-trend-down{{color:#EF4444!important;font-size:.78rem;font-weight:600;}}

/* ═══════════════════════ SECTION HEADER ═══════════════════════ */
.section-header{{display:flex;align-items:center;gap:.75rem;margin:1.75rem 0 1.1rem;padding-bottom:.75rem;border-bottom:1px solid {border};}}
.section-header .sh-icon{{width:36px;height:36px;background:linear-gradient(135deg,{accent_glow},{accent_glow});border:1px solid {border};border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:1rem;}}
.section-header .sh-title{{font-size:1.05rem;font-weight:700;color:{text_secondary};letter-spacing:-.01em;}}
.section-header .sh-subtitle{{font-size:.78rem;color:{text_muted};}}

/* ═══════════════════════ PAGE HEADER ═══════════════════════ */
.page-header{{
  background:{page_hdr_grad};border:1px solid {border};border-radius:22px;
  padding:1.6rem 2.25rem;margin-bottom:1.75rem;position:relative;overflow:hidden;
  box-shadow:{shadow_card};
}}
.page-header::after{{content:'';position:absolute;top:-60px;right:-60px;width:220px;height:220px;background:radial-gradient(circle,{accent_glow} 0%,transparent 70%);pointer-events:none;}}
.page-header .ph-greeting{{font-size:.72rem;font-weight:700;color:{accent};text-transform:uppercase;letter-spacing:.12em;margin-bottom:.4rem;}}
.page-header .ph-title{{font-size:1.6rem;font-weight:800;color:{text_primary};letter-spacing:-.03em;margin-bottom:.3rem;}}
.page-header .ph-sub{{font-size:.875rem;color:{text_muted};}}

/* ═══════════════════════ INSIGHT CARDS ═══════════════════════ */
.insight-card{{background:{insight_bg};border-radius:13px;padding:1.1rem 1.3rem;border-left:3px solid var(--insight-color,#2563EB);margin-bottom:.75rem;transition:var(--transition);box-shadow:{shadow_card};}}
.insight-card:hover{{transform:translateX(4px);}}
.insight-card .ic-type{{font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.12em;color:var(--insight-color,#2563EB);margin-bottom:.3rem;}}
.insight-card .ic-text{{font-size:.875rem;color:{text_secondary};line-height:1.55;}}
.insight-card .ic-footer{{font-size:.7rem;color:{text_muted};margin-top:.35rem;}}

/* ═══════════════════════ PROGRESS BAR ═══════════════════════ */
.progress-wrap{{margin:.3rem 0;}}
.progress-label{{display:flex;justify-content:space-between;font-size:.76rem;color:{text_muted};margin-bottom:.28rem;}}
.progress-bar-bg{{height:6px;background:{progress_track};border-radius:99px;overflow:hidden;}}
.progress-bar-fill{{height:100%;border-radius:99px;background:var(--bar-color,linear-gradient(90deg,#2563EB,#7C3AED));transition:width .65s ease;}}

/* ═══════════════════════ BADGES ═══════════════════════ */
.badge{{display:inline-block;padding:3px 10px;border-radius:99px;font-size:.68rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;}}
.badge-blue  {{background:rgba(37,99,235,.14); color:{"#60A5FA" if dark else "#1D4ED8"};border:1px solid rgba(37,99,235,.28);}}
.badge-green {{background:rgba(16,185,129,.14);color:{"#34D399" if dark else "#047857"};border:1px solid rgba(16,185,129,.28);}}
.badge-yellow{{background:rgba(245,158,11,.14);color:{"#FCD34D" if dark else "#92400E"};border:1px solid rgba(245,158,11,.28);}}
.badge-red   {{background:rgba(239,68,68,.14); color:{"#F87171" if dark else "#991B1B"};border:1px solid rgba(239,68,68,.28);}}
.badge-purple{{background:rgba(139,92,246,.14);color:{"#A78BFA" if dark else "#5B21B6"};border:1px solid rgba(139,92,246,.28);}}

/* ═══════════════════════ GLASS CARD ═══════════════════════ */
.glass-card{{background:{bg_card}!important;backdrop-filter:blur(14px)!important;border:1px solid {border}!important;border-radius:var(--radius-card)!important;padding:1.5rem!important;transition:var(--transition)!important;}}
.glass-card:hover{{border-color:{border_hover}!important;transform:translateY(-2px)!important;box-shadow:{shadow_hover}!important;}}

/* ═══════════════════════ FORMS & INPUTS ═══════════════════════ */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stSelectbox"] select,
[data-testid="stDateInput"] input,
[data-testid="stTextArea"] textarea {{
  background:{input_bg}!important;border:1.5px solid {border}!important;
  border-radius:var(--radius-input)!important;color:{text_primary}!important;
  font-family:'Inter',sans-serif!important;font-size:.875rem!important;transition:border-color .2s!important;
}}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {{
  border-color:{accent}!important;box-shadow:0 0 0 3px {accent_glow}!important;
}}
label,[data-testid="stWidgetLabel"] p{{color:{text_label}!important;font-size:.78rem!important;font-weight:600!important;text-transform:uppercase!important;letter-spacing:.07em!important;}}
[data-testid="stSelectbox"]>div>div{{background:{input_bg}!important;border:1.5px solid {border}!important;border-radius:var(--radius-input)!important;color:{text_primary}!important;}}

/* ═══════════════════════ BUTTONS ═══════════════════════ */
.stButton>button{{
  background:linear-gradient(135deg,#2563EB,#1D4ED8)!important;color:#fff!important;
  border:none!important;border-radius:10px!important;padding:.6rem 1.5rem!important;
  font-family:'Inter',sans-serif!important;font-weight:600!important;font-size:.875rem!important;
  transition:var(--transition)!important;box-shadow:0 4px 16px rgba(37,99,235,.28)!important;
}}
.stButton>button:hover{{background:linear-gradient(135deg,#3B82F6,#2563EB)!important;transform:translateY(-2px)!important;box-shadow:0 8px 24px rgba(37,99,235,.4)!important;}}
.stButton>button:active{{transform:translateY(0)!important;}}
.stButton>button[kind="secondary"]{{background:{accent_glow}!important;border:1px solid {border}!important;color:{accent_light}!important;box-shadow:none!important;}}
[data-testid="stFormSubmitButton"]>button{{
  background:linear-gradient(135deg,#2563EB,#7C3AED)!important;color:#fff!important;
  border:none!important;border-radius:10px!important;font-weight:600!important;
  width:100%!important;padding:.72rem!important;font-size:.9rem!important;
  box-shadow:0 4px 20px rgba(37,99,235,.33)!important;transition:var(--transition)!important;
}}
[data-testid="stFormSubmitButton"]>button:hover{{transform:translateY(-2px)!important;box-shadow:0 8px 28px rgba(37,99,235,.45)!important;}}

/* ═══════════════════════ TABS ═══════════════════════ */
[data-testid="stTabs"] [data-baseweb="tab-list"]{{
  background:{tab_list_bg}!important;border-radius:12px!important;
  border:1px solid {border}!important;padding:4px!important;gap:3px!important;
}}
[data-testid="stTabs"] [data-baseweb="tab"]{{background:transparent!important;color:{text_muted}!important;border-radius:8px!important;font-size:.84rem!important;font-weight:500!important;padding:8px 18px!important;transition:var(--transition)!important;}}
[data-testid="stTabs"] [aria-selected="true"]{{background:linear-gradient(135deg,{accent_glow},{accent_glow})!important;color:{accent_light}!important;font-weight:600!important;}}

/* ═══════════════════════ MISC ═══════════════════════ */
[data-testid="stExpander"]{{background:{expander_bg}!important;border:1px solid {border}!important;border-radius:12px!important;}}
[data-testid="stAlert"]{{border-radius:12px!important;border:none!important;font-size:.875rem!important;}}
hr{{border-color:{border}!important;margin:1.5rem 0!important;}}
[data-testid="stDataFrame"]{{border:1px solid {border}!important;border-radius:12px!important;overflow:hidden!important;box-shadow:{shadow_card}!important;}}
[data-testid="stDataFrame"] th{{background:{df_th_bg}!important;color:{text_muted}!important;font-size:.7rem!important;font-weight:700!important;text-transform:uppercase!important;letter-spacing:.08em!important;}}
[data-testid="stDataFrame"] td{{color:{text_secondary}!important;font-size:.84rem!important;}}
.js-plotly-plot .plotly{{background:transparent!important;}}

/* ═══════════════════════ TWIN VISUALIZATION ═══════════════════════ */
.twin-container{{background:{page_hdr_grad};border:1px solid {border};border-radius:22px;padding:2rem;text-align:center;position:relative;overflow:hidden;box-shadow:{shadow_card};}}
.twin-container::before{{content:'';position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:320px;height:320px;background:radial-gradient(circle,{accent_glow} 0%,transparent 70%);pointer-events:none;}}
.twin-node{{background:{bg_surface};border:1px solid {border};border-radius:13px;padding:.75rem 1rem;text-align:center;transition:var(--transition);box-shadow:{shadow_card};}}
.twin-node:hover{{border-color:{border_hover};transform:scale(1.04);box-shadow:{shadow_hover};}}
.twin-node .tn-icon{{font-size:1.4rem;}}
.twin-node .tn-label{{font-size:.68rem;font-weight:700;color:{text_muted};text-transform:uppercase;letter-spacing:.09em;margin-top:.2rem;}}
.twin-node .tn-score{{font-size:1.1rem;font-weight:700;color:{accent_light};}}

/* ═══════════════════════ LOGIN ═══════════════════════ */
.login-container{{max-width:480px;margin:0 auto;padding:2.5rem;background:{login_bg};border:1px solid {border};border-radius:24px;box-shadow:{shadow_hover};}}
.login-logo{{text-align:center;margin-bottom:2rem;}}
.login-logo .ll-icon{{font-size:3rem;margin-bottom:.75rem;display:block;}}
.login-logo .ll-title{{font-size:1.5rem;font-weight:800;color:{login_title};letter-spacing:-.02em;}}
.login-logo .ll-sub{{font-size:.8rem;color:{text_muted};margin-top:.25rem;}}

/* ═══════════════════════ VERSION FOOTER ═══════════════════════ */
[data-testid="stSidebar"] .version-footer{{position:absolute;bottom:1rem;left:0;right:0;text-align:center;font-size:.58rem;color:{text_muted};opacity:.5;}}
</style>"""


DARK_CSS  = _build_css(dark=True)
LIGHT_CSS = _build_css(dark=False)


def inject_theme() -> None:
    """Inject the active theme CSS. Call once per page after bootstrap_session()."""
    theme = st.session_state.get("theme", "dark")
    st.markdown(DARK_CSS if theme == "dark" else LIGHT_CSS, unsafe_allow_html=True)
