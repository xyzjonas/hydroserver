"""Control.value -> str

Revision ID: d39156cb45f2
Revises: 00ff037d31f6
Create Date: 2021-08-20 16:24:50.023351

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd39156cb45f2'
down_revision = '00ff037d31f6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('control', sa.Column('value', sa.String(length=80), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('control', 'value')
    # ### end Alembic commands ###
