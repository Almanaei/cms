import os
from flask import render_template, redirect, url_for, flash, request, current_app, jsonify, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.admin import bp
from app.models import Post, Category, User, MediaItem, Tag, Role, Comment, UserActivity, Settings, BackupSchedule, Backup, PageView
from functools import wraps
from datetime import datetime
import json
import shutil
from app.forms import PostForm  # Import PostForm

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
    form = PostForm()
    
    # Set category choices
    categories = Category.query.order_by(Category.name).all()
    form.category_id.choices = [(c.id, c.name) for c in categories]
    
    if form.validate_on_submit():
        post = Post()
        # Don't populate tags field or featured_image directly
        form_data = {field.name: field.data for field in form 
                    if field.name not in ['tags', 'featured_image']}
        for field, value in form_data.items():
            setattr(post, field, value)
            
        post.user_id = current_user.id
        
        # Handle tags
        if form.tags.data:
            tag_names = [t.strip() for t in form.tags.data.split(',') if t.strip()]
            for tag_name in tag_names:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                post.tags.append(tag)
        
        # Handle scheduling
        if form.schedule.data:
            if form.scheduled_date.data and form.scheduled_time.data:
                post.published_at = datetime.strptime(
                    f"{form.scheduled_date.data} {form.scheduled_time.data}", 
                    "%Y-%m-%d %H:%M"
                )
        else:
            post.published_at = datetime.utcnow() if post.published else None
            
        # Handle featured image
        if form.featured_image.data:
            file = form.featured_image.data
            if file and file.filename:
                # Create upload directory if it doesn't exist
                upload_folder = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)
                
                filename = secure_filename(file.filename)
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                post.featured_image = filename
        
        db.session.add(post)
        db.session.commit()
        
        flash('Post created successfully!', 'success')
        return redirect(url_for('admin.posts'))
    
    return render_template('admin/edit_post.html', form=form, post=None)

@bp.route('/categories')
@login_required
@admin_required
def categories():
    page = request.args.get('page', 1, type=int)
    per_page = 20

    # Get all categories with their post counts
    categories_with_counts = db.session.query(
        Category,
        db.func.count(Post.id).label('post_count')
    ).outerjoin(Post).group_by(Category.id).order_by(Category.name.asc())
    
    # Manual pagination
    total = categories_with_counts.count()
    offset = (page - 1) * per_page
    categories_list = categories_with_counts.offset(offset).limit(per_page).all()
    
    # Create pagination object
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'pages': (total + per_page - 1) // per_page
    }
    
    return render_template('admin/categories.html', 
                         categories=categories_list,
                         pagination=pagination)

@bp.route('/category/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_category():
    if request.method == 'POST':
        category = Category(
            name=request.form['name'],
            slug=request.form['slug'],
            description=request.form.get('description', '')
        )
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
        category.slug = request.form['slug']
        category.description = request.form.get('description', '')
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
    form = PostForm(obj=post)
    
    # Set category choices
    categories = Category.query.order_by(Category.name).all()
    form.category_id.choices = [(c.id, c.name) for c in categories]
    
    if form.validate_on_submit():
        # Update post fields from form
        post.title = form.title.data
        post.slug = form.slug.data
        post.content = form.content.data
        post.summary = form.summary.data
        post.meta_title = form.meta_title.data
        post.meta_description = form.meta_description.data
        post.category_id = form.category_id.data
        post.published = form.published.data
        
        # Handle scheduling
        if form.schedule.data:
            if form.scheduled_date.data and form.scheduled_time.data:
                post.published_at = datetime.strptime(
                    f"{form.scheduled_date.data} {form.scheduled_time.data}", 
                    "%Y-%m-%d %H:%M"
                )
        else:
            post.published_at = datetime.utcnow() if post.published else None
            
        # Handle featured image
        if form.featured_image.data:
            file = form.featured_image.data
            if file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                post.featured_image = filename
        
        # Handle tags
        if form.tags.data:
            tags = form.tags.data.split(',')
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
    
    # Pre-fill form fields for GET request
    if request.method == 'GET':
        form.title.data = post.title
        form.slug.data = post.slug
        form.content.data = post.content
        form.summary.data = post.summary
        form.meta_title.data = post.meta_title
        form.meta_description.data = post.meta_description
        form.category_id.data = post.category_id
        form.published.data = post.published
        form.tags.data = ', '.join(tag.name for tag in post.tags)
        
        if post.published_at and post.published_at > datetime.utcnow():
            form.schedule.data = True
            form.scheduled_date.data = post.published_at.strftime('%Y-%m-%d')
            form.scheduled_time.data = post.published_at.strftime('%H:%M')
    
    return render_template('admin/edit_post.html', form=form, post=post)

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

@bp.route('/post/<int:id>/remove-featured-image', methods=['POST'])
@login_required
@admin_required
def remove_featured_image(id):
    post = Post.query.get_or_404(id)
    
    # Remove the file if it exists
    if post.featured_image:
        try:
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], post.featured_image)
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            current_app.logger.error(f"Error removing featured image: {e}")
    
    # Update the database
    post.featured_image = None
    db.session.commit()
    
    return jsonify({'success': True})

