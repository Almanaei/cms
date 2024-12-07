from datetime import datetime
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask import current_app, request
from app import db, login_manager
from slugify import slugify
from datetime import timedelta
from flask import url_for
from sqlalchemy import event
import os
import json

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(255))
    permissions = db.Column(db.Integer, default=0)  # Bitwise permissions
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', backref='role', lazy='dynamic')
    
    # Permission definitions
    VIEW_DASHBOARD = 0x01
    MANAGE_POSTS = 0x02
    MANAGE_USERS = 0x04
    MANAGE_ROLES = 0x08
    MANAGE_SETTINGS = 0x10
    MANAGE_MEDIA = 0x20
    MODERATE_COMMENTS = 0x40
    
    @staticmethod
    def insert_roles():
        roles = {
            'User': [Role.VIEW_DASHBOARD],
            'Editor': [Role.VIEW_DASHBOARD, Role.MANAGE_POSTS, Role.MODERATE_COMMENTS],
            'Admin': [Role.VIEW_DASHBOARD, Role.MANAGE_POSTS, Role.MANAGE_USERS,
                     Role.MANAGE_ROLES, Role.MANAGE_SETTINGS, Role.MANAGE_MEDIA,
                     Role.MODERATE_COMMENTS]
        }
        
        for role_name, permissions in roles.items():
            role = Role.query.filter_by(name=role_name).first()
            if role is None:
                role = Role(name=role_name)
            role.reset_permissions()
            for perm in permissions:
                role.add_permission(perm)
            db.session.add(role)
        db.session.commit()
    
    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm
    
    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm
    
    def reset_permissions(self):
        self.permissions = 0
    
    def has_permission(self, perm):
        return self.permissions & perm == perm
    
    def get_permissions_list(self):
        """Convert bitwise permissions to list of permission names."""
        permissions_list = []
        if self.has_permission(self.VIEW_DASHBOARD):
            permissions_list.append('View Dashboard')
        if self.has_permission(self.MANAGE_POSTS):
            permissions_list.append('Manage Posts')
        if self.has_permission(self.MANAGE_USERS):
            permissions_list.append('Manage Users')
        if self.has_permission(self.MANAGE_ROLES):
            permissions_list.append('Manage Roles')
        if self.has_permission(self.MANAGE_SETTINGS):
            permissions_list.append('Manage Settings')
        if self.has_permission(self.MANAGE_MEDIA):
            permissions_list.append('Manage Media')
        if self.has_permission(self.MODERATE_COMMENTS):
            permissions_list.append('Moderate Comments')
        return permissions_list

class UserActivity(db.Model):
    __tablename__ = 'user_activities'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    activity_type = db.Column(db.String(50))  # login, comment, like, share
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    activity_data = db.Column(db.JSON)
    session_id = db.Column(db.String(100))
    success = db.Column(db.Boolean, default=True)
    ip_address = db.Column(db.String(45))

class AnalyticsEvent(db.Model):
    __tablename__ = 'analytics_events'
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(50))  # scroll, click, search, download
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    session_id = db.Column(db.String(100))
    url = db.Column(db.String(500))
    element_id = db.Column(db.String(100))
    element_class = db.Column(db.String(100))
    event_data = db.Column(db.JSON)  # Renamed from metadata to event_data

