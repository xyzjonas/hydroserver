"""initial migration

Revision ID: 0d5237bc1c58
Revises: 
Create Date: 2021-07-19 13:26:42.477539

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0d5237bc1c58'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('device',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('time_modified', sa.DateTime(), nullable=True),
    sa.Column('last_seen_online', sa.DateTime(), nullable=True),
    sa.Column('uuid', sa.String(length=80), nullable=True),
    sa.Column('name', sa.String(length=80), nullable=False),
    sa.Column('url', sa.String(length=80), nullable=True),
    sa.Column('type', sa.String(length=80), nullable=True),
    sa.Column('is_online', sa.Boolean(), nullable=True),
    sa.Column('_unknown_commands', sa.String(length=500), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('uuid')
    )
    op.create_table('control',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=80), nullable=False),
    sa.Column('description', sa.String(length=80), nullable=True),
    sa.Column('_state', sa.Boolean(), nullable=True),
    sa.Column('device_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['device_id'], ['device.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('sensor',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=80), nullable=False),
    sa.Column('description', sa.String(length=80), nullable=True),
    sa.Column('_last_value', sa.Float(), nullable=True),
    sa.Column('unit', sa.String(length=80), nullable=True),
    sa.Column('device_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['device_id'], ['device.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('task',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=80), nullable=True),
    sa.Column('cron', sa.String(length=80), nullable=True),
    sa.Column('type', sa.String(length=80), nullable=True),
    sa.Column('_task_meta', sa.String(length=200), nullable=True),
    sa.Column('last_run', sa.DateTime(), nullable=True),
    sa.Column('last_run_success', sa.Boolean(), nullable=True),
    sa.Column('last_run_error', sa.String(length=80), nullable=True),
    sa.Column('control_id', sa.Integer(), nullable=True),
    sa.Column('sensor_id', sa.Integer(), nullable=True),
    sa.Column('device_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['control_id'], ['control.id'], ),
    sa.ForeignKeyConstraint(['device_id'], ['device.id'], ),
    sa.ForeignKeyConstraint(['sensor_id'], ['sensor.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('task')
    op.drop_table('sensor')
    op.drop_table('control')
    op.drop_table('device')
    # ### end Alembic commands ###
