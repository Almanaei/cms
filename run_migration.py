from flask.cli import FlaskGroup
from app import create_app, db

app = create_app()

def init_db():
    with app.app_context():
        # Drop all tables if they exist
        print("Dropping all existing tables...")
        db.drop_all()
        print("All tables dropped.")
        
        # Create all tables
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully!")

if __name__ == '__main__':
    try:
        init_db()
    except Exception as e:
        print(f"Error: {e}")
