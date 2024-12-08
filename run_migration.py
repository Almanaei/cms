from flask.cli import FlaskGroup
from app import create_app, db
from flask_migrate import Migrate, upgrade, stamp

app = create_app()
migrate = Migrate(app, db)

if __name__ == '__main__':
    try:
        with app.app_context():
            # First try to stamp the database with our merge migration
            try:
                stamp(revision='202312082143_merge_heads')
                print("Successfully stamped database with merge migration")
            except Exception as e:
                print(f"Warning during stamp: {e}")
                
            # Then try to upgrade to the latest
            try:
                upgrade(revision='heads')
                print("Successfully upgraded database to latest revision")
            except Exception as e:
                if "already exists" in str(e):
                    print(f"Warning: Table already exists. This is expected if running migrations on an existing database.")
                    print("Continuing with remaining migrations...")
                    # Try to stamp with the latest migration to skip the table creation
                    try:
                        stamp(revision='202312082146_stamp_existing_tables')
                        print("Successfully stamped database with latest migration")
                        upgrade(revision='heads')
                    except Exception as inner_e:
                        print(f"Error during recovery: {inner_e}")
                else:
                    print(f"Error during upgrade: {e}")
    except Exception as e:
        print(f"Error: {e}")
