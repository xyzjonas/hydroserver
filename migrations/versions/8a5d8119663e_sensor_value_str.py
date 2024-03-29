"""Sensor value -> str

Revision ID: 8a5d8119663e
Revises: 9641285ca9d7
Create Date: 2021-08-26 13:17:23.748401

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8a5d8119663e'
down_revision = '9641285ca9d7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('sensor', schema=None) as batch_op:
        batch_op.add_column(sa.Column('_value', sa.String(length=80), default="-1"))
        batch_op.drop_column('_last_value')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('sensor', schema=None) as batch_op:
        batch_op.add_column(sa.Column('_last_value', sa.FLOAT(), nullable=True))
        batch_op.drop_column('_value')

    # ### end Alembic commands ###
