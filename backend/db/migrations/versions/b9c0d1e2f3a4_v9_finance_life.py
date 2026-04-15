"""v9: finance & life management tables

Revision ID: b9c0d1e2f3a4
Revises: a8b9c0d1e2f3
Create Date: 2026-04-15 15:40:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = 'b9c0d1e2f3a4'
down_revision: Union[str, None] = 'a8b9c0d1e2f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # M53: Bill Reminders
    op.create_table('bill_reminders',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), index=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2)),
        sa.Column('currency', sa.String(3), server_default='VND'),
        sa.Column('due_day', sa.Integer(), nullable=False),
        sa.Column('frequency', sa.String(20), server_default='monthly'),
        sa.Column('category', sa.String(50), server_default='utilities'),
        sa.Column('auto_paid', sa.Boolean(), server_default='false'),
        sa.Column('last_paid', sa.Date()),
        sa.Column('notes', sa.Text()),
        sa.Column('enabled', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # M54: Subscriptions
    op.create_table('subscriptions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), index=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('currency', sa.String(3), server_default='VND'),
        sa.Column('frequency', sa.String(20), server_default='monthly'),
        sa.Column('category', sa.String(50), server_default='entertainment'),
        sa.Column('next_billing', sa.Date()),
        sa.Column('cancel_url', sa.String(500)),
        sa.Column('active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # M55+M56: Contacts
    op.create_table('contacts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), index=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(20)),
        sa.Column('email', sa.String(255)),
        sa.Column('relationship', sa.String(50)),
        sa.Column('birthday', sa.Date()),
        sa.Column('anniversary', sa.Date()),
        sa.Column('company', sa.String(255)),
        sa.Column('notes', sa.Text()),
        sa.Column('preferences', JSONB, server_default='{}'),
        sa.Column('last_contact', sa.Date()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # M57: Documents
    op.create_table('documents',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), index=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('doc_type', sa.String(50), nullable=False),
        sa.Column('file_key', sa.String(500)),
        sa.Column('doc_number', sa.String(100)),
        sa.Column('issuer', sa.String(255)),
        sa.Column('issue_date', sa.Date()),
        sa.Column('expiry_date', sa.Date()),
        sa.Column('notes', sa.Text()),
        sa.Column('metadata', JSONB, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # M59: Shopping Lists
    op.create_table('shopping_lists',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), index=True, nullable=False),
        sa.Column('name', sa.String(255), server_default='Danh sách mua sắm'),
        sa.Column('completed', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table('shopping_items',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('list_id', UUID(as_uuid=True), sa.ForeignKey('shopping_lists.id', ondelete='CASCADE'), index=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('quantity', sa.Integer(), server_default='1'),
        sa.Column('unit', sa.String(20)),
        sa.Column('checked', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('shopping_items')
    op.drop_table('shopping_lists')
    op.drop_table('documents')
    op.drop_table('contacts')
    op.drop_table('subscriptions')
    op.drop_table('bill_reminders')
