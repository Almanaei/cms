from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app import create_app, db
import click

app = create_app()
migrate = Migrate(app, db)

@click.group()
def cli():
    """Management script for the CMS application."""
    pass

@cli.command()
def run():
    """Run the development server."""
    app.run(debug=True)

if __name__ == '__main__':
    cli()
