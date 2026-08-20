# Digital Twin AI

Digital Twin AI is a personal life simulation and decision assistant focused on Milestone 1: data collection and user profiling.

## Features
- User registration and login
- JWT-authenticated profile management
- Financial, study, habit, fitness, and goal tracking
- Analytics logging
- Streamlit frontend

## Setup
1. Create and activate a virtual environment.
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and adjust values.

## Run backend
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Run frontend
```bash
streamlit run frontend/app.py
```

## Testing
```bash
pytest tests/ -v --tb=short
pytest --cov=backend/app --cov-report=html
```