@bp.route('/users')
@login_required
@permission_required(Role.MANAGE_USERS)
def users():
    # Default pagination settings
    default_page = 1
    per_page = 10
    
    # Get the page parameter and sanitize it
    page_param = request.args.get('page')
    
    # Ensure we have a valid page number
    try:
        # Only attempt conversion if we have a non-empty string
        if page_param and page_param.strip():
            page = max(1, int(page_param))
        else:
            page = default_page
    except (TypeError, ValueError):
        page = default_page
    
    # Get total number of users for pagination
    total_users = User.query.count()
    max_pages = (total_users + per_page - 1) // per_page
    
    # Ensure page number doesn't exceed maximum pages
    page = min(page, max(1, max_pages))
    
    # Query users with proper ordering
    users_query = User.query.order_by(User.created_at.desc())
    
    # Get paginated results with error handling
    try:
        users = users_query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        if not users.items and page > 1:
            # If no items found and we're not on first page, redirect to first page
            return redirect(url_for('admin.users', page=1))
    except Exception as e:
        current_app.logger.error(f"Pagination error: {str(e)}")
        users = users_query.paginate(
            page=1,
            per_page=per_page,
            error_out=False
        )
    
    return render_template(
        'admin/users.html',
        users=users,
        current_time=datetime.utcnow()
    )

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

@bp.route('/user-activity')
@login_required
@admin_required
def user_activity_list():
    page = request.args.get('page', 1, type=int)
    activities = UserActivity.query.order_by(UserActivity.timestamp.desc()).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('admin/user_activity.html', activities=activities)

