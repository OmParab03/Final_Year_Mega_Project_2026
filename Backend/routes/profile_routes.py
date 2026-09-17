# routes/profile_routes.py
# ─────────────────────────────────────────────
# GET  /api/profile          → get profile
# PUT  /api/profile          → update name/phone/dob
# POST /api/profile/photo    → upload photo
# ─────────────────────────────────────────────

from flask              import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models              import user as user_model
from datetime           import datetime
import os, uuid

profile_bp = Blueprint('profile', __name__)

# ── Helper: allowed file check ────────────────
def allowed_file(filename: str) -> bool:
    allowed = current_app.config['ALLOWED_EXTENSIONS']
    return (
        '.' in filename and
        filename.rsplit('.', 1)[1].lower() in allowed
    )

# ── GET /api/profile ──────────────────────────
@profile_bp.route('', methods=['GET'])
@jwt_required()
def get_profile():
    user = user_model.find_by_id(get_jwt_identity())

    if not user:
        return jsonify({'message': 'User not found!'}), 404

    return jsonify(user_model.to_dict(user)), 200


# ── PUT /api/profile ──────────────────────────
@profile_bp.route('', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    user    = user_model.find_by_id(user_id)

    if not user:
        return jsonify({'message': 'User not found!'}), 404

    data    = request.get_json()
    updates = {}

    # Update only provided fields
    if 'name' in data:
        name = data['name'].strip()
        if not name:
            return jsonify({'message': 'Name cannot be empty!'}), 400
        updates['name'] = name

    if 'phone' in data:
        updates['phone'] = data['phone'].strip() or None

    if 'dob' in data:
        dob_str = data['dob'].strip()
        if dob_str:
            try:
                updates['dob'] = datetime.strptime(dob_str, '%Y-%m-%d')
            except ValueError:
                return jsonify({'message': 'Date format must be YYYY-MM-DD'}), 400
        else:
            updates['dob'] = None

    if 'allergies' in data:
        raw = data['allergies']
        if isinstance(raw, list):
            updates['allergies'] = [a.strip() for a in raw if a.strip()]
        elif isinstance(raw, str):
            # Convert comma-separated string to list
            updates['allergies'] = [a.strip() for a in raw.split(',') if a.strip()]
        else:
            updates['allergies'] = []

    if 'skin_type' in data:
        updates['skin_type'] = data['skin_type'].strip() or None

    if 'skin_condition' in data:
        updates['skin_condition'] = data['skin_condition'].strip() or None

    user = user_model.update_user(user_id, updates)

    return jsonify({
        'message': 'Profile updated successfully!',
        'user':    user_model.to_dict(user)
    }), 200


# ── POST /api/profile/photo ───────────────────
@profile_bp.route('/photo', methods=['POST'])
@jwt_required()
def upload_photo():
    user_id = get_jwt_identity()
    user    = user_model.find_by_id(user_id)

    if not user:
        return jsonify({'message': 'User not found!'}), 404

    # ── Option A: multipart/form-data file upload
    if 'photo' in request.files:
        file = request.files['photo']

        if file.filename == '':
            return jsonify({'message': 'No file selected!'}), 400

        if not allowed_file(file.filename):
            return jsonify({
                'message': 'Only JPG, PNG, WEBP allowed!'
            }), 400

        # Save file with unique name
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)

        ext      = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{user_id}_{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)

        # Delete old photo file if exists
        old_photo = user.get('photo_url')
        if old_photo and old_photo.startswith('/uploads/'):
            old_path = os.path.join(os.getcwd(), old_photo.lstrip('/'))
            if os.path.exists(old_path):
                os.remove(old_path)

        photo_url = f'/uploads/profiles/{filename}'
        user_model.update_user(user_id, {'photo_url': photo_url})

        return jsonify({
            'message':  'Photo uploaded successfully!',
            'photoUrl': photo_url
        }), 200

    # ── Option B: base64 string in JSON body
    data = request.get_json()
    if data and 'photoBase64' in data:
        base64_str = data['photoBase64']

        # Validate it's actually base64 image
        if not base64_str.startswith('data:image'):
            return jsonify({'message': 'Invalid image data!'}), 400

        user_model.update_user(user_id, {'photo_url': base64_str})

        return jsonify({
            'message':  'Photo saved successfully!',
            'photoUrl': base64_str
        }), 200

    return jsonify({'message': 'No photo provided!'}), 400
