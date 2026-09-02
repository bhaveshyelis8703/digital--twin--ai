"""
backend/app/services/conversational_ai.py

Milestone 4 — Digital Twin Conversational AI Engine.

Architecture:
  1. Intent classification  →  forecast | simulate | advice | explain | general
  2. Dynamic system prompt  →  injects real user data from existing services
  3. LangChain tool calling →  4 tools wired to real backend services
  4. Conversation memory    →  last-10-exchange window, keyed by conversation_id
  5. Streaming support      →  yields tokens via generator
  6. Safety filters         →  refuse dangerous financial instructions
  7. Graceful degradation   →  works without API key (returns helpful error)

All data flows through existing service functions — NEVER hardcoded.
"""
from __future__ import annotations

import json
import logging
import re
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Generator

logger = logging.getLogger(__name__)

# ── path bootstrap ────────────────────────────────────────────────────────────
_BACKEND = Path(__file__).resolve().parents[2]
_ROOT    = _BACKEND.parent
for _p in [str(_ROOT), str(_BACKEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── in-process conversation memory  (conversation_id → list[dict]) ────────────
# Each entry: {"role": "user"|"assistant", "content": str}
_MEMORY: dict[str, list[dict]] = defaultdict(list)
_MEMORY_MAX_TURNS = 10  # keep last 10 exchanges (20 messages)


# ═══════════════════════════════════════════════════════════════════════════════
# SAFETY FILTER
# ═══════════════════════════════════════════════════════════════════════════════

_UNSAFE_PATTERNS = [
    r"\b(gambl\w*|bet\b|casino|poker|lottery|ponzi|pyramid scheme)\b",
    r"borrow.*invest|loan.*crypto|loan.*stock|leverage.*gambl",
    r"get rich quick|guaranteed return|100\s*%.*profit",
    r"money laundering|tax evasion|fraud\b",
]
_UNSAFE_COMPILED = [re.compile(p, re.IGNORECASE) for p in _UNSAFE_PATTERNS]

_SAFETY_REFUSAL = (
    "I can't provide guidance on that request as it involves high financial risk "
    "or potentially harmful activity. Instead, I'd encourage you to focus on "
    "sustainable strategies: building an emergency fund, diversifying savings, "
    "and working with a qualified financial advisor for high-stakes decisions."
)


def _is_unsafe(message: str) -> bool:
    """Return True if the message matches known unsafe/harmful patterns."""
    return any(p.search(message) for p in _UNSAFE_COMPILED)


# ═══════════════════════════════════════════════════════════════════════════════
# INTENT CLASSIFICATION
# ═══════════════════════════════════════════════════════════════════════════════

_INTENT_PATTERNS: dict[str, list[str]] = {
    "forecast": [
        r"\b(forecast|predict|project|next year|next month|in \d+ year|will i save|how much.*save|future|trajectory|trend.*future|expected|project\w*)\b",
        r"will i (be able|manage|have|reach|achieve|save|earn)",
        r"how much (will|would|can|could) i (save|earn|have|accumulate)",
    ],
    "simulate": [
        r"\b(what if|simulate|scenario|if i (invest|save|cut|increase|reduce|start|stop|add|remove))\b",
        r"\b(impact of|effect of|suppose|hypothetical|what would happen)\b",
    ],
    "advice": [
        r"\b(how (can|do|should) i|advice|recommend|suggest|improve|better|tips|strategy)\b",
        r"\b(should i|what.*best|how to (save|invest|spend|reduce|improve))\b",
    ],
    "explain": [
        r"\b(why|explain|reason|cause|because|how does|tell me about|understand)\b",
        r"\b(my .*(score|index|trend|drop|decrease|increase) .*(fell|went|changed|is))\b",
    ],
}
_INTENT_COMPILED: dict[str, list] = {
    k: [re.compile(p, re.IGNORECASE) for p in patterns]
    for k, patterns in _INTENT_PATTERNS.items()
}


def classify_intent(message: str) -> str:
    """
    Classify user message into one of: forecast, simulate, advice, explain, general.
    Uses regex first; falls back to 'general'.
    """
    for intent, patterns in _INTENT_COMPILED.items():
        if any(p.search(message) for p in patterns):
            return intent
    return "general"


# ═══════════════════════════════════════════════════════════════════════════════
# USER CONTEXT BUILDER  (real data, never hardcoded)
# ═══════════════════════════════════════════════════════════════════════════════

def _build_user_context(user_id: int) -> dict[str, Any]:
    """
    Fetch current user state from existing services.
    Returns dict used to build the system prompt.
    Swallows individual service failures — partial context is better than none.
    """
    ctx: dict[str, Any] = {"user_id": user_id, "fetched_at": datetime.utcnow().isoformat()}

    # Digital Twin current state
    try:
        from app.services.digital_twin_service import get_current_twin
        state = get_current_twin(user_id)
        ctx["twin_state"] = state
        ctx["financial"]  = state.get("financial", {})
        ctx["study"]      = state.get("study", {})
        ctx["habits"]     = state.get("habits", {})
        ctx["fitness"]    = state.get("fitness", {})
        ctx["goals"]      = state.get("goals", [])
        ctx["productivity_score"] = state.get("productivity_score", 0)
        ctx["risk_score"]         = state.get("risk_score", 0)
    except Exception as exc:
        logger.warning("Could not load twin state for user %s: %s", user_id, exc)

    # User profile
    try:
        from app.core.database import SessionLocal
        from app.models.user import User
        db = SessionLocal()
        try:
            u = db.query(User).filter(User.id == user_id).first()
            if u:
                ctx["profile"] = {
                    "name": u.name, "age": u.age, "occupation": u.occupation,
                    "email": u.email,
                }
        finally:
            db.close()
    except Exception as exc:
        logger.warning("Could not load profile for user %s: %s", user_id, exc)

    # Recommendations
    try:
        from app.services.recommendation_service import generate_all_recommendations
        recs = generate_all_recommendations(user_id)
        ctx["recommendations"] = recs.get("recommendations", [])[:3]
    except Exception as exc:
        logger.warning("Could not load recommendations for user %s: %s", user_id, exc)

    # Risk analysis
    try:
        from app.services.digital_twin_service import generate_risk_analysis
        ctx["risk_analysis"] = generate_risk_analysis(user_id)
    except Exception as exc:
        logger.warning("Could not load risk analysis for user %s: %s", user_id, exc)

    return ctx


def _build_system_prompt(ctx: dict[str, Any]) -> str:
    """Build a rich, data-grounded system prompt from user context."""
    profile   = ctx.get("profile", {})
    financial = ctx.get("financial", {})
    study     = ctx.get("study", {})
    habits    = ctx.get("habits", {})
    fitness   = ctx.get("fitness", {})
    goals     = ctx.get("goals", [])
    recs      = ctx.get("recommendations", [])
    risk      = ctx.get("risk_analysis", {})

    name       = profile.get("name", "the user")
    age        = profile.get("age", "unknown")
    occupation = profile.get("occupation", "unknown")

    fin_income  = financial.get("monthly_avg_income", 0)
    fin_expense = financial.get("monthly_avg_expenses", 0)
    fin_savings = financial.get("net_savings", 0)
    fin_rate    = financial.get("savings_rate", 0)
    fin_top_cat = financial.get("top_expense_category", "unknown")

    prod_score   = ctx.get("productivity_score", 0)
    risk_score   = ctx.get("risk_score", 0)
    risk_level   = risk.get("risk_level", "unknown")

    study_perf   = study.get("avg_performance_score", 0)
    study_hrs    = study.get("avg_study_hours", 0)
    habit_rate   = habits.get("completion_rate", 0)
    habit_streak = habits.get("best_streak", 0)
    fit_sessions = fitness.get("sessions_per_week", 0)
    fit_cal      = fitness.get("avg_calories", 0)

    goals_summary = ""
    for g in goals[:5]:
        goals_summary += (
            f"\n  - {g.get('name','?')}: {g.get('progress_pct',0):.0f}% complete "
            f"({g.get('days_remaining',0)} days left, {'on track' if g.get('on_track') else 'behind'})"
        )

    recs_summary = ""
    for r in recs[:3]:
        recs_summary += f"\n  - [{r.get('priority','').upper()}] {r.get('title','')}: {r.get('description','')[:120]}"

    return f"""You are the Digital Twin AI assistant for {name}.

IMPORTANT RULES:
1. ALWAYS use the real data provided below — never invent numbers.
2. When data is missing, say so clearly rather than guessing.
3. Be concise (3-5 sentences) unless the user asks for detail.
4. Distinguish actual data from predictions/simulations.
5. Explain assumptions when using projections.
6. Never give reckless financial advice. Recommend professional consultation for major decisions.
7. Use the available tools (get_savings_projection, run_simulation, get_current_analytics, get_recommendations) when a question requires fresh calculations.

USER PROFILE:
- Name: {name}
- Age: {age}
- Occupation: {occupation}

CURRENT FINANCIAL STATE (real data from database):
- Monthly income: ${fin_income:,.0f}
- Monthly expenses: ${fin_expense:,.0f}
- Net savings (all time): ${fin_savings:,.0f}
- Savings rate: {fin_rate*100:.1f}%
- Largest expense category: {fin_top_cat}

PRODUCTIVITY & WELLNESS:
- Productivity score: {prod_score:.0f}/100
- Risk score: {risk_score:.0f}/100 ({risk_level} risk)
- Study avg performance: {study_perf:.0f}/100 | Avg hours/session: {study_hrs:.1f}h
- Habit completion rate: {habit_rate*100:.0f}% | Best streak: {habit_streak} days
- Fitness: {fit_sessions:.1f} sessions/week | Avg {fit_cal:.0f} cal/session

ACTIVE GOALS:{goals_summary if goals_summary else " No goals defined yet."}

TOP RECOMMENDATIONS:{recs_summary if recs_summary else " No recommendations available yet."}

Current date: {datetime.utcnow().strftime('%B %d, %Y')}

When the user asks about forecasts, savings projections, or simulations, use the appropriate tool to get fresh calculated results rather than estimating manually.
"""


# ═══════════════════════════════════════════════════════════════════════════════
# LANGCHAIN TOOLS  (wired to real backend services)
# ═══════════════════════════════════════════════════════════════════════════════

def _make_tools(user_id: int):
    """Create 4 LangChain tools bound to the authenticated user."""
    try:
        from langchain.tools import tool
    except ImportError:
        return []

    @tool
    def get_savings_projection(months: int = 12) -> str:
        """
        Get a savings projection for the next N months using the Prophet ML model.
        Use this when the user asks about future savings, financial trajectory, or
        'will I save X amount?'.
        Args:
            months: Number of months to project (1-36).
        """
        try:
            from app.services.forecasting_service import generate_savings_projection
            months = max(1, min(36, int(months)))
            result = generate_savings_projection(user_id, months)
            if not result:
                return "No savings projection available — insufficient financial data."
            total = sum(r.get("predicted_savings", 0) for r in result)
            final = result[-1].get("predicted_savings", 0) if result else 0
            first = result[0].get("predicted_savings", 0) if result else 0
            growth = ((final - first) / abs(first) * 100) if first != 0 else 0
            return (
                f"Savings projection over {months} months:\n"
                f"- Projected total savings accumulation: ${total:,.0f}\n"
                f"- End-of-period monthly savings: ${final:,.0f}\n"
                f"- Growth from month 1: {growth:+.1f}%\n"
                f"- Data points: {len(result)} monthly forecasts\n"
                f"Note: Based on Prophet ML model trained on your transaction history."
            )
        except Exception as exc:
            logger.error("get_savings_projection tool error: %s", exc)
            return f"Could not generate savings projection: {exc}"

    @tool
    def run_simulation(decision_type: str, parameters: str = "{}") -> str:
        """
        Run a what-if simulation for a financial, study, habit, or fitness decision.
        Use this when the user asks 'what if I...' or wants to model a decision.
        Args:
            decision_type: One of: financial.savings_increase, financial.expense_reduction,
                          financial.investment_growth, financial.loan_impact,
                          study.extra_hours, habit.new_habit, fitness.workout_plan, full
            parameters: JSON string with simulation parameters, e.g.
                       '{"monthly_increase": 500, "horizon_months": 12}'
        """
        try:
            from app.services.digital_twin_service import run_simulation as svc_sim
            try:
                params = json.loads(parameters) if isinstance(parameters, str) else parameters
            except json.JSONDecodeError:
                params = {}

            result = svc_sim(user_id, decision_type, params)
            if "error" in result:
                return f"Simulation error: {result['error']}"

            cur   = result.get("current_state", {})
            fut   = result.get("future_state", {})
            diff  = result.get("difference", {})
            conf  = result.get("confidence_score", 0)
            recs  = result.get("recommendations", [])

            summary_lines = [
                f"Simulation: {result.get('simulation_type','').replace('_',' ').title()}",
                f"Confidence: {conf*100:.0f}%",
            ]
            for k in list(diff.keys())[:4]:
                v = diff.get(k)
                if isinstance(v, (int, float)):
                    cur_v = cur.get(k, 0)
                    fut_v = fut.get(k, 0)
                    summary_lines.append(
                        f"- {k.replace('_',' ').title()}: {cur_v:,.2f} → {fut_v:,.2f} "
                        f"(Δ {v:+,.2f})"
                    )
            if recs:
                summary_lines.append("Key recommendation: " + recs[0])

            return "\n".join(summary_lines)
        except Exception as exc:
            logger.error("run_simulation tool error: %s", exc)
            return f"Could not run simulation: {exc}"

    @tool
    def get_current_analytics() -> str:
        """
        Get the full analytics report including financial, study, and habit analysis.
        Use this when the user asks about their overall performance, productivity,
        or wants a summary of their current state.
        """
        try:
            import asyncio
            from app.services.analytics_service import get_full_analytics

            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, get_full_analytics(user_id))
                    data = future.result(timeout=15)
            except RuntimeError:
                data = asyncio.run(get_full_analytics(user_id))

            fin_data  = data.get("financial", {})
            study_data = data.get("study", {})
            habit_data = data.get("habits", {})

            savings_fc = fin_data.get("savings_projection", [])
            next_month = savings_fc[0].get("predicted_savings", 0) if savings_fc else 0

            readiness  = study_data.get("exam_readiness", {})
            prod_idx   = habit_data.get("productivity_index", {})

            return (
                f"Current Analytics Summary:\n"
                f"Financial:\n"
                f"  - Projected savings next month: ${next_month:,.0f}\n"
                f"  - Cashflow trend: {len(fin_data.get('cashflow_forecast', []))} months forecasted\n"
                f"Study:\n"
                f"  - Exam readiness score: {readiness.get('score', 0):.0f}/100 "
                f"({readiness.get('interpretation', 'N/A')})\n"
                f"  - Study trend: {study_data.get('trend', {}).get('trend', 'unknown')}\n"
                f"Habits & Productivity:\n"
                f"  - Productivity index: {prod_idx.get('productivity_index', 0):.0f}/100 "
                f"({prod_idx.get('interpretation', 'N/A')})\n"
                f"  - Trend: {habit_data.get('productivity_trend', {}).get('trend', 'unknown')}"
            )
        except Exception as exc:
            logger.error("get_current_analytics tool error: %s", exc)
            return f"Could not retrieve analytics: {exc}"

    @tool
    def get_recommendations() -> str:
        """
        Get the top AI-generated recommendations for this user based on their current data.
        Use this when the user asks how to improve, what they should focus on, or
        what their biggest risks/opportunities are.
        """
        try:
            from app.services.recommendation_service import generate_all_recommendations
            data = generate_all_recommendations(user_id)
            recs = data.get("recommendations", [])
            health = data.get("overall_health_score", 0)

            if not recs:
                return "No recommendations available yet — add more data across domains."

            lines = [f"Overall Health Score: {health:.0f}/100\n", "Top Recommendations:"]
            for i, r in enumerate(recs[:5], 1):
                priority = r.get("priority", "").upper()
                domain   = r.get("domain", "").upper()
                title    = r.get("title", "")
                desc     = r.get("description", "")[:150]
                actions  = r.get("action_steps", [])
                first_action = actions[0] if actions else ""
                lines.append(
                    f"{i}. [{domain} | {priority}] {title}\n"
                    f"   {desc}\n"
                    f"   → Action: {first_action}"
                )
            return "\n".join(lines)
        except Exception as exc:
            logger.error("get_recommendations tool error: %s", exc)
            return f"Could not retrieve recommendations: {exc}"

    return [get_savings_projection, run_simulation, get_current_analytics, get_recommendations]


# ═══════════════════════════════════════════════════════════════════════════════
# MEMORY MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def get_memory(conversation_id: str) -> list[dict]:
    """Return the in-process memory for a conversation."""
    return _MEMORY[conversation_id]


def add_to_memory(conversation_id: str, role: str, content: str) -> None:
    """Append a message to the conversation memory, trimming to window size."""
    _MEMORY[conversation_id].append({"role": role, "content": content})
    # Keep only the last _MEMORY_MAX_TURNS exchanges (2 × turns = messages)
    max_msgs = _MEMORY_MAX_TURNS * 2
    if len(_MEMORY[conversation_id]) > max_msgs:
        _MEMORY[conversation_id] = _MEMORY[conversation_id][-max_msgs:]


def clear_memory(conversation_id: str) -> None:
    """Remove a conversation from in-process memory."""
    _MEMORY.pop(conversation_id, None)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ASSISTANT FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def chat(
    user_id: int,
    message: str,
    conversation_id: str,
) -> dict[str, Any]:
    """
    Process a user message and return an AI response.

    Returns:
        {
            "response": str,
            "tools_used": list[str],
            "conversation_id": str,
            "intent": str,
            "response_time_ms": float,
        }
    """
    t_start = time.perf_counter()

    # Safety check
    if _is_unsafe(message):
        return {
            "response": _SAFETY_REFUSAL,
            "tools_used": [],
            "conversation_id": conversation_id,
            "intent": "refused",
            "response_time_ms": round((time.perf_counter() - t_start) * 1000, 2),
        }

    # Classify intent
    intent = classify_intent(message)

    # Check for OpenAI key
    from app.core.config import settings
    if not settings.OPENAI_API_KEY:
        fallback = _fallback_response(user_id, message, intent)
        return {
            "response": fallback,
            "tools_used": [],
            "conversation_id": conversation_id,
            "intent": intent,
            "response_time_ms": round((time.perf_counter() - t_start) * 1000, 2),
        }

    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    except ImportError as exc:
        logger.error("LangChain import error: %s", exc)
        fallback = _fallback_response(user_id, message, intent)
        return {
            "response": fallback,
            "tools_used": [],
            "conversation_id": conversation_id,
            "intent": intent,
            "response_time_ms": round((time.perf_counter() - t_start) * 1000, 2),
        }

    try:
        # Build context + system prompt
        ctx     = _build_user_context(user_id)
        sys_msg = _build_system_prompt(ctx)

        # Build message history for LangChain
        history = get_memory(conversation_id)
        lc_messages = [SystemMessage(content=sys_msg)]
        for h in history:
            if h["role"] == "user":
                lc_messages.append(HumanMessage(content=h["content"]))
            else:
                lc_messages.append(AIMessage(content=h["content"]))
        lc_messages.append(HumanMessage(content=message))

        # Build tools and LLM
        tools = _make_tools(user_id)
        llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE,
            max_tokens=settings.OPENAI_MAX_TOKENS,
        )

        tools_used: list[str] = []

        if tools:
            llm_with_tools = llm.bind_tools(tools)
            ai_msg = llm_with_tools.invoke(lc_messages)

            # Process tool calls if any
            response_text = ""
            if hasattr(ai_msg, "tool_calls") and ai_msg.tool_calls:
                from langchain_core.messages import ToolMessage
                tool_map = {t.name: t for t in tools}
                tool_results = []

                for tc in ai_msg.tool_calls:
                    tool_name = tc["name"]
                    tool_args = tc.get("args", {})
                    tools_used.append(tool_name)

                    if tool_name in tool_map:
                        try:
                            tool_fn = tool_map[tool_name]
                            result  = tool_fn.invoke(tool_args)
                        except Exception as te:
                            result = f"Tool error: {te}"
                    else:
                        result = f"Unknown tool: {tool_name}"

                    tool_results.append(ToolMessage(
                        content=str(result),
                        tool_call_id=tc["id"],
                    ))

                # Second pass: LLM interprets tool results
                lc_messages.append(ai_msg)
                lc_messages.extend(tool_results)
                final_msg = llm.invoke(lc_messages)
                response_text = final_msg.content or ""
            else:
                response_text = ai_msg.content or ""
        else:
            # No tools available
            ai_msg = llm.invoke(lc_messages)
            response_text = ai_msg.content or ""

        # Update memory
        add_to_memory(conversation_id, "user", message)
        add_to_memory(conversation_id, "assistant", response_text)

        return {
            "response": response_text,
            "tools_used": tools_used,
            "conversation_id": conversation_id,
            "intent": intent,
            "response_time_ms": round((time.perf_counter() - t_start) * 1000, 2),
        }

    except Exception as exc:
        logger.error("AI chat error for user %s: %s", user_id, exc, exc_info=True)
        error_msg = _friendly_error(exc)
        return {
            "response": error_msg,
            "tools_used": [],
            "conversation_id": conversation_id,
            "intent": intent,
            "response_time_ms": round((time.perf_counter() - t_start) * 1000, 2),
        }


