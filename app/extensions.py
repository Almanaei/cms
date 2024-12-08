"""
Flask extensions module.
This module contains all Flask extensions used by the application.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_moment import Moment
from flask_wtf.csrf import CSRFProtect
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize SQLAlchemy for database operations
db = SQLAlchemy()

# Initialize Flask-Migrate for database migrations
migrate = Migrate()

# Initialize Flask-Login for user session management
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = 'Please log in to access this page.'
login.login_message_category = 'info'

# Initialize Flask-Mail for email support
mail = Mail()

# Initialize Flask-Moment for datetime handling
moment = Moment()

# Initialize CSRF protection
csrf = CSRFProtect()

# Initialize Flask-Cache for caching support
cache = Cache(config={
    'CACHE_TYPE': 'simple'
})

# Initialize Flask-Limiter for rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
