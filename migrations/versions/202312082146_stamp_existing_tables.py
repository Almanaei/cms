"""stamp existing tables

Revision ID: 202312082146
Revises: 202312082143
Create Date: 2023-12-08 21:46:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '202312082146'
down_revision = '202312082143'
branch_labels = None
depends_on = None


def upgrade():
    # This is a stamp migration - it doesn't make any changes
    # It just marks that all previous migrations have been applied
    pass


def downgrade():
    pass