class PageView(db.Model):
    __tablename__ = 'page_views'
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_pageview_user'), nullable=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id', name='fk_pageview_post'), nullable=True)
    session_id = db.Column(db.String(100))
    referrer = db.Column(db.String(500))
    user_agent = db.Column(db.String(500))
    duration = db.Column(db.Integer)
    bounce = db.Column(db.Boolean, default=False)
    device_type = db.Column(db.String(20))
    country = db.Column(db.String(2))
    browser = db.Column(db.String(50))
    os = db.Column(db.String(50))
    exit_url = db.Column(db.String(500))
    page_type = db.Column(db.String(50))
    content_id = db.Column(db.Integer)
    post = db.relationship('Post', back_populates='page_views')
    user = db.relationship('User', back_populates='page_views')

    @staticmethod
    def record(path, ip_address=None, user_agent=None, user=None):
        """Record a page view"""
        page_view = PageView(
            url=path,
            user_id=user.id if user else None,
            session_id=request.cookies.get('session_id'),
            referrer=request.referrer,
            user_agent=user_agent or request.user_agent.string,
            device_type='mobile' if request.user_agent.platform in ['iphone', 'android'] else 'desktop',
            browser=request.user_agent.browser,
            os=request.user_agent.platform
        )
        db.session.add(page_view)
        db.session.commit()
        return page_view

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    profile_image = db.Column(db.String(200))
    bio = db.Column(db.Text)
    website = db.Column(db.String(200))
    social_facebook = db.Column(db.String(200))
    social_twitter = db.Column(db.String(200))
    social_instagram = db.Column(db.String(200))
    email_confirmed = db.Column(db.Boolean, default=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    failed_login_attempts = db.Column(db.Integer, default=0)
    account_locked = db.Column(db.Boolean, default=False)
    account_locked_until = db.Column(db.DateTime)
    must_change_password = db.Column(db.Boolean, default=False)
    password_changed_at = db.Column(db.DateTime)
    
    # Relationships
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    likes = db.relationship('Like', backref='user', lazy='dynamic')
    page_views = db.relationship('PageView', back_populates='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': datetime.utcnow() + timedelta(seconds=expires_in)},
            current_app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                          algorithms=['HS256'])['reset_password']
        except:
            return None
        return User.query.get(id)

    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)
    
    def is_administrator(self):
        return self.role is not None and self.role.name == 'Admin'
        
    def log_activity(self, action, details=None, ip_address=None):
        activity = UserActivity(
            user_id=self.id,
            activity_type=action,
            activity_data=details,
            ip_address=ip_address
        )
        db.session.add(activity)
        db.session.commit()
    
    def update_last_activity(self):
        self.last_activity = datetime.utcnow()
        db.session.add(self)
        db.session.commit()
    
    def lock_account(self, duration_minutes=30):
        self.account_locked = True
        self.account_locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        db.session.add(self)
        db.session.commit()
    
    def unlock_account(self):
        self.account_locked = False
        self.account_locked_until = None
        self.failed_login_attempts = 0
        db.session.add(self)
        db.session.commit()

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.String(500))
    featured_image = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published = db.Column(db.Boolean, default=False)
    published_at = db.Column(db.DateTime)
    views = db.Column(db.Integer, default=0)
    meta_title = db.Column(db.String(200))
    meta_description = db.Column(db.String(300))
    featured = db.Column(db.Boolean, default=False)
    allow_comments = db.Column(db.Boolean, default=True)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    
    # Relationships
    comments = db.relationship('Comment', backref='post', lazy='dynamic')
    tags = db.relationship('Tag', secondary='post_tags', backref=db.backref('posts', lazy='dynamic'))
    likes = db.relationship('Like', backref='post', lazy='dynamic')
    page_views = db.relationship('PageView', back_populates='post', lazy='dynamic')

    def __init__(self, *args, **kwargs):
        if not kwargs.get('slug') and kwargs.get('title'):
            kwargs['slug'] = slugify(kwargs.get('title'))
        super().__init__(*args, **kwargs)
    
    def increment_views(self):
        self.views += 1
        db.session.add(self)
        db.session.commit()

    def get_related_posts(self, limit=3):
        """Get related posts based on category and tags."""
        # Start with posts in the same category
        related = Post.query.filter(
            Post.category_id == self.category_id,
            Post.id != self.id,
            Post.published == True
        )

        # Get posts with common tags
        if self.tags:
            tag_posts = Post.query.join(post_tags).join(Tag).filter(
                Tag.id.in_([tag.id for tag in self.tags]),
                Post.id != self.id,
                Post.published == True
            )
            # Combine both queries and remove duplicates
            related = related.union(tag_posts)

        # Order by date and limit results
        return related.order_by(Post.created_at.desc()).limit(limit).all()

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    slug = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.String(200))
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    posts = db.relationship('Post', backref='category', lazy='dynamic')
    children = db.relationship('Category', backref=db.backref('parent', remote_side=[id]))

    def __init__(self, *args, **kwargs):
        if not kwargs.get('slug') and kwargs.get('name'):
            kwargs['slug'] = slugify(kwargs.get('name'))
        super().__init__(*args, **kwargs)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved = db.Column(db.Boolean, default=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'))
    
    # Foreign Keys
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]))

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    slug = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, *args, **kwargs):
        if not kwargs.get('slug') and kwargs.get('name'):
            kwargs['slug'] = slugify(kwargs.get('name'))
        super().__init__(*args, **kwargs)

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

class Media(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    size = db.Column(db.Integer, nullable=False)  # Size in bytes
    width = db.Column(db.Integer)  # For images
    height = db.Column(db.Integer)  # For images
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    s3_key = db.Column(db.String(512))  # For S3 storage
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class MediaItem(db.Model):
    __tablename__ = 'media_items'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(512), nullable=False, unique=True)
    thumbnail_path = db.Column(db.String(512))
    type = db.Column(db.String(50), nullable=False)  # image, video, document, other
    mime_type = db.Column(db.String(100), nullable=False)
    size = db.Column(db.Integer, nullable=False)  # in bytes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<MediaItem {self.filename}>'
    
    @property
    def url(self):
        return url_for('media.download_media', id=self.id)
    
    @property
    def thumbnail_url(self):
        if self.thumbnail_path:
            return url_for('media.download_media', id=self.id, thumbnail=True)
        return None

