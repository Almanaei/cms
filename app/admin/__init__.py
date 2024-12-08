from flask import Blueprint

bp = Blueprint('admin', __name__, url_prefix='/admin')

from app.admin import routes

@bp.context_processor
def inject_admin_context():
    from app.models import Settings, Role, Backup
    return dict(Settings=Settings, Role=Role, Backup=Backup)
