"""add user activities table

Revision ID: add_user_activities
Revises: 
Create Date: 2024-12-07 01:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_user_activities'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create user_activities table
    op.create_table('user_activities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('activity_type', sa.String(length=50), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('activity_data', sa.JSON(), nullable=True),
        sa.Column('session_id', sa.String(length=100), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    # Drop user_activities table
    op.drop_table('user_activities')