class BackupSchedule(db.Model):
    """Model for backup schedule settings."""
    id = db.Column(db.Integer, primary_key=True)
    frequency = db.Column(db.String(20), default='daily')  # daily, weekly, monthly
    time = db.Column(db.String(5), default='00:00')  # 24-hour format HH:MM
    retention = db.Column(db.Integer, default=30)  # days to keep backups
    notify_on_failure = db.Column(db.Boolean, default=True)
    enabled = db.Column(db.Boolean, default=True)
    last_run = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get_schedule():
        """Get the current backup schedule or create a default one."""
        schedule = BackupSchedule.query.first()
        if not schedule:
            schedule = BackupSchedule()
            db.session.add(schedule)
            db.session.commit()
        return schedule

class Backup(db.Model):
    """Model for database backups."""
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    type = db.Column(db.String(50))  # manual, scheduled
    status = db.Column(db.String(50), default='pending')  # pending, completed, failed
    size = db.Column(db.Integer)  # Size in bytes
    note = db.Column(db.Text)
    
    @property
    def filepath(self):
        """Get the full path to the backup file."""
        return os.path.join(current_app.config['BACKUP_DIR'], self.filename)
    
    def delete_file(self):
        """Delete the backup file from disk."""
        if os.path.exists(self.filepath):
            os.remove(self.filepath)

class Settings(db.Model):
    __tablename__ = 'settings'
    
    # Class-level cache
    _cache = {}
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(500))
    type = db.Column(db.String(20), default='string')
    description = db.Column(db.String(200))

    @staticmethod
    def get(key, default=None):
        """Get a setting value by key."""
        setting = Settings.query.filter_by(key=key).first()
        if setting is None:
            return default
            
        try:
            if setting.type == 'boolean':
                return setting.value.lower() in ('true', '1', 'yes', 'on')
            elif setting.type == 'integer':
                # Handle float strings by converting to float first then to int
                return int(float(setting.value))
            elif setting.type == 'float':
                return float(setting.value)
            elif setting.type == 'json':
                return json.loads(setting.value)
            else:  # string
                return setting.value
        except (ValueError, json.JSONDecodeError) as e:
            current_app.logger.error(f"Error converting setting {key}: {str(e)}")
            return default

    @staticmethod
    def set(key, value, type='string', description=None):
        """Set a setting value."""
        setting = Settings.query.filter_by(key=key).first()
        
        # Convert value to string based on type
        if isinstance(value, bool):
            str_value = str(value).lower()
            type = 'boolean'
        elif isinstance(value, (int, float)):
            str_value = str(value)
            type = 'float' if isinstance(value, float) else 'integer'
        elif isinstance(value, (dict, list)):
            str_value = json.dumps(value)
            type = 'json'
        else:
            str_value = str(value)
            type = 'string'

        if setting is None:
            setting = Settings(key=key, value=str_value, type=type, description=description)
            db.session.add(setting)
        else:
            setting.value = str_value
            setting.type = type
            if description:
                setting.description = description

        try:
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error saving setting {key}: {str(e)}")
            return False

class UserActivityLog(db.Model):
    """Model for tracking detailed user activity"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # e.g., 'report_generated', 'report_exported'
    details = db.Column(db.JSON)  # Store additional details as JSON
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('activity_logs', lazy=True))

    @staticmethod
    def log_activity(user_id, action, details=None):
        """Helper method to log user activity"""
        log = UserActivityLog(
            user_id=user_id,
            action=action,
            details=details or {}
        )
        db.session.add(log)
        db.session.commit()
        return log

class ReportDraft(db.Model):
    """Model for storing report drafts"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100))
    metrics = db.Column(db.JSON)  # Store selected metrics
    timeframe = db.Column(db.String(10))
    last_modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('report_drafts', lazy=True))

    @staticmethod
    def get_or_create(user_id, name="Untitled Report"):
        """Get existing draft or create new one"""
        draft = ReportDraft.query.filter_by(user_id=user_id, name=name).first()
        if not draft:
            draft = ReportDraft(user_id=user_id, name=name)
            db.session.add(draft)
            db.session.commit()
        return draft

# Settings model event listeners
@event.listens_for(Settings, 'after_update')
def receive_after_update(mapper, connection, target):
    """Clear cache entry when a setting is updated."""
    Settings._cache.pop(target.key, None)

@event.listens_for(Settings, 'after_delete')
def receive_after_delete(mapper, connection, target):
    """Clear cache entry when a setting is deleted."""
    Settings._cache.pop(target.key, None)

# Association Tables
post_tags = db.Table('post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)
