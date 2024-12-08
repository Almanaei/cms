import os
from datetime import timedelta
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    # Basic Config
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    DEBUG = True  # Enable debug mode
    
    # Database Config
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File Upload Config
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')
    BACKUP_DIR = os.path.join(basedir, 'app', 'static', 'backups')
    BACKUP_FILE_PREFIX = 'backup_'
    MAX_BACKUPS = 10
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Database Config for cPanel
    if os.environ.get('CPANEL_ENV') == 'true':
        USER = os.environ.get('USER', 'gdcdksdd')
        HOME = f'/home/{USER}'
        SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or \
            'sqlite:///' + os.path.join(HOME, 'cms', 'app.db')
        UPLOAD_FOLDER = os.path.join(HOME, 'cms', 'app', 'static', 'uploads')
        BACKUP_DIR = os.path.join(HOME, 'cms', 'app', 'static', 'backups')
        
    # Ensure directories exist with proper permissions
    @classmethod
    def init_app(cls, app):
        # Create necessary directories
        for directory in [cls.UPLOAD_FOLDER, cls.BACKUP_DIR]:
            if not os.path.exists(directory):
                os.makedirs(directory, mode=0o755, exist_ok=True)
                
        # Ensure log directory exists
        log_dir = os.path.join(os.path.dirname(app.instance_path), 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, mode=0o755, exist_ok=True)
            
        # Set up logging
        if not app.debug and not app.testing:
            from logging.handlers import RotatingFileHandler
            import logging
            
            log_file = os.path.join(log_dir, 'cms.log')
            file_handler = RotatingFileHandler(log_file, maxBytes=10240, backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            
            app.logger.setLevel(logging.INFO)
            app.logger.info('CMS startup')
    
    # AWS S3 Config (for production file storage)
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_BUCKET_NAME = os.environ.get('AWS_BUCKET_NAME')
    USE_S3 = os.environ.get('USE_S3', 'False').lower() == 'true'
    
    # Email Config
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Redis Config
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # Celery Config
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    
    # Cache Config
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300
    
    # API Rate Limiting
    RATELIMIT_DEFAULT = "200 per day;50 per hour;1 per second"
    RATELIMIT_STORAGE_URL = REDIS_URL
    
    # Security Config
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    
    # Babel Config
    LANGUAGES = ['en', 'es', 'fr', 'ar']
    BABEL_DEFAULT_LOCALE = 'en'
    
    # SEO Config
    SITE_NAME = 'Your CMS'
    META_DESCRIPTION = 'A powerful content management system'
    META_KEYWORDS = 'cms, content management, blog'
    
    # Social Media Config
    SOCIAL_FACEBOOK = os.environ.get('SOCIAL_FACEBOOK')
    SOCIAL_TWITTER = os.environ.get('SOCIAL_TWITTER')
    SOCIAL_INSTAGRAM = os.environ.get('SOCIAL_INSTAGRAM')
    SOCIAL_LINKEDIN = os.environ.get('SOCIAL_LINKEDIN')
    
    # Analytics Config
    GOOGLE_ANALYTICS_ID = os.environ.get('GOOGLE_ANALYTICS_ID')
    
    # Admin Config
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
    POSTS_PER_PAGE = 10
    ADMIN_POSTS_PER_PAGE = 20
    
    # Comment Config
    COMMENT_MODERATION = True
    MAX_COMMENT_LENGTH = 1000
    
    # Search Config
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
    SEARCH_RESULTS_PER_PAGE = 10
