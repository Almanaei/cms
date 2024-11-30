import os
from flask import render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.admin import bp
from app.models import Post, Category, User, MediaItem, Tag, Role, Comment, UserActivity
from functools import wraps
from datetime import datetime

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You need to be an admin to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.can(permission):
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('admin.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

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

@bp.route('/category/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_category(id):
    category = Category.query.get_or_404(id)
    if request.method == 'POST':
        category.name = request.form['name']
        db.session.commit()
        flash('Category updated successfully!', 'success')
        return redirect(url_for('admin.categories'))
    return render_template('admin/edit_category.html', category=category)

@bp.route('/category/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_category(id):
    category = Category.query.get_or_404(id)
    db.session.delete(category)
    db.session.commit()
    flash('Category deleted successfully!', 'success')
    return redirect(url_for('admin.categories'))

@bp.route('/media')
@login_required
@admin_required
def media():
    page = request.args.get('page', 1, type=int)
    media_items = MediaItem.query.order_by(MediaItem.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('admin/media.html', media_items=media_items)

@bp.route('/media/upload', methods=['POST'])
@login_required
@admin_required
def upload_media():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        mime_type = file.content_type
        filepath = os.path.join('uploads', filename)
        absolute_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        # Create thumbnails directory if it doesn't exist
        thumbnails_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'thumbnails')
        if not os.path.exists(thumbnails_dir):
            os.makedirs(thumbnails_dir)
        
        # Save the original file
        file.save(absolute_path)
        
        # Create thumbnail for images
        thumbnail_path = None
        if mime_type.startswith('image/'):
            from PIL import Image
            try:
                with Image.open(absolute_path) as img:
                    # Create thumbnail
                    img.thumbnail((200, 200))
                    thumbnail_filename = f'thumb_{filename}'
                    thumbnail_path = os.path.join('uploads/thumbnails', thumbnail_filename)
                    absolute_thumbnail_path = os.path.join(thumbnails_dir, thumbnail_filename)
                    img.save(absolute_thumbnail_path)
            except Exception as e:
                current_app.logger.error(f'Error creating thumbnail: {str(e)}')
        
        # Create media item
        media_item = MediaItem(
            filename=filename,
            filepath=filepath,
            thumbnail_path=thumbnail_path,
            type='image' if mime_type.startswith('image/') else 'file',
            mime_type=mime_type,
            size=os.path.getsize(absolute_path)
        )
        
        db.session.add(media_item)
        db.session.commit()
        
        return jsonify({
            'id': media_item.id,
            'url': url_for('static', filename=filepath),
            'thumbnail_url': url_for('static', filename=thumbnail_path) if thumbnail_path else None,
            'filename': filename,
            'type': media_item.type
        })
    
    return jsonify({'error': 'File upload failed'}), 400

@bp.route('/media/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_media(id):
    media_item = MediaItem.query.get_or_404(id)
    
    # Delete physical files
    try:
        os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], media_item.filename))
        if media_item.thumbnail_path:
            thumbnail_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 
                                        'thumbnails', 
                                        os.path.basename(media_item.thumbnail_path))
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
    except Exception as e:
        current_app.logger.error(f'Error deleting files: {str(e)}')
    
    # Delete database record
    db.session.delete(media_item)
    db.session.commit()
    
    return jsonify({'success': True})

