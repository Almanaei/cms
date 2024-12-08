"""
Flask extensions module.
This module contains all Flask extensions used by the application.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# Initialize SQLAlchemy for database operations
db = SQLAlchemy()

# Initialize Flask-Migrate for database migrations
migrate = Migrate()

# Initialize Flask-Login for user session management
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = 'Please log in to access this page.'
login.login_message_category = 'info'

# Initialize CSRF protection
csrf = CSRFProtect()
