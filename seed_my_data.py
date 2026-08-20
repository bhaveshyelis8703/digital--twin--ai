"""
Seed real-looking data into user bhaveshyelis2005@gmail.com (id=2).
Run once: python seed_my_data.py
"""
import sys, random
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.core.database import SessionLocal
from app.models.user import (
    User, FinancialRecord, StudyActivity,
    Habit, FitnessActivity, Goal,
)

db = SessionLocal()
USER_EMAIL = "bhaveshyelis2005@gmail.com"
u = db.query(User).filter(User.email == USER_EMAIL).first()
if not u:
    print("User not found, exiting.")
    db.close()
    sys.exit(1)

uid  = u.id
today = datetime.today()
print(f"Seeding data for: {u.name} (id={uid})")

# ── Financial Records ─────────────────────────────────────────────────────────
fin_data = [
    ("income",  50000, "Monthly Salary",           "salary",       "monthly"),
    ("income",  12000, "Freelance Project",         "freelance",    "once"),
    ("income",   8000, "Stock Dividends",           "investment",   "quarterly"),
    ("expense",  9500, "Monthly Rent",              "housing",      "monthly"),
    ("expense",  3200, "Groceries",                 "food",         "weekly"),
    ("expense",  1800, "Internet + Phone",          "utilities",    "monthly"),
    ("expense",  2500, "Course Subscriptions",      "education",    "monthly"),
    ("expense",  1200, "Gym Membership",            "health",       "monthly"),
    ("expense",  4500, "Transport / Petrol",        "transport",    "monthly"),
    ("expense",   850, "Netflix + Spotify",         "entertainment","monthly"),
    ("income",   3000, "Part-time Tutoring",        "freelance",    "weekly"),
    ("expense",  2000, "Eating Out",                "food",         "weekly"),
]

existing_fin = db.query(FinancialRecord).filter(FinancialRecord.user_id == uid).count()
if existing_fin < 5:
    for i, (rtype, amount, desc, cat, freq) in enumerate(fin_data):
        date = today - timedelta(days=i * 7)
        db.add(FinancialRecord(
            user_id=uid, record_type=rtype, amount=float(amount),
            description=desc, date=date, category=cat,
            recurring_frequency=freq, goal_impact=None,
        ))
    print(f"  Added {len(fin_data)} financial records")
else:
    print(f"  Financial records already exist ({existing_fin}), skipping")

# ── Study Sessions ────────────────────────────────────────────────────────────
subjects = ["Mathematics", "Python", "Data Structures", "Machine Learning", "Physics", "English"]
existing_study = db.query(StudyActivity).filter(StudyActivity.user_id == uid).count()
if existing_study < 5:
    for i in range(20):
        date = today - timedelta(days=i * 2)
        db.add(StudyActivity(
            user_id=uid,
            subject=subjects[i % len(subjects)],
            study_date=date,
            study_hours=round(random.uniform(1.0, 4.0), 1),
            focus_score=random.randint(60, 95),
            task_completion=random.randint(65, 100),
            performance_score=random.randint(62, 92),
        ))
    print("  Added 20 study sessions")
else:
    print(f"  Study sessions already exist ({existing_study}), skipping")

# ── Habits ────────────────────────────────────────────────────────────────────
habit_data = [
    ("Morning Exercise",          "daily",   True,  14),
    ("Read 30 min/day",           "daily",   True,   7),
    ("Meditate",                  "daily",   False,  0),
    ("Drink 2L Water",            "daily",   True,  21),
    ("No Social Media before 10am","daily",  True,   5),
]
existing_habits = db.query(Habit).filter(Habit.user_id == uid).count()
if existing_habits < 3:
    for name, freq, completed, streak in habit_data:
        db.add(Habit(
            user_id=uid, name=name,
            target_frequency=freq,
            completed=completed, streak=streak,
        ))
    print(f"  Added {len(habit_data)} habits")
else:
    print(f"  Habits already exist ({existing_habits}), skipping")

# ── Fitness Activities ────────────────────────────────────────────────────────
fitness_types = ["Running", "Cycling", "Weight Training", "Yoga", "Swimming", "HIIT"]
existing_fitness = db.query(FitnessActivity).filter(FitnessActivity.user_id == uid).count()
if existing_fitness < 3:
    for i in range(12):
        date = today - timedelta(days=i * 3)
        db.add(FitnessActivity(
            user_id=uid,
            activity_type=fitness_types[i % len(fitness_types)],
            duration=random.randint(25, 75),
            calories_burned=random.randint(180, 520),
            activity_date=date,
        ))
    print("  Added 12 fitness activities")
else:
    print(f"  Fitness activities already exist ({existing_fitness}), skipping")

# ── Goals ─────────────────────────────────────────────────────────────────────
goals_data = [
    ("Save 1,00,000 INR",   "Save 1 lakh rupees for emergency fund",    100000, 42000, "in progress", "2027-03-01"),
    ("Run 5km",             "Build cardio to run a continuous 5km",     5.0,    3.2,   "in progress", "2026-10-01"),
    ("Complete ML Course",  "Finish all 10 modules of the ML course",   10,     7,     "in progress", "2026-09-15"),
    ("Read 12 Books",       "Read one book per month this year",        12,     5,     "in progress", "2026-12-31"),
    ("Lose 5kg",            "Reach target weight through diet + gym",   5.0,    2.5,   "in progress", "2026-11-01"),
]
existing_goals = db.query(Goal).filter(Goal.user_id == uid).count()
if existing_goals < 3:
    for name, desc, tgt, curr, status, td in goals_data:
        db.add(Goal(
            user_id=uid, name=name, description=desc,
            target_value=tgt, current_value=curr,
            target_date=datetime.fromisoformat(td), status=status,
        ))
    print(f"  Added {len(goals_data)} goals")
else:
    print(f"  Goals already exist ({existing_goals}), skipping")

db.commit()
db.close()
print("\nAll done! Now refresh your Streamlit app — data will appear.")
