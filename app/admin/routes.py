from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, flash, request, jsonify, send_file
from flask import current_app, abort, Response
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user
from app import db, csrf
from app.admin import bp
from app.models import Post, Category, User, Settings, Role, Backup
from app.extensions import db, csrf
from app.decorators import admin_required, permission_required
import os
import json
import logging

# Setup logging
logger = logging.getLogger(__name__)

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

@bp.route('/user/create', methods=['GET', 'POST'])
@login_required
@permission_required(Role.MANAGE_USERS)
def create_user():
    try:
        form = UserForm()
        roles = Role.query.all()
        form.role_id.choices = [(role.id, role.name) for role in roles]
        
        if form.validate_on_submit():
            # Check if username already exists
            if User.query.filter_by(username=form.username.data).first():
                flash('Username already exists', 'danger')
                return render_template('admin/create_user.html', form=form)
            
            # Check if email already exists
            if User.query.filter_by(email=form.email.data).first():
                flash('Email already exists', 'danger')
                return render_template('admin/create_user.html', form=form)
            
            user = User(
                username=form.username.data,
                email=form.email.data,
                role_id=form.role_id.data,
                is_active=form.is_active.data
            )
            user.set_password(form.password.data)
            user.must_change_password = True
            
            db.session.add(user)
            db.session.commit()
            
            # Log the activity
            log_activity(
                user_id=current_user.id,
                activity_type='create_user',
                activity_data={
                    'created_user_id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role_id': user.role_id,
                    'is_active': user.is_active
                }
            )
            
            flash('User created successfully!', 'success')
            return redirect(url_for('admin.users'))
            
        return render_template('admin/create_user.html', form=form)
        
    except Exception as e:
        db.session.rollback()
        # Log the failed attempt
        log_activity(
            user_id=current_user.id,
            activity_type='create_user',
            activity_data={
                'attempted_username': form.username.data if form else None,
                'error': str(e)
            },
            success=False
        )
        current_app.logger.error(f'Error creating user: {str(e)}', exc_info=True)
        flash('An error occurred while creating the user. Please try again.', 'danger')
        return redirect(url_for('admin.users'))

@bp.route('/user/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required(Role.MANAGE_USERS)
def edit_user(id):
    user = User.query.get_or_404(id)
    form = UserForm(obj=user)
    roles = Role.query.all()
    form.role_id.choices = [(role.id, role.name) for role in roles]
    
    if form.validate_on_submit():
        try:
            # Track changes for activity logging
            changes = {}
            if user.username != form.username.data:
                changes['username'] = {'old': user.username, 'new': form.username.data}
            if user.email != form.email.data:
                changes['email'] = {'old': user.email, 'new': form.email.data}
            if user.role_id != form.role_id.data:
                old_role = Role.query.get(user.role_id)
                new_role = Role.query.get(form.role_id.data)
                changes['role'] = {'old': old_role.name if old_role else None, 'new': new_role.name if new_role else None}
            if user.is_active != form.is_active.data:
                changes['is_active'] = {'old': user.is_active, 'new': form.is_active.data}
            
            user.username = form.username.data
            user.email = form.email.data
            user.role_id = form.role_id.data
            user.is_active = form.is_active.data
            
            if form.password.data:
                user.set_password(form.password.data)
                changes['password'] = {'changed': True}
            
            db.session.commit()
            
            # Log the activity
            log_activity(
                user_id=current_user.id,
                activity_type='edit_user',
                activity_data={
                    'user_id': user.id,
                    'changes': changes
                }
            )
            
            flash('User updated successfully!', 'success')
            return redirect(url_for('admin.users'))
            
        except Exception as e:
            db.session.rollback()
            # Log the failed attempt
            log_activity(
                user_id=current_user.id,
                activity_type='edit_user',
                activity_data={
                    'target_user_id': id,
                    'error': str(e)
                },
                success=False
            )
            current_app.logger.error(f'Error editing user: {str(e)}', exc_info=True)
            flash('An error occurred while updating the user. Please try again.', 'danger')
            
    return render_template('admin/edit_user.html', form=form, user=user)

@bp.route('/user/<int:id>/delete', methods=['POST'])
@login_required
@permission_required(Role.MANAGE_USERS)
def delete_user(id):
    try:
        user = User.query.get_or_404(id)
        
        # Don't allow deleting your own account
        if user.id == current_user.id:
            flash('You cannot delete your own account.', 'danger')
            return redirect(url_for('admin.users'))
        
        # Store user info for logging before deletion
        user_info = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role_id': user.role_id
        }
        
        db.session.delete(user)
        db.session.commit()
        
        # Log the successful deletion
        log_activity(
            user_id=current_user.id,
            activity_type='delete_user',
            activity_data={
                'deleted_user': user_info
            }
        )
        
        flash('User deleted successfully!', 'success')
        return redirect(url_for('admin.users'))
        
    except Exception as e:
        db.session.rollback()
        # Log the failed deletion attempt
        log_activity(
            user_id=current_user.id,
            activity_type='delete_user',
            activity_data={
                'target_user_id': id,
                'error': str(e)
            },
            success=False
        )
        current_app.logger.error(f'Error deleting user: {str(e)}', exc_info=True)
        flash('An error occurred while deleting the user. Please try again.', 'danger')
        return redirect(url_for('admin.users'))

