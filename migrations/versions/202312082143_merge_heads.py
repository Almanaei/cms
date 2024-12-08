"""merge heads

Revision ID: 202312082143
Revises: f622ce7cb309, 202312080047
Create Date: 2023-12-08 21:43:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '202312082143'
down_revision = None
branch_labels = None
depends_on = ('f622ce7cb309', '202312080047')


def upgrade():
    pass


def downgrade():
    pass
