from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import Config
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
import os
import sys

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Configure logging
    try:
        # Get the absolute path to the logs directory
        logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
            print(f"Created logs directory at: {logs_dir}", file=sys.stderr)

        # Configure logging format
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        )
        
        # File handler for error.log
        log_file = os.path.join(logs_dir, 'error.log')
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.ERROR)
        
        # Also log to stderr for debugging
        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(logging.ERROR)
        
        # Add handlers to the app logger
        app.logger.addHandler(file_handler)
        app.logger.addHandler(stream_handler)
        app.logger.setLevel(logging.ERROR)
        
        print(f"Logging configured. Log file: {log_file}", file=sys.stderr)
        app.logger.info('CMS startup')
        
    except Exception as e:
        print(f"Error setting up logging: {str(e)}", file=sys.stderr)

    # Add datetime to Jinja2 environment
    app.jinja_env.globals.update(now=datetime.utcnow)

    # Register custom filters
    from app.utils.filters import timeago, number_format
    app.jinja_env.filters['timeago'] = timeago
    app.jinja_env.filters['number_format'] = number_format

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
