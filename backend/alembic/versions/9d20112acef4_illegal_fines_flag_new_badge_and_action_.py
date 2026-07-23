"""illegal fines flag, new badge and action values

Revision ID: 9d20112acef4
Revises: ecd429d6909b
Create Date: 2026-07-23 11:08:15.403501

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9d20112acef4'
down_revision: Union[str, Sequence[str], None] = 'ecd429d6909b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# CHECK-констрейнт мәндері (autogenerate байқамайды, қолмен жазылады)
OLD_BADGES = "'salary_not_confirmed', 'repeated_language_discrimination', 'officially_confirmed_violation'"
NEW_BADGES = "'salary_not_confirmed', 'repeated_language_discrimination', 'repeated_illegal_fines', 'officially_confirmed_violation'"

OLD_ACTIONS = "'hide', 'unhide', 'approve', 'reject', 'mask_pii', 'verify_review', 'award_badge', 'revoke_badge', 'ban_user', 'other'"
NEW_ACTIONS = "'hide', 'unhide', 'approve', 'reject', 'mask_pii', 'verify_review', 'award_badge', 'revoke_badge', 'ban_user', 'appeal_uphold', 'appeal_overturn', 'other'"


def upgrade() -> None:
    op.add_column('reviews', sa.Column('illegal_fines', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.drop_constraint('badge_valid', 'company_badges', type_='check')
    op.create_check_constraint('badge_valid', 'company_badges', f'badge IN ({NEW_BADGES})')
    op.drop_constraint('action_valid', 'moderation_actions', type_='check')
    op.create_check_constraint('action_valid', 'moderation_actions', f'action IN ({NEW_ACTIONS})')


def downgrade() -> None:
    op.drop_constraint('action_valid', 'moderation_actions', type_='check')
    op.create_check_constraint('action_valid', 'moderation_actions', f'action IN ({OLD_ACTIONS})')
    op.drop_constraint('badge_valid', 'company_badges', type_='check')
    op.create_check_constraint('badge_valid', 'company_badges', f'badge IN ({OLD_BADGES})')
    op.drop_column('reviews', 'illegal_fines')
