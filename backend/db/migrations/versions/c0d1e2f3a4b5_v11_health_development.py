"""v11: health & personal development tables

Revision ID: c0d1e2f3a4b5
Revises: b9c0d1e2f3a4
Create Date: 2026-04-15 18:50:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = 'c0d1e2f3a4b5'
down_revision: Union[str, None] = 'b9c0d1e2f3a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('health_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), index=True, nullable=False),
        sa.Column('log_date', sa.Date(), server_default=sa.text('CURRENT_DATE')),
        sa.Column('metric', sa.String(50), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(20), server_default=''),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_health_logs_user_date', 'health_logs', ['user_id', 'log_date'])

    op.create_table('medications',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), index=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('dosage', sa.String(100)),
        sa.Column('frequency', sa.String(50), server_default='daily'),
        sa.Column('times', JSONB, server_default='[]'),
        sa.Column('start_date', sa.Date()),
        sa.Column('end_date', sa.Date()),
        sa.Column('notes', sa.Text()),
        sa.Column('active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table('flashcards',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), index=True, nullable=False),
        sa.Column('deck', sa.String(100), server_default='general'),
        sa.Column('front', sa.Text(), nullable=False),
        sa.Column('back', sa.Text(), nullable=False),
        sa.Column('interval', sa.Integer(), server_default='1'),
        sa.Column('ease_factor', sa.Float(), server_default='2.5'),
        sa.Column('repetitions', sa.Integer(), server_default='0'),
        sa.Column('next_review', sa.Date(), server_default=sa.text('CURRENT_DATE')),
        sa.Column('last_reviewed', sa.Date()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_flashcards_review', 'flashcards', ['user_id', 'deck', 'next_review'])

    op.create_table('book_notes',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), index=True, nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('author', sa.String(255)),
        sa.Column('status', sa.String(20), server_default='reading'),
        sa.Column('rating', sa.Integer()),
        sa.Column('highlights', JSONB, server_default='[]'),
        sa.Column('summary', sa.Text()),
        sa.Column('tags', JSONB, server_default='[]'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('book_notes')
    op.drop_index('ix_flashcards_review')
    op.drop_table('flashcards')
    op.drop_table('medications')
    op.drop_index('ix_health_logs_user_date')
    op.drop_table('health_logs')
