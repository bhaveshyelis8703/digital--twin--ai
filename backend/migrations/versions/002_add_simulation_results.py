"""add simulation_results table

Revision ID: 002
Revises: 001
Create Date: 2026-08-13
"""
from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "simulation_results",
        sa.Column("id",               sa.Integer(),     primary_key=True, index=True),
        sa.Column("user_id",          sa.Integer(),     sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("scenario_name",    sa.String(100),   nullable=False),
        sa.Column("scenario_type",    sa.String(50),    nullable=False),
        sa.Column("input_data",       sa.Text(),        nullable=False, server_default="{}"),
        sa.Column("result_data",      sa.Text(),        nullable=False, server_default="{}"),
        sa.Column("confidence_score", sa.Float(),       nullable=False, server_default="0.0"),
        sa.Column("created_at",       sa.DateTime(),    nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("simulation_results")
