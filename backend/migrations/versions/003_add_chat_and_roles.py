"""add chat history and user roles

Revision ID: 003
Revises: 002
Create Date: 2026-08-27
"""
from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add role column to users
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("role", sa.String(20), nullable=False, server_default="user"))

    # Create conversation_messages table
    op.create_table(
        "conversation_messages",
        sa.Column("id",               sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id",          sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("conversation_id",  sa.String(36), nullable=False, index=True),
        sa.Column("role",             sa.String(20), nullable=False),
        sa.Column("content",          sa.Text(),    nullable=False),
        sa.Column("tools_used",       sa.Text(),    nullable=False, server_default="[]"),
        sa.Column("response_time_ms", sa.Float(),   nullable=True),
        sa.Column("timestamp",        sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_conv_user", "conversation_messages", ["user_id"])
    op.create_index("ix_conv_id",   "conversation_messages", ["conversation_id"])
    op.create_index("ix_conv_ts",   "conversation_messages", ["timestamp"])


def downgrade() -> None:
    op.drop_table("conversation_messages")
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("role")
