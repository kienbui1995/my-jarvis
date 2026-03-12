"""v3 phase e: preferences and tool permissions

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-03-12 14:07:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user_preferences',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), unique=True, index=True),
        sa.Column('tone', sa.String(20)),
        sa.Column('verbosity', sa.String(20)),
        sa.Column('language', sa.String(10)),
        sa.Column('interests', JSONB, server_default='[]'),
        sa.Column('work_context', JSONB, server_default='{}'),
        sa.Column('custom_rules', JSONB, server_default='{}'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_table(
        'user_prompt_rules',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), index=True),
        sa.Column('rule', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), server_default='0.5'),
        sa.Column('source', sa.String(20), server_default="'explicit'"),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('last_validated', sa.DateTime()),
    )
    op.create_table(
        'user_tool_permissions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), index=True),
        sa.Column('tool_name', sa.String(100), nullable=False),
        sa.Column('enabled', sa.Boolean(), server_default='true'),
        sa.Column('requires_approval', sa.Boolean(), server_default='false'),
        sa.UniqueConstraint('user_id', 'tool_name', name='uq_user_tool'),
    )


def downgrade() -> None:
    op.drop_table('user_tool_permissions')
    op.drop_table('user_prompt_rules')
    op.drop_table('user_preferences')
