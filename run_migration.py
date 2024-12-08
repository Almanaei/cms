from flask.cli import FlaskGroup
from app import create_app, db
from flask_migrate import Migrate, init, stamp
import os
import shutil

app = create_app()
migrate = Migrate(app, db)

def setup_migrations():
    with app.app_context():
        # Remove existing migrations directory if it exists
        migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
        if os.path.exists(migrations_dir):
            print("Removing existing migrations directory...")
            shutil.rmtree(migrations_dir)
            print("Migrations directory removed.")
        
        # Initialize migrations
        print("Initializing migrations...")
        init()
        
        # Create initial migration and stamp the database
        print("Stamping database with current state...")
        stamp()
        
        print("Migration setup complete!")

if __name__ == '__main__':
    try:
        setup_migrations()
    except Exception as e:
        print(f"Error: {e}")
