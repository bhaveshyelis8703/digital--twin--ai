import os
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

# Always use backend/ as working context so the DB path is correct
_BACKEND = Path(__file__).resolve().parent / "backend"
os.chdir(_BACKEND)
sys.path.insert(0, str(_BACKEND))

from app.core.database import SessionLocal
from app.core.security import get_password_hash, verify_password
from app.models.user import (
    FinancialRecord, FitnessActivity, Goal, Habit, StudyActivity, User,
)

EMAIL    = "ramprasad16007@gmail.com"
PASSWORD = "12345678"

db  = SessionLocal()
rng = np.random.default_rng(42)

# ── check if user already exists ─────────────────────────────────────────────
existing = db.query(User).filter(User.email == EMAIL).first()
if existing:
    print(f"User already exists: id={existing.id}")
    ok = verify_password(PASSWORD, existing.hashed_password)
    print(f"Password valid: {ok}")
    if not ok:
        existing.hashed_password = get_password_hash(PASSWORD)
        db.commit()
        print("Password updated.")
    uid = existing.id
    # check data
    fin_count = db.query(FinancialRecord).filter(FinancialRecord.user_id == uid).count()
    study_count = db.query(StudyActivity).filter(StudyActivity.user_id == uid).count()
    print(f"Existing data: financial={fin_count}  study={study_count}")
    if fin_count >= 12 and study_count >= 10:
        print("Data already seeded. Done.")
        db.close()
        sys.exit(0)
else:
    u = User(
        name="Ramprasad",
        email=EMAIL,
        hashed_password=get_password_hash(PASSWORD),
        age=20,
        occupation="Student",
        is_active=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    uid = u.id
    print(f"Created user id={uid}")

# ── financial records — 12 months ────────────────────────────────────────────
CATS = ["Food", "Transport", "Housing", "Entertainment",
        "Education", "Shopping", "Utilities"]
BASE_SPEND = {"Food": 3000, "Transport": 1500, "Housing": 8000,
              "Entertainment": 2000, "Education": 2500,
              "Shopping": 2000, "Utilities": 1200}

for m in range(12):
    month = m + 1
    year  = 2025
    dt    = datetime(year, month, 1)
    salary = round(float(rng.uniform(15000, 20000)), 2)
    db.add(FinancialRecord(
        user_id=uid, record_type="income", amount=salary,
        description="Monthly Stipend", date=dt,
        category="Income", recurring_frequency="monthly",
    ))
    for _ in range(4):
        cat = random.choice(CATS)
        base = BASE_SPEND.get(cat, 1500)
        amt  = round(float(rng.uniform(base * 0.8, base * 1.2)), 2)
        db.add(FinancialRecord(
            user_id=uid, record_type="expense", amount=amt,
            description=f"{cat} expense",
            date=dt + timedelta(days=int(rng.integers(1, 28))),
            category=cat, recurring_frequency="monthly",
        ))

db.commit()
print("Financial records seeded: 60")

# ── study sessions — 50 sessions ─────────────────────────────────────────────
SUBJECTS = ["Mathematics", "Programming", "Physics", "Data Science", "ML/AI"]

for _ in range(50):
    dt    = datetime(2025, 1, 1) + timedelta(days=int(rng.integers(0, 365)))
    hours = round(float(rng.uniform(1, 4)), 1)
    focus = round(float(rng.uniform(65, 95)), 1)
    task  = round(float(rng.uniform(70, 95)), 1)
    perf  = round(float(min(focus * 0.4 + task * 0.35 + hours * 5 + float(rng.normal(0, 5)), 100)), 1)
    db.add(StudyActivity(
        user_id=uid, subject=random.choice(SUBJECTS),
        study_date=dt, study_hours=hours,
        focus_score=focus, task_completion=task,
        performance_score=max(perf, 40.0),
    ))

db.commit()
print("Study sessions seeded: 50")

# ── habits ────────────────────────────────────────────────────────────────────
HABITS = [
    ("Morning Workout", "daily"),
    ("Reading", "daily"),
    ("Meditation", "daily"),
    ("Coding Practice", "daily"),
    ("Journaling", "weekly"),
]

for name, freq in HABITS:
    streak = int(rng.integers(5, 30))
    db.add(Habit(
        user_id=uid, name=name, target_frequency=freq,
        completed=bool(rng.random() > 0.3), streak=streak,
    ))

db.commit()
print("Habits seeded: 5")

# ── fitness ───────────────────────────────────────────────────────────────────
ACTS = ["Running", "Gym", "Cycling", "Swimming", "Yoga"]

for _ in range(40):
    dt  = datetime(2025, 1, 1) + timedelta(days=int(rng.integers(0, 365)))
    dur = round(float(rng.uniform(30, 90)), 1)
    cal = round(dur * float(rng.uniform(7, 12)), 1)
    db.add(FitnessActivity(
        user_id=uid, activity_type=random.choice(ACTS),
        duration=dur, calories_burned=cal, activity_date=dt,
    ))

db.commit()
print("Fitness activities seeded: 40")

# ── goals ─────────────────────────────────────────────────────────────────────
GOALS = [
    ("Complete ML Course",   "Finish Andrew Ng ML course",    100.0,   65.0, "2026-12-31"),
    ("Save Emergency Fund",  "Save 50000 rupees",           50000.0, 18000.0, "2026-06-30"),
    ("Run 5K",               "Complete 5K under 30 minutes",   30.0,   22.0, "2026-03-31"),
    ("Read 12 Books",        "One book per month this year",   12.0,    7.0, "2026-12-31"),
]

for name, desc, tv, cv, td in GOALS:
    db.add(Goal(
        user_id=uid, name=name, description=desc,
        target_value=tv, current_value=cv,
        target_date=datetime.fromisoformat(td),
        status="In Progress",
    ))

db.commit()
print("Goals seeded: 4")

db.close()
print(f"\nAll done! Login with:\n  email   : {EMAIL}\n  password: {PASSWORD}")
