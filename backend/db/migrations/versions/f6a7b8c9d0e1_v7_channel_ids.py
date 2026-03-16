"""v7: add whatsapp_id, slack_id, discord_id to users

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-03-16 23:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('whatsapp_id', sa.String(100),
                  unique=True, index=True, nullable=True))
    op.add_column('users', sa.Column('slack_id', sa.String(100),
                  unique=True, index=True, nullable=True))
    op.add_column('users', sa.Column('discord_id', sa.String(100),
                  unique=True, index=True, nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'discord_id')
    op.drop_column('users', 'slack_id')
    op.drop_column('users', 'whatsapp_id')
