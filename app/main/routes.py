from flask import render_template, redirect, url_for, request, current_app
from app.main import bp
from app.models import Post, Category

@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(published=True).order_by(
        Post.created_at.desc()
    ).paginate(page=page, per_page=10, error_out=False)
    return render_template('main/index.html', posts=posts)

@bp.route('/post/<string:slug>')
def post(slug):
    post = Post.query.filter_by(slug=slug, published=True).first_or_404()
    return render_template('main/post.html', post=post)

@bp.route('/category/<string:slug>')
def category(slug):
    category = Category.query.filter_by(slug=slug).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(
        category_id=category.id, published=True
    ).order_by(Post.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template('main/category.html', category=category, posts=posts)
