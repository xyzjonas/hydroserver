"""add prop color

Revision ID: e2f70869d0bd
Revises: eaa32cda685a
Create Date: 2021-09-08 10:24:22.749303

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e2f70869d0bd'
down_revision = 'eaa32cda685a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('grow_property', schema=None) as batch_op:
        batch_op.add_column(sa.Column('color', sa.String(length=9), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('grow_property', schema=None) as batch_op:
        batch_op.drop_column('color')

    # ### end Alembic commands ###