@bp.route('/user-activity')
@login_required
@admin_required
def user_activity_list():
    try:
        page = request.args.get('page', 1, type=int)
        activities = UserActivity.query.order_by(UserActivity.timestamp.desc()).paginate(
            page=page, per_page=20, error_out=False)
        return render_template('admin/user_activity.html', activities=activities)
    except Exception as e:
        current_app.logger.error(f'Error loading user activity list: {str(e)}', exc_info=True)
        flash('An error occurred while loading the activity list. Please try again.', 'danger')
        return redirect(url_for('admin.index'))

@bp.route('/user-activity/<int:id>')
@login_required
@admin_required
def user_activity_detail(id):
    try:
        user = User.query.get_or_404(id)
        page = request.args.get('page', 1, type=int)
        activities = UserActivity.query.filter_by(user_id=id).order_by(
            UserActivity.timestamp.desc()).paginate(page=page, per_page=20, error_out=False)
        return render_template('admin/user_activity_detail.html', user=user, activities=activities)
    except Exception as e:
        current_app.logger.error(f'Error loading user activity detail for user {id}: {str(e)}', exc_info=True)
        flash('An error occurred while loading the activity details. Please try again.', 'danger')
        return redirect(url_for('admin.user_activity_list'))

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
    try:
        from sqlalchemy import func
        from datetime import datetime, timedelta
        from collections import defaultdict
        
        # Initialize default values
        metrics = {
            'views': {'current': 0, 'growth': 0},
            'visitors': {'current': 0, 'growth': 0},
            'duration': {'current': 0, 'growth': 0},
            'bounce_rate': {'current': 0, 'growth': 0}
        }
        content_perf = {'top_content': []}
        top_posts = []
        top_countries = []
        
        # Initialize traffic data with default empty values
        traffic = {
            'peak_hours': {f"{hour:02d}:00": 0 for hour in range(24)},  # Initialize all 24 hours
            'sources': {'Direct': 0, 'Search': 0, 'Social': 0, 'Referral': 0},  # Initialize common sources
            'devices': {'Desktop': 0, 'Mobile': 0, 'Tablet': 0}  # Initialize device types
        }
        
        # Initialize behavior data with default empty values
        behavior = {
            'events': {
                'Post View': 0,
                'Category View': 0,
                'Home Page': 0,
                'Comments': 0
            }
        }
        
        # Initialize tech metrics with default empty values
        tech_metrics = {
            'browsers': {'Chrome': 0, 'Firefox': 0, 'Safari': 0, 'Edge': 0, 'Other': 0},
            'operating_systems': {'Windows': 0, 'MacOS': 0, 'Linux': 0, 'iOS': 0, 'Android': 0, 'Other': 0}
        }
        
        # Initialize geographic data
        geo_data = {
            'countries': defaultdict(int)
        }
        
        # Get time ranges
        now = datetime.utcnow()
        last_30_days = now - timedelta(days=30)
        last_60_days = now - timedelta(days=60)
        
        # Get total views and growth
        try:
            current_views = PageView.query.filter(PageView.timestamp >= last_30_days).count()
            previous_views = PageView.query.filter(
                PageView.timestamp >= last_60_days,
                PageView.timestamp < last_30_days
            ).count()
            view_growth = ((current_views - previous_views) / (previous_views or 1)) * 100
            metrics['views'] = {'current': current_views, 'growth': view_growth}
            
            # Calculate peak hours and traffic sources
            page_views = PageView.query.filter(PageView.timestamp >= last_30_days).all()
            for view in page_views:
                hour = view.timestamp.strftime('%H:00')
                traffic['peak_hours'][hour] += 1
                
                # Categorize traffic sources
                if not view.referrer or view.referrer == '':
                    traffic['sources']['Direct'] += 1
                elif 'google' in view.referrer.lower() or 'bing' in view.referrer.lower():
                    traffic['sources']['Search'] += 1
                elif any(social in view.referrer.lower() for social in ['facebook', 'twitter', 'instagram', 'linkedin']):
                    traffic['sources']['Social'] += 1
                else:
                    traffic['sources']['Referral'] += 1
                
                # Track user behavior
                if view.url.startswith('/post/'):
                    behavior['events']['Post View'] += 1
                elif view.url.startswith('/category/'):
                    behavior['events']['Category View'] += 1
                elif view.url == '/':
                    behavior['events']['Home Page'] += 1
                
                # Track device types
                if view.device_type:
                    device_type = view.device_type.capitalize()
                    if device_type in traffic['devices']:
                        traffic['devices'][device_type] += 1
                    
                # Track browser usage
                if view.browser:
                    browser = view.browser.capitalize()
                    if browser in tech_metrics['browsers']:
                        tech_metrics['browsers'][browser] += 1
                    else:
                        tech_metrics['browsers']['Other'] += 1
                        
                # Track operating systems
                if view.os:
                    os_name = view.os.capitalize()
                    if os_name in tech_metrics['operating_systems']:
                        tech_metrics['operating_systems'][os_name] += 1
                    else:
                        tech_metrics['operating_systems']['Other'] += 1
                        
                # Track geographic data
                if view.country:
                    geo_data['countries'][view.country] += 1
                
        except Exception as e:
            current_app.logger.error(f'Error calculating view metrics: {str(e)}', exc_info=True)

        # Get active users and growth
        try:
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
            metrics['visitors'] = {'current': current_active_users, 'growth': user_growth}
        except Exception as e:
            current_app.logger.error(f'Error calculating user metrics: {str(e)}', exc_info=True)

        # Get total content and growth
        try:
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
        except Exception as e:
            current_app.logger.error(f'Error calculating content metrics: {str(e)}', exc_info=True)

        # Get engagement metrics
        try:
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
            
            # Track comment events
            behavior['events']['Comments'] = current_engagement
        except Exception as e:
            current_app.logger.error(f'Error calculating engagement metrics: {str(e)}', exc_info=True)

        # Get top posts by views
        try:
            top_posts_query = db.session.query(
                Post,
                func.count(PageView.id).label('views')
            ).join(
                PageView, PageView.url.like(func.concat('/post/%', Post.slug))
            ).filter(
                Post.published == True,
                PageView.timestamp >= last_30_days
            ).group_by(
                Post.id
            ).order_by(
                func.count(PageView.id).desc()
            ).limit(5).all()
            
            # Format top posts for content performance section
            top_posts = top_posts_query
            content_perf['top_content'] = [(post.title, views) for post, views in top_posts_query]
        except Exception as e:
            current_app.logger.error(f'Error getting top posts: {str(e)}', exc_info=True)

        # Get top countries
        try:
            top_countries = db.session.query(
                PageView.country,
                func.count(PageView.id).label('views')
            ).filter(
                PageView.timestamp >= last_30_days,
                PageView.country.isnot(None)
            ).group_by(
                PageView.country
            ).order_by(
                func.count(PageView.id).desc()
            ).limit(5).all()
        except Exception as e:
            current_app.logger.error(f'Error getting top countries: {str(e)}', exc_info=True)

        # Convert defaultdict to regular dict for JSON serialization
        geo_data['countries'] = dict(geo_data['countries'])

        return render_template('admin/analytics.html',
            metrics=metrics,
            content_perf=content_perf,
            top_posts=top_posts,
            top_countries=top_countries,
            traffic=traffic,
            behavior=behavior,
            tech_metrics=tech_metrics,
            geo_data=geo_data
        )
    except Exception as e:
        current_app.logger.error(f'Error in analytics route: {str(e)}\nTraceback:', exc_info=True)
        db.session.rollback()  # Roll back any failed transactions
        # Initialize empty data for the template
        empty_data = {
            'metrics': {
                'views': {'current': 0, 'growth': 0},
                'visitors': {'current': 0, 'growth': 0},
                'duration': {'current': 0, 'growth': 0},
                'bounce_rate': {'current': 0, 'growth': 0}
            },
            'content_perf': {'top_content': []},
            'top_posts': [],
            'top_countries': [],
            'traffic': {
                'peak_hours': {f"{hour:02d}:00": 0 for hour in range(24)},
                'sources': {'Direct': 0, 'Search': 0, 'Social': 0, 'Referral': 0},
                'devices': {'Desktop': 0, 'Mobile': 0, 'Tablet': 0}
            },
            'behavior': {
                'events': {
                    'Post View': 0,
                    'Category View': 0,
                    'Home Page': 0,
                    'Comments': 0
                }
            },
            'tech_metrics': {
                'browsers': {'Chrome': 0, 'Firefox': 0, 'Safari': 0, 'Edge': 0, 'Other': 0},
                'operating_systems': {'Windows': 0, 'MacOS': 0, 'Linux': 0, 'iOS': 0, 'Android': 0, 'Other': 0}
            },
            'geo_data': {
                'countries': {}
            }
        }
        return render_template('admin/analytics.html', **empty_data)

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

