from flask.cli import FlaskGroup
from app import create_app, db
from flask_migrate import Migrate, upgrade, stamp

app = create_app()
migrate = Migrate(app, db)

if __name__ == '__main__':
    with app.app_context():
        try:
            # First, stamp the database with our merge migration
            stamp(revision='202312082143')
            print("Database stamped successfully!")
            
            # Then upgrade to all heads
            upgrade(revision='heads')
            print("Database migration completed successfully!")
        except Exception as e:
            print(f"Error during migration: {str(e)}")
            raise
