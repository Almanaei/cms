import os
import boto3
from PIL import Image
from flask import current_app
from werkzeug.utils import secure_filename
from datetime import datetime
import bleach
import markdown2
from functools import wraps
from flask_login import current_user
from flask import abort, request
import jwt

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_image(file, folder='uploads'):
    """Save image to local storage or S3 based on configuration"""
    if not file:
        return None
    
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{filename}"
    
    if current_app.config['USE_S3']:
        return save_to_s3(file, filename)
    else:
        return save_to_local(file, filename, folder)

def save_to_local(file, filename, folder='uploads'):
    """Save file to local storage"""
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], folder, filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Save original
    file.save(filepath)
    
    # Create thumbnail if it's an image
    if allowed_file(filename):
        create_thumbnail(filepath)
    
    return filename

def save_to_s3(file, filename):
    """Save file to AWS S3"""
    s3 = boto3.client(
        's3',
        aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY']
    )
    
    try:
        s3.upload_fileobj(
            file,
            current_app.config['AWS_BUCKET_NAME'],
            filename,
            ExtraArgs={'ACL': 'public-read'}
        )
        return filename
    except Exception as e:
        current_app.logger.error(f"Error uploading to S3: {str(e)}")
        return None

def create_thumbnail(filepath, size=(300, 300)):
    """Create thumbnail for an image"""
    try:
        with Image.open(filepath) as img:
            img.thumbnail(size)
            filename = os.path.splitext(filepath)[0] + '_thumb' + os.path.splitext(filepath)[1]
            img.save(filename)
    except Exception as e:
        current_app.logger.error(f"Error creating thumbnail: {str(e)}")

def sanitize_html(html_content):
    """Sanitize HTML content"""
    allowed_tags = [
        'a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
        'h1', 'h2', 'h3', 'p', 'img'
    ]
    allowed_attrs = {
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'title']
    }
    return bleach.clean(html_content, tags=allowed_tags, attributes=allowed_attrs)

def markdown_to_html(content):
    """Convert markdown to HTML"""
    return markdown2.markdown(content, extras=['fenced-code-blocks', 'tables'])

def admin_required(f):
    """Decorator for views that require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def rate_limit(limits):
    """Decorator for rate limiting"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Implementation of rate limiting logic
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def generate_token(data, expiration=3600):
    """Generate JWT token"""
    token = jwt.encode(
        {
            'data': data,
            'exp': datetime.utcnow() + timedelta(seconds=expiration)
        },
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )
    return token

def verify_token(token):
    """Verify JWT token"""
    try:
        data = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256']
        )
        return data['data']
    except:
        return None

def get_client_ip():
    """Get client IP address"""
    if 'X-Forwarded-For' in request.headers:
        return request.headers['X-Forwarded-For'].split(',')[0]
    return request.remote_addr

def format_datetime(value, format='medium'):
    """Format datetime based on locale"""
    if format == 'full':
        format = "EEEE, d. MMMM y 'at' HH:mm"
    elif format == 'medium':
        format = "EE dd.MM.y HH:mm"
    return babel.dates.format_datetime(value, format)