@bp.route('/database-backups')
@login_required
@admin_required
def database_backups():
    """View database backups."""
    try:
        backups = Backup.query.order_by(Backup.created_at.desc()).all()
        return render_template('admin/database_backups.html', backups=backups)
    except Exception as e:
        current_app.logger.error(f"Error accessing database backups: {str(e)}")
        flash('Error accessing database backups', 'error')
        return render_template('admin/database_backups.html', backups=[]), 500

@bp.route('/database-backups/create', methods=['POST'])
@login_required
@admin_required
@csrf.exempt
def create_database_backup():
    """Create a new database backup."""
    try:
        # Get backup directory from config, defaulting to 'backups' in instance folder
        backup_dir = current_app.config.get('BACKUP_DIR', os.path.join(current_app.instance_path, 'backups'))
        
        # Convert relative path to absolute if necessary
        if not os.path.isabs(backup_dir):
            backup_dir = os.path.join(current_app.root_path, '..', backup_dir)
            
        # Create backup filename
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"backup_{timestamp}.db"
        
        # Get database path
        if os.environ.get('CPANEL_ENV') == 'true':
            db_path = os.path.join('/home', os.environ.get('USER', ''), 'app.db')
        else:
            db_path = os.path.join(current_app.root_path, '..', 'app.db')
        
        if not os.path.exists(db_path):
            raise FileNotFoundError(f'Database file not found at {db_path}')
        
        backup_path = os.path.join(backup_dir, filename)
        
        # Create backup file
        shutil.copy2(db_path, backup_path)
        os.chmod(backup_path, 0o644)  # Set file permissions to 644
        
        # Create backup record
        backup = Backup(
            filename=filename,
            size=os.path.getsize(backup_path),
            description=request.form.get('note', f"Manual backup created on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
        )
        db.session.add(backup)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Backup created successfully',
            'backup': backup.to_dict()
        })
        
    except Exception as e:
        current_app.logger.error(f'Backup creation failed: {str(e)}')
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Failed to create backup: {str(e)}'
        }), 500

