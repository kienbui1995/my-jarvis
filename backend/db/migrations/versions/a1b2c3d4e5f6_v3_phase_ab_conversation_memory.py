"""v3 phase ab: conversation memory fields

Revision ID: a1b2c3d4e5f6
Revises: 5bad8188c497
Create Date: 2026-03-12 11:37:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '5bad8188c497'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('conversations', sa.Column('rolling_summary', sa.Text(), server_default='', nullable=True))
    op.add_column('conversations', sa.Column('summary_turn_count', sa.Integer(), server_default='0', nullable=False))
    op.add_column('conversations', sa.Column('total_turns', sa.Integer(), server_default='0', nullable=False))


def downgrade() -> None:
    op.drop_column('conversations', 'total_turns')
    op.drop_column('conversations', 'summary_turn_count')
    op.drop_column('conversations', 'rolling_summary')
