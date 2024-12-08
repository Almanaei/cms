import os
from datetime import timedelta
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))

# Load the appropriate .env file
if os.environ.get('CPANEL_ENV') == 'true':
    env_file = os.path.join(basedir, '.env.production')
else:
    env_file = os.path.join(basedir, '.env')

load_dotenv(env_file)

class Config:
    # Basic Config
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DEBUG = False
    
    # Database Config
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File Upload Config
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(basedir, 'app', 'static', 'uploads'))
    BACKUP_DIR = os.path.join(os.path.dirname(UPLOAD_FOLDER), 'backups')
    BACKUP_FILE_PREFIX = 'backup_'
    MAX_BACKUPS = 10
    
    # File upload settings
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16777216))  # 16MB default
    ALLOWED_EXTENSIONS = set(os.environ.get('ALLOWED_EXTENSIONS', 'png,jpg,jpeg,gif').split(','))
    
    # Mail settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
        
    # Ensure directories exist with proper permissions
    @classmethod
    def init_app(cls, app):
        # Create necessary directories
        dirs_to_create = [
            cls.UPLOAD_FOLDER,
            cls.BACKUP_DIR,
            os.path.join(os.path.dirname(app.instance_path), 'logs')
        ]
        
        for directory in dirs_to_create:
            if not os.path.exists(directory):
                try:
                    os.makedirs(directory, mode=0o755, exist_ok=True)
                    print(f"Created directory: {directory}")
                except Exception as e:
                    print(f"Error creating directory {directory}: {e}")
                
        # Set up logging
        if not app.debug:
            from logging.handlers import RotatingFileHandler
            import logging
            
            log_dir = os.path.join(os.path.dirname(app.instance_path), 'logs')
            if not os.path.exists(log_dir):
                os.makedirs(log_dir, mode=0o755, exist_ok=True)
            
            log_file = os.path.join(log_dir, 'cms.log')
            if not os.path.exists(log_file):
                open(log_file, 'a').close()
                os.chmod(log_file, 0o666)
            
            file_handler = RotatingFileHandler(log_file, maxBytes=10240, backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            
            app.logger.setLevel(logging.INFO)
            app.logger.info('CMS startup')
