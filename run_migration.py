from flask.cli import FlaskGroup
from app import create_app, db
from flask_migrate import Migrate, upgrade, stamp, init, revision
import shutil
import os

app = create_app()
migrate = Migrate(app, db)

if __name__ == '__main__':
    try:
        with app.app_context():
            # Delete existing migrations
            migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
            if os.path.exists(migrations_dir):
                print("Removing existing migrations directory...")
                shutil.rmtree(migrations_dir)
                print("Migrations directory removed.")
            
            # Initialize new migrations directory
            init()
            print("Initialized new migrations directory.")
            
            # Create initial migration
            revision(autogenerate=True, message="Initial migration")
            print("Created initial migration.")
            
            # Upgrade to the latest
            try:
                upgrade(revision='head')
                print("Successfully upgraded database to latest revision")
            except Exception as e:
                print(f"Error during upgrade: {e}")
                
    except Exception as e:
        print(f"Error: {e}")
