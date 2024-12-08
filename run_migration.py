from flask.cli import FlaskGroup
from app import create_app, db
from flask_migrate import Migrate, upgrade

app = create_app()
migrate = Migrate(app, db)

if __name__ == '__main__':
    with app.app_context():
        # Explicitly upgrade to all heads
        upgrade(revision='heads')
        print("Database migration completed successfully!")