def stream_chat(
    user_id: int,
    message: str,
    conversation_id: str,
) -> Generator[str, None, None]:
    """
    Stream AI response tokens. Yields string chunks.
    Falls back to a single-chunk response if streaming is unavailable.
    """
    if _is_unsafe(message):
        yield _SAFETY_REFUSAL
        return

    from app.core.config import settings
    if not settings.OPENAI_API_KEY:
        yield _fallback_response(user_id, message, classify_intent(message))
        return

    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

        ctx     = _build_user_context(user_id)
        sys_msg = _build_system_prompt(ctx)
        history = get_memory(conversation_id)

        lc_messages = [SystemMessage(content=sys_msg)]
        for h in history:
            cls = HumanMessage if h["role"] == "user" else AIMessage
            lc_messages.append(cls(content=h["content"]))
        lc_messages.append(HumanMessage(content=message))

        llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE,
            max_tokens=settings.OPENAI_MAX_TOKENS,
            streaming=True,
        )

        tools = _make_tools(user_id)
        llm_with_tools = llm.bind_tools(tools) if tools else llm
        initial_msg = llm_with_tools.invoke(lc_messages)
        tool_calls = getattr(initial_msg, "tool_calls", [])

        if tool_calls:
            tool_map = {tool_fn.name: tool_fn for tool_fn in tools}
            tool_results = []
            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call.get("args", {})
                tool_fn = tool_map.get(tool_name)
                if tool_fn is None:
                    result = f"Unknown tool: {tool_name}"
                else:
                    try:
                        result = tool_fn.invoke(tool_args)
                    except Exception as tool_error:
                        result = f"Tool error: {tool_error}"
                tool_results.append(
                    ToolMessage(content=str(result), tool_call_id=tool_call["id"])
                )
            lc_messages.append(initial_msg)
            lc_messages.extend(tool_results)

        full_response = ""
        response_stream = llm.stream(lc_messages) if tool_calls else [initial_msg]
        for chunk in response_stream:
            token = chunk.content or ""
            full_response += token
            yield token

        # Save to memory after streaming completes
        add_to_memory(conversation_id, "user", message)
        add_to_memory(conversation_id, "assistant", full_response)

    except Exception as exc:
        logger.error("Streaming error for user %s: %s", user_id, exc)
        yield _friendly_error(exc)


