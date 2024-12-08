from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, current
from app import create_app, db

app = create_app()
migrate = Migrate(app, db)

if __name__ == '__main__':
    with app.app_context():
        # Get current revision(s)
        current_heads = current.get_heads()
        print("\nCurrent Database State:")
        print("----------------------")
        if current_heads:
            print("Current heads:")
            for head in current_heads:
                print(f"- {head}")
        else:
            print("No migration heads found. Database might be empty or not initialized.")

        # Get current revision
        current_rev = current.get_current_revision()
        if current_rev:
            print(f"\nCurrent revision: {current_rev}")
        else:
            print("\nNo current revision found. Database might be empty or not initialized.")
