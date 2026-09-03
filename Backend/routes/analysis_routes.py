# routes/analysis_routes.py
# ─────────────────────────────────────────────
# POST   /api/analysis/scan     → upload a photo, run the two HF models, save + return result
# POST   /api/analysis/save     → save a client-supplied result (legacy/manual path)
# GET    /api/analysis/history  → get user history
# DELETE /api/analysis/<id>     → delete one result
# ─────────────────────────────────────────────

from flask              import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models              import skin_analysis as analysis_model
from models              import user_settings as settings_model
from services.hf_analysis import analyze_skin_image
import os, uuid

analysis_bp = Blueprint('analysis', __name__)

_ALLOWED_EXT = {'jpg', 'jpeg', 'png', 'webp'}


def _allowed(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in _ALLOWED_EXT


# ── POST /api/analysis/scan ───────────────────
@analysis_bp.route('/scan', methods=['POST'])
@jwt_required()
def scan_skin():
    user_id = get_jwt_identity()

    if 'photo' not in request.files:
        return jsonify({'message': 'No photo provided!'}), 400

    file = request.files['photo']
    if file.filename == '' or not _allowed(file.filename):
        return jsonify({'message': 'Please upload a JPG, PNG, or WEBP image.'}), 400

    scan_folder = current_app.config['SKIN_SCAN_FOLDER']
    os.makedirs(scan_folder, exist_ok=True)

    ext      = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{user_id}_{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(scan_folder, filename)
    file.save(filepath)

    try:
        analysis = analyze_skin_image(filepath)
    except Exception as exc:
        current_app.logger.exception('Hugging Face analysis failed')
        return jsonify({'message': f'Skin analysis failed: {exc}'}), 502

    image_url = f'/uploads/skin_scans/{filename}'
    record_fields = {
        'image_url':               image_url,
        'skin_type':                analysis['skin_type'],
        'skin_type_confidence':     analysis['skin_type_confidence'],
        'conditions':               analysis['conditions'],
        'severity':                 analysis['severity'],
        'score':                    analysis['score'],
        'raw_classifier_response':  analysis['raw_classifier_response'],
        'raw_yolo_response':        analysis['raw_yolo_response'],
    }

    settings = settings_model.get_or_create_settings(user_id)

    if settings.get('save_analysis_history', True):
        record = analysis_model.create_analysis(user_id, record_fields)
        result = analysis_model.to_dict(record)
    else:
        # User opted out of history — still return the result, just don't persist it.
        conditions = record_fields['conditions']
        summary = ', '.join(c['label'] for c in conditions) if conditions else 'No issues detected'
        result = {
            'imageUrl':   image_url,
            'skinType':   analysis['skin_type'],
            'conditions': conditions,
            'result':     f"{analysis['skin_type']} • {summary}",
            'severity':   analysis['severity'],
            'score':      analysis['score'],
        }

    return jsonify({'message': 'Analysis complete!', 'analysis': result}), 201


# ── POST /api/analysis/save ───────────────────
@analysis_bp.route('/save', methods=['POST'])
@jwt_required()
def save_analysis():
    user_id = get_jwt_identity()

    # Check if user has history saving ON
    settings = settings_model.get_or_create_settings(user_id)
    if not settings.get('save_analysis_history', True):
        return jsonify({
            'message': 'History saving is disabled by user settings.'
        }), 200     # not an error — user chose this

    data = request.get_json()

    record = analysis_model.create_analysis(user_id, {
        'image_url':               data.get('imageUrl', ''),
        'skin_type':                data.get('result', ''),
        'skin_type_confidence':     None,
        'conditions':               [],
        'severity':                 data.get('severity', 'low'),
        'score':                    0,
        'raw_classifier_response':  data.get('aiResponse', {}),
        'raw_yolo_response':        None,
    })

    return jsonify({
        'message':  'Analysis saved!',
        'analysis': analysis_model.to_dict(record)
    }), 201


# ── GET /api/analysis/history ─────────────────
@analysis_bp.route('/history', methods=['GET'])
@jwt_required()
def get_history():
    user_id  = get_jwt_identity()
    page     = request.args.get('page',  1,  type=int)
    per_page = request.args.get('limit', 10, type=int)

    items, total, pages = analysis_model.get_history(user_id, page, per_page)

    return jsonify({
        'history':  [analysis_model.to_dict(item) for item in items],
        'total':    total,
        'page':     page,
        'pages':    pages
    }), 200


# ── DELETE /api/analysis/<id> ─────────────────
@analysis_bp.route('/<analysis_id>', methods=['DELETE'])
@jwt_required()
def delete_analysis(analysis_id):
    user_id = get_jwt_identity()

    if not analysis_model.delete_analysis(analysis_id, user_id):
        return jsonify({'message': 'Analysis not found!'}), 404

    return jsonify({'message': 'Analysis deleted!'}), 200
