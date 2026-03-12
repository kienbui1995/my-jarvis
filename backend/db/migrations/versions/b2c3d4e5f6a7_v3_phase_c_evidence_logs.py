"""v3 phase c: evidence logs table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-12 13:37:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'evidence_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), index=True),
        sa.Column('conversation_id', UUID(as_uuid=True), index=True),
        sa.Column('session_id', sa.String(100), server_default=''),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.func.now(), index=True),
        sa.Column('node', sa.String(50), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('tool_name', sa.String(100), server_default=''),
        sa.Column('tool_input', JSONB),
        sa.Column('tool_output', sa.Text(), server_default=''),
        sa.Column('model_used', sa.String(50), server_default=''),
        sa.Column('tokens_used', sa.Integer(), server_default='0'),
        sa.Column('cost', sa.Float(), server_default='0'),
        sa.Column('duration_ms', sa.Integer(), server_default='0'),
        sa.Column('error', sa.Text(), server_default=''),
    )


def downgrade() -> None:
    op.drop_table('evidence_logs')
