# routes/settings_routes.py
# ─────────────────────────────────────────────
# GET /api/settings   → load settings
# PUT /api/settings   → save settings
# ─────────────────────────────────────────────

from flask              import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions         import db
from models.user_settings import UserSettings

settings_bp = Blueprint('settings', __name__)


# ── GET /api/settings ─────────────────────────
@settings_bp.route('', methods=['GET'])
@jwt_required()
def get_settings():
    user_id  = int(get_jwt_identity())
    settings = UserSettings.query.filter_by(user_id=user_id).first()

    # If no row yet → create default
    if not settings:
        settings = UserSettings(user_id=user_id)
        db.session.add(settings)
        db.session.commit()

    return jsonify(settings.to_dict()), 200


# ── PUT /api/settings ─────────────────────────
@settings_bp.route('', methods=['PUT'])
@jwt_required()
def update_settings():
    user_id  = int(get_jwt_identity())
    settings = UserSettings.query.filter_by(user_id=user_id).first()

    if not settings:
        settings = UserSettings(user_id=user_id)
        db.session.add(settings)

    data = request.get_json()

    # Update only fields that are sent
    if 'emailNotifications' in data:
        settings.email_notifications = bool(data['emailNotifications'])

    if 'saveAnalysisHistory' in data:
        settings.save_analysis_history = bool(data['saveAnalysisHistory'])

    if 'darkMode' in data:
        settings.dark_mode = bool(data['darkMode'])

    db.session.commit()

    return jsonify({
        'message':  'Settings saved!',
        'settings': settings.to_dict()
    }), 200