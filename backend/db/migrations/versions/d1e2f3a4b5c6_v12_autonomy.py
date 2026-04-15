"""v12: autonomy — goals & decision journal

Revision ID: d1e2f3a4b5c6
Revises: c0d1e2f3a4b5
Create Date: 2026-04-15 19:05:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, None] = 'c0d1e2f3a4b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('goals',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), index=True, nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('goal_type', sa.String(20), server_default='objective'),
        sa.Column('parent_id', sa.String(36)),
        sa.Column('target_value', sa.Float()),
        sa.Column('current_value', sa.Float(), server_default='0'),
        sa.Column('unit', sa.String(50)),
        sa.Column('deadline', sa.Date()),
        sa.Column('status', sa.String(20), server_default='active'),
        sa.Column('tags', JSONB, server_default='[]'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table('decisions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), index=True, nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('context', sa.Text()),
        sa.Column('options', JSONB, server_default='[]'),
        sa.Column('chosen', sa.Text()),
        sa.Column('reasoning', sa.Text()),
        sa.Column('outcome', sa.Text()),
        sa.Column('rating', sa.Integer()),
        sa.Column('review_date', sa.Date()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('decisions')
    op.drop_table('goals')
