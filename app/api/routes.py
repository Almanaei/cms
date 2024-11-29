from flask import jsonify, request, url_for, current_app
from app import db
from app.api import bp
from app.models import Post, Category, User, Comment, Tag
from app.utils import admin_required, rate_limit
from flask_login import current_user, login_required

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
def get_post_comments(id):
    post = Post.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    
    comments = Comment.query.filter_by(post_id=id, approved=True)\
        .order_by(Comment.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'items': [comment.to_dict() for comment in comments.items],
        'meta': {
            'page': page,
            'per_page': per_page,
            'total_pages': comments.pages,
            'total_items': comments.total
        }
    })

@bp.route('/posts/<int:id>/comments', methods=['POST'])
@login_required
def create_comment(id):
    post = Post.query.get_or_404(id)
    if not post.allow_comments:
        return bad_request('Comments are not allowed on this post')
    
    data = request.get_json() or {}
    if 'content' not in data:
        return bad_request('must include content field')
    
    comment = Comment()
    comment.from_dict(data)
    comment.author = current_user
    comment.post = post
    comment.approved = not current_app.config['COMMENT_MODERATION']
    
    db.session.add(comment)
    db.session.commit()
    
    response = jsonify(comment.to_dict())
    response.status_code = 201
    return response

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
