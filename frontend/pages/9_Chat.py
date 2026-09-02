"""
Digital Twin AI — Conversational AI Chat (Milestone 4)
"""
import html
import os, sys, uuid
import streamlit as st

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from components.theme import inject_theme
from components.ui import bootstrap_session, render_sidebar, render_topbar, require_auth

st.set_page_config(
    page_title="AI Chat · Digital Twin",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_theme()
bootstrap_session()
render_sidebar()
render_topbar("AI Assistant")
require_auth()

client = st.session_state.api_client
token  = st.session_state.token
is_light = st.session_state.get("theme", "dark") == "light"

# ── colour tokens ──────────────────────────────────────────────────────────────
if is_light:
    bg_chat     = "#FFFFFF"
    bg_user     = "#EEF3FF"
    bg_ai       = "#F8FAFF"
    border_c    = "rgba(37,99,235,.14)"
    text_c      = "#0F172A"
    muted_c     = "#64748B"
    user_bub    = "linear-gradient(135deg,#2563EB,#1D4ED8)"
    ai_bub      = "#F0F5FF"
    ai_text     = "#0F172A"
    ai_border   = "rgba(37,99,235,.18)"
    input_bg    = "#F8FAFF"
    header_bg   = "linear-gradient(135deg,#FFFFFF,#F0F5FF)"
else:
    bg_chat     = "rgba(8,11,20,.95)"
    bg_user     = "rgba(37,99,235,.12)"
    bg_ai       = "rgba(13,17,28,.95)"
    border_c    = "rgba(37,99,235,.14)"
    text_c      = "#F1F5F9"
    muted_c     = "#64748B"
    user_bub    = "linear-gradient(135deg,#2563EB,#1D4ED8)"
    ai_bub      = "rgba(13,17,28,.92)"
    ai_text     = "#CBD5E1"
    ai_border   = "rgba(37,99,235,.2)"
    input_bg    = "rgba(8,11,18,.9)"
    header_bg   = "linear-gradient(135deg,rgba(8,11,20,.99),rgba(14,19,42,.99))"

# ── session state init ─────────────────────────────────────────────────────────
if "chat_messages"     not in st.session_state:
    st.session_state.chat_messages     = []
if "chat_conv_id"      not in st.session_state:
    st.session_state.chat_conv_id      = str(uuid.uuid4())
if "chat_thinking"     not in st.session_state:
    st.session_state.chat_thinking     = False
if "chat_history_open" not in st.session_state:
    st.session_state.chat_history_open = False


# ── API helpers ────────────────────────────────────────────────────────────────
def _send(message: str) -> dict:
    try:
        return client.post(
            "/api/assistant/chat",
            payload={
                "message": message,
                "conversation_id": st.session_state.chat_conv_id,
                "stream": False,
            },
            token=token,
        )
    except Exception as exc:
        return {"response": f"Connection error: {exc}", "tools_used": [], "intent": "error"}


def _stream_send(message: str):
    return client.post_stream(
        "/api/assistant/chat",
        payload={
            "message": message,
            "conversation_id": st.session_state.chat_conv_id,
            "stream": True,
        },
        token=token,
    )


def _load_history(conv_id: str) -> list:
    try:
        return client.get(f"/api/assistant/history/{conv_id}", token=token) or []
    except Exception:
        return []


def _list_conversations() -> list:
    try:
        return client.get("/api/assistant/conversations", token=token) or []
    except Exception:
        return []


def _delete_conv(conv_id: str) -> None:
    try:
        client.delete(f"/api/assistant/history/{conv_id}", token=token)
    except Exception:
        pass


# ── layout: chat (left 65%) | history panel (right 35%) ───────────────────────
col_chat, col_history = st.columns([1.9, 1], gap="large")

with col_chat:
    # ── Chat header ────────────────────────────────────────────────────────────
    st.markdown(
        f'<div style="background:{header_bg};border:1px solid {border_c};'
        f'border-radius:18px;padding:1.25rem 1.75rem;margin-bottom:1rem;">'
        f'<div style="display:flex;align-items:center;justify-content:space-between;">'
        f'<div style="display:flex;align-items:center;gap:.9rem;">'
        f'<div style="width:44px;height:44px;background:linear-gradient(135deg,#2563EB,#7C3AED);'
        f'border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:1.4rem;'
        f'box-shadow:0 4px 14px rgba(37,99,235,.35);">🤖</div>'
        f'<div>'
        f'<div style="font-size:1.1rem;font-weight:800;color:{text_c};letter-spacing:-.02em;">Digital Twin AI</div>'
        f'<div style="display:flex;align-items:center;gap:.4rem;margin-top:.15rem;">'
        f'<span style="width:7px;height:7px;border-radius:50%;background:#10B981;display:inline-block;'
        f'box-shadow:0 0 6px #10B981;"></span>'
        f'<span style="font-size:.7rem;font-weight:700;color:#10B981;text-transform:uppercase;letter-spacing:.1em;">AI Powered · Online</span>'
        f'</div></div></div>'
        f'<div style="font-size:.75rem;color:{muted_c};">Conv: <code style="color:#60A5FA;">'
        f'{st.session_state.chat_conv_id[:8]}…</code></div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    # ── New conversation button ────────────────────────────────────────────────
    if st.button("＋ New Conversation", key="new_conv", use_container_width=False):
        st.session_state.chat_conv_id  = str(uuid.uuid4())
        st.session_state.chat_messages = []
        st.rerun()

    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    # ── Suggested questions (shown when no messages yet) ──────────────────────
    if not st.session_state.chat_messages:
        suggestions = [
            "Will I be able to save $50K in 3 years?",
            "What if I start investing 10% of my income?",
            "What is my biggest financial risk?",
            "How can I improve my productivity?",
            "Show me my savings forecast for 12 months",
            "What are my top recommendations?",
        ]
        st.markdown(
            f'<div style="font-size:.72rem;font-weight:700;color:{muted_c};'
            f'text-transform:uppercase;letter-spacing:.1em;margin-bottom:.6rem;">Suggested questions</div>',
            unsafe_allow_html=True,
        )
        cols = st.columns(2)
        for i, q in enumerate(suggestions):
            with cols[i % 2]:
                if st.button(q, key=f"sugg_{i}", use_container_width=True):
                    st.session_state.chat_messages.append({"role": "user", "content": q})
                    with st.spinner("AI is thinking…"):
                        resp = _send(q)
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": resp.get("response", ""),
                        "tools_used": resp.get("tools_used", []),
                        "intent": resp.get("intent", "general"),
                    })
                    st.rerun()
        st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)

    # ── Message thread ─────────────────────────────────────────────────────────
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_messages:
            role    = msg["role"]
            content = msg["content"]
            tools   = msg.get("tools_used", [])

            if role == "user":
                st.markdown(
                    f'<div style="display:flex;justify-content:flex-end;margin-bottom:.75rem;">'
                    f'<div style="max-width:75%;background:{user_bub};color:#fff;'
                    f'border-radius:18px 18px 4px 18px;padding:.85rem 1.1rem;'
                    f'font-size:.9rem;line-height:1.55;box-shadow:0 4px 16px rgba(37,99,235,.3);">'
                    f'{html.escape(str(content)).replace(chr(10), "<br>")}'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )
            else:
                tools_html = ""
                if tools:
                    tool_chips = "".join(
                        f'<span style="background:rgba(37,99,235,.15);color:#60A5FA;'
                        f'border:1px solid rgba(37,99,235,.25);border-radius:99px;'
                        f'padding:2px 8px;font-size:.65rem;font-weight:700;margin-right:.3rem;">'
                        f'🔧 {html.escape(str(t).replace("_", " "))}</span>'
                        for t in tools
                    )
                    tools_html = (
                        f'<div style="margin-top:.5rem;padding-top:.4rem;'
                        f'border-top:1px solid {border_c};">{tool_chips}</div>'
                    )
                st.markdown(
                    f'<div style="display:flex;align-items:flex-start;gap:.7rem;margin-bottom:.75rem;">'
                    f'<div style="width:32px;height:32px;background:linear-gradient(135deg,#2563EB,#7C3AED);'
                    f'border-radius:50%;display:flex;align-items:center;justify-content:center;'
                    f'font-size:.9rem;flex-shrink:0;margin-top:2px;">🤖</div>'
                    f'<div style="max-width:80%;background:{ai_bub};color:{ai_text};'
                    f'border:1px solid {ai_border};border-radius:4px 18px 18px 18px;'
                    f'padding:.85rem 1.1rem;font-size:.9rem;line-height:1.6;'
                    f'box-shadow:0 2px 12px rgba(0,0,0,.12);">'
                    f'{html.escape(str(content)).replace(chr(10), "<br>")}'
                    f'{tools_html}'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )

    # ── Thinking indicator ─────────────────────────────────────────────────────
    if st.session_state.chat_thinking:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:.7rem;margin-bottom:.75rem;">'
            f'<div style="width:32px;height:32px;background:linear-gradient(135deg,#2563EB,#7C3AED);'
            f'border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:.9rem;">🤖</div>'
            f'<div style="background:{ai_bub};border:1px solid {ai_border};border-radius:4px 18px 18px 18px;'
            f'padding:.7rem 1.1rem;">'
            f'<span style="color:{muted_c};font-size:.85rem;font-style:italic;">AI is thinking</span>'
            f'<span style="color:#60A5FA;font-weight:700;"> ···</span>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    # ── Input bar ──────────────────────────────────────────────────────────────
    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
    with st.form("chat_input_form", clear_on_submit=True):
        inp_col, btn_col = st.columns([5, 1], gap="small")
        with inp_col:
            user_input = st.text_input(
                label="message",
                placeholder="Ask about your future…",
                label_visibility="collapsed",
                key="chat_input",
            )
        with btn_col:
            send_btn = st.form_submit_button("Send ➤", use_container_width=True)

    if send_btn and user_input.strip():
        msg = user_input.strip()
        st.session_state.chat_messages.append({"role": "user", "content": msg})
        st.session_state.chat_thinking = True
        st.rerun()

    # Process thinking state
    if st.session_state.chat_thinking and st.session_state.chat_messages:
        last = st.session_state.chat_messages[-1]
        if last["role"] == "user":
            streamed = []
            stream_placeholder = st.empty()
            try:
                for chunk in _stream_send(last["content"]):
                    streamed.append(str(chunk))
                    rendered = html.escape("".join(streamed)).replace(chr(10), "<br>")
                    stream_placeholder.markdown(
                        f'<div style="background:{ai_bub};color:{ai_text};border:1px solid {ai_border};'
                        f'border-radius:4px 18px 18px 18px;padding:.85rem 1.1rem;line-height:1.6;">'
                        f'{rendered}</div>',
                        unsafe_allow_html=True,
                    )
                response_text = "".join(streamed)
                if not response_text:
                    raise RuntimeError("The streaming response was empty")
                resp = {"response": response_text, "tools_used": [], "intent": "general"}
            except Exception:
                # Retry through the JSON endpoint when streaming is unavailable.
                resp = _send(last["content"])
            stream_placeholder.empty()
            st.session_state.chat_messages.append({
                "role":       "assistant",
                "content":    resp.get("response", "Sorry, I encountered an error."),
                "tools_used": resp.get("tools_used", []),
                "intent":     resp.get("intent", "general"),
            })
            st.session_state.chat_thinking = False
            st.rerun()

