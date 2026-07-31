# routes/analysis_routes.py
# ─────────────────────────────────────────────
# FOR YOUR COLLEAGUE who handles AI analysis
#
# POST /api/analysis/save     → save a result
# GET  /api/analysis/history  → get user history
# DELETE /api/analysis/<id>   → delete one result
# ─────────────────────────────────────────────

from flask              import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions         import db
from models.skin_analysis import SkinAnalysis
from models.user_settings import UserSettings
import json

analysis_bp = Blueprint('analysis', __name__)


# ── POST /api/analysis/save ───────────────────
@analysis_bp.route('/save', methods=['POST'])
@jwt_required()
def save_analysis():
    user_id = int(get_jwt_identity())

    # Check if user has history saving ON
    settings = UserSettings.query.filter_by(user_id=user_id).first()
    if settings and not settings.save_analysis_history:
        return jsonify({
            'message': 'History saving is disabled by user settings.'
        }), 200     # not an error — user chose this

    data = request.get_json()

    analysis = SkinAnalysis(
        user_id    = user_id,
        image_url  = data.get('imageUrl',  ''),
        result     = data.get('result',    ''),
        severity   = data.get('severity',  'low'),
        ai_response = json.dumps(data.get('aiResponse', {}))
    )

    db.session.add(analysis)
    db.session.commit()

    return jsonify({
        'message':  'Analysis saved!',
        'analysis': analysis.to_dict()
    }), 201


# ── GET /api/analysis/history ─────────────────
@analysis_bp.route('/history', methods=['GET'])
@jwt_required()
def get_history():
    user_id  = int(get_jwt_identity())
    page     = request.args.get('page',  1,  type=int)
    per_page = request.args.get('limit', 10, type=int)

    pagination = (
        SkinAnalysis.query
        .filter_by(user_id=user_id)
        .order_by(SkinAnalysis.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return jsonify({
        'history':  [a.to_dict() for a in pagination.items],
        'total':    pagination.total,
        'page':     page,
        'pages':    pagination.pages
    }), 200


# ── DELETE /api/analysis/<id> ─────────────────
@analysis_bp.route('/<int:analysis_id>', methods=['DELETE'])
@jwt_required()
def delete_analysis(analysis_id):
    user_id  = int(get_jwt_identity())
    analysis = SkinAnalysis.query.filter_by(
        id=analysis_id,
        user_id=user_id
    ).first()

    if not analysis:
        return jsonify({'message': 'Analysis not found!'}), 404

    db.session.delete(analysis)
    db.session.commit()

    return jsonify({'message': 'Analysis deleted!'}), 200