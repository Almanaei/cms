from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request, send_file, make_response
from flask_login import login_required, current_user
from flask_login import admin_required
from sqlalchemy import func, desc, and_, text
from ..models import Post, User, PageView, UserActivity, AnalyticsEvent, Comment, UserActivityLog, ReportDraft
from ..utils.decorators import admin_required
from .. import db
import json
import pandas as pd
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

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
    elif timeframe == '1y':
        start_date = end_date - timedelta(days=365)
    else:
        start_date = end_date - timedelta(days=30)
    return start_date, end_date

@analytics.route('/analytics')
@login_required
@admin_required
def dashboard():
    timeframe = request.args.get('timeframe', '30d')
    start_date, end_date = get_date_range(timeframe)
    prev_start_date = start_date - (end_date - start_date)

    # Basic Metrics
    metrics = get_basic_metrics(start_date, end_date, prev_start_date)
    
    # User Engagement Metrics
    engagement = get_engagement_metrics(start_date, end_date)
    
    # Content Performance
    content_perf = get_content_performance(start_date, end_date)
    
    # Traffic Analysis
    traffic = get_traffic_analysis(start_date, end_date)
    
    # User Behavior
    behavior = get_user_behavior(start_date, end_date)
    
    # Geographic Data
    geo_data = get_geographic_data(start_date, end_date)
    
    # Technical Metrics
    tech_metrics = get_technical_metrics(start_date, end_date)

    return render_template('admin/analytics.html',
                         timeframe=timeframe,
                         metrics=metrics,
                         engagement=engagement,
                         content_perf=content_perf,
                         traffic=traffic,
                         behavior=behavior,
                         geo_data=geo_data,
                         tech_metrics=tech_metrics)

def get_basic_metrics(start_date, end_date, prev_start_date):
    """Get basic analytics metrics"""
    current_period = and_(PageView.timestamp >= start_date, PageView.timestamp <= end_date)
    prev_period = and_(PageView.timestamp >= prev_start_date, PageView.timestamp < start_date)
    
    # Page Views
    current_views = db.session.query(func.count(PageView.id)).filter(current_period).scalar() or 0
    prev_views = db.session.query(func.count(PageView.id)).filter(prev_period).scalar() or 0
    
    # Unique Visitors
    current_visitors = db.session.query(func.count(func.distinct(PageView.session_id))).filter(current_period).scalar() or 0
    prev_visitors = db.session.query(func.count(func.distinct(PageView.session_id))).filter(prev_period).scalar() or 0
    
    # Average Session Duration
    avg_duration = db.session.query(func.avg(PageView.duration)).filter(current_period).scalar() or 0
    prev_avg_duration = db.session.query(func.avg(PageView.duration)).filter(prev_period).scalar() or 0
    
    # Bounce Rate
    bounce_rate = db.session.query(func.avg(PageView.bounce)).filter(current_period).scalar() or 0
    prev_bounce_rate = db.session.query(func.avg(PageView.bounce)).filter(prev_period).scalar() or 0
    
    return {
        'views': {
            'current': current_views,
            'previous': prev_views,
            'growth': get_growth_rate(current_views, prev_views)
        },
        'visitors': {
            'current': current_visitors,
            'previous': prev_visitors,
            'growth': get_growth_rate(current_visitors, prev_visitors)
        },
        'duration': {
            'current': round(avg_duration or 0),
            'previous': round(prev_avg_duration or 0),
            'growth': get_growth_rate(avg_duration or 0, prev_avg_duration or 0)
        },
        'bounce_rate': {
            'current': round(bounce_rate * 100, 1) if bounce_rate else 0,
            'previous': round(prev_bounce_rate * 100, 1) if prev_bounce_rate else 0,
            'growth': get_growth_rate(bounce_rate or 0, prev_bounce_rate or 0)
        }
    }

def get_engagement_metrics(start_date, end_date):
    """Get user engagement metrics"""
    # Comments per Post
    comments = db.session.query(
        func.count(Comment.id).label('count'),
        Post.id
    ).join(Post).filter(
        Comment.created_at.between(start_date, end_date)
    ).group_by(Post.id).all()
    
    avg_comments = sum([c.count for c in comments]) / len(comments) if comments else 0
    
    # User Activity Distribution
    activities = db.session.query(
        UserActivity.activity_type,
        func.count(UserActivity.id).label('count')
    ).filter(
        UserActivity.timestamp.between(start_date, end_date)
    ).group_by(UserActivity.activity_type).all()
    
    # Time to First Action
    first_actions = db.session.query(
        func.min(UserActivity.timestamp) - User.created_at
    ).join(User).filter(
        User.created_at.between(start_date, end_date)
    ).scalar()
    
    return {
        'avg_comments': round(avg_comments, 1),
        'activities': {a.activity_type: a.count for a in activities},
        'time_to_action': first_actions.total_seconds() if first_actions else 0
    }

