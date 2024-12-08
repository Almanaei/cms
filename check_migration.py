from flask.cli import FlaskGroup
from app import create_app
from flask_migrate import current

app = create_app()
cli = FlaskGroup(app)

if __name__ == '__main__':
    with app.app_context():
        # Get current revision
        revision = current()
        print(f"Current database revision: {revision}")
        print("If this matches the latest migration file in your versions folder, you're up to date!")
