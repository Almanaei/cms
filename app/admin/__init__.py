from flask import Blueprint

bp = Blueprint('admin', __name__)

from app.admin import routes

@bp.context_processor
def inject_settings():
    from app.models import Settings
    return dict(Settings=Settings)
