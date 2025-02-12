"""Fix models detection

Revision ID: fe91db3cfac7
Revises: 
Create Date: 2025-02-12 16:57:37.504548

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fe91db3cfac7'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        'moderation_results',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_flagged', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )



def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
