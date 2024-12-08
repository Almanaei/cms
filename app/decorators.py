"""Decorators for the application."""
from functools import wraps
from flask import abort
from flask_login import current_user

def admin_required(f):
    """Require admin role for a view."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        if not current_user.role or current_user.role.name != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
