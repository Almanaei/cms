from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app import create_app, db
from alembic.script import ScriptDirectory
from alembic.config import Config

app = create_app()
migrate = Migrate(app, db)

if __name__ == '__main__':
    with app.app_context():
        # Get Alembic config and script directory
        config = Config("migrations/alembic.ini")
        script = ScriptDirectory.from_config(config)
        
        # Get current heads from script
        heads = script.get_heads()
        
        print("\nCurrent Database State:")
        print("----------------------")
        if heads:
            print("Current heads:")
            for head in heads:
                print(f"- {head}")
        else:
            print("No migration heads found. Database might be empty or not initialized.")

        # Get current revision from database
        from alembic.runtime.migration import MigrationContext
        from sqlalchemy import create_engine
        
        engine = db.engine
        conn = engine.connect()
        context = MigrationContext.configure(conn)
        current_rev = context.get_current_revision()
        
        if current_rev:
            print(f"\nCurrent revision: {current_rev}")
            if current_rev in heads:
                print("Database is up to date!")
            else:
                print("Database needs to be upgraded to latest revision.")
        else:
            print("\nNo current revision found. Database might be empty or not initialized.")
            
        conn.close()
