"""initial schema: users, score_history

Revision ID: 0001
Revises:
Create Date: 2026-09-21

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    user_role = postgresql.ENUM("user", "admin", name="user_role")
    user_role.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column(
            "role",
            postgresql.ENUM("user", "admin", name="user_role", create_type=False),
            nullable=False,
            server_default="user",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.create_table(
        "score_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("game_id", sa.String(100), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("score_date", sa.Date(), server_default=sa.func.current_date(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_score_history_user_id", "score_history", ["user_id"])
    op.create_index("ix_score_history_game_id", "score_history", ["game_id"])
    op.create_index("ix_score_history_score_date", "score_history", ["score_date"])
    op.create_index("ix_score_history_created_at", "score_history", ["created_at"])


def downgrade() -> None:
    op.drop_table("score_history")
    op.drop_table("users")
    postgresql.ENUM(name="user_role").drop(op.get_bind(), checkfirst=True)
