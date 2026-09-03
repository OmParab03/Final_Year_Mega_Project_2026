# routes/settings_routes.py
# ─────────────────────────────────────────────
# GET /api/settings   → load settings
# PUT /api/settings   → save settings
# ─────────────────────────────────────────────

from flask              import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models              import user_settings as settings_model

settings_bp = Blueprint('settings', __name__)


# ── GET /api/settings ─────────────────────────
@settings_bp.route('', methods=['GET'])
@jwt_required()
def get_settings():
    settings = settings_model.get_or_create_settings(get_jwt_identity())
    return jsonify(settings_model.to_dict(settings)), 200


# ── PUT /api/settings ─────────────────────────
@settings_bp.route('', methods=['PUT'])
@jwt_required()
def update_settings():
    user_id = get_jwt_identity()
    settings_model.get_or_create_settings(user_id)  # ensure a doc exists first

    data     = request.get_json()
    settings = settings_model.update_settings(user_id, data)

    return jsonify({
        'message':  'Settings saved!',
        'settings': settings_model.to_dict(settings)
    }), 200
