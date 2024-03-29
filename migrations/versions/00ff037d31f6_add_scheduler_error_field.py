"""Add scheduler error field

Revision ID: 00ff037d31f6
Revises: 00166eb2f28d
Create Date: 2021-08-19 16:15:39.890924

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '00ff037d31f6'
down_revision = '00166eb2f28d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('device', sa.Column('scheduler_error', sa.String(length=80), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('device', 'scheduler_error')
    # ### end Alembic commands ###
