# routes/product_routes.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import os
import uuid
from models import product_scan as product_scan_model
from models import user as user_model
from models import skin_analysis as skin_analysis_model
from models import user_settings as settings_model
from services.nvidia_analysis import analyze_product_image

product_bp = Blueprint('product', __name__)

_ALLOWED_EXT = {'jpg', 'jpeg', 'png', 'webp'}

def _allowed(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in _ALLOWED_EXT

@product_bp.route('/scan', methods=['POST'])
@jwt_required()
def scan_product():
    user_id = get_jwt_identity()

    if 'photo' not in request.files:
        return jsonify({'message': 'No photo provided!'}), 400

    file = request.files['photo']
    if file.filename == '' or not _allowed(file.filename):
        return jsonify({'message': 'Please upload a JPG, PNG, or WEBP image.'}), 400

    scan_folder = current_app.config.get('PRODUCT_SCAN_FOLDER', os.path.join(current_app.config['UPLOAD_FOLDER'], 'product_scans'))
    os.makedirs(scan_folder, exist_ok=True)

    ext      = file.filename.rsplit('.', 1)[1].lower()
    filename = f"prod_{user_id}_{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(scan_folder, filename)
    file.save(filepath)

    try:
        # Fetch user profile data
        user_record = user_model.find_by_id(user_id)
        if not user_record:
            return jsonify({'message': 'User not found'}), 404

        # Fetch latest skin analysis to include in context
        recent_analyses, _, _ = skin_analysis_model.get_history(user_id, page=1, per_page=1)
        recent_conditions = recent_analyses[0].get('conditions', []) if recent_analyses else []

        user_profile = {
            'age':      user_record.get('age') or (
                # fallback: compute from dob if age not stored yet
                (datetime.utcnow().year - user_record['dob'].year) if user_record.get('dob') else None
            ),
            'skinType':      user_record.get('skin_type') or 'Unknown',
            'allergies':     user_record.get('allergies') or [],
            'skin_condition':user_record.get('skin_condition') or '',
            'conditions':    recent_conditions
        }

        # Analyze with NVIDIA API
        analysis_result = analyze_product_image(filepath, user_profile)
        
    except Exception as exc:
        current_app.logger.exception('Product analysis failed')
        return jsonify({'message': f'Product analysis failed: {exc}'}), 502

    image_url = f'/uploads/product_scans/{filename}'
    record_fields = {
        'image_url':             image_url,
        'score':                 analysis_result.get('score', 0),
        'score_label':           analysis_result.get('score_label', ''),
        'score_summary':         analysis_result.get('score_summary', ''),
        'harmful_ingredients':   analysis_result.get('harmful_ingredients', []),
        'beneficial_ingredients':analysis_result.get('beneficial_ingredients', []),
        'ai_summary':            analysis_result.get('ai_summary', ''),
        'potential_issues':      analysis_result.get('potential_issues', {}),
        'recommended_alternatives': analysis_result.get('recommended_alternatives', []),
        # Legacy fields kept for backward compat
        'ingredients': analysis_result.get('ingredients', []),
        'analysis':    analysis_result.get('analysis', [])
    }

    settings = settings_model.get_or_create_settings(user_id)

    if settings.get('save_analysis_history', True):
        record = product_scan_model.create_scan(user_id, record_fields)
        result = product_scan_model.to_dict(record)
    else:
        result = {
            'imageUrl':               image_url,
            'score':                  record_fields['score'],
            'score_label':            record_fields['score_label'],
            'score_summary':          record_fields['score_summary'],
            'harmful_ingredients':    record_fields['harmful_ingredients'],
            'beneficial_ingredients': record_fields['beneficial_ingredients'],
            'ai_summary':             record_fields['ai_summary'],
            'potential_issues':       record_fields['potential_issues'],
            'recommended_alternatives': record_fields['recommended_alternatives'],
        }

    return jsonify({'message': 'Product scan complete!', 'analysis': result}), 201


@product_bp.route('/history', methods=['GET'])
@jwt_required()
def get_history():
    user_id  = get_jwt_identity()
    page     = request.args.get('page',  1,  type=int)
    per_page = request.args.get('limit', 10, type=int)

    items, total, pages = product_scan_model.get_history(user_id, page, per_page)

    return jsonify({
        'history':  [product_scan_model.to_dict(item) for item in items],
        'total':    total,
        'page':     page,
        'pages':    pages
    }), 200

@product_bp.route('/<scan_id>', methods=['DELETE'])
@jwt_required()
def delete_scan(scan_id):
    user_id = get_jwt_identity()

    if not product_scan_model.delete_scan(scan_id, user_id):
        return jsonify({'message': 'Scan not found!'}), 404

    return jsonify({'message': 'Product scan deleted!'}), 200