def get_content_performance(start_date, end_date):
    """Get content performance metrics"""
    # Most Viewed Content
    top_content = db.session.query(
        Post.title,
        func.count(PageView.id).label('views')
    ).join(PageView).filter(
        PageView.timestamp.between(start_date, end_date)
    ).group_by(Post.id).order_by(desc('views')).limit(10).all()
    
    # Content Categories Performance
    category_perf = db.session.query(
        Post.category_id,
        func.count(PageView.id).label('views')
    ).join(PageView).filter(
        PageView.timestamp.between(start_date, end_date)
    ).group_by(Post.category_id).all()
    
    return {
        'top_content': [(post.title, views) for post, views in top_content],
        'category_performance': category_perf
    }

def get_traffic_analysis(start_date, end_date):
    """Get traffic analysis metrics"""
    # Traffic Sources
    sources = db.session.query(
        PageView.referrer,
        func.count(PageView.id).label('count')
    ).filter(
        PageView.timestamp.between(start_date, end_date)
    ).group_by(PageView.referrer).all()
    
    # Device Distribution
    devices = db.session.query(
        PageView.device_type,
        func.count(PageView.id).label('count')
    ).filter(
        PageView.timestamp.between(start_date, end_date)
    ).group_by(PageView.device_type).all()
    
    # Peak Hours
    peak_hours = db.session.query(
        func.extract('hour', PageView.timestamp).label('hour'),
        func.count(PageView.id).label('count')
    ).filter(
        PageView.timestamp.between(start_date, end_date)
    ).group_by('hour').order_by(desc('count')).all()
    
    return {
        'sources': {s.referrer or 'direct': s.count for s in sources},
        'devices': {d.device_type: d.count for d in devices},
        'peak_hours': {h.hour: h.count for h in peak_hours}
    }

def get_user_behavior(start_date, end_date):
    """Get user behavior metrics"""
    # Event Types Distribution
    events = db.session.query(
        AnalyticsEvent.event_type,
        func.count(AnalyticsEvent.id).label('count')
    ).filter(
        AnalyticsEvent.timestamp.between(start_date, end_date)
    ).group_by(AnalyticsEvent.event_type).all()
    
    # User Flow
    flow = db.session.query(
        PageView.url,
        PageView.exit_url,
        func.count(PageView.id).label('count')
    ).filter(
        PageView.timestamp.between(start_date, end_date)
    ).group_by(PageView.url, PageView.exit_url).all()
    
    return {
        'events': {e.event_type: e.count for e in events},
        'flow': [(f.url, f.exit_url, f.count) for f in flow]
    }

def get_geographic_data(start_date, end_date):
    """Get geographic metrics"""
    # Country Distribution
    countries = db.session.query(
        PageView.country,
        func.count(PageView.id).label('count')
    ).filter(
        PageView.timestamp.between(start_date, end_date)
    ).group_by(PageView.country).all()
    
    return {
        'countries': {c.country: c.count for c in countries}
    }

def get_technical_metrics(start_date, end_date):
    """Get technical metrics"""
    # Browser Distribution
    browsers = db.session.query(
        PageView.browser,
        func.count(PageView.id).label('count')
    ).filter(
        PageView.timestamp.between(start_date, end_date)
    ).group_by(PageView.browser).all()
    
    # OS Distribution
    os_dist = db.session.query(
        PageView.os,
        func.count(PageView.id).label('count')
    ).filter(
        PageView.timestamp.between(start_date, end_date)
    ).group_by(PageView.os).all()
    
    return {
        'browsers': {b.browser: b.count for b in browsers},
        'operating_systems': {o.os: o.count for o in os_dist}
    }

@analytics.route('/analytics/export')
@login_required
@admin_required
def export_analytics():
    """Export analytics data"""
    timeframe = request.args.get('timeframe', '30d')
    start_date, end_date = get_date_range(timeframe)
    
    # Gather all metrics
    data = {
        'basic_metrics': get_basic_metrics(start_date, end_date, start_date - (end_date - start_date)),
        'engagement': get_engagement_metrics(start_date, end_date),
        'content_performance': get_content_performance(start_date, end_date),
        'traffic': get_traffic_analysis(start_date, end_date),
        'user_behavior': get_user_behavior(start_date, end_date),
        'geographic': get_geographic_data(start_date, end_date),
        'technical': get_technical_metrics(start_date, end_date)
    }
    
    return jsonify(data)

