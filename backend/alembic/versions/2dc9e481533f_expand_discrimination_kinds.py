"""expand discrimination kinds

Revision ID: 2dc9e481533f
Revises: 8fbd58b368e1
Create Date: 2026-07-23 19:14:31.801988

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '2dc9e481533f'
down_revision: Union[str, Sequence[str], None] = '8fbd58b368e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Қысқа атау: naming convention ck_<table>_ префиксін өзі жалғайды
CONSTRAINT = "kind_valid"
TABLE = "discrimination_details"

OLD_KINDS = "'language', 'age', 'gender', 'ethnicity', 'other'"
NEW_KINDS = (
    "'language', 'age', 'gender', 'ethnicity', 'religion', 'pregnancy', "
    "'disability', 'appearance', 'other', "
    "'bullying', 'dignity_abuse', 'sexual_harassment', 'threats', 'extortion'"
)


def upgrade() -> None:
    op.drop_constraint(CONSTRAINT, TABLE, type_="check")
    op.create_check_constraint(CONSTRAINT, TABLE, f"kind IN ({NEW_KINDS})")


def downgrade() -> None:
    op.drop_constraint(CONSTRAINT, TABLE, type_="check")
    op.create_check_constraint(CONSTRAINT, TABLE, f"kind IN ({OLD_KINDS})")
