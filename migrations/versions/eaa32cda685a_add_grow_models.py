"""add grow models

Revision ID: eaa32cda685a
Revises: 53f36208ed3e
Create Date: 2021-09-07 17:01:07.472865

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'eaa32cda685a'
down_revision = '53f36208ed3e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('grow_properties',
    sa.Column('grow_property_id', sa.Integer(), nullable=False),
    sa.Column('grow_system_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['grow_property_id'], ['grow_property.id'], ),
    sa.ForeignKeyConstraint(['grow_system_id'], ['grow_system.id'], ),
    sa.PrimaryKeyConstraint('grow_property_id', 'grow_system_id')
    )
    with op.batch_alter_table('grow_system_instance', schema=None) as batch_op:
        batch_op.add_column(sa.Column('device_id', sa.Integer(), nullable=False))
        batch_op.create_foreign_key('x', 'device', ['device_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('grow_system_instance', schema=None) as batch_op:
        batch_op.drop_constraint('x', type_='foreignkey')
        batch_op.drop_column('device_id')

    op.drop_table('grow_properties')
    # ### end Alembic commands ###