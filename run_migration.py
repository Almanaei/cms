from flask.cli import FlaskGroup
from app import create_app, db
from flask_migrate import Migrate
import os
import shutil

app = create_app()
migrate = Migrate(app, db)

def init_db():
    # Delete existing migrations
    migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
    if os.path.exists(migrations_dir):
        print("Removing existing migrations directory...")
        shutil.rmtree(migrations_dir)
        print("Migrations directory removed.")

    with app.app_context():
        # Create all tables
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully.")

        # Now set up migrations
        from flask_migrate import init, migrate
        
        print("Initializing migrations...")
        init()
        
        print("Creating initial migration...")
        migrate("Initial migration")
        
        print("Database initialization complete!")

if __name__ == '__main__':
    try:
        init_db()
    except Exception as e:
        print(f"Error: {e}")
