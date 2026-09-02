# Digital Twin AI — Deployment Guide

## Prerequisites
- Docker Desktop 24+ and Docker Compose v2
- Git
- (Optional) Python 3.11 + venv for local dev

---

## Option 1: Docker (Recommended for Production)

### 1. Clone and configure
```bash
git clone <repo-url>
cd "bhavesh 123"
cp .env.example .env
# Edit .env — set SECRET_KEY and OPENAI_API_KEY
# ALLOWED_ORIGINS should contain the public frontend origin(s), comma-separated.
```

### 2. Start all services
```bash
docker compose up --build
```

### 3. Access
- Frontend: http://localhost:8501
- API Docs: http://localhost:8000/docs
- API Health: http://localhost:8000/health

### 4. Stop
```bash
docker compose down          # keep data
docker compose down -v       # remove all volumes (fresh start)
```

---

## Option 2: Local Development (Windows)

### 1. Setup
```bash
cd "C:\Users\bhave\Downloads\bhavesh 123"
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

### 2. Configure environment
```bash
copy .env.example .env
# Edit .env — set at minimum:
#   SECRET_KEY=your-random-256-bit-key
#   OPENAI_API_KEY=sk-...  (optional — app works without it)
#   ALLOWED_ORIGINS=http://127.0.0.1:8501,http://localhost:8501
```

### 3. Start
```
Double-click: Start App.bat
```
Or manually:
```bash
# Terminal 1 — Backend
cd backend
.\.venv\Scripts\uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2 — Frontend
.\.venv\Scripts\streamlit run frontend/app.py --server.port 8501
```

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | No | SQLite (auto-path) | PostgreSQL URL for Docker |
| `SECRET_KEY` | Yes | `dev-secret` (unsafe) | JWT signing key — change in production |
| `ALLOWED_ORIGINS` | No | Local Streamlit origins | Comma-separated browser origins allowed by the API |
| `OPENAI_API_KEY` | No | Empty | GPT-4o key — app works without it |
| `OPENAI_MODEL` | No | `gpt-4o` | LLM model name |
| `RATE_LIMIT_MESSAGES_PER_HOUR` | No | `30` | AI chat rate limit |
| `REDIS_URL` | No | Empty (in-memory) | Redis for rate limiting |
| `REPORTS_DIR` | No | `./reports` | PDF output directory |

---

## Train ML Models (optional, improves forecast accuracy)
```bash
# Train for a specific user (replace 2 with user ID)
.venv\Scripts\python.exe train_user_models.py --user-id 2
```

---

## Demo Account (pre-seeded data)
```
Email:    synthetic_259_ce036a08@example.com
Password: demo123
Data:     81 financial records, 156 study sessions, 120 fitness activities
```

---

## Run Tests
```bash
.venv\Scripts\python.exe -m pytest tests/ -v --tb=short
```

## Run Migrations
```bash
.venv\Scripts\alembic.exe -c alembic.ini upgrade head
```
The backend container applies migrations before starting FastAPI. Local startup through `Start App.bat` does the same.

## Security Scan
```bash
.venv\Scripts\python.exe -m bandit -r backend/ -ll
```
