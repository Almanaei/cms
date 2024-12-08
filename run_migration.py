from flask.cli import FlaskGroup
from app import create_app
from flask_migrate import upgrade

app = create_app()
cli = FlaskGroup(app)

if __name__ == '__main__':
    with app.app_context():
        upgrade()
        print("Database migration completed successfully!")
