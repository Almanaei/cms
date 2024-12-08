from flask.cli import FlaskGroup
from app import create_app, db
from flask_migrate import Migrate, current, heads

app = create_app()
migrate = Migrate(app, db)

if __name__ == '__main__':
    with app.app_context():
        # Get all current heads
        current_heads = heads()
        print("Current database heads:")
        for head in current_heads:
            print(f"- {head}")
        
        # Get current revision
        revision = current()
        print(f"\nCurrent database revision: {revision}")
        print("If this matches one of the heads above, that branch is up to date!")