@bp.route('/user-activity/<int:id>')
@login_required
@admin_required
def user_activity_detail(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    activities = UserActivity.query.filter_by(user_id=id).order_by(
        UserActivity.timestamp.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/user_activity_detail.html', user=user, activities=activities)

@bp.route('/roles')
@login_required
@permission_required(Role.MANAGE_ROLES)
def roles():
    roles = Role.query.all()
    available_permissions = [
        {'id': Role.VIEW_DASHBOARD, 'name': 'View Dashboard'},
        {'id': Role.MANAGE_POSTS, 'name': 'Manage Posts'},
        {'id': Role.MANAGE_USERS, 'name': 'Manage Users'},
        {'id': Role.MANAGE_ROLES, 'name': 'Manage Roles'},
        {'id': Role.MANAGE_SETTINGS, 'name': 'Manage Settings'},
        {'id': Role.MANAGE_MEDIA, 'name': 'Manage Media'},
        {'id': Role.MODERATE_COMMENTS, 'name': 'Moderate Comments'}
    ]
    return render_template('admin/roles.html', roles=roles, available_permissions=available_permissions)

@bp.route('/comments')
@login_required
@admin_required
def comments():
    page = request.args.get('page', 1, type=int)
    comments = Comment.query.order_by(Comment.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('admin/comments.html', comments=comments)

@bp.route('/analytics')
@login_required
@admin_required
def analytics():
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    # Get time ranges
    now = datetime.utcnow()
    last_30_days = now - timedelta(days=30)
    last_60_days = now - timedelta(days=60)
    
    # Get total views and growth
    current_views = PageView.query.filter(PageView.timestamp >= last_30_days).count()
    previous_views = PageView.query.filter(
        PageView.timestamp >= last_60_days,
        PageView.timestamp < last_30_days
    ).count()
    view_growth = ((current_views - previous_views) / (previous_views or 1)) * 100

    # Get active users and growth
    current_active_users = User.query.filter(
        User.last_seen >= last_30_days,
        User.is_active == True
    ).count()
    previous_active_users = User.query.filter(
        User.last_seen >= last_60_days,
        User.last_seen < last_30_days,
        User.is_active == True
    ).count()
    user_growth = ((current_active_users - previous_active_users) / (previous_active_users or 1)) * 100

    # Get total content and growth
    current_content = Post.query.filter(
        Post.created_at >= last_30_days,
        Post.published == True
    ).count()
    previous_content = Post.query.filter(
        Post.created_at >= last_60_days,
        Post.created_at < last_30_days,
        Post.published == True
    ).count()
    content_growth = ((current_content - previous_content) / (previous_content or 1)) * 100

    # Get engagement metrics
    current_engagement = Comment.query.filter(
        Comment.created_at >= last_30_days
    ).count()
    previous_engagement = Comment.query.filter(
        Comment.created_at >= last_60_days,
        Comment.created_at < last_30_days
    ).count()
    engagement_growth = ((current_engagement - previous_engagement) / (previous_engagement or 1)) * 100
    
    # Calculate engagement rate
    total_posts = Post.query.filter(Post.published == True).count()
    engagement_rate = (current_engagement / (total_posts or 1)) * 100

    # Get top posts by views
    top_posts = db.session.query(
        Post,
        func.count(PageView.id).label('views')
    ).join(
        PageView, PageView.path.like(func.concat('/post/%', Post.slug))
    ).filter(
        Post.published == True,
        PageView.timestamp >= last_30_days
    ).group_by(
        Post.id
    ).order_by(
        func.count(PageView.id).desc()
    ).limit(5).all()

    # Get traffic data for chart
    traffic_data = []
    for i in range(30, -1, -1):
        date = now - timedelta(days=i)
        views = PageView.query.filter(
            PageView.timestamp >= date.replace(hour=0, minute=0, second=0),
            PageView.timestamp < (date + timedelta(days=1)).replace(hour=0, minute=0, second=0)
        ).count()
        traffic_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'views': views
        })

    # Get recent user activity
    recent_activities = UserActivity.query.order_by(
        UserActivity.timestamp.desc()
    ).limit(5).all()

    return render_template('admin/analytics.html',
                         total_views=current_views,
                         view_growth=round(view_growth, 1),
                         active_users=current_active_users,
                         user_growth=round(user_growth, 1),
                         total_content=total_posts,
                         content_growth=round(content_growth, 1),
                         engagement_rate=round(engagement_rate, 1),
                         engagement_growth=round(engagement_growth, 1),
                         recent_activities=recent_activities,
                         top_posts=top_posts,
                         traffic_data=traffic_data)

@bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    if request.method == 'POST':
        for key, value in request.form.items():
            if key.startswith('setting_'):
                setting_key = key.replace('setting_', '')
                setting = Settings.query.filter_by(key=setting_key).first()
                if setting:
                    # Convert value based on setting type
                    if setting.type == 'boolean':
                        value = value.lower() in ('true', '1', 'yes', 'on')
                    elif setting.type == 'integer':
                        try:
                            value = int(float(value))
                        except ValueError:
                            value = 0
                    elif setting.type == 'float':
                        try:
                            value = float(value)
                        except ValueError:
                            value = 0.0
                            
                    Settings.set(setting_key, value, setting.type)

        flash('Settings updated successfully.', 'success')
        return redirect(url_for('admin.settings'))

    # Get all settings
    all_settings = Settings.query.all()
    return render_template('admin/settings.html', settings=all_settings)

@bp.route('/settings/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_setting(id):
    """Delete a setting."""
    setting = Settings.query.get_or_404(id)
    
    # Don't allow deletion of critical settings
    critical_settings = ['site_name', 'items_per_page', 'enable_comments']
    if setting.key in critical_settings:
        flash('Cannot delete critical system setting.', 'error')
        return redirect(url_for('admin.settings'))
    
    db.session.delete(setting)
    db.session.commit()
    flash('Setting deleted successfully.', 'success')
    return redirect(url_for('admin.settings'))

@bp.route('/settings/export')
@login_required
@admin_required
def export_settings():
    """Export all settings as JSON."""
    settings = Settings.query.all()
    settings_data = [{
        'key': setting.key,
        'value': setting.value,
        'type': setting.type,
        'description': setting.description
    } for setting in settings]
    
    return jsonify({
        'settings': settings_data,
        'exported_at': datetime.utcnow().isoformat(),
        'version': '1.0'
    })

@bp.route('/settings/import', methods=['POST'])
@login_required
@admin_required
def import_settings():
    """Import settings from JSON."""
    if 'settings_file' not in request.files:
        flash('No file uploaded.', 'error')
        return redirect(url_for('admin.settings'))
        
    file = request.files['settings_file']
    if file.filename == '':
        flash('No file selected.', 'error')
        return redirect(url_for('admin.settings'))
        
    try:
        settings_data = json.loads(file.read())
        if 'settings' not in settings_data:
            raise ValueError('Invalid settings file format')
            
        for setting_item in settings_data['settings']:
            key = setting_item['key']
            value = setting_item['value']
            type = setting_item.get('type', 'text')
            description = setting_item.get('description', '')
            
            # Don't override critical settings
            if key in ['site_name', 'items_per_page', 'enable_comments']:
                continue
                
            setting = Settings.query.filter_by(key=key).first()
            if setting:
                setting.value = value
                setting.type = type
                setting.description = description
            else:
                setting = Settings(key=key, value=value, type=type, description=description)
                db.session.add(setting)
        
        db.session.commit()
        Settings.clear_cache()  # Clear the entire cache after bulk import
        flash('Settings imported successfully.', 'success')
        
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        flash(f'Error importing settings: {str(e)}', 'error')
        
    return redirect(url_for('admin.settings'))

@bp.route('/backups')
@login_required
@admin_required
def backups():
    """Display and manage backups."""
    from app.models import BackupSchedule, Backup
    
    schedule = BackupSchedule.get_schedule()
    backups_list = Backup.query.order_by(Backup.created_at.desc()).all()
    
    return render_template('admin/backups.html',
                         schedule=schedule,
                         backups=backups_list)

@bp.route('/backups/create', methods=['POST'])
@login_required
@admin_required
def create_backup():
    """Create a new backup."""
    import shutil
    from datetime import datetime
    
    # Ensure backup directory exists
    if not os.path.exists(current_app.config['BACKUP_DIR']):
        os.makedirs(current_app.config['BACKUP_DIR'])
    
    # Create backup record
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    filename = f"{current_app.config['BACKUP_FILE_PREFIX']}{timestamp}.db"
    backup = Backup(
        filename=filename,
        type='manual',
        note=request.form.get('note', '')
    )
    db.session.add(backup)
    db.session.commit()
    
    try:
        # Get the database file path
        db_path = current_app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        if not db_path.startswith('/'):  # Relative path
            db_path = os.path.join(current_app.root_path, '..', db_path)
        
        backup_path = os.path.join(current_app.config['BACKUP_DIR'], filename)
        
        # Ensure the source database exists
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database file not found at {db_path}")
        
        # Copy the database file
        shutil.copy2(db_path, backup_path)
        
        # Update backup record
        backup.status = 'completed'
        backup.completed_at = datetime.utcnow()
        backup.size = os.path.getsize(backup_path)
        db.session.commit()
        
        # Clean up old backups if needed
        cleanup_old_backups()
        
        return jsonify({
            'status': 'success',
            'message': 'Backup created successfully',
            'backup': {
                'id': backup.id,
                'filename': backup.filename,
                'created_at': backup.created_at.isoformat(),
                'size': backup.size
            }
        })
        
    except Exception as e:
        backup.status = 'failed'
        backup.note = str(e)
        db.session.commit()
        return jsonify({
            'status': 'error',
            'message': f'Failed to create backup: {str(e)}'
        }), 500

@bp.route('/backups/<int:id>/download')
@login_required
@admin_required
def download_backup(id):
    """Download a backup file."""
    backup = Backup.query.get_or_404(id)
    
    if not os.path.exists(backup.filepath):
        flash('Backup file not found.', 'error')
        return redirect(url_for('admin.backups'))
    
    return send_file(
        backup.filepath,
        as_attachment=True,
        download_name=backup.filename
    )

@bp.route('/backups/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_backup(id):
    """Delete a backup."""
    backup = Backup.query.get_or_404(id)
    
    try:
        # Delete the file
        backup.delete_file()
        
        # Delete the record
        db.session.delete(backup)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Backup deleted successfully'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to delete backup: {str(e)}'
        }), 500

def cleanup_old_backups():
    """Remove old backups if we exceed the maximum allowed."""
    max_backups = current_app.config.get('MAX_BACKUPS', 10)
    backups = Backup.query.order_by(Backup.created_at.desc()).all()
    
    if len(backups) > max_backups:
        for backup in backups[max_backups:]:
            backup.delete_file()
            db.session.delete(backup)
        
        db.session.commit()

@bp.route('/backups/schedule', methods=['POST'])
@login_required
@admin_required
def update_backup_schedule():
    """Update backup schedule settings."""
    from app.models import BackupSchedule
    
    schedule = BackupSchedule.get_schedule()
    schedule.frequency = request.form.get('frequency', 'daily')
    schedule.time = request.form.get('time', '00:00')
    schedule.retention = int(request.form.get('retention', 30))
    schedule.notify_on_failure = request.form.get('notify_on_failure') == 'true'
    schedule.enabled = True
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Backup schedule updated successfully'
    })

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

@bp.route('/upload-editor-image', methods=['POST'])
@login_required
@admin_required
def upload_editor_image():
    if 'upload' not in request.files:
        return jsonify({'error': {'message': 'No file uploaded'}}), 400
        
    file = request.files['upload']
    if file.filename == '':
        return jsonify({'error': {'message': 'No file selected'}}), 400
        
    if file and allowed_file(file.filename, {'png', 'jpg', 'jpeg', 'gif'}):
        filename = secure_filename(file.filename)
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        url = url_for('static', filename=f'uploads/{filename}')
        return jsonify({'url': url})
        
    return jsonify({'error': {'message': 'Invalid file type'}}), 400

def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions
