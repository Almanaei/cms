from datetime import datetime
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask import current_app
from app import db, login_manager
from slugify import slugify
from datetime import timedelta
from flask import url_for

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

class UserActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(64), nullable=False)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserActivity {self.action}>'

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
    activities = db.relationship('UserActivity', backref='user', lazy='dynamic')
    page_views = db.relationship('PageView', backref='viewer', lazy='dynamic')

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
            action=action,
            details=details,
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
    page_views = db.relationship('PageView', backref='viewed_post', lazy='dynamic')

    def __init__(self, *args, **kwargs):
        if not kwargs.get('slug') and kwargs.get('title'):
            kwargs['slug'] = slugify(kwargs.get('title'))
        super().__init__(*args, **kwargs)
    
    def increment_views(self):
        self.views += 1
        db.session.add(self)
        db.session.commit()

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

class PageView(db.Model):
    """Model for tracking page views and analytics"""
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    referrer = db.Column(db.String(255))
    duration = db.Column(db.Integer, default=0)  # Duration in seconds
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Define relationships without backrefs to avoid conflicts
    post = db.relationship('Post')
    user = db.relationship('User')

    def __repr__(self):
        return f'<PageView {self.id}>'

# Association Tables
post_tags = db.Table('post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)
