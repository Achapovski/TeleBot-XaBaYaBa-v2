"""Create CategoryTimestamps 2

Revision ID: 055a5c5a94bd
Revises: 9eed4518f257
Create Date: 2024-11-19 22:28:12.585183

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '055a5c5a94bd'
down_revision: Union[str, None] = '9eed4518f257'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('category_timestamps',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('current_day', sa.DECIMAL(), nullable=False),
    sa.Column('current_week', sa.DECIMAL(), nullable=False),
    sa.Column('current_month', sa.DECIMAL(), nullable=False),
    sa.Column('current_quart', sa.DECIMAL(), nullable=False),
    sa.Column('current_half_year', sa.DECIMAL(), nullable=False),
    sa.Column('current_year', sa.DECIMAL(), nullable=False),
    sa.Column('day_week_month', sa.String(), server_default=sa.text("concat(EXTRACT(doy FROM now()), '.', EXTRACT(week FROM now()), '.', EXTRACT(month FROM now()))"), nullable=False),
    sa.Column('category_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('category_id'),
    sa.UniqueConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('category_timestamps')
    # ### end Alembic commands ###
