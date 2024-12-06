from app import db
from app.models import UserActivity

def upgrade():
    # Create the user_activities table
    UserActivity.__table__.create(db.engine)

def downgrade():
    # Drop the user_activities table
    UserActivity.__table__.drop(db.engine)
