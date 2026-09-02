# 🧠 Digital Twin AI

> A personal life simulation platform that creates your virtual twin — modeling finances, productivity, habits, fitness, and goals — powered by ML forecasting, AI simulations, and a conversational AI assistant.

![Version](https://img.shields.io/badge/version-4.0.0-blue)
![Python](https://img.shields.io/badge/python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.37-red)
![LangChain](https://img.shields.io/badge/LangChain-0.2-purple)

---

## Problem Statement

People make financial and lifestyle decisions without accurate projections of their consequences. Digital Twin AI creates a personalized virtual model that answers: *"Will I be able to save $50K in 3 years?"* using your **actual data** — not generic advice.

---

## Architecture

```
Streamlit Frontend (11 pages)
        │
        │ REST API (JWT auth)
        ▼
FastAPI Backend v4.0.0 (15 route groups)
        │
        ├── Service Layer (9 services)
        │       ├── conversational_ai (LangChain + GPT-4o)
        │       ├── digital_twin (unified state model)
        │       ├── simulation_engine (16 deterministic simulations)
        │       ├── forecasting (Prophet + XGBoost + ARIMA)
        │       ├── recommendation (rule-based AI)
        │       └── report (fpdf2 PDF generation)
        │
        ├── ML Layer
        │       ├── Prophet (savings projection)
        │       ├── XGBoost (expense forecasting)
        │       ├── ARIMA (cashflow)
        │       └── RandomForest (study performance)
        │
        └── Database (SQLite / PostgreSQL)
                └── 9 tables: users, financial, study, habits,
                    fitness, goals, analytics, simulation_results,
                    conversation_messages
```

---

## Features

### Milestones 1–3 (Data + ML + Simulation)
- ✅ Financial records tracking (income/expenses/savings)
- ✅ Study session logging with performance tracking
- ✅ Habit management with streak tracking
- ✅ Fitness activity logging
- ✅ Goal progress tracking
- ✅ ML forecasting: savings (Prophet), expenses (XGBoost), cashflow (ARIMA)
- ✅ Digital Twin visualization (5 domain scores → overall alignment)
- ✅ 16 deterministic simulations (savings, investment, loans, study, habits, fitness)
- ✅ Scenario comparison with radar charts
- ✅ AI recommendations engine

### Milestone 4 (Conversational AI + Dashboard + Reports)
- ✅ Conversational AI with GPT-4o (LangChain + 4 tools)
- ✅ Intent classification (forecast/simulate/advice/explain/general)
- ✅ Safety filters for harmful financial advice
- ✅ Rate limiting (30 messages/hour, Redis or in-memory)
- ✅ Chat history persistence (DB + in-process memory)
- ✅ Full Dashboard with period selector (1M/3M/1Y/3Y)
- ✅ PDF report generation (5 report types)
- ✅ Period comparison (financial/study/fitness/habits)
- ✅ RBAC (user/admin roles)
- ✅ Docker containerization (4-service compose)
- ✅ GitHub Actions CI/CD

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit 1.37, Plotly 5.20 |
| Backend | FastAPI 0.111, uvicorn |
| AI | LangChain 0.2, OpenAI GPT-4o |
| ML | Prophet, XGBoost, ARIMA, scikit-learn |
| Database | SQLite (dev), PostgreSQL 15 (Docker) |
| Cache | Redis 7 |
| Auth | JWT (python-jose), bcrypt |
| PDF | fpdf2 |
| Testing | pytest, bandit |
| CI/CD | GitHub Actions |
| Container | Docker, Docker Compose |

---

## Quick Start

### Docker (Recommended)
```bash
cp .env.example .env
# Set SECRET_KEY and optionally OPENAI_API_KEY
docker compose up --build
# → Frontend: http://localhost:8501
# → API Docs: http://localhost:8000/docs
```

### Local Development (Windows)
```bash
copy .env.example .env
# Edit .env, including SECRET_KEY and (optionally) OPENAI_API_KEY
# Run migrations before starting the backend:
.venv\Scripts\alembic.exe -c alembic.ini upgrade head
Start App.bat
```

### Demo Account
```
Email:    synthetic_259_ce036a08@example.com
Password: demo123
Data:     363 records across all domains
```

---

## API Endpoints

| Group | Endpoints |
|---|---|
| Auth | POST /register, POST /login, GET /me |
| Users | GET/PUT /profile, GET /summary |
| Financial | CRUD /records, GET /summary |
| Study | CRUD + /exam-readiness, /trend, /optimal-plan |
| Habits | CRUD + /analysis, /productivity-index, /trend |
| Fitness | CRUD |
| Goals | CRUD |
| Forecasting | GET /savings, /expenses, /cashflow, POST /scenario |
| Digital Twin | GET /summary, /risk, /snapshot; POST /project, /recommendations |
| Simulation | POST /financial, /study, /habits, /fitness, /goals, /full |
| Scenarios | POST /compare, /risk-analysis; GET /best-path |
| **Assistant** | **POST /chat, GET /history/{id}, DELETE /history/{id}** |
| **Reports** | **GET /generate, GET /comparison** |
| **Admin** | **GET /users, GET /analytics-global** |

---

## Running Tests
```bash
.venv\Scripts\python.exe -m pytest tests/ -v
```

The assistant falls back to data-grounded rule-based responses when `OPENAI_API_KEY` is empty. PDF reports require the dependencies in `requirements.txt`; the configured project environment can be provisioned with:

```bash
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

For Docker deployment, use `docker compose up --build`. The backend container runs `alembic upgrade head` before starting FastAPI.

---

## Known Limitations
- OpenAI API key needed for full AI — app works without it (rule-based fallback)
- ML models need 3+ months of data for best accuracy
- SQLite for development only — use Docker/PostgreSQL for production

---

## Future Work
- Real-time collaborative twins (family finance view)
- Mobile app (React Native)
- Bank API integration (Plaid)
- Voice interface
- Email digest with weekly projections
