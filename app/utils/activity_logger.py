from flask import request, current_app
from app import db
from app.models import UserActivity
from datetime import datetime

def log_activity(user_id, activity_type, activity_data=None, success=True):
    """
    Log user activity with detailed information.
    
    Args:
        user_id (int): ID of the user performing the action
        activity_type (str): Type of activity (e.g., 'login', 'create_post', etc.)
        activity_data (dict): Additional data about the activity
        success (bool): Whether the activity was successful
    """
    try:
        activity = UserActivity(
            user_id=user_id,
            activity_type=activity_type,
            activity_data=activity_data,
            session_id=request.cookies.get('session', None),
            success=success,
            ip_address=request.remote_addr,
            timestamp=datetime.utcnow()
        )
        db.session.add(activity)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error logging activity: {str(e)}')
