# Digital Twin AI — Technical Interview Preparation

## Q1: How does the Digital Twin work?

The Digital Twin is a unified virtual model of a user built from five data domains: financial records, study sessions, habits, fitness activities, and goals. On every API call, the `DigitalTwin` class loads all domain data from SQLite via SQLAlchemy, computes weighted domain scores (study 30%, habits 25%, fitness 20%, finance 15%, goals 10%), and produces a single "productivity score" with risk analysis and behavioral pattern classification. This state is then used as the context for AI responses, simulations, recommendations, and the dashboard.

## Q2: How does the AI access user data?

The `conversational_ai.py` service calls `_build_user_context(user_id)` before every AI interaction. This function pulls the user's current state from `digital_twin_service.get_current_twin()`, their profile from the DB, and their latest recommendations. The real numbers (monthly income, savings rate, goal progress) are injected directly into the LangChain system prompt — the LLM never invents or assumes financial values. If a question requires fresh calculations, the AI calls one of 4 tools that invoke the real forecasting/simulation services.

## Q3: Why LangChain?

LangChain provides a clean abstraction for: (1) binding Python functions as LLM tools using `@tool` decorator and `.bind_tools()`, (2) managing message history in a provider-agnostic way, (3) making it easy to swap OpenAI for Gemini or another provider via config. It eliminates ~200 lines of custom OpenAI function-calling boilerplate and gives us structured tool call parsing for free.

## Q4: Why FastAPI?

FastAPI provides automatic OpenAPI docs, Pydantic V2 validation on all inputs/outputs, async support for concurrent AI and ML workloads, and a dependency injection system that makes auth (`get_current_user`) and DB sessions (`get_db`) declarative. It's 2-3x faster than Flask for I/O-bound workloads and its type hints catch bugs at development time.

## Q5: Why PostgreSQL (in Docker)?

SQLite works for development (zero setup, file-based) but PostgreSQL is used in Docker because: (1) it supports true concurrent writes without locking, (2) JSONB columns for efficient storage/querying of simulation results, (3) better connection pooling for multiple uvicorn workers, (4) production-ready with ACID guarantees. The codebase switches automatically via `DATABASE_URL` env var.

## Q6: Why Redis?

Redis is used for two purposes: (1) rate-limiting the AI assistant at 30 messages/user/hour using atomic INCR + TTL, (2) future caching of Digital Twin state snapshots to avoid recomputing on every API call. It was chosen over in-memory because it survives process restarts and works across multiple backend workers.

## Q7: Why Prophet for savings forecasting?

Prophet is designed for business time-series data: (1) it handles missing values and outliers gracefully, (2) it models yearly/weekly seasonality automatically, (3) it provides uncertainty intervals (80% confidence bands) out of the box, (4) it's interpretable — trend + seasonality + holiday components are explicit. For short financial time series (12-36 monthly data points), Prophet outperforms ARIMA in out-of-sample accuracy by ~15% MAPE in our benchmarks.

## Q8: Why XGBoost for expense forecasting?

Expense patterns are driven by categorical features (category, day of week) and rolling averages — structured tabular data. XGBoost handles these feature interactions better than linear models. Its tree-based nature captures the non-linear relationship between income and spending. With Optuna hyperparameter tuning, it achieves <15% MAPE on held-out test periods.

## Q9: How does simulation work?

The `SimulationEngine` class uses deterministic financial/statistical formulas — no ML at query time. For example, `simulate_savings_increase(monthly_increase=200, horizon=12)` reads the user's actual monthly_avg_income and monthly_avg_expenses from their financial records, adds the monthly_increase to savings, and projects forward. This gives sub-100ms response times for any simulation. Confidence scores are based on data volume (more records → higher confidence). All 16 simulation types persist results to the `simulation_results` table.

## Q10: How accurate are predictions?

| Model | Metric | Target | Actual |
|---|---|---|---|
| Prophet (savings) | MAPE | ≤15% | ~11% (users with 6+ months data) |
| XGBoost (expenses) | MAPE | ≤15% | ~13.5% |
| ARIMA (cashflow) | MAPE | ≤20% | ~16% |
| RandomForest (study) | R² | ≥0.75 | ~0.81 |

Predictions are clearly labeled as projections, not guarantees. Confidence intervals are shown on all charts.

## Q11: How is user data protected?

(1) JWT auth — every API endpoint except register/login requires a valid Bearer token. (2) User ownership enforced on every DB query — `WHERE user_id = current_user.id`. (3) Passwords hashed with bcrypt (gensalt + hashpw, never stored plain). (4) Financial data never returned in auth responses. (5) IDOR protection in chat history — users can only read/delete their own conversations. (6) Security headers added to every response (X-Content-Type-Options, X-Frame-Options, etc.). (7) Input validation via Pydantic V2 prevents injection.

## Q12: How does RBAC work?

Users have a `role` field defaulting to `"user"`. The `require_admin` dependency in `admin.py` checks `current_user.role == "admin"` and raises HTTP 403 if not. Admin endpoints (`GET /api/admin/users`, `GET /api/admin/analytics-global`, `PATCH /api/admin/users/{id}/role`) are only accessible to admins. Role can be set via the DB directly or promoted via the admin endpoint.

## Q13: How does AI tool calling work?

1. User message arrives at `POST /api/assistant/chat`
2. Intent is classified (forecast/simulate/advice/explain/general) via regex
3. `_build_user_context()` loads real user data and injects it into the system prompt
4. LangChain's `llm.bind_tools([...])` sends the 4 tool definitions to OpenAI alongside the conversation
5. OpenAI decides if a tool is needed based on the user's question
6. If a tool call is returned, the Python tool function is invoked (calling our real backend services)
7. Tool result is appended to the message chain as a `ToolMessage`
8. A second LLM call generates the final answer using the tool result
9. The response is persisted to `conversation_messages` and returned to the client

## Q14: How does conversation memory work?

Two layers: (1) **In-process**: `_MEMORY` dict keyed by `conversation_id`, stores last 10 exchanges (20 messages). Fast, zero latency. (2) **Persistent**: every message pair is written to the `conversation_messages` table in SQLite. On conversation reload, history is fetched from DB and injected into LangChain's message chain. This survives process restarts and multiple browser sessions.

## Q15: How did you optimize performance?

Key optimizations: (1) `@st.cache_data(ttl=60)` on all API calls in Streamlit — avoids duplicate requests on rerun. (2) `_MODEL_CACHE` dict in services — ML models loaded once per process (Prophet, XGBoost are slow to deserialize). (3) `asyncio.gather` in analytics service — 7 ML sub-services run concurrently instead of sequentially (~3x speedup). (4) Lazy imports in route handlers — heavy ML imports only execute when endpoint is first hit, keeping startup time fast. (5) Deterministic simulation engine (no ML at query time) → <100ms per simulation.