# ═══════════════════════════════════════════════════════════════════════════════
# FALLBACK + ERROR HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _fallback_response(user_id: int, message: str, intent: str) -> str:
    """
    Rule-based response when LLM is unavailable.
    Uses real data where possible.
    """
    try:
        ctx = _build_user_context(user_id)
        fin = ctx.get("financial", {})
        name = ctx.get("profile", {}).get("name", "there")

        if intent == "forecast":
            monthly_savings = fin.get("monthly_avg_income", 0) - fin.get("monthly_avg_expenses", 0)
            return (
                f"Hi {name}! Based on your current data: you save approximately "
                f"${monthly_savings:,.0f}/month. Over 12 months that projects to "
                f"${monthly_savings * 12:,.0f} additional savings. "
                f"For a detailed ML-powered forecast, please configure your OpenAI API key."
            )
        elif intent == "simulate":
            return (
                f"Hi {name}! I can run simulations on your data once an OpenAI API key is configured. "
                f"Your current savings rate is {fin.get('savings_rate', 0)*100:.1f}%. "
                f"Try the Simulation page for what-if scenarios without AI."
            )
        elif intent == "advice":
            recs = ctx.get("recommendations", [])
            if recs:
                top = recs[0]
                return (
                    f"Hi {name}! Top recommendation for you: [{top.get('domain','').upper()}] "
                    f"{top.get('title','')} — {top.get('description','')[:200]}"
                )
            return f"Hi {name}! Add more data to your profile to receive personalized recommendations."
        else:
            return (
                f"Hi {name}! I'm your Digital Twin AI assistant. To enable AI-powered responses, "
                f"please set your OPENAI_API_KEY in the .env file. "
                f"Your current productivity score is {ctx.get('productivity_score', 0):.0f}/100."
            )
    except Exception:
        return (
            "I'm your Digital Twin AI assistant. To enable full AI capabilities, "
            "please configure your OPENAI_API_KEY in the .env file."
        )


def _friendly_error(exc: Exception) -> str:
    """Convert raw exceptions into user-friendly messages."""
    msg = str(exc).lower()
    if "api key" in msg or "authentication" in msg or "401" in msg:
        return (
            "I couldn't connect to the AI service — your OpenAI API key may be invalid or missing. "
            "Please check your OPENAI_API_KEY in the .env file."
        )
    if "rate limit" in msg or "429" in msg:
        return (
            "The AI service is temporarily rate-limited. Please wait a moment and try again."
        )
    if "timeout" in msg or "connect" in msg:
        return (
            "I couldn't reach the AI service right now. Please check your internet connection "
            "and try again in a moment."
        )
    return (
        "I encountered an issue processing your request. Please try again. "
        "If this persists, check the application logs."
    )
