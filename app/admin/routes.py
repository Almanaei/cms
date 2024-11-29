import os
from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.admin import bp
from app.models import Post, Category, User
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You need to be an admin to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@login_required
@admin_required
def index():
    posts_count = Post.query.count()
    categories_count = Category.query.count()
    users_count = User.query.count()
    return render_template('admin/index.html',
                         posts_count=posts_count,
                         categories_count=categories_count,
                         users_count=users_count)

@bp.route('/posts')
@login_required
@admin_required
def posts():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('admin/posts.html', posts=posts)

@bp.route('/post/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_post():
    if request.method == 'POST':
        post = Post(
            title=request.form['title'],
            content=request.form['content'],
            category_id=request.form.get('category_id'),
            user_id=current_user.id,
            published=request.form.get('published') == 'on'
        )
        
        if 'featured_image' in request.files:
            file = request.files['featured_image']
            if file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                post.featured_image = filename
        
        db.session.add(post)
        db.session.commit()
        flash('Post created successfully!', 'success')
        return redirect(url_for('admin.posts'))
    
    categories = Category.query.all()
    return render_template('admin/create_post.html', categories=categories)

@bp.route('/categories')
@login_required
@admin_required
def categories():
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)

@bp.route('/category/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_category():
    if request.method == 'POST':
        category = Category(name=request.form['name'])
        db.session.add(category)
        db.session.commit()
        flash('Category created successfully!', 'success')
        return redirect(url_for('admin.categories'))
    return render_template('admin/create_category.html')
