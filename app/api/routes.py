from flask import jsonify, request, url_for, current_app
from app import db
from app.api import bp
from app.models import Post, Category, User, Comment, Tag, Media, PageView, Like
from app.utils import admin_required, rate_limit
from flask_login import current_user, login_required
from datetime import datetime, timedelta
from sqlalchemy import func, distinct

# API Documentation
API_DOCS = {
    'posts': {
        'GET /api/posts': 'Get all posts with pagination',
        'GET /api/posts/<id>': 'Get a specific post',
        'POST /api/posts': 'Create a new post (admin only)',
        'PUT /api/posts/<id>': 'Update a post (admin only)',
        'DELETE /api/posts/<id>': 'Delete a post (admin only)'
    },
    'comments': {
        'GET /api/posts/<id>/comments': 'Get comments for a post',
        'POST /api/posts/<id>/comments': 'Create a comment on a post',
        'PUT /api/comments/<id>': 'Update a comment (owner or admin only)',
        'DELETE /api/comments/<id>': 'Delete a comment (owner or admin only)'
    },
    'categories': {
        'GET /api/categories': 'Get all categories',
        'POST /api/categories': 'Create a category (admin only)',
        'PUT /api/categories/<id>': 'Update a category (admin only)',
        'DELETE /api/categories/<id>': 'Delete a category (admin only)'
    },
    'media': {
        'GET /api/media': 'Get all media files',
        'GET /api/media/<id>': 'Get a specific media file',
        'POST /api/media': 'Upload media (admin only)',
        'DELETE /api/media/<id>': 'Delete media (admin only)'
    },
    'analytics': {
        'GET /api/analytics/views': 'Get page view statistics',
        'GET /api/analytics/popular': 'Get popular content',
        'GET /api/analytics/users': 'Get user engagement metrics (admin only)'
    }
}

@bp.route('/')
def api_docs():
    """Get API documentation"""
    return jsonify(API_DOCS)

@bp.route('/posts')
@rate_limit('50 per minute')
def get_posts():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = Post.query.filter_by(published=True)\
        .order_by(Post.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'items': [item.to_dict() for item in data.items],
        'meta': {
            'page': page,
            'per_page': per_page,
            'total_pages': data.pages,
            'total_items': data.total
        }
    })

@bp.route('/posts/<int:id>')
@rate_limit('100 per minute')
def get_post(id):
    post = Post.query.get_or_404(id)
    if not post.published and (not current_user.is_authenticated or not current_user.is_admin):
        abort(404)
    return jsonify(post.to_dict())