@bp.route('/database-backups/<int:id>/download')
@login_required
@admin_required
def download_database_backup(id):
    """Download a backup file."""
    try:
        backup = Backup.query.get_or_404(id)
        backup_dir = current_app.config.get('BACKUP_DIR', os.path.join(current_app.instance_path, 'backups'))
        
        if not backup_dir:
            raise ValueError('Backup directory not configured')
            
        # Convert relative path to absolute if necessary
        if not os.path.isabs(backup_dir):
            backup_dir = os.path.join(current_app.root_path, '..', backup_dir)
            
        backup_path = os.path.join(backup_dir, backup.filename)
        
        if not os.path.exists(backup_path):
            flash('Backup file not found.', 'error')
            return redirect(url_for('admin.database_backups'))
        
        return send_file(
            backup_path,
            as_attachment=True,
            download_name=backup.filename
        )
        
    except Exception as e:
        current_app.logger.error(f'Error downloading backup: {str(e)}')
        flash(f'Error downloading backup: {str(e)}', 'error')
        return redirect(url_for('admin.database_backups'))

@bp.route('/database-backups/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_database_backup(id):
    """Delete a backup."""
    try:
        backup = Backup.query.get_or_404(id)
        backup_dir = current_app.config.get('BACKUP_DIR', os.path.join(current_app.instance_path, 'backups'))
        
        if not backup_dir:
            raise ValueError('Backup directory not configured')
            
        # Convert relative path to absolute if necessary
        if not os.path.isabs(backup_dir):
            backup_dir = os.path.join(current_app.root_path, '..', backup_dir)
            
        backup_path = os.path.join(backup_dir, backup.filename)
        
        # Delete file if it exists
        if os.path.exists(backup_path):
            os.remove(backup_path)
        
        # Delete database record
        db.session.delete(backup)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Backup deleted successfully'
        })
        
    except Exception as e:
        current_app.logger.error(f'Error deleting backup: {str(e)}')
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Failed to delete backup: {str(e)}'
        }), 500

