# Digital Twin AI — Milestone 4 Implementation Plan

## 1. Current Architecture (Milestones 1–3)

### Backend (FastAPI + SQLite)
- `backend/main.py` — 12 routers, analytics middleware, CORS
- `backend/app/core/` — config (Settings class, .env loading), database (SQLAlchemy 2.0), security (bcrypt + jose JWT)
- `backend/app/models/user.py` — 7 ORM models: User, FinancialRecord, StudyActivity, Goal, Habit, FitnessActivity, AnalyticsLog, SimulationResult
- `backend/app/api/routes/` — 12 route files covering all domains
- `backend/app/services/` — 7 services: analytics, digital_twin, forecasting, habit, recommendation, scenario, study
- `backend/app/ml/` — DigitalTwin class, SimulationEngine (16 simulate_* methods)
- `ml/` — training pipeline: Prophet, XGBoost, ARIMA, RandomForest

### Frontend (Streamlit)
- 9 pages: Login, Profile, Finance, Study, Habits & Fitness, Goals, Analytics, Forecasting, Simulation
- `components/theme.py` — dual dark/light CSS via `_build_css(dark)` function
- `components/ui.py` — shared widgets + `render_topbar()` + `render_sidebar()`

### Database (SQLite → PostgreSQL-ready)
- 8 tables, auto-created via `Base.metadata.create_all()` at startup
- Alembic migrations in `migrations/versions/`
- JSON stored as TEXT (swap to JSONB on PostgreSQL)

### Auth
- JWT Bearer tokens (python-jose), bcrypt passwords
- `get_current_user()` dependency in `auth.py`

### Existing Services (available to M4 AI tools)
| Service | Key Functions |
|---|---|
| `forecasting_service` | `generate_savings_projection`, `generate_expense_forecast`, `generate_cashflow_forecast` |
| `digital_twin_service` | `get_current_twin`, `run_simulation`, `generate_recommendations`, `generate_risk_analysis` |
| `analytics_service` | `get_full_analytics` (async, aggregates all ML) |
| `recommendation_service` | `generate_all_recommendations` |
| `scenario_service` | `best_future_path`, `compare_two_scenarios` |

---

## 2. Milestone 4 Implementation Status

| Feature | Status |
|---|---|
| Conversational AI, fallback, intent, safety, and tools | ✅ Implemented |
| Chat APIs, persistence, ownership, and rate limiting | ✅ Implemented |
| Streaming responses and frontend streaming | ✅ Implemented |
| RBAC APIs and inactive-user protection | ✅ Implemented |
| Enhanced period-aware dashboard | ✅ Implemented |
| PDF reports and authenticated downloads | ✅ Implemented |
| Equal-window period comparison | ✅ Implemented |
| Docker and CI/CD configuration | ✅ Implemented; Docker runtime pending environment verification |
| Comprehensive M4 tests | 🟡 Implemented; live provider and Docker E2E remain unverified |
| Documentation and release polish | 🟡 In progress |

---

## 3. Files To Create

### Backend
- `backend/app/api/routes/assistant.py` — POST /chat, GET /history/{id}, DELETE /history/{id}
- `backend/app/api/routes/reports.py` — GET /generate, GET /comparison
- `backend/app/api/routes/admin.py` — GET /users, GET /analytics-global
- `backend/app/services/conversational_ai.py` — LangChain + GPT-4o + 4 tools + intent + memory
- `backend/app/services/report_service.py` — PDF generation with fpdf2
- `backend/migrations/versions/003_add_chat_and_roles.py`

### Frontend
- `frontend/pages/9_Chat.py` — Chat UI with streaming
- `frontend/pages/10_Dashboard.py` — Enhanced dashboard with period selector

### Infrastructure
- `docker/Dockerfile.backend`
- `docker/Dockerfile.frontend`
- `docker-compose.yml`
- `.github/workflows/ci.yml`

### Tests
- `tests/test_assistant.py`
- `tests/test_reports.py`

### Documentation
- `docs/MILESTONE_4_IMPLEMENTATION_PLAN.md` ← this file
- `docs/FINAL_REPORT.md`
- `docs/TECHNICAL_INTERVIEW.md`
- `docs/DEMO_SCRIPT.md`
- `docs/UAT_REPORT.md`
- `docs/PERFORMANCE_FINAL.md`
- `README.md` (major update)

---

## 4. Files To Modify

| File | Change |
|---|---|
| `backend/app/models/user.py` | Add `ConversationMessage` model, add `role` field to `User` |
| `backend/app/core/config.py` | Add `OPENAI_API_KEY`, `OPENAI_MODEL`, `RATE_LIMIT_*`, `REDIS_URL` |
| `backend/main.py` | Register assistant, reports, admin routers |
| `requirements.txt` | Add openai, langchain*, fpdf2, reportlab, redis, requests |
| `.env.example` | Add all new env vars |
| `frontend/components/ui.py` | Add Chat + Dashboard links to sidebar |

---

## 5. New Dependencies

```
openai>=1.30.0
langchain>=0.2.0
langchain-openai>=0.1.0
langchain-community>=0.2.0
fpdf2>=2.7.0
redis>=5.0.0
requests>=2.31.0
bandit>=1.7.0
black>=24.0.0
```

---

## 6. Implementation Order

1. packages + config
2. DB model (ConversationMessage + User.role)
3. conversational_ai.py (the AI engine)
4. assistant API routes
5. Register router + migration
6. Safety + rate limiting
7. RBAC
8. Chat UI (Streamlit)
9. Dashboard page
10. Reports service + routes
11. Period comparison
12. Docker
13. CI/CD
14. Tests
15. Documentation and release verification

---

## 7. Testing Strategy

- **Unit**: intent classifier, safety filter, tool functions, PDF generation
- **Integration**: chat → tool → service → DB, full API flow
- **E2E**: register → data → chat → report
- **Security**: auth bypass, IDOR, rate limit enforcement

---

## 8. Risks

| Risk | Mitigation |
|---|---|
| OpenAI key not available | Graceful degradation, clear error message |
| LangChain API breaking changes | Pin version, test on install |
| PDF generation slow | Background task, async |
| SQLite concurrency | Acceptable for dev; Docker uses PostgreSQL |
| Streaming in Streamlit | Use `st.write_stream()` with generator |