@bp.route('/post/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_post(id):
    post = Post.query.get_or_404(id)
    if request.method == 'POST':
        post.title = request.form['title']
        post.content = request.form['content']
        post.summary = request.form['summary']
        post.meta_title = request.form['meta_title']
        post.meta_description = request.form['meta_description']
        post.category_id = request.form.get('category_id')
        post.published = request.form.get('published') == 'on'
        
        # Handle scheduling
        if request.form.get('schedule') == 'on':
            scheduled_date = request.form.get('scheduled_date')
            scheduled_time = request.form.get('scheduled_time')
            if scheduled_date and scheduled_time:
                post.published_at = datetime.strptime(f"{scheduled_date} {scheduled_time}", "%Y-%m-%d %H:%M")
        else:
            post.published_at = datetime.utcnow() if post.published else None
            
        # Handle featured image
        if 'featured_image' in request.files:
            file = request.files['featured_image']
            if file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                post.featured_image = filename
        
        # Handle tags
        tags = request.form.get('tags', '').split(',')
        post.tags = []
        for tag_name in tags:
            tag_name = tag_name.strip()
            if tag_name:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                post.tags.append(tag)
        
        db.session.commit()
        flash('Post updated successfully!', 'success')
        return redirect(url_for('admin.posts'))
        
    categories = Category.query.all()
    return render_template('admin/edit_post.html', post=post, categories=categories)

@bp.route('/post/<int:id>/preview')
@login_required
@admin_required
def preview_post(id):
    post = Post.query.get_or_404(id)
    return render_template('admin/preview_post.html', post=post)

@bp.route('/post/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_post(id):
    post = Post.query.get_or_404(id)
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted successfully!', 'success')
    return redirect(url_for('admin.posts'))

@bp.route('/users')
@login_required
@permission_required(Role.MANAGE_USERS)
def users():
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('admin/users.html', users=users)

@bp.route('/user/new', methods=['GET', 'POST'])
@login_required
@permission_required(Role.MANAGE_USERS)
def create_user():
    if request.method == 'POST':
        user = User(
            username=request.form['username'],
            email=request.form['email'],
            role_id=request.form.get('role_id'),
            is_active=request.form.get('is_active') == 'on',
            must_change_password=True
        )
        user.set_password(request.form['password'])
        
        db.session.add(user)
        db.session.commit()
        
        current_user.log_activity(
            'created_user',
            f'Created user: {user.username}',
            request.remote_addr
        )
        
        flash('User created successfully!', 'success')
        return redirect(url_for('admin.users'))
    
    roles = Role.query.all()
    return render_template('admin/create_user.html', roles=roles)

@bp.route('/user/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required(Role.MANAGE_USERS)
def edit_user(id):
    user = User.query.get_or_404(id)
    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']
        user.role_id = request.form.get('role_id')
        user.is_active = request.form.get('is_active') == 'on'
        
        if request.form.get('password'):
            user.set_password(request.form['password'])
            user.must_change_password = True
            user.password_changed_at = None
        
        db.session.commit()
        
        current_user.log_activity(
            'updated_user',
            f'Updated user: {user.username}',
            request.remote_addr
        )
        
        flash('User updated successfully!', 'success')
        return redirect(url_for('admin.users'))
    
    roles = Role.query.all()
    return render_template('admin/edit_user.html', user=user, roles=roles)

@bp.route('/user/<int:id>/delete', methods=['POST'])
@login_required
@permission_required(Role.MANAGE_USERS)
def delete_user(id):
    user = User.query.get_or_404(id)
    if user == current_user:
        flash('You cannot delete your own account!', 'danger')
        return redirect(url_for('admin.users'))
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    current_user.log_activity(
        'deleted_user',
        f'Deleted user: {username}',
        request.remote_addr
    )
    
    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin.users'))

@bp.route('/user/<int:id>/activity')
@login_required
@permission_required(Role.MANAGE_USERS)
def user_activity(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    activities = user.activities.order_by(UserActivity.created_at.desc()).paginate(
        page=page, per_page=50, error_out=False)
    return render_template('admin/user_activity.html', user=user, activities=activities)

@bp.route('/roles')
@login_required
@permission_required(Role.MANAGE_ROLES)
def roles():
    roles = Role.query.all()
    return render_template('admin/roles.html', roles=roles)

@bp.route('/comments/bulk-action', methods=['POST'])
@login_required
@admin_required
def bulk_action():
    data = request.get_json()
    
    if not data or 'action' not in data or 'comments' not in data:
        return jsonify({'success': False, 'error': 'Invalid request data'}), 400
    
    action = data['action']
    comment_ids = data['comments']
    
    if action not in ['approve', 'pending', 'spam', 'delete']:
        return jsonify({'success': False, 'error': 'Invalid action'}), 400
    
    comments = Comment.query.filter(Comment.id.in_(comment_ids)).all()
    
    for comment in comments:
        if action == 'delete':
            activity = UserActivity(
                user_id=current_user.id,
                action='delete_comment',
                details=f'Deleted comment on post: {comment.post.title}'
            )
            db.session.delete(comment)
            db.session.add(activity)
        else:
            comment.status = action
            activity = UserActivity(
                user_id=current_user.id,
                action='update_comment_status',
                details=f'Updated comment status to {action} on post: {comment.post.title}'
            )
            db.session.add(activity)
    
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/role/new', methods=['GET', 'POST'])
@login_required
@permission_required(Role.MANAGE_ROLES)
def create_role():
    if request.method == 'POST':
        role = Role(
            name=request.form['name'],
            description=request.form['description']
        )
        
        # Handle permissions
        for perm in [Role.VIEW_DASHBOARD, Role.MANAGE_POSTS, Role.MANAGE_USERS,
                    Role.MANAGE_ROLES, Role.MANAGE_SETTINGS, Role.MANAGE_MEDIA,
                    Role.MODERATE_COMMENTS]:
            if request.form.get(f'perm_{perm}') == 'on':
                role.add_permission(perm)
        
        db.session.add(role)
        db.session.commit()
        
        current_user.log_activity(
            'created_role',
            f'Created role: {role.name}',
            request.remote_addr
        )
        
        flash('Role created successfully!', 'success')
        return redirect(url_for('admin.roles'))
    
    return render_template('admin/create_role.html')