@bp.route('/posts', methods=['POST'])
@login_required
@admin_required
def create_post():
    data = request.get_json() or {}
    if 'title' not in data or 'content' not in data:
        return bad_request('must include title and content fields')
    
    post = Post()
    post.from_dict(data)
    post.author = current_user
    db.session.add(post)
    db.session.commit()
    
    response = jsonify(post.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_post', id=post.id)
    return response

@bp.route('/posts/<int:id>', methods=['PUT'])
@login_required
@admin_required
def update_post(id):
    post = Post.query.get_or_404(id)
    data = request.get_json() or {}
    post.from_dict(data)
    db.session.commit()
    return jsonify(post.to_dict())

@bp.route('/posts/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def delete_post(id):
    post = Post.query.get_or_404(id)
    db.session.delete(post)
    db.session.commit()
    return '', 204

@bp.route('/categories')
def get_categories():
    categories = Category.query.all()
    return jsonify([cat.to_dict() for cat in categories])

@bp.route('/tags')
def get_tags():
    tags = Tag.query.all()
    return jsonify([tag.to_dict() for tag in tags])

@bp.route('/posts/<int:id>/comments')
@rate_limit('50 per minute')
def get_post_comments(id):
    """Get comments for a specific post"""
    post = Post.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    
    query = Comment.query.filter_by(post=post, status='approved')
    comments = query.order_by(Comment.created_at.desc())\
        .paginate(page=page, per_page=per_page)
    
    return jsonify({
        'items': [comment.to_dict() for comment in comments.items],
        'total': comments.total,
        'pages': comments.pages,
        'current_page': comments.page
    })

@bp.route('/posts/<int:id>/comments', methods=['POST'])
@login_required
def create_comment(id):
    """Create a new comment on a post"""
    post = Post.query.get_or_404(id)
    data = request.get_json()
    
    if not data.get('content'):
        return jsonify({'error': 'Content is required'}), 400
    
    comment = Comment(
        content=data['content'],
        author=current_user,
        post=post,
        status='approved' if current_user.is_admin else 'pending'
    )
    
    db.session.add(comment)
    db.session.commit()
    
    return jsonify(comment.to_dict()), 201

@bp.route('/comments/<int:id>', methods=['PUT'])
@login_required
def update_comment(id):
    """Update a comment (owner or admin only)"""
    comment = Comment.query.get_or_404(id)
    
    # Check permissions
    if not current_user.is_admin and current_user != comment.author:
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    if 'content' in data:
        comment.content = data['content']
        comment.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify(comment.to_dict())
    
    return jsonify({'error': 'No content provided'}), 400

@bp.route('/comments/<int:id>', methods=['DELETE'])
@login_required
def delete_comment(id):
    """Delete a comment (owner or admin only)"""
    comment = Comment.query.get_or_404(id)
    
    if not current_user.is_admin and current_user != comment.author:
        return jsonify({'error': 'Permission denied'}), 403
    
    db.session.delete(comment)
    db.session.commit()
    return jsonify({'message': 'Comment deleted'})

@bp.route('/search')
@rate_limit('30 per minute')
def search():
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    
    if not query:
        return jsonify({
            'items': [],
            'meta': {
                'page': page,
                'per_page': per_page,
                'total_pages': 0,
                'total_items': 0
            }
        })
    
    # Implement search logic here
    # This could use Elasticsearch or database full-text search
    pass

@bp.route('/posts/<int:id>/like', methods=['POST'])
@login_required
def like_post(id):
    post = Post.query.get_or_404(id)
    if current_user.has_liked_post(post):
        return bad_request('You have already liked this post')
    
    like = Like(user=current_user, post=post)
    db.session.add(like)
    db.session.commit()
    
    return jsonify({'likes_count': post.likes.count()})

def get_date_range(timeframe):
    """Helper function to get date range based on timeframe"""
    end_date = datetime.utcnow()
    if timeframe == '24h':
        start_date = end_date - timedelta(days=1)
    elif timeframe == '7d':
        start_date = end_date - timedelta(days=7)
    elif timeframe == '30d':
        start_date = end_date - timedelta(days=30)
    elif timeframe == '90d':
        start_date = end_date - timedelta(days=90)
    else:
        start_date = end_date - timedelta(days=7)
    return start_date, end_date

@bp.route('/analytics/views')
@rate_limit('30 per minute')
def get_view_stats():
    """Get page view statistics"""
    timeframe = request.args.get('timeframe', '7d')
    start_date = get_date_range(timeframe)[0]
    
    views = db.session.query(
        PageView.post_id,
        func.count(PageView.id).label('view_count')
    ).filter(PageView.timestamp >= start_date)\
    .group_by(PageView.post_id)\
    .order_by(func.count(PageView.id).desc())\
    .limit(10)\
    .all()
    
    return jsonify({
        'timeframe': timeframe,
        'views': [{
            'post_id': view[0],
            'count': view[1]
        } for view in views]
    })

@bp.route('/analytics/popular')
@rate_limit('30 per minute')
def get_popular_content():
    """Get popular content based on views and engagement"""
    timeframe = request.args.get('timeframe', '7d')
    start_date = get_date_range(timeframe)[0]
    
    popular = db.session.query(
        Post,
        func.count(PageView.id).label('views'),
        func.count(distinct(Comment.id)).label('comments'),
        func.count(distinct(Like.id)).label('likes')
    ).join(PageView, PageView.post_id == Post.id)\
    .outerjoin(Comment, Comment.post_id == Post.id)\
    .outerjoin(Like, Like.post_id == Post.id)\
    .filter(PageView.timestamp >= start_date)\
    .group_by(Post.id)\
    .order_by(
        (func.count(PageView.id) * 1.0 +
         func.count(distinct(Comment.id)) * 2.0 +
         func.count(distinct(Like.id)) * 1.5
        ).desc()
    ).limit(10).all()
    
    return jsonify({
        'timeframe': timeframe,
        'popular': [{
            'post': post.to_dict(),
            'stats': {
                'views': views,
                'comments': comments,
                'likes': likes
            }
        } for post, views, comments, likes in popular]
    })

@bp.route('/analytics/users')
@login_required
@admin_required
def get_user_metrics():
    """Get user engagement metrics (admin only)"""
    timeframe = request.args.get('timeframe', '7d')
    start_date = get_date_range(timeframe)[0]
    
    metrics = db.session.query(
        User,
        func.count(distinct(Comment.id)).label('comment_count'),
        func.count(distinct(Like.id)).label('like_count'),
        func.count(distinct(PageView.id)).label('view_count')
    ).outerjoin(Comment, Comment.author_id == User.id)\
    .outerjoin(Like, Like.user_id == User.id)\
    .outerjoin(PageView, PageView.user_id == User.id)\
    .filter(User.last_activity >= start_date)\
    .group_by(User.id)\
    .order_by(
        (func.count(distinct(Comment.id)) +
         func.count(distinct(Like.id)) +
         func.count(distinct(PageView.id))
        ).desc()
    ).limit(20).all()
    
    return jsonify({
        'timeframe': timeframe,
        'users': [{
            'user': user.to_dict(),
            'engagement': {
                'comments': comment_count,
                'likes': like_count,
                'views': view_count
            }
        } for user, comment_count, like_count, view_count in metrics]
    })
