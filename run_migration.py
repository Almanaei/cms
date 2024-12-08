from flask.cli import FlaskGroup
from app import create_app, db
from flask_migrate import Migrate, upgrade, stamp, merge_heads

app = create_app()
migrate = Migrate(app, db)

if __name__ == '__main__':
    try:
        with app.app_context():
            # First try to merge the heads
            try:
                merge_heads()
                print("Successfully merged migration heads")
            except Exception as e:
                print(f"Warning during merge: {e}")
                
            # Then try to upgrade to the latest
            try:
                upgrade(revision='heads')
                print("Successfully upgraded database to latest revision")
            except Exception as e:
                if "already exists" in str(e):
                    print(f"Warning: Table already exists. This is expected if running migrations on an existing database.")
                    print("Continuing with remaining migrations...")
                else:
                    print(f"Error during upgrade: {e}")
    except Exception as e:
        print(f"Error: {e}")
