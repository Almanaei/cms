from flask import Flask
from flask_migrate import Migrate
from app import create_app, db
import os

app = create_app()
migrate = Migrate(app, db)

if __name__ == '__main__':
    with app.app_context():
        # Get the migrations directory
        migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations', 'versions')
        
        print("\nCurrent Database State:")
        print("----------------------")
        
        # List all migration files
        print("Available migrations:")
        for filename in sorted(os.listdir(migrations_dir)):
            if filename.endswith('.py') and not filename.startswith('__'):
                print(f"- {filename}")
        
        # Get current revision from database
        from flask_migrate import current
        current_rev = current()
        
        print(f"\nCurrent database revision: {current_rev}")
        if current_rev:
            print("Database is initialized with migrations.")
        else:
            print("Database might be empty or not initialized.")
