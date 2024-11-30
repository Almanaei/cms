from flask import Blueprint, render_template, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from ..models import db, MediaItem
from ..utils.storage import get_storage_usage
from flask_login import login_required
import mimetypes
from PIL import Image
import magic
import shutil

bp = Blueprint('media', __name__)

ALLOWED_EXTENSIONS = {
    'image': {'png', 'jpg', 'jpeg', 'gif', 'webp'},
    'video': {'mp4', 'webm', 'ogg'},
    'document': {'pdf', 'doc', 'docx', 'txt', 'md'}
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {
        ext for types in ALLOWED_EXTENSIONS.values() for ext in types
    }

def get_file_type(filename, mime_type):
    ext = filename.rsplit('.', 1)[1].lower()
    for type_name, extensions in ALLOWED_EXTENSIONS.items():
        if ext in extensions:
            return type_name
    return 'other'

@bp.route('/media')
@login_required
def media_library():
    page = request.args.get('page', 1, type=int)
    sort = request.args.get('sort', 'date_desc')
    
    # Define sorting options
    sort_options = {
        'date_desc': MediaItem.created_at.desc(),
        'date_asc': MediaItem.created_at.asc(),
        'name_asc': MediaItem.filename.asc(),
        'name_desc': MediaItem.filename.desc(),
        'size_desc': MediaItem.size.desc(),
        'size_asc': MediaItem.size.asc()
    }
    
    query = MediaItem.query.order_by(sort_options.get(sort, 'date_desc'))
    pagination = query.paginate(page=page, per_page=24, error_out=False)
    
    storage_used, storage_total = get_storage_usage()
    storage_usage_percent = (storage_used / storage_total) * 100 if storage_total > 0 else 0
    
    return render_template('admin/media.html',
                         media_items=pagination.items,
                         pagination=pagination,
                         storage_used=storage_used,
                         storage_total=storage_total,
                         storage_usage_percent=storage_usage_percent)

@bp.route('/media/upload', methods=['POST'])
@login_required
def upload_media():
    if 'files[]' not in request.files:
        return jsonify({'success': False, 'error': 'No file part'})

    files = request.files.getlist('files[]')
    uploaded_files = []
    errors = []

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{timestamp}_{filename}"
            
            # Create year/month based directory structure
            year_month = datetime.now().strftime('%Y/%m')
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], year_month)
            os.makedirs(upload_path, exist_ok=True)
            
            file_path = os.path.join(upload_path, unique_filename)
            file.save(file_path)
            
            # Get file info
            mime_type = magic.from_file(file_path, mime=True)
            file_size = os.path.getsize(file_path)
            file_type = get_file_type(filename, mime_type)
            
            # Create thumbnail for images
            thumbnail_path = None
            if file_type == 'image':
                try:
                    thumbnail_path = os.path.join(upload_path, f"thumb_{unique_filename}")
                    with Image.open(file_path) as img:
                        img.thumbnail((200, 200))
                        img.save(thumbnail_path)
                except Exception as e:
                    current_app.logger.error(f"Thumbnail creation failed: {str(e)}")
            
            # Save to database
            media_item = MediaItem(
                filename=filename,
                filepath=os.path.join(year_month, unique_filename),
                thumbnail_path=os.path.join(year_month, f"thumb_{unique_filename}") if thumbnail_path else None,
                type=file_type,
                mime_type=mime_type,
                size=file_size
            )
            db.session.add(media_item)
            uploaded_files.append(filename)
        else:
            errors.append(f"Invalid file: {file.filename}")
    
    if uploaded_files:
        db.session.commit()
        
    return jsonify({
        'success': True,
        'uploaded': uploaded_files,
        'errors': errors
    })

@bp.route('/media/delete/<int:id>', methods=['DELETE'])
@login_required
def delete_media(id):
    media_item = MediaItem.query.get_or_404(id)
    
    try:
        # Delete file
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], media_item.filepath)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete thumbnail if exists
        if media_item.thumbnail_path:
            thumbnail_path = os.path.join(current_app.config['UPLOAD_FOLDER'], media_item.thumbnail_path)
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
        
        # Remove from database
        db.session.delete(media_item)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        current_app.logger.error(f"File deletion failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/media/download/<int:id>')
@login_required
def download_media(id):
    media_item = MediaItem.query.get_or_404(id)
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], media_item.filepath)
    
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'error': 'File not found'}), 404
        
    return send_file(
        file_path,
        mimetype=media_item.mime_type,
        as_attachment=True,
        download_name=media_item.filename
    )

@bp.route('/media/bulk-delete', methods=['POST'])
@login_required
def bulk_delete_media():
    ids = request.json.get('ids', [])
    if not ids:
        return jsonify({'success': False, 'error': 'No items selected'})
    
    success_count = 0
    errors = []
    
    for id in ids:
        try:
            media_item = MediaItem.query.get(id)
            if media_item:
                # Delete file and thumbnail
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], media_item.filepath)
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                if media_item.thumbnail_path:
                    thumbnail_path = os.path.join(current_app.config['UPLOAD_FOLDER'], media_item.thumbnail_path)
                    if os.path.exists(thumbnail_path):
                        os.remove(thumbnail_path)
                
                db.session.delete(media_item)
                success_count += 1
        except Exception as e:
            errors.append(f"Error deleting item {id}: {str(e)}")
    
    if success_count > 0:
        db.session.commit()
    
    return jsonify({
        'success': True,
        'deleted_count': success_count,
        'errors': errors
    })

@bp.route('/media/bulk-download', methods=['POST'])
@login_required
def bulk_download_media():
    ids = request.json.get('ids', [])
    if not ids:
        return jsonify({'success': False, 'error': 'No items selected'})
    
    # Create a temporary zip file
    temp_dir = os.path.join(current_app.config['TEMP_FOLDER'], 'downloads')
    os.makedirs(temp_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    zip_filename = f'media_download_{timestamp}.zip'
    zip_path = os.path.join(temp_dir, zip_filename)
    
    try:
        # Create zip file
        shutil.make_archive(
            zip_path[:-4],  # Remove .zip extension
            'zip',
            root_dir=current_app.config['UPLOAD_FOLDER'],
            base_dir='.'
        )
        
        return send_file(
            zip_path,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )
    except Exception as e:
        current_app.logger.error(f"Bulk download failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})
    finally:
        # Cleanup temp files
        if os.path.exists(zip_path):
            os.remove(zip_path)
