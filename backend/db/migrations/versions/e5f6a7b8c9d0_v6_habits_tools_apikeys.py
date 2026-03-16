"""v6: habits, custom_tools, api_keys tables

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-03-16 22:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Habits
    op.create_table(
        'habits',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'),
                  index=True, nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('frequency', sa.String(20), server_default='daily'),
        sa.Column('streak', sa.Integer, server_default='0'),
        sa.Column('best_streak', sa.Integer, server_default='0'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # Habit logs
    op.create_table(
        'habit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('habit_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('habits.id', ondelete='CASCADE'),
                  index=True, nullable=False),
        sa.Column('checked_at', sa.DateTime, server_default=sa.func.now()),
    )

    # Custom tools
    op.create_table(
        'custom_tools',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'),
                  index=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('code', sa.Text, nullable=False),
        sa.Column('enabled', sa.Boolean, server_default='true'),
        sa.Column('install_count', sa.Integer, server_default='0'),
        sa.Column('public', sa.Boolean, server_default='false'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # API keys
    op.create_table(
        'api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'),
                  index=True, nullable=False),
        sa.Column('key', sa.String(64), unique=True, index=True,
                  nullable=False),
        sa.Column('name', sa.String(100), server_default='default'),
        sa.Column('active', sa.Boolean, server_default='true'),
        sa.Column('request_count', sa.Integer, server_default='0'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('api_keys')
    op.drop_table('custom_tools')
    op.drop_table('habit_logs')
    op.drop_table('habits')
