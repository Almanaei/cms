from app import db, create_app
from app.models import UserActivity
from sqlalchemy import text

def upgrade():
    app = create_app()
    with app.app_context():
        # Create the user_activities table using raw SQL to ensure it exists
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS user_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                activity_type VARCHAR(50),
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                activity_data JSON,
                session_id VARCHAR(100),
                success BOOLEAN DEFAULT 1,
                ip_address VARCHAR(45),
                FOREIGN KEY (user_id) REFERENCES user (id)
            )
        """))
        db.session.commit()

def downgrade():
    app = create_app()
    with app.app_context():
        # Drop the user_activities table
        db.session.execute(text("DROP TABLE IF EXISTS user_activities"))
        db.session.commit()
