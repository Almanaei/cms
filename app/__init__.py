from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from config import Config
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
import os
import sys
import traceback
from app.extensions import (
    db, migrate, login, csrf
)

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    
    if test_config is None:
        app.config.from_object('config.Config')
    else:
        app.config.update(test_config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    csrf.init_app(app)

    # Configure login
    login.login_view = 'auth.login'
    login.login_message = 'Please log in to access this page.'
    login.login_message_category = 'info'

    # Create instance directory if it doesn't exist
    if not os.path.exists(app.instance_path):
        os.makedirs(app.instance_path)
        
    # Create backup directory if it doesn't exist
    backup_dir = os.path.join(app.instance_path, 'backups')
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    app.config['BACKUP_DIR'] = backup_dir

    # Ensure backup directory exists
    backup_dir = app.config.get('BACKUP_DIR')
    if backup_dir and not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    # Configure logging
    try:
        # Get the absolute path to the logs directory
        logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir, exist_ok=True)
            print(f"Created logs directory at: {logs_dir}", file=sys.stderr)

        # Create log file immediately
        log_file = os.path.join(logs_dir, 'error.log')
        with open(log_file, 'a') as f:
            f.write(f'Log file initialized at {datetime.utcnow()}\n')

        # Configure logging format
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s\n'
            'Path: %(pathname)s:%(lineno)d\n'
            'Function: %(funcName)s\n'
            'Traceback:\n%(exc_info)s\n'
        )
        
        # File handler for error.log
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10240000,  # 10MB
            backupCount=10,
            encoding='utf-8',
            delay=False  # Create file immediately
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.ERROR)
        
        # Also log to stderr for debugging
        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(logging.ERROR)
        
        # Configure the root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.ERROR)
        for handler in root_logger.handlers[:]:  # Remove any existing handlers
            root_logger.removeHandler(handler)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(stream_handler)
        
        # Configure Flask app logger
        app.logger.handlers = []  # Remove default handlers
        app.logger.addHandler(file_handler)
        app.logger.addHandler(stream_handler)
        app.logger.setLevel(logging.INFO)
        
        # Log an initial message to verify logging is working (only if debug mode)
        if app.debug:
            app.logger.info('Logging system initialized')

        # Register error handlers
        @app.errorhandler(Exception)
        def handle_exception(e):
            # Log the exception with full traceback
            tb = traceback.format_exc()
            app.logger.error(f'Unhandled exception: {str(e)}\n{tb}')
            # Return error page
            return render_template('errors/500.html'), 500

        @app.errorhandler(404)
        def not_found_error(error):
            app.logger.error(f'Page not found: {request.url}')
            return render_template('errors/404.html'), 404

        @app.errorhandler(500)
        def internal_error(error):
            db.session.rollback()
            app.logger.error(f'Server Error: {str(error)}')
            return render_template('errors/500.html'), 500
        
    except Exception as e:
        print(f"Error setting up logging: {str(e)}\n{traceback.format_exc()}", file=sys.stderr)

    # Register blueprints
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from app.media import bp as media_bp
    app.register_blueprint(media_bp)

    # Import models to ensure they are known to Flask-Migrate
    from app import models

    @app.context_processor
    def utility_processor():
        from app.models import Settings
        return {
            'get_setting': Settings.get
        }

    from app.cli import init_roles_command, create_admin_command, settings_group
    app.cli.add_command(init_roles_command)
    app.cli.add_command(create_admin_command)
    app.cli.add_command(settings_group)

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

    return app