# ── History panel (right) ──────────────────────────────────────────────────────
with col_history:
    st.markdown(
        f'<div style="background:{header_bg};border:1px solid {border_c};'
        f'border-radius:18px;padding:1.1rem 1.4rem;margin-bottom:.75rem;">'
        f'<div style="font-size:.95rem;font-weight:700;color:{text_c};">💬 Conversation History</div>'
        f'<div style="font-size:.75rem;color:{muted_c};margin-top:.2rem;">Past conversations</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    convs = _list_conversations()
    if convs:
        for conv in convs[:15]:
            cid      = conv.get("conversation_id", "")
            preview  = conv.get("preview", "No preview")
            count    = conv.get("message_count", 0)
            last_at  = conv.get("last_message_at", "")[:10]
            is_active = cid == st.session_state.chat_conv_id

            bg_conv = "rgba(37,99,235,.12)" if is_active else ("rgba(248,250,255,.8)" if is_light else "rgba(13,17,28,.7)")
            bdr_conv = "#2563EB" if is_active else border_c

            st.markdown(
                f'<div style="background:{bg_conv};border:1px solid {bdr_conv};'
                f'border-radius:12px;padding:.75rem 1rem;margin-bottom:.4rem;">'
                f'<div style="font-size:.8rem;color:{text_c};font-weight:{"600" if is_active else "400"};'
                f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{html.escape(str(preview))}</div>'
                f'<div style="font-size:.68rem;color:{muted_c};margin-top:.25rem;">'
                f'{count} messages · {last_at}'
                f'{"  ✓ active" if is_active else ""}'
                f'</div></div>',
                unsafe_allow_html=True,
            )
            btn1, btn2 = st.columns(2, gap="small")
            with btn1:
                if st.button("Load", key=f"load_{cid}", use_container_width=True):
                    history = _load_history(cid)
                    st.session_state.chat_conv_id  = cid
                    st.session_state.chat_messages = [
                        {"role": m["role"], "content": m["content"],
                         "tools_used": m.get("tools_used", [])}
                        for m in history
                    ]
                    st.rerun()
            with btn2:
                if st.button("🗑", key=f"del_{cid}", use_container_width=True, help="Delete conversation"):
                    _delete_conv(cid)
                    if cid == st.session_state.chat_conv_id:
                        st.session_state.chat_conv_id  = str(uuid.uuid4())
                        st.session_state.chat_messages = []
                    st.rerun()
    else:
        st.markdown(
            f'<div style="text-align:center;padding:2rem 1rem;color:{muted_c};font-size:.85rem;">'
            f'No conversations yet.<br>Start chatting to build history.</div>',
            unsafe_allow_html=True,
        )

    # ── Quick stats ────────────────────────────────────────────────────────────
    if st.session_state.chat_messages:
        total_msgs = len(st.session_state.chat_messages)
        ai_msgs    = sum(1 for m in st.session_state.chat_messages if m["role"] == "assistant")
        tools_used = [t for m in st.session_state.chat_messages for t in m.get("tools_used", [])]
        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
        st.markdown(
            f'<div style="background:{ai_bub};border:1px solid {border_c};'
            f'border-radius:12px;padding:.85rem 1.1rem;">'
            f'<div style="font-size:.7rem;font-weight:700;color:{muted_c};text-transform:uppercase;'
            f'letter-spacing:.1em;margin-bottom:.4rem;">Current Session</div>'
            f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:.35rem;">'
            f'<div style="font-size:.78rem;color:{text_c};">Messages: <b>{total_msgs}</b></div>'
            f'<div style="font-size:.78rem;color:{text_c};">AI replies: <b>{ai_msgs}</b></div>'
            f'<div style="font-size:.78rem;color:{text_c};">Tools used: <b>{len(tools_used)}</b></div>'
            f'<div style="font-size:.78rem;color:#60A5FA;">Conv: <b>{st.session_state.chat_conv_id[:6]}…</b></div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )
