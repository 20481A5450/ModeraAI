"""Fix circular import and models

Revision ID: 0a41a2e7900a
Revises: fe91db3cfac7
Create Date: 2025-02-12 17:17:47.389858

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0a41a2e7900a'
down_revision: Union[str, None] = 'fe91db3cfac7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('moderation_results',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('is_flagged', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_moderation_results_id'), 'moderation_results', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_moderation_results_id'), table_name='moderation_results')
    op.drop_table('moderation_results')
    # ### end Alembic commands ###
