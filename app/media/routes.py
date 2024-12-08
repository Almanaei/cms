import os
from flask import send_from_directory, current_app, abort
from app.media import bp

@bp.route('/<path:filename>')
def serve_media(filename):
    """Serve media files."""
    try:
        media_dir = current_app.config.get('MEDIA_DIR', 'media')
        if not os.path.isabs(media_dir):
            media_dir = os.path.join(current_app.root_path, '..', media_dir)
        return send_from_directory(media_dir, filename)
    except Exception as e:
        current_app.logger.error(f"Error serving media file {filename}: {str(e)}")
        abort(404)