@analytics.route('/analytics/custom-report', methods=['POST'])
@login_required
@admin_required
def generate_custom_report():
    """Generate a custom analytics report based on selected metrics"""
    data = request.get_json()
    timeframe = data.get('timeframe', '30d')
    metrics = data.get('metrics', [])
    start_date, end_date = get_date_range(timeframe)
    
    # Log report generation activity
    UserActivityLog.log_activity(
        current_user.id,
        'report_generated',
        {'timeframe': timeframe, 'metrics': metrics}
    )
    
    report_data = {}
    
    if 'basic_metrics' in metrics:
        report_data['basic_metrics'] = get_basic_metrics(start_date, end_date, start_date - (end_date - start_date))
    if 'engagement' in metrics:
        report_data['engagement'] = get_engagement_metrics(start_date, end_date)
    if 'content' in metrics:
        report_data['content'] = get_content_performance(start_date, end_date)
    if 'traffic' in metrics:
        report_data['traffic'] = get_traffic_analysis(start_date, end_date)
    if 'behavior' in metrics:
        report_data['behavior'] = get_user_behavior(start_date, end_date)
    if 'geographic' in metrics:
        report_data['geographic'] = get_geographic_data(start_date, end_date)
    if 'technical' in metrics:
        report_data['technical'] = get_technical_metrics(start_date, end_date)
    
    return jsonify(report_data)

@analytics.route('/analytics/export/<format>')
@login_required
@admin_required
def export_report(format):
    """Export analytics report in various formats"""
    timeframe = request.args.get('timeframe', '30d')
    metrics = request.args.getlist('metrics')
    
    # Log export activity
    UserActivityLog.log_activity(
        current_user.id,
        'report_exported',
        {'format': format, 'timeframe': timeframe, 'metrics': metrics}
    )
    
    # Gather report data
    report_data = {}
    for metric in metrics:
        if metric == 'basic_metrics':
            report_data['Basic Metrics'] = get_basic_metrics(start_date, end_date, start_date - (end_date - start_date))
        elif metric == 'engagement':
            report_data['Engagement'] = get_engagement_metrics(start_date, end_date)
        elif metric == 'content':
            report_data['Content Performance'] = get_content_performance(start_date, end_date)
        elif metric == 'traffic':
            report_data['Traffic Analysis'] = get_traffic_analysis(start_date, end_date)
        elif metric == 'behavior':
            report_data['User Behavior'] = get_user_behavior(start_date, end_date)
        elif metric == 'geographic':
            report_data['Geographic Data'] = get_geographic_data(start_date, end_date)
        elif metric == 'technical':
            report_data['Technical Metrics'] = get_technical_metrics(start_date, end_date)

    if format == 'csv':
        # Convert to DataFrame and export as CSV
        df = pd.DataFrame.from_dict(report_data, orient='index')
        output = BytesIO()
        df.to_csv(output)
        output.seek(0)
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'analytics_report_{timeframe}.csv'
        )
        
    elif format == 'excel':
        # Export as Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            for sheet_name, data in report_data.items():
                df = pd.DataFrame.from_dict(data, orient='index')
                df.to_excel(writer, sheet_name=sheet_name)
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'analytics_report_{timeframe}.xlsx'
        )
        
    elif format == 'pdf':
        # Generate PDF report
        output = BytesIO()
        doc = SimpleDocTemplate(output, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Add title
        elements.append(Paragraph(f"Analytics Report - {timeframe}", styles['Title']))
        
        # Add each section
        for section_name, data in report_data.items():
            elements.append(Paragraph(section_name, styles['Heading1']))
            table_data = [[k, str(v)] for k, v in data.items()]
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table)
        
        doc.build(elements)
        output.seek(0)
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'analytics_report_{timeframe}.pdf'
        )
    
    return jsonify({'error': 'Invalid export format'})

@analytics.route('/analytics/autosave', methods=['POST'])
@login_required
@admin_required
def autosave_report():
    """Autosave report draft"""
    data = request.get_json()
    draft = ReportDraft.get_or_create(current_user.id)
    
    draft.metrics = data.get('metrics', [])
    draft.timeframe = data.get('timeframe', '30d')
    draft.name = data.get('name', 'Untitled Report')
    
    db.session.commit()
    
    UserActivityLog.log_activity(
        current_user.id,
        'report_autosaved',
        {'draft_id': draft.id, 'metrics': draft.metrics}
    )
    
    return jsonify({
        'status': 'success',
        'message': 'Report draft saved',
        'last_modified': draft.last_modified.isoformat()
    })

@analytics.route('/analytics/drafts', methods=['GET'])
@login_required
@admin_required
def get_report_drafts():
    """Get user's saved report drafts"""
    drafts = ReportDraft.query.filter_by(user_id=current_user.id).order_by(ReportDraft.last_modified.desc()).all()
    return jsonify([{
        'id': draft.id,
        'name': draft.name,
        'metrics': draft.metrics,
        'timeframe': draft.timeframe,
        'last_modified': draft.last_modified.isoformat()
    } for draft in drafts])

@analytics.route('/analytics/activity-log', methods=['GET'])
@login_required
@admin_required
def get_activity_log():
    """Get user's activity log"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    logs = UserActivityLog.query.filter_by(user_id=current_user.id)\
        .order_by(UserActivityLog.timestamp.desc())\
        .paginate(page=page, per_page=per_page)
    
    return jsonify({
        'logs': [{
            'action': log.action,
            'details': log.details,
            'timestamp': log.timestamp.isoformat()
        } for log in logs.items],
        'total': logs.total,
        'pages': logs.pages,
        'current_page': logs.page
    })
