from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    occupation: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    financial_records: Mapped[list["FinancialRecord"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    study_activities: Mapped[list["StudyActivity"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    goals: Mapped[list["Goal"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    habits: Mapped[list["Habit"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    fitness_activities: Mapped[list["FitnessActivity"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    analytics_logs: Mapped[list["AnalyticsLog"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    simulation_results: Mapped[list["SimulationResult"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class FinancialRecord(Base):
    __tablename__ = "financial_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    record_type: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[float] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    recurring_frequency: Mapped[str] = mapped_column(String(20), nullable=False)
    goal_impact: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates="financial_records")


class StudyActivity(Base):
    __tablename__ = "study_activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    study_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    study_hours: Mapped[float] = mapped_column(nullable=False)
    focus_score: Mapped[float] = mapped_column(nullable=False)
    task_completion: Mapped[float] = mapped_column(nullable=False)
    performance_score: Mapped[float] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates="study_activities")


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    target_value: Mapped[float] = mapped_column(nullable=False)
    current_value: Mapped[float] = mapped_column(nullable=False, default=0.0)
    target_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates="goals")


class Habit(Base):
    __tablename__ = "habits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    target_frequency: Mapped[str] = mapped_column(String(50), nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completion_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates="habits")


class FitnessActivity(Base):
    __tablename__ = "fitness_activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    activity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    duration: Mapped[float] = mapped_column(nullable=False)
    calories_burned: Mapped[float] = mapped_column(nullable=False)
    activity_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates="fitness_activities")


class AnalyticsLog(Base):
    __tablename__ = "analytics_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    method: Mapped[str] = mapped_column(String(20), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    response_time_ms: Mapped[float] = mapped_column(nullable=False)

    user: Mapped[User | None] = relationship(back_populates="analytics_logs")


class SimulationResult(Base):
    """Persists every simulation run so users can review history."""
    __tablename__ = "simulation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    scenario_name: Mapped[str] = mapped_column(String(100), nullable=False)
    scenario_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # JSON stored as TEXT (SQLite-compatible; swap for JSONB on PostgreSQL)
    input_data: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    result_data: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship(back_populates="simulation_results")
