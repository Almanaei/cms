from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
from sqlalchemy import func
from ..models import Post, User, PageView, UserActivity
from ..utils.decorators import admin_required
from .. import db

analytics = Blueprint('analytics', __name__)

def get_growth_rate(current, previous):
    """Calculate growth rate between two values"""
    if not previous:
        return 0
    return round(((current - previous) / previous) * 100, 1)

def get_date_range(timeframe):
    """Get start and end dates based on timeframe"""
    end_date = datetime.utcnow()
    if timeframe == '7d':
        start_date = end_date - timedelta(days=7)
    elif timeframe == '30d':
        start_date = end_date - timedelta(days=30)
    elif timeframe == '90d':
        start_date = end_date - timedelta(days=90)
    else:
        start_date = end_date - timedelta(days=30)  # Default to 30 days
    return start_date, end_date

def get_previous_period(start_date, end_date):
    """Get start and end dates for the previous period"""
    period_length = end_date - start_date
    prev_end_date = start_date
    prev_start_date = prev_end_date - period_length
    return prev_start_date, prev_end_date

@analytics.route('/analytics')
@login_required
@admin_required
def dashboard():
    timeframe = request.args.get('timeframe', '30d')
    start_date, end_date = get_date_range(timeframe)
    prev_start_date, prev_end_date = get_previous_period(start_date, end_date)

    # Get page views
    current_views = db.session.query(func.count(PageView.id))\
        .filter(PageView.timestamp.between(start_date, end_date))\
        .scalar() or 0
    
    previous_views = db.session.query(func.count(PageView.id))\
        .filter(PageView.timestamp.between(prev_start_date, prev_end_date))\
        .scalar() or 0

    # Get active users
    current_users = db.session.query(func.count(User.id))\
        .filter(User.last_activity >= start_date)\
        .scalar() or 0
    
    previous_users = db.session.query(func.count(User.id))\
        .filter(User.last_activity.between(prev_start_date, prev_end_date))\
        .scalar() or 0

    # Get published content
    current_content = db.session.query(func.count(Post.id))\
        .filter(Post.status == 'published')\
        .filter(Post.published_at <= end_date)\
        .scalar() or 0
    
    previous_content = db.session.query(func.count(Post.id))\
        .filter(Post.status == 'published')\
        .filter(Post.published_at <= prev_end_date)\
        .scalar() or 0

    # Calculate average time on page
    avg_time = db.session.query(func.avg(PageView.duration))\
        .filter(PageView.timestamp.between(start_date, end_date))\
        .scalar() or 0
    
    prev_avg_time = db.session.query(func.avg(PageView.duration))\
        .filter(PageView.timestamp.between(prev_start_date, prev_end_date))\
        .scalar() or 0

    # Get traffic data for chart
    traffic_data = []
    traffic_dates = []
    current_date = start_date
    while current_date <= end_date:
        next_date = current_date + timedelta(days=1)
        views = db.session.query(func.count(PageView.id))\
            .filter(PageView.timestamp.between(current_date, next_date))\
            .scalar() or 0
        traffic_data.append(views)
        traffic_dates.append(current_date.strftime('%Y-%m-%d'))
        current_date = next_date

    # Get traffic sources
    sources = db.session.query(
        PageView.referrer,
        func.count(PageView.id).label('count')
    ).filter(PageView.timestamp.between(start_date, end_date))\
    .group_by(PageView.referrer)\
    .order_by(func.count(PageView.id).desc())\
    .limit(5)\
    .all()

    source_labels = [s[0] or 'Direct' for s in sources]
    source_data = [s[1] for s in sources]

    # Get top performing content
    top_content = db.session.query(
        Post,
        func.count(PageView.id).label('views'),
        func.avg(PageView.duration).label('avg_time')
    ).join(PageView, PageView.post_id == Post.id)\
    .filter(PageView.timestamp.between(start_date, end_date))\
    .group_by(Post.id)\
    .order_by(func.count(PageView.id).desc())\
    .limit(5)\
    .all()

    top_content_data = []
    for post, views, avg_time in top_content:
        # Calculate engagement score (example algorithm)
        engagement = min(10, round((views / 100) + (avg_time / 60), 1))
        
        # Calculate trend
        prev_views = db.session.query(func.count(PageView.id))\
            .filter(PageView.post_id == post.id)\
            .filter(PageView.timestamp.between(prev_start_date, prev_end_date))\
            .scalar() or 0
        trend = get_growth_rate(views, prev_views)

        top_content_data.append({
            'title': post.title,
            'category': post.category,
            'featured_image': post.featured_image,
            'views': views,
            'avg_time': f"{int(avg_time // 60)}:{int(avg_time % 60):02d}",
            'engagement': engagement,
            'trend': trend
        })

    # Get recent activities
    recent_activities = []
    activities = UserActivity.query\
        .order_by(UserActivity.created_at.desc())\
        .limit(10)\
        .all()

    for activity in activities:
        icon = {
            'created_post': 'plus',
            'updated_post': 'edit',
            'deleted_post': 'trash',
            'login': 'sign-in-alt',
            'uploaded_media': 'upload'
        }.get(activity.action, 'info')

        recent_activities.append({
            'type': activity.action.split('_')[0],
            'icon': icon,
            'timestamp': activity.created_at,
            'description': activity.details
        })

    return render_template('admin/analytics.html',
        total_views=current_views,
        view_growth=get_growth_rate(current_views, previous_views),
        active_users=current_users,
        user_growth=get_growth_rate(current_users, previous_users),
        total_content=current_content,
        content_growth=get_growth_rate(current_content, previous_content),
        avg_time_on_page=f"{int(avg_time // 60)}:{int(avg_time % 60):02d}",
        time_growth=get_growth_rate(avg_time, prev_avg_time),
        traffic_dates=traffic_dates,
        traffic_data=traffic_data,
        source_labels=source_labels,
        source_data=source_data,
        top_content=top_content_data,
        recent_activities=recent_activities
    )

@analytics.route('/analytics/data')
@login_required
@admin_required
def get_analytics_data():
    """AJAX endpoint for updating dashboard data"""
    timeframe = request.args.get('timeframe', '30d')
    # Reuse the same data gathering logic but return JSON
    # This will be implemented based on frontend needs
    return jsonify({'status': 'success'})
