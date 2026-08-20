"""
ml/synthetic_data_generator.py
Generate 500 synthetic users with 12 months of realistic data and seed into SQLite.
Run: python ml/synthetic_data_generator.py
"""
from __future__ import annotations

import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from faker import Faker

_BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.user import (
    FinancialRecord, FitnessActivity, Goal, Habit, StudyActivity, User,
)

fake = Faker()
rng  = np.random.default_rng(42)

# ─────────────────────────────────────────────────────────────────────────────
OCCUPATIONS      = ["Student", "Engineer", "Designer", "Teacher", "Doctor",
                    "Analyst", "Manager", "Developer", "Artist", "Consultant"]
CATEGORIES       = ["Food", "Transport", "Housing", "Entertainment",
                    "Healthcare", "Education", "Shopping", "Utilities", "Fitness"]
ACTIVITY_TYPES   = ["Running", "Cycling", "Swimming", "Gym", "Yoga",
                    "HIIT", "Walking", "Basketball", "Tennis"]
HABIT_NAMES      = ["Morning Workout", "Reading", "Meditation", "Journaling",
                    "Cold Shower", "Meal Prep", "Evening Walk", "No Social Media",
                    "Sleep by 10 PM", "Daily Study"]
SUBJECTS         = ["Mathematics", "Programming", "Physics", "History",
                    "Chemistry", "Literature", "Biology", "Economics", "ML/AI"]
SEASONAL_MULT    = {1: 1.2, 2: 1.0, 3: 1.1, 4: 1.0, 5: 0.9, 6: 0.8,
                    7: 0.8, 8: 0.9, 9: 1.0, 10: 1.1, 11: 1.3, 12: 1.5}


def _random_date_in_month(year: int, month: int) -> datetime:
    import calendar
    day = rng.integers(1, calendar.monthrange(year, month)[1] + 1)
    return datetime(year, month, int(day), int(rng.integers(6, 23)), int(rng.integers(0, 60)))


def generate_financial_records(user_id: int, salary: float) -> list[FinancialRecord]:
    records = []
    start = datetime(2025, 1, 1)
    for m in range(12):
        month_dt = start + timedelta(days=30 * m)
        year, month = month_dt.year, month_dt.month
        seasonal = SEASONAL_MULT.get(month, 1.0)

        # salary with ±5% variation
        income = salary * (1 + rng.normal(0, 0.05))
        records.append(FinancialRecord(
            user_id=user_id, record_type="income",
            amount=round(float(income), 2), description="Monthly Salary",
            date=datetime(year, month, 1),
            category="Income", recurring_frequency="monthly",
        ))

        # 3-7 expense records per month
        n_exp = int(rng.integers(3, 8))
        for _ in range(n_exp):
            cat = random.choice(CATEGORIES)
            base = {"Food": 300, "Transport": 150, "Housing": 800,
                    "Entertainment": 200, "Healthcare": 100, "Education": 200,
                    "Shopping": 250, "Utilities": 120, "Fitness": 80}.get(cat, 150)
            amount = base * seasonal * (1 + rng.normal(0, 0.2))
            records.append(FinancialRecord(
                user_id=user_id, record_type="expense",
                amount=round(max(float(amount), 1.0), 2),
                description=f"{cat} expense",
                date=_random_date_in_month(year, month),
                category=cat, recurring_frequency="monthly",
            ))
    return records


def generate_study_activities(user_id: int, performance_base: float) -> list[StudyActivity]:
    activities = []
    start = datetime(2025, 1, 1)
    for week in range(52):
        # 0–5 sessions per week, correlated with performance
        n_sessions = int(rng.integers(0, 6))
        for _ in range(n_sessions):
            day_offset = int(rng.integers(0, 7))
            dt = start + timedelta(weeks=week, days=day_offset)
            hours = float(np.clip(rng.normal(2.5, 1.0), 0.5, 8.0))
            focus = float(np.clip(rng.normal(performance_base, 10), 30, 100))
            perf  = float(np.clip(performance_base + hours * 3 + rng.normal(0, 8), 30, 100))
            task  = float(np.clip(focus * 0.9 + rng.normal(0, 5), 30, 100))
            activities.append(StudyActivity(
                user_id=user_id, subject=random.choice(SUBJECTS),
                study_date=dt, study_hours=round(hours, 1),
                focus_score=round(focus, 1), task_completion=round(task, 1),
                performance_score=round(perf, 1),
            ))
    return activities


def generate_habits(user_id: int) -> list[Habit]:
    habits = []
    n_habits = int(rng.integers(3, 7))
    selected = rng.choice(HABIT_NAMES, size=n_habits, replace=False)
    for name in selected:
        # realistic dropout: streak decays with some probability
        streak = int(np.clip(rng.exponential(15), 0, 90))
        completed = bool(rng.random() > 0.35)
        habits.append(Habit(
            user_id=user_id, name=str(name),
            target_frequency=random.choice(["daily", "weekly", "3x/week"]),
            completed=completed, streak=streak,
        ))
    return habits


def generate_fitness_activities(user_id: int) -> list[FitnessActivity]:
    activities = []
    start = datetime(2025, 1, 1)
    # ~3-5 sessions per week with realistic dropout
    for week in range(52):
        n = int(rng.integers(0, 6)) if rng.random() > 0.15 else 0  # 15% rest weeks
        for _ in range(n):
            day_offset = int(rng.integers(0, 7))
            dt = start + timedelta(weeks=week, days=day_offset)
            activity = random.choice(ACTIVITY_TYPES)
            duration = float(np.clip(rng.normal(45, 15), 10, 120))
            calories = duration * float(rng.uniform(6, 12))
            activities.append(FitnessActivity(
                user_id=user_id, activity_type=activity,
                duration=round(duration, 1),
                calories_burned=round(calories, 1),
                activity_date=dt,
            ))
    return activities


def seed_database(n_users: int = 500, batch_size: int = 50) -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.query(User).count()
        if existing >= n_users:
            print(f"Database already has {existing} users. Skipping seed.")
            return

        print(f"Seeding {n_users} synthetic users…")
        hashed_pw = get_password_hash("synthetic_pass_123")

        for batch_start in range(0, n_users, batch_size):
            batch_end = min(batch_start + batch_size, n_users)
            users_batch = []
            for i in range(batch_start, batch_end):
                u = User(
                    name=fake.name(), email=f"synthetic_{i}_{fake.uuid4()[:8]}@example.com",
                    hashed_password=hashed_pw,
                    age=int(rng.integers(18, 55)),
                    occupation=random.choice(OCCUPATIONS),
                    is_active=True,
                )
                users_batch.append(u)

            db.add_all(users_batch)
            db.flush()  # get IDs

            for u in users_batch:
                salary = float(rng.uniform(30_000, 150_000) / 12)
                perf_base = float(rng.uniform(55, 90))
                db.add_all(generate_financial_records(u.id, salary))
                db.add_all(generate_study_activities(u.id, perf_base))
                db.add_all(generate_habits(u.id))
                db.add_all(generate_fitness_activities(u.id))

            db.commit()
            print(f"  Seeded users {batch_start+1}–{batch_end}")

        print(f"Done. Total users in DB: {db.query(User).count()}")
    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    seed_database(n_users=n)
