from flask import render_template, redirect, url_for, request, current_app, flash
from flask_login import login_required, current_user
from app.main import bp
from app.models import Post, Category, Comment, db, PageView, Settings, Tag, User

@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = Settings.get('posts_per_page', 10)
    posts = Post.query.filter_by(published=True).order_by(Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    categories = Category.query.all()
    return render_template('main/index.html',
                         posts=posts,
                         categories=categories,
                         title='Home')

@bp.route('/post/<string:slug>')
def post(slug):
    post = Post.query.filter_by(slug=slug, published=True).first_or_404()
    
    # Record page view
    PageView.record(
        path=request.path,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string if request.user_agent else None,
        user=current_user if current_user.is_authenticated else None
    )
    
    return render_template('main/post.html',
                         title=post.title,
                         post=post,
                         related_posts=post.get_related_posts())

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

@bp.route('/categories')
def categories():
    categories = Category.query.order_by(Category.name.asc()).all()
    return render_template('main/categories.html',
                         title='Categories',
                         categories=categories)

@bp.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    if not Settings.get('enable_comments', True):
        flash('Comments are currently disabled.', 'error')
        post = Post.query.get_or_404(post_id)
        return redirect(url_for('main.post', slug=post.slug))
        
    post = Post.query.get_or_404(post_id)
    content = request.form.get('content')
    
    if not content:
        flash('Comment cannot be empty.', 'error')
        return redirect(url_for('main.post', slug=post.slug))
        
    comment = Comment(content=content, author=current_user, post=post)
    db.session.add(comment)
    db.session.commit()
    
    flash('Your comment has been added.', 'success')
    return redirect(url_for('main.post', slug=post.slug))

@bp.route('/search')
def search():
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    per_page = Settings.get('posts_per_page', 10)
    
    if not query:
        return redirect(url_for('main.index'))
    
    # Search in title, content, and summary
    search_query = f"%{query}%"
    posts = Post.query.filter(
        Post.published == True,
        (Post.title.ilike(search_query) |
         Post.content.ilike(search_query) |
         Post.summary.ilike(search_query))
    ).order_by(Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('main/search.html',
                         title=f'Search: {query}',
                         query=query,
                         posts=posts)
