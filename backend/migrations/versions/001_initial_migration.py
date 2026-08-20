from alembic import op
import sqlalchemy as sa


revision = "001_initial_migration"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("occupation", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    op.create_table(
        "financial_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("record_type", sa.String(length=20), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("recurring_frequency", sa.String(length=20), nullable=False),
        sa.Column("goal_impact", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index(op.f("ix_financial_records_id"), "financial_records", ["id"], unique=False)
    op.create_index(op.f("ix_financial_records_user_id"), "financial_records", ["user_id"], unique=False)

    op.create_table(
        "study_activities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("subject", sa.String(length=100), nullable=False),
        sa.Column("study_date", sa.DateTime(), nullable=False),
        sa.Column("study_hours", sa.Float(), nullable=False),
        sa.Column("focus_score", sa.Float(), nullable=False),
        sa.Column("task_completion", sa.Float(), nullable=False),
        sa.Column("performance_score", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index(op.f("ix_study_activities_id"), "study_activities", ["id"], unique=False)
    op.create_index(op.f("ix_study_activities_user_id"), "study_activities", ["user_id"], unique=False)

    op.create_table(
        "goals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("target_value", sa.Float(), nullable=False),
        sa.Column("current_value", sa.Float(), nullable=False),
        sa.Column("target_date", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index(op.f("ix_goals_id"), "goals", ["id"], unique=False)
    op.create_index(op.f("ix_goals_user_id"), "goals", ["user_id"], unique=False)

    op.create_table(
        "habits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("target_frequency", sa.String(length=50), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("completion_date", sa.DateTime(), nullable=True),
        sa.Column("streak", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index(op.f("ix_habits_id"), "habits", ["id"], unique=False)
    op.create_index(op.f("ix_habits_user_id"), "habits", ["user_id"], unique=False)

    op.create_table(
        "fitness_activities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("activity_type", sa.String(length=50), nullable=False),
        sa.Column("duration", sa.Float(), nullable=False),
        sa.Column("calories_burned", sa.Float(), nullable=False),
        sa.Column("activity_date", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index(op.f("ix_fitness_activities_id"), "fitness_activities", ["id"], unique=False)
    op.create_index(op.f("ix_fitness_activities_user_id"), "fitness_activities", ["user_id"], unique=False)

    op.create_table(
        "analytics_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("endpoint", sa.String(length=255), nullable=False),
        sa.Column("method", sa.String(length=20), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("response_time_ms", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index(op.f("ix_analytics_logs_id"), "analytics_logs", ["id"], unique=False)
    op.create_index(op.f("ix_analytics_logs_user_id"), "analytics_logs", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_table("analytics_logs")
    op.drop_table("fitness_activities")
    op.drop_table("habits")
    op.drop_table("goals")
    op.drop_table("study_activities")
    op.drop_table("financial_records")
    op.drop_table("users")
