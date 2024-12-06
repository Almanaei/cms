from flask import Blueprint

bp = Blueprint('admin', __name__)

from app.admin import routes

@bp.context_processor
def inject_admin_context():
    from app.models import Settings, Role
    return dict(Settings=Settings, Role=Role)
