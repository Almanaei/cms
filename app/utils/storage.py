import os
import shutil
from flask import current_app

def get_storage_usage():
    """
    Get storage usage statistics for the upload directory.
    Returns tuple of (used_bytes, total_bytes)
    """
    upload_path = current_app.config['UPLOAD_FOLDER']
    
    # Get total disk space
    total = shutil.disk_usage(upload_path).total
    
    # Calculate used space in upload directory
    used = 0
    for dirpath, dirnames, filenames in os.walk(upload_path):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            used += os.path.getsize(file_path)
    
    return used, total

def create_upload_directories():
    """
    Create necessary upload directories if they don't exist
    """
    paths = [
        current_app.config['UPLOAD_FOLDER'],
        current_app.config['TEMP_FOLDER']
    ]
    
    for path in paths:
        os.makedirs(path, exist_ok=True)

def cleanup_temp_files(max_age_hours=24):
    """
    Clean up temporary files older than max_age_hours
    """
    import time
    from datetime import datetime, timedelta
    
    temp_dir = current_app.config['TEMP_FOLDER']
    max_age = timedelta(hours=max_age_hours)
    now = datetime.now()
    
    for filename in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, filename)
        if os.path.isfile(file_path):
            file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
            if now - file_modified > max_age:
                try:
                    os.remove(file_path)
                except OSError:
                    pass  # Ignore errors during cleanup
