from app import db, create_app
from app.models import UserActivity

def upgrade():
    app = create_app()
    with app.app_context():
        # Create the user_activities table
        UserActivity.__table__.create(db.engine)

def downgrade():
    app = create_app()
    with app.app_context():
        # Drop the user_activities table
        UserActivity.__table__.drop(db.engine)
