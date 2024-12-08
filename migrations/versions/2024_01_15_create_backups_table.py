"""Create backups table

Revision ID: 2024_01_15_create_backups
Revises: 2024_01_14_add_media_table
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2024_01_15_create_backups'
down_revision = '2024_01_14_add_media_table'
branch_labels = None
depends_on = None


def upgrade():
    # Create backups table
    op.create_table('backups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('size', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    # Drop backups table
    op.drop_table('backups')
