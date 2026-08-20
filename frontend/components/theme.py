"""
Shared CSS theme for Digital Twin AI.
Supports Dark (default) and Light mode.
Call inject_theme() once at the top of every page.
"""
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# DARK THEME
# ─────────────────────────────────────────────────────────────────────────────
DARK_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --bg-base:        #05070D;
  --bg-surface:     #0D1117;
  --bg-elevated:    #111827;
  --bg-card:        rgba(13,17,28,0.95);
  --bg-card-hover:  rgba(15,20,38,0.98);
  --border:         rgba(37,99,235,0.15);
  --border-hover:   rgba(37,99,235,0.40);
  --accent:         #2563EB;
  --accent-purple:  #7C3AED;
  --accent-light:   #60A5FA;
  --text-primary:   #F1F5F9;
  --text-secondary: #CBD5E1;
  --text-muted:     #64748B;
  --text-label:     #94A3B8;
  --input-bg:       rgba(8,11,18,0.9);
  --sidebar-bg:     linear-gradient(180deg,#060810 0%,#090D1A 100%);
  --shadow-card:    0 4px 24px rgba(0,0,0,0.4);
  --shadow-hover:   0 12px 40px rgba(37,99,235,0.18);
  --radius-card:    16px;
  --radius-input:   10px;
  --transition:     all 0.22s ease;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stApp"] {
    background: var(--bg-base) !important;
    font-family: 'Inter', sans-serif !important;
    color: var(--text-primary) !important;
}

#MainMenu, footer, header          { visibility: hidden !important; }
[data-testid="stDecoration"]       { display: none !important; }
.stDeployButton                    { display: none !important; }

/* ── scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg-surface); }
::-webkit-scrollbar-thumb { background: #1E3A5F; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent); }

/* ── sidebar collapse toggle ── */
[data-testid="collapsedControl"] {
    display: flex !important; visibility: visible !important; opacity: 1 !important;
    background: rgba(37,99,235,0.2) !important;
    border: 1px solid rgba(37,99,235,0.45) !important;
    border-left: none !important;
    border-radius: 0 12px 12px 0 !important;
    width: 26px !important; min-height: 52px !important;
    align-items: center !important; justify-content: center !important;
    box-shadow: 4px 0 16px rgba(37,99,235,0.18) !important;
    transition: var(--transition) !important; cursor: pointer !important; z-index: 9999 !important;
}
[data-testid="collapsedControl"]:hover {
    background: rgba(37,99,235,0.38) !important; width: 32px !important;
}
[data-testid="collapsedControl"] svg { color:#fff !important; fill:#fff !important; width:14px !important; height:14px !important; }
[data-testid="stSidebarCollapseButton"] button {
    color: var(--accent-light) !important; background: rgba(37,99,235,0.1) !important;
    border-radius: 8px !important; border: 1px solid rgba(37,99,235,0.2) !important;
}

/* ════════════════════════════════════
   SIDEBAR
════════════════════════════════════ */
[data-testid="stSidebar"] {
    background: var(--sidebar-bg) !important;
    border-right: 1px solid rgba(37,99,235,0.12) !important;
    min-width: 248px !important; max-width: 248px !important;
    box-shadow: 4px 0 32px rgba(0,0,0,0.35) !important;
}
[data-testid="stSidebar"] > div:first-child { padding: 0 !important; }

[data-testid="stSidebarNavLink"] {
    color: var(--text-label) !important; border-radius: 9px !important;
    margin: 2px 10px !important; padding: 9px 14px !important;
    transition: var(--transition) !important; font-size: 0.875rem !important; font-weight: 500 !important;
}
[data-testid="stSidebarNavLink"]:hover {
    background: rgba(37,99,235,0.14) !important; color: var(--accent-light) !important;
}
[data-testid="stSidebarNavLink"][aria-current="page"] {
    background: linear-gradient(135deg,rgba(37,99,235,0.22),rgba(139,92,246,0.14)) !important;
    color: var(--accent-light) !important; border-left: 3px solid var(--accent) !important;
    font-weight: 600 !important;
}

/* ════════════════════════════════════
   MAIN CONTENT
════════════════════════════════════ */
[data-testid="stMainBlockContainer"], .main .block-container {
    padding: 1.5rem 2.25rem 2.5rem !important; max-width: 1440px !important;
}

/* ════════════════════════════════════
   TYPOGRAPHY
════════════════════════════════════ */
h1,h2,h3,h4,h5,h6 { font-family:'Inter',sans-serif !important; letter-spacing:-0.02em !important; }
h1 { color:var(--text-primary) !important; font-weight:800 !important; font-size:1.875rem !important; }
h2 { color:var(--text-secondary) !important; font-weight:700 !important; font-size:1.4rem !important; }
h3 { color:#CBD5E1 !important; font-weight:600 !important; font-size:1.1rem !important; }
p, li { color:var(--text-label) !important; line-height:1.65 !important; }
.twin-container p, .twin-container div { color:inherit; }

/* ════════════════════════════════════
   METRIC CARDS
════════════════════════════════════ */
.metric-card {
    background: linear-gradient(145deg,rgba(10,14,24,0.97) 0%,rgba(13,18,34,0.97) 100%);
    border: 1px solid var(--border);
    border-radius: var(--radius-card);
    padding: 1.3rem 1.6rem;
    position: relative; overflow: hidden;
    transition: var(--transition);
    box-shadow: var(--shadow-card);
}
.metric-card::before {
    content:''; position:absolute; top:0; left:0; right:0; height:2px;
    background: var(--accent, linear-gradient(90deg,#2563EB,#7C3AED));
}
.metric-card::after {
    content:''; position:absolute; top:-30px; right:-30px;
    width:100px; height:100px;
    background: radial-gradient(circle, rgba(37,99,235,0.06) 0%, transparent 70%);
    pointer-events:none;
}
.metric-card:hover {
    border-color: var(--border-hover); transform:translateY(-3px); box-shadow:var(--shadow-hover);
}
.metric-card .mc-icon  { font-size:1.8rem; margin-bottom:.5rem; display:block; }
.metric-card .mc-label { font-size:.7rem; font-weight:700; color:var(--text-muted); text-transform:uppercase; letter-spacing:.1em; margin-bottom:.3rem; }
.metric-card .mc-value { font-size:2rem; font-weight:800; color:var(--text-primary); letter-spacing:-.03em; line-height:1; }
.metric-card .mc-sub   { font-size:.78rem; color:var(--text-muted); margin-top:.3rem; }
.metric-card .mc-trend-up   { color:#10B981 !important; font-size:.78rem; font-weight:600; }
.metric-card .mc-trend-down { color:#EF4444 !important; font-size:.78rem; font-weight:600; }

/* ════════════════════════════════════
   SECTION HEADER
════════════════════════════════════ */
.section-header {
    display:flex; align-items:center; gap:.75rem;
    margin:1.75rem 0 1.1rem; padding-bottom:.75rem;
    border-bottom: 1px solid rgba(37,99,235,0.1);
}
.section-header .sh-icon {
    width:36px; height:36px;
    background: linear-gradient(135deg,rgba(37,99,235,0.18),rgba(139,92,246,0.18));
    border:1px solid rgba(37,99,235,0.28); border-radius:10px;
    display:flex; align-items:center; justify-content:center; font-size:1rem;
}
.section-header .sh-title    { font-size:1.05rem; font-weight:700; color:var(--text-secondary); letter-spacing:-.01em; }
.section-header .sh-subtitle { font-size:.78rem; color:var(--text-muted); }

/* ════════════════════════════════════
   PAGE HEADER
════════════════════════════════════ */
.page-header {
    background: linear-gradient(135deg,rgba(8,11,20,0.99) 0%,rgba(14,19,42,0.99) 100%);
    border:1px solid rgba(37,99,235,0.14); border-radius:22px;
    padding:1.75rem 2.25rem; margin-bottom:1.75rem;
    position:relative; overflow:hidden;
    box-shadow: 0 4px 32px rgba(0,0,0,0.35);
}
.page-header::after {
    content:''; position:absolute; top:-60px; right:-60px;
    width:220px; height:220px;
    background:radial-gradient(circle,rgba(37,99,235,0.07) 0%,transparent 70%);
    pointer-events:none;
}
.page-header .ph-greeting {
    font-size:.75rem; font-weight:700; color:var(--accent); text-transform:uppercase;
    letter-spacing:.12em; margin-bottom:.4rem;
}
.page-header .ph-title  { font-size:1.75rem; font-weight:800; color:var(--text-primary); letter-spacing:-.03em; margin-bottom:.3rem; }
.page-header .ph-sub    { font-size:.875rem; color:var(--text-muted); }

/* ════════════════════════════════════
   INSIGHT CARDS
════════════════════════════════════ */
.insight-card {
    background: rgba(10,13,22,0.92); border-radius:13px;
    padding:1.1rem 1.3rem;
    border-left:3px solid var(--insight-color, #2563EB);
    margin-bottom:.75rem; transition:var(--transition);
    box-shadow: 0 2px 12px rgba(0,0,0,0.25);
}
.insight-card:hover { transform:translateX(4px); }
.insight-card .ic-type   { font-size:.68rem; font-weight:700; text-transform:uppercase; letter-spacing:.12em; color:var(--insight-color,#2563EB); margin-bottom:.3rem; }
.insight-card .ic-text   { font-size:.875rem; color:var(--text-secondary); line-height:1.55; }
.insight-card .ic-footer { font-size:.7rem; color:var(--text-muted); margin-top:.35rem; }

/* ════════════════════════════════════
   PROGRESS BAR
════════════════════════════════════ */
.progress-wrap { margin:.3rem 0; }
.progress-label { display:flex; justify-content:space-between; font-size:.76rem; color:var(--text-muted); margin-bottom:.28rem; }
.progress-bar-bg { height:6px; background:rgba(30,41,59,0.75); border-radius:99px; overflow:hidden; }
.progress-bar-fill { height:100%; border-radius:99px; background:var(--bar-color,linear-gradient(90deg,#2563EB,#7C3AED)); transition:width .65s ease; }

/* ════════════════════════════════════
   BADGES
════════════════════════════════════ */
.badge { display:inline-block; padding:3px 10px; border-radius:99px; font-size:.68rem; font-weight:700; letter-spacing:.06em; text-transform:uppercase; }
.badge-blue   { background:rgba(37,99,235,.14);  color:#60A5FA; border:1px solid rgba(37,99,235,.28); }
.badge-green  { background:rgba(16,185,129,.14); color:#34D399; border:1px solid rgba(16,185,129,.28); }
.badge-yellow { background:rgba(245,158,11,.14); color:#FCD34D; border:1px solid rgba(245,158,11,.28); }
.badge-red    { background:rgba(239,68,68,.14);  color:#F87171; border:1px solid rgba(239,68,68,.28); }
.badge-purple { background:rgba(139,92,246,.14); color:#A78BFA; border:1px solid rgba(139,92,246,.28); }

/* ════════════════════════════════════
   GLASS CARD
════════════════════════════════════ */
.glass-card {
    background:rgba(13,17,28,0.78) !important; backdrop-filter:blur(14px) !important;
    border:1px solid var(--border) !important; border-radius:var(--radius-card) !important;
    padding:1.5rem !important; transition:var(--transition) !important;
}
.glass-card:hover { border-color:var(--border-hover) !important; transform:translateY(-2px) !important; box-shadow:var(--shadow-hover) !important; }

/* ════════════════════════════════════
   FORMS & INPUTS
════════════════════════════════════ */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stSelectbox"] select,
[data-testid="stDateInput"] input,
[data-testid="stTextArea"] textarea {
    background: var(--input-bg) !important; border:1px solid rgba(37,99,235,.22) !important;
    border-radius:var(--radius-input) !important; color:var(--text-primary) !important;
    font-family:'Inter',sans-serif !important; font-size:.875rem !important; transition:border-color .2s !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color:var(--accent) !important; box-shadow:0 0 0 3px rgba(37,99,235,.14) !important;
}
label, [data-testid="stWidgetLabel"] p {
    color:var(--text-label) !important; font-size:.78rem !important;
    font-weight:600 !important; text-transform:uppercase !important; letter-spacing:.07em !important;
}
[data-testid="stSelectbox"] > div > div {
    background:var(--input-bg) !important; border:1px solid rgba(37,99,235,.22) !important;
    border-radius:var(--radius-input) !important; color:var(--text-primary) !important;
}

/* ════════════════════════════════════
   BUTTONS
════════════════════════════════════ */
.stButton > button {
    background:linear-gradient(135deg,#2563EB,#1D4ED8) !important;
    color:#fff !important; border:none !important; border-radius:10px !important;
    padding:.6rem 1.5rem !important; font-family:'Inter',sans-serif !important;
    font-weight:600 !important; font-size:.875rem !important; letter-spacing:.02em !important;
    transition:var(--transition) !important; box-shadow:0 4px 16px rgba(37,99,235,.28) !important;
}
.stButton > button:hover {
    background:linear-gradient(135deg,#3B82F6,#2563EB) !important;
    transform:translateY(-2px) !important; box-shadow:0 8px 24px rgba(37,99,235,.4) !important;
}
.stButton > button:active { transform:translateY(0) !important; }
.stButton > button[kind="secondary"] {
    background:rgba(37,99,235,.1) !important; border:1px solid rgba(37,99,235,.3) !important;
    color:#60A5FA !important; box-shadow:none !important;
}
[data-testid="stFormSubmitButton"] > button {
    background:linear-gradient(135deg,#2563EB,#7C3AED) !important; color:#fff !important;
    border:none !important; border-radius:10px !important; font-weight:600 !important;
    width:100% !important; padding:.72rem !important; font-size:.9rem !important;
    box-shadow:0 4px 20px rgba(37,99,235,.33) !important; transition:var(--transition) !important;
}
[data-testid="stFormSubmitButton"] > button:hover {
    transform:translateY(-2px) !important; box-shadow:0 8px 28px rgba(37,99,235,.45) !important;
}

/* ════════════════════════════════════
   TABS
════════════════════════════════════ */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background:rgba(8,11,20,.7) !important; border-radius:12px !important;
    border:1px solid rgba(37,99,235,.14) !important; padding:4px !important; gap:3px !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    background:transparent !important; color:var(--text-muted) !important; border-radius:8px !important;
    font-size:.84rem !important; font-weight:500 !important; padding:8px 18px !important; transition:var(--transition) !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background:linear-gradient(135deg,rgba(37,99,235,.24),rgba(139,92,246,.14)) !important;
    color:var(--accent-light) !important; font-weight:600 !important;
}

/* ════════════════════════════════════
   EXPANDER / ALERTS / DATAFRAME / HR
════════════════════════════════════ */
[data-testid="stExpander"] {
    background:rgba(10,13,22,.75) !important; border:1px solid rgba(37,99,235,.14) !important; border-radius:12px !important;
}
[data-testid="stAlert"] { border-radius:12px !important; border:none !important; font-size:.875rem !important; }
hr { border-color:rgba(37,99,235,.1) !important; margin:1.5rem 0 !important; }
[data-testid="stDataFrame"] { border:1px solid rgba(37,99,235,.14) !important; border-radius:12px !important; overflow:hidden !important; }
[data-testid="stDataFrame"] th { background:rgba(8,11,20,.92) !important; color:var(--text-muted) !important; font-size:.7rem !important; font-weight:700 !important; text-transform:uppercase !important; letter-spacing:.08em !important; }
[data-testid="stDataFrame"] td { color:var(--text-secondary) !important; font-size:.84rem !important; }
.js-plotly-plot .plotly { background:transparent !important; }

/* ════════════════════════════════════
   TWIN VISUALIZATION
════════════════════════════════════ */
.twin-container {
    background:linear-gradient(135deg,rgba(8,11,20,.99) 0%,rgba(14,19,42,.99) 100%);
    border:1px solid rgba(37,99,235,.18); border-radius:22px;
    padding:2rem; text-align:center; position:relative; overflow:hidden;
    box-shadow: 0 4px 32px rgba(0,0,0,0.4);
}
.twin-container::before {
    content:''; position:absolute; top:50%; left:50%; transform:translate(-50%,-50%);
    width:320px; height:320px;
    background:radial-gradient(circle,rgba(37,99,235,.05) 0%,transparent 70%); pointer-events:none;
}
.twin-node {
    background:rgba(8,11,20,.92); border:1px solid rgba(37,99,235,.18); border-radius:13px;
    padding:.75rem 1rem; text-align:center; transition:var(--transition);
}
.twin-node:hover { border-color:rgba(37,99,235,.5); transform:scale(1.04); box-shadow:0 4px 16px rgba(37,99,235,.15); }
.twin-node .tn-icon  { font-size:1.4rem; }
.twin-node .tn-label { font-size:.68rem; font-weight:700; color:var(--text-muted); text-transform:uppercase; letter-spacing:.09em; margin-top:.2rem; }
.twin-node .tn-score { font-size:1.1rem; font-weight:700; color:var(--accent-light); }

/* ════════════════════════════════════
   LOGIN / SIDEBAR EXTRAS
════════════════════════════════════ */
.login-container {
    max-width:480px; margin:0 auto; padding:2.5rem;
    background:linear-gradient(135deg,rgba(8,11,20,.99),rgba(14,19,42,.99));
    border:1px solid rgba(37,99,235,.2); border-radius:24px;
    box-shadow:0 25px 80px rgba(0,0,0,.6), 0 0 60px rgba(37,99,235,.06);
}
.login-logo { text-align:center; margin-bottom:2rem; }
.login-logo .ll-icon  { font-size:3rem; margin-bottom:.75rem; display:block; }
.login-logo .ll-title { font-size:1.5rem; font-weight:800; color:#60A5FA; letter-spacing:-.02em; }
.login-logo .ll-sub   { font-size:.8rem; color:var(--text-muted); margin-top:.25rem; }

[data-testid="stSidebar"] .version-footer {
    position:absolute; bottom:1rem; left:0; right:0;
    text-align:center; font-size:.62rem; color:#1E293B;
}
[data-testid="stSidebar"] [data-testid="stButton"]:last-of-type > button {
    background:transparent !important; border:1px solid rgba(37,99,235,.14) !important;
    color:#475569 !important; font-size:.75rem !important; box-shadow:none !important; padding:.4rem 1rem !important;
}
[data-testid="stSidebar"] [data-testid="stButton"]:last-of-type > button:hover {
    background:rgba(37,99,235,.08) !important; color:#60A5FA !important;
    border-color:rgba(37,99,235,.35) !important; transform:none !important;
}
</style>
"""

# ─────────────────────────────────────────────────────────────────────────────
# LIGHT THEME
# ─────────────────────────────────────────────────────────────────────────────
LIGHT_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --bg-base:        #F0F4FF;
  --bg-surface:     #FFFFFF;
  --bg-elevated:    #F8FAFF;
  --bg-card:        rgba(255,255,255,0.96);
  --border:         rgba(37,99,235,0.14);
  --border-hover:   rgba(37,99,235,0.38);
  --accent:         #2563EB;
  --accent-purple:  #7C3AED;
  --accent-light:   #1D4ED8;
  --text-primary:   #0F172A;
  --text-secondary: #1E293B;
  --text-muted:     #64748B;
  --text-label:     #475569;
  --input-bg:       rgba(248,250,255,0.95);
  --sidebar-bg:     linear-gradient(180deg,#EEF3FF 0%,#E8EFFF 100%);
  --shadow-card:    0 2px 16px rgba(37,99,235,0.07);
  --shadow-hover:   0 8px 32px rgba(37,99,235,0.14);
  --radius-card:    16px;
  --radius-input:   10px;
  --transition:     all 0.22s ease;
}

*, *::before, *::after { box-sizing:border-box; margin:0; padding:0; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stApp"] {
    background: var(--bg-base) !important;
    font-family:'Inter',sans-serif !important;
    color:var(--text-primary) !important;
}

#MainMenu, footer, header          { visibility:hidden !important; }
[data-testid="stDecoration"]       { display:none !important; }
.stDeployButton                    { display:none !important; }

::-webkit-scrollbar { width:5px; height:5px; }
::-webkit-scrollbar-track { background:#E8EFFF; }
::-webkit-scrollbar-thumb { background:#BFCFFF; border-radius:4px; }
::-webkit-scrollbar-thumb:hover { background:var(--accent); }

[data-testid="collapsedControl"] {
    display:flex !important; visibility:visible !important; opacity:1 !important;
    background:rgba(37,99,235,.15) !important; border:1px solid rgba(37,99,235,.35) !important;
    border-left:none !important; border-radius:0 12px 12px 0 !important;
    width:26px !important; min-height:52px !important;
    align-items:center !important; justify-content:center !important;
    box-shadow:4px 0 14px rgba(37,99,235,.12) !important; cursor:pointer !important; z-index:9999 !important;
}
[data-testid="collapsedControl"]:hover { background:rgba(37,99,235,.28) !important; width:32px !important; }
[data-testid="collapsedControl"] svg { color:var(--accent) !important; fill:var(--accent) !important; width:14px !important; height:14px !important; }
[data-testid="stSidebarCollapseButton"] button {
    color:var(--accent) !important; background:rgba(37,99,235,.08) !important;
    border-radius:8px !important; border:1px solid rgba(37,99,235,.2) !important;
}

/* ── sidebar ── */
[data-testid="stSidebar"] {
    background:var(--sidebar-bg) !important;
    border-right:1px solid rgba(37,99,235,.12) !important;
    min-width:248px !important; max-width:248px !important;
    box-shadow:4px 0 24px rgba(37,99,235,.08) !important;
}
[data-testid="stSidebar"] > div:first-child { padding:0 !important; }
[data-testid="stSidebarNavLink"] {
    color:var(--text-label) !important; border-radius:9px !important;
    margin:2px 10px !important; padding:9px 14px !important;
    transition:var(--transition) !important; font-size:.875rem !important; font-weight:500 !important;
}
[data-testid="stSidebarNavLink"]:hover { background:rgba(37,99,235,.1) !important; color:var(--accent) !important; }
[data-testid="stSidebarNavLink"][aria-current="page"] {
    background:linear-gradient(135deg,rgba(37,99,235,.15),rgba(139,92,246,.1)) !important;
    color:var(--accent) !important; border-left:3px solid var(--accent) !important; font-weight:600 !important;
}

/* ── main content ── */
[data-testid="stMainBlockContainer"], .main .block-container {
    padding:1.5rem 2.25rem 2.5rem !important; max-width:1440px !important;
}

/* ── typography ── */
h1,h2,h3,h4,h5,h6 { font-family:'Inter',sans-serif !important; letter-spacing:-.02em !important; }
h1 { color:var(--text-primary) !important; font-weight:800 !important; font-size:1.875rem !important; }
h2 { color:var(--text-secondary) !important; font-weight:700 !important; font-size:1.4rem !important; }
h3 { color:#334155 !important; font-weight:600 !important; font-size:1.1rem !important; }
p, li { color:var(--text-label) !important; line-height:1.65 !important; }
.twin-container p, .twin-container div { color:inherit; }

/* ── metric cards ── */
.metric-card {
    background:linear-gradient(145deg,#FFFFFF 0%,#F8FAFF 100%);
    border:1px solid rgba(37,99,235,.12); border-radius:var(--radius-card);
    padding:1.3rem 1.6rem; position:relative; overflow:hidden;
    transition:var(--transition); box-shadow:var(--shadow-card);
}
.metric-card::before { content:''; position:absolute; top:0; left:0; right:0; height:2px; background:var(--accent,linear-gradient(90deg,#2563EB,#7C3AED)); }
.metric-card::after { content:''; position:absolute; top:-30px; right:-30px; width:100px; height:100px; background:radial-gradient(circle,rgba(37,99,235,.04) 0%,transparent 70%); pointer-events:none; }
.metric-card:hover { border-color:var(--border-hover); transform:translateY(-3px); box-shadow:var(--shadow-hover); }
.metric-card .mc-icon  { font-size:1.8rem; margin-bottom:.5rem; display:block; }
.metric-card .mc-label { font-size:.7rem; font-weight:700; color:var(--text-muted); text-transform:uppercase; letter-spacing:.1em; margin-bottom:.3rem; }
.metric-card .mc-value { font-size:2rem; font-weight:800; color:var(--text-primary); letter-spacing:-.03em; line-height:1; }
.metric-card .mc-sub   { font-size:.78rem; color:var(--text-muted); margin-top:.3rem; }
.metric-card .mc-trend-up   { color:#059669 !important; font-size:.78rem; font-weight:600; }
.metric-card .mc-trend-down { color:#DC2626 !important; font-size:.78rem; font-weight:600; }

/* ── section header ── */
.section-header {
    display:flex; align-items:center; gap:.75rem;
    margin:1.75rem 0 1.1rem; padding-bottom:.75rem;
    border-bottom:1px solid rgba(37,99,235,.1);
}
.section-header .sh-icon {
    width:36px; height:36px;
    background:linear-gradient(135deg,rgba(37,99,235,.12),rgba(139,92,246,.12));
    border:1px solid rgba(37,99,235,.22); border-radius:10px;
    display:flex; align-items:center; justify-content:center; font-size:1rem;
}
.section-header .sh-title    { font-size:1.05rem; font-weight:700; color:var(--text-secondary); }
.section-header .sh-subtitle { font-size:.78rem; color:var(--text-muted); }

/* ── page header ── */
.page-header {
    background:linear-gradient(135deg,#FFFFFF 0%,#F0F5FF 100%);
    border:1px solid rgba(37,99,235,.12); border-radius:22px;
    padding:1.75rem 2.25rem; margin-bottom:1.75rem;
    position:relative; overflow:hidden; box-shadow:0 2px 20px rgba(37,99,235,.07);
}
.page-header::after { content:''; position:absolute; top:-60px; right:-60px; width:220px; height:220px; background:radial-gradient(circle,rgba(37,99,235,.06) 0%,transparent 70%); pointer-events:none; }
.page-header .ph-greeting { font-size:.75rem; font-weight:700; color:var(--accent); text-transform:uppercase; letter-spacing:.12em; margin-bottom:.4rem; }
.page-header .ph-title    { font-size:1.75rem; font-weight:800; color:var(--text-primary); letter-spacing:-.03em; margin-bottom:.3rem; }
.page-header .ph-sub      { font-size:.875rem; color:var(--text-muted); }

/* ── insight cards ── */
.insight-card {
    background:#FFFFFF; border-radius:13px; padding:1.1rem 1.3rem;
    border-left:3px solid var(--insight-color,#2563EB);
    margin-bottom:.75rem; transition:var(--transition);
    box-shadow:0 2px 10px rgba(37,99,235,.07);
}
.insight-card:hover { transform:translateX(4px); box-shadow:0 4px 18px rgba(37,99,235,.12); }
.insight-card .ic-type   { font-size:.68rem; font-weight:700; text-transform:uppercase; letter-spacing:.12em; color:var(--insight-color,#2563EB); margin-bottom:.3rem; }
.insight-card .ic-text   { font-size:.875rem; color:var(--text-secondary); line-height:1.55; }
.insight-card .ic-footer { font-size:.7rem; color:var(--text-muted); margin-top:.35rem; }

/* ── progress bar ── */
.progress-wrap { margin:.3rem 0; }
.progress-label { display:flex; justify-content:space-between; font-size:.76rem; color:var(--text-muted); margin-bottom:.28rem; }
.progress-bar-bg { height:6px; background:rgba(37,99,235,.1); border-radius:99px; overflow:hidden; }
.progress-bar-fill { height:100%; border-radius:99px; background:var(--bar-color,linear-gradient(90deg,#2563EB,#7C3AED)); transition:width .65s ease; }

/* ── badges ── */
.badge { display:inline-block; padding:3px 10px; border-radius:99px; font-size:.68rem; font-weight:700; letter-spacing:.06em; text-transform:uppercase; }
.badge-blue   { background:rgba(37,99,235,.1);  color:#1D4ED8; border:1px solid rgba(37,99,235,.25); }
.badge-green  { background:rgba(5,150,105,.1);  color:#047857; border:1px solid rgba(5,150,105,.25); }
.badge-yellow { background:rgba(217,119,6,.1);  color:#92400E; border:1px solid rgba(217,119,6,.25); }
.badge-red    { background:rgba(220,38,38,.1);  color:#991B1B; border:1px solid rgba(220,38,38,.25); }
.badge-purple { background:rgba(109,40,217,.1); color:#5B21B6; border:1px solid rgba(109,40,217,.25); }

/* ── glass card ── */
.glass-card {
    background:rgba(255,255,255,0.85) !important; backdrop-filter:blur(14px) !important;
    border:1px solid var(--border) !important; border-radius:var(--radius-card) !important;
    padding:1.5rem !important; transition:var(--transition) !important; box-shadow:var(--shadow-card) !important;
}
.glass-card:hover { border-color:var(--border-hover) !important; transform:translateY(-2px) !important; box-shadow:var(--shadow-hover) !important; }

/* ── forms ── */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stSelectbox"] select,
[data-testid="stDateInput"] input,
[data-testid="stTextArea"] textarea {
    background:var(--input-bg) !important; border:1.5px solid rgba(37,99,235,.18) !important;
    border-radius:var(--radius-input) !important; color:var(--text-primary) !important;
    font-family:'Inter',sans-serif !important; font-size:.875rem !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color:var(--accent) !important; box-shadow:0 0 0 3px rgba(37,99,235,.1) !important;
}
label, [data-testid="stWidgetLabel"] p {
    color:var(--text-label) !important; font-size:.78rem !important;
    font-weight:600 !important; text-transform:uppercase !important; letter-spacing:.07em !important;
}
[data-testid="stSelectbox"] > div > div {
    background:var(--input-bg) !important; border:1.5px solid rgba(37,99,235,.18) !important;
    border-radius:var(--radius-input) !important; color:var(--text-primary) !important;
}

/* ── buttons ── */
.stButton > button {
    background:linear-gradient(135deg,#2563EB,#1D4ED8) !important; color:#fff !important;
    border:none !important; border-radius:10px !important; padding:.6rem 1.5rem !important;
    font-family:'Inter',sans-serif !important; font-weight:600 !important; font-size:.875rem !important;
    transition:var(--transition) !important; box-shadow:0 4px 14px rgba(37,99,235,.25) !important;
}
.stButton > button:hover { background:linear-gradient(135deg,#3B82F6,#2563EB) !important; transform:translateY(-2px) !important; box-shadow:0 8px 22px rgba(37,99,235,.35) !important; }
.stButton > button[kind="secondary"] {
    background:rgba(37,99,235,.08) !important; border:1.5px solid rgba(37,99,235,.28) !important;
    color:var(--accent) !important; box-shadow:none !important;
}
[data-testid="stFormSubmitButton"] > button {
    background:linear-gradient(135deg,#2563EB,#7C3AED) !important; color:#fff !important;
    border:none !important; border-radius:10px !important; font-weight:600 !important;
    width:100% !important; padding:.72rem !important; font-size:.9rem !important;
    box-shadow:0 4px 18px rgba(37,99,235,.3) !important;
}
[data-testid="stFormSubmitButton"] > button:hover { transform:translateY(-2px) !important; }

/* ── tabs ── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background:rgba(240,245,255,.9) !important; border-radius:12px !important;
    border:1px solid rgba(37,99,235,.12) !important; padding:4px !important; gap:3px !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    background:transparent !important; color:var(--text-muted) !important;
    border-radius:8px !important; font-size:.84rem !important; font-weight:500 !important; padding:8px 18px !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background:linear-gradient(135deg,rgba(37,99,235,.15),rgba(139,92,246,.1)) !important;
    color:var(--accent) !important; font-weight:600 !important;
}

/* ── misc ── */
[data-testid="stExpander"] { background:#FFFFFF !important; border:1px solid rgba(37,99,235,.12) !important; border-radius:12px !important; }
[data-testid="stAlert"] { border-radius:12px !important; border:none !important; }
hr { border-color:rgba(37,99,235,.1) !important; margin:1.5rem 0 !important; }
[data-testid="stDataFrame"] { border:1px solid rgba(37,99,235,.12) !important; border-radius:12px !important; overflow:hidden !important; box-shadow:var(--shadow-card) !important; }
[data-testid="stDataFrame"] th { background:#F0F5FF !important; color:var(--text-muted) !important; font-size:.7rem !important; font-weight:700 !important; text-transform:uppercase !important; }
[data-testid="stDataFrame"] td { color:var(--text-secondary) !important; font-size:.84rem !important; }
.js-plotly-plot .plotly { background:transparent !important; }

/* ── twin visualization ── */
.twin-container {
    background:linear-gradient(135deg,#FFFFFF 0%,#F0F5FF 100%);
    border:1px solid rgba(37,99,235,.14); border-radius:22px;
    padding:2rem; text-align:center; position:relative; overflow:hidden;
    box-shadow:0 4px 24px rgba(37,99,235,.08);
}
.twin-container::before { content:''; position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:320px; height:320px; background:radial-gradient(circle,rgba(37,99,235,.04) 0%,transparent 70%); pointer-events:none; }
.twin-node { background:#F8FAFF; border:1px solid rgba(37,99,235,.14); border-radius:13px; padding:.75rem 1rem; text-align:center; transition:var(--transition); box-shadow:0 2px 8px rgba(37,99,235,.06); }
.twin-node:hover { border-color:rgba(37,99,235,.4); transform:scale(1.04); box-shadow:0 6px 18px rgba(37,99,235,.12); }
.twin-node .tn-icon  { font-size:1.4rem; }
.twin-node .tn-label { font-size:.68rem; font-weight:700; color:var(--text-muted); text-transform:uppercase; letter-spacing:.09em; margin-top:.2rem; }
.twin-node .tn-score { font-size:1.1rem; font-weight:700; color:var(--accent); }

/* ── login ── */
.login-container {
    max-width:480px; margin:0 auto; padding:2.5rem;
    background:linear-gradient(135deg,#FFFFFF,#F0F5FF);
    border:1px solid rgba(37,99,235,.16); border-radius:24px;
    box-shadow:0 20px 60px rgba(37,99,235,.12), 0 4px 20px rgba(0,0,0,.06);
}
.login-logo { text-align:center; margin-bottom:2rem; }
.login-logo .ll-icon  { font-size:3rem; margin-bottom:.75rem; display:block; }
.login-logo .ll-title { font-size:1.5rem; font-weight:800; color:var(--accent); letter-spacing:-.02em; }
.login-logo .ll-sub   { font-size:.8rem; color:var(--text-muted); margin-top:.25rem; }

[data-testid="stSidebar"] .version-footer {
    position:absolute; bottom:1rem; left:0; right:0;
    text-align:center; font-size:.62rem; color:#94A3B8;
}
[data-testid="stSidebar"] [data-testid="stButton"]:last-of-type > button {
    background:transparent !important; border:1px solid rgba(37,99,235,.2) !important;
    color:#94A3B8 !important; font-size:.75rem !important; box-shadow:none !important; padding:.4rem 1rem !important;
}
</style>
"""


def inject_theme() -> None:
    """
    Inject the active theme (dark or light).
    Reads st.session_state.theme — defaults to 'dark'.
    The theme toggle is rendered by render_sidebar() in ui.py.
    """
    theme = st.session_state.get("theme", "dark")
    css = DARK_CSS if theme == "dark" else LIGHT_CSS
    st.markdown(css, unsafe_allow_html=True)
