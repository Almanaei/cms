from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from ..models import Comment, Post, UserActivity
from ..utils.decorators import admin_required
from .. import db
from . import bp as admin_bp

comments = Blueprint('comments', __name__, url_prefix='/comments')
admin_bp.register_blueprint(comments)

@comments.route('/')
@login_required
@admin_required
def comment_list():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'all')
    
    query = Comment.query
    if status != 'all':
        query = query.filter(Comment.status == status)
    
    comments = query.order_by(Comment.created_at.desc())\
        .paginate(page=page, per_page=20)
    
    return render_template('admin/comments.html', comments=comments)

@comments.route('/<int:id>/status', methods=['POST'])
@login_required
@admin_required
def update_status(id):
    comment = Comment.query.get_or_404(id)
    data = request.get_json()
    
    if data.get('status') in ['approved', 'pending', 'spam']:
        old_status = comment.status
        comment.status = data['status']
        
        # Log the activity
        activity = UserActivity(
            user=current_user,
            action=f'updated_comment_status',
            details=f'Changed comment status from {old_status} to {comment.status}'
        )
        db.session.add(activity)
        db.session.commit()
        
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Invalid status'}), 400

@comments.route('/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def delete_comment(id):
    comment = Comment.query.get_or_404(id)
    
    # Log the activity
    activity = UserActivity(
        user=current_user,
        action='deleted_comment',
        details=f'Deleted comment on post: {comment.post.title}'
    )
    
    db.session.delete(comment)
    db.session.add(activity)
    db.session.commit()
    
    return jsonify({'success': True})

@comments.route('/bulk-action', methods=['POST'])
@login_required
@admin_required
def bulk_action():
    data = request.get_json()
    action = data.get('action')
    comment_ids = data.get('comments', [])
    
    if not action or not comment_ids:
        return jsonify({'success': False, 'error': 'Invalid request'}), 400
    
    comments = Comment.query.filter(Comment.id.in_(comment_ids)).all()
    
    if action in ['approve', 'pending', 'spam']:
        status = 'approved' if action == 'approve' else action
        for comment in comments:
            comment.status = status
    elif action == 'delete':
        for comment in comments:
            db.session.delete(comment)
    
    # Log the activity
    activity = UserActivity(
        user=current_user,
        action=f'bulk_{action}_comments',
        details=f'Bulk {action} action on {len(comments)} comments'
    )
    db.session.add(activity)
    db.session.commit()
    
    return jsonify({'success': True})
