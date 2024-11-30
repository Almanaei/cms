from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import Config
from datetime import datetime

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Add datetime to Jinja2 environment
    app.jinja_env.globals.update(now=datetime.utcnow)

    # Register custom filters
    from app.utils.filters import timeago
    app.jinja_env.filters['timeago'] = timeago

    # Register Jinja2 filters
    @app.template_filter('datetime')
    def format_datetime(value, format='%Y-%m-%d %H:%M:%S'):
        if value is None:
            return ''
        return value.strftime(format)

    # Register template context processors
    @app.context_processor
    def utility_processor():
        from app.models import Settings
        return {
            'get_setting': Settings.get
        }

    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Register blueprints
    from .admin import media
    app.register_blueprint(media.bp, url_prefix='/admin')

    from app.cli import init_roles_command, create_admin_command, settings_group
    app.cli.add_command(init_roles_command)
    app.cli.add_command(create_admin_command)
    app.cli.add_command(settings_group)

    return app

from app import models