@bp.route('/database-backups/<int:id>/restore', methods=['POST'])
@login_required
@admin_required
def restore_database_backup(id):
    """Restore a database backup."""
    try:
        backup = Backup.query.get_or_404(id)
        backup_dir = current_app.config.get('BACKUP_DIR', os.path.join(current_app.instance_path, 'backups'))
        
        if not backup_dir:
            raise ValueError('Backup directory not configured')
            
        # Convert relative path to absolute if necessary
        if not os.path.isabs(backup_dir):
            backup_dir = os.path.join(current_app.root_path, '..', backup_dir)
            
        backup_path = os.path.join(backup_dir, backup.filename)
        
        if not os.path.exists(backup_path):
            raise FileNotFoundError('Backup file not found')
            
        # Get database path
        if os.environ.get('CPANEL_ENV') == 'true':
            db_path = os.path.join('/home', os.environ.get('USER', ''), 'app.db')
        else:
            db_path = os.path.join(current_app.root_path, '..', 'app.db')
            
        # Create a temporary backup of the current database
        temp_backup = f"{db_path}.temp"
        shutil.copy2(db_path, temp_backup)
        
        try:
            # Restore the backup
            shutil.copy2(backup_path, db_path)
            os.remove(temp_backup)  # Remove temporary backup after successful restore
            
            return jsonify({
                'status': 'success',
                'message': 'Database restored successfully'
            })
            
        except Exception as e:
            # If restore fails, try to restore from temporary backup
            if os.path.exists(temp_backup):
                shutil.copy2(temp_backup, db_path)
                os.remove(temp_backup)
            raise e
            
    except Exception as e:
        current_app.logger.error(f'Error restoring backup: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': f'Failed to restore backup: {str(e)}'
        }), 500

@bp.route('/database-backups/schedule', methods=['POST'])
@login_required
@admin_required
def update_backup_schedule():
    """Update backup schedule settings."""
    try:
        # Get settings from request
        enabled = request.form.get('enabled', 'false') == 'true'
        frequency = request.form.get('frequency', 'daily')
        backup_time = request.form.get('time', '00:00')
        keep_count = int(request.form.get('keep_count', 10))
        
        # Store settings
        Settings.set('backup_enabled', str(enabled).lower(), type='boolean')
        Settings.set('backup_frequency', frequency)
        Settings.set('backup_time', backup_time)
        Settings.set('backup_keep_count', str(keep_count), type='integer')
        
        return jsonify({
            'status': 'success',
            'message': 'Backup schedule updated successfully'
        })
        
    except Exception as e:
        current_app.logger.error(f'Error updating backup schedule: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': f'Failed to update backup schedule: {str(e)}'
        }), 500

def cleanup_old_backups():
    """Delete old backups if we exceed the maximum number."""
    try:
        max_backups = int(Settings.get('backup_keep_count', 10))
        backups = Backup.query.order_by(Backup.created_at.desc()).all()
        
        if len(backups) > max_backups:
            for backup in backups[max_backups:]:
                backup_path = os.path.join(current_app.config.get('BACKUP_DIR', os.path.join(current_app.instance_path, 'backups')), backup.filename)
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                db.session.delete(backup)
            
            db.session.commit()
            current_app.logger.info(f'Cleaned up old backups, keeping {max_backups} most recent')
            
    except Exception as e:
        current_app.logger.error(f'Error cleaning up old backups: {str(e)}')
        db.session.rollback()

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

def cleanup_old_backups():
    """Delete old backups if we exceed the maximum number."""
    try:
        max_backups = int(Settings.get('backup_keep_count', 10))
        backups = Backup.query.order_by(Backup.created_at.desc()).all()
        
        if len(backups) > max_backups:
            for backup in backups[max_backups:]:
                backup_path = os.path.join(current_app.config.get('BACKUP_DIR', os.path.join(current_app.instance_path, 'backups')), backup.filename)
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                db.session.delete(backup)
            
            db.session.commit()
            current_app.logger.info(f'Cleaned up old backups, keeping {max_backups} most recent')
            
    except Exception as e:
        current_app.logger.error(f'Error cleaning up old backups: {str(e)}')
        db.session.rollback()
