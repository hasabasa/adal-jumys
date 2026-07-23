"""add representative target type

Revision ID: ecd429d6909b
Revises: 070cc39f9476
Create Date: 2026-07-21 23:32:29.238345

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'ecd429d6909b'
down_revision: Union[str, Sequence[str], None] = '070cc39f9476'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Қысқа атау: env.py-дегі naming convention ck_<table>_ префиксін өзі жалғайды
CONSTRAINT = "target_type_valid"
TABLE = "moderation_actions"

OLD_VALUES = "'review', 'complaint', 'evidence', 'response', 'company', 'user', 'badge'"
NEW_VALUES = OLD_VALUES + ", 'representative'"


def upgrade() -> None:
    op.drop_constraint(CONSTRAINT, TABLE, type_="check")
    op.create_check_constraint(CONSTRAINT, TABLE, f"target_type IN ({NEW_VALUES})")


def downgrade() -> None:
    op.drop_constraint(CONSTRAINT, TABLE, type_="check")
    op.create_check_constraint(CONSTRAINT, TABLE, f"target_type IN ({OLD_VALUES})")
