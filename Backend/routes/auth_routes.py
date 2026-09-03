# routes/auth_routes.py
# ─────────────────────────────────────────────
# POST /api/signup
# POST /api/signin
# ─────────────────────────────────────────────

from flask               import Blueprint, request, jsonify
from flask_jwt_extended  import create_access_token
from werkzeug.security   import generate_password_hash, check_password_hash
from models              import user as user_model
from models              import user_settings as settings_model

auth_bp = Blueprint('auth', __name__)

# ── Sign Up ───────────────────────────────────
@auth_bp.route('/signup', methods=['POST'])
def signup():
    data     = request.get_json()
    name     = data.get('name',     '').strip()
    email    = data.get('email',    '').strip().lower()
    password = data.get('password', '').strip()

    # Validate
    if not name or not email or not password:
        return jsonify({'message': 'All fields are required!'}), 400

    if len(password) < 6:
        return jsonify({'message': 'Password must be at least 6 characters!'}), 400

    # Check duplicate email
    if user_model.find_by_email(email):
        return jsonify({'message': 'Email already registered!'}), 409

    # Create user
    hashed = generate_password_hash(password)
    user   = user_model.create_user(name, email, hashed)

    # Auto-create default settings doc for this user
    settings_model.get_or_create_settings(user['_id'])

    token = create_access_token(identity=str(user['_id']))

    return jsonify({
        'message': 'Account created successfully!',
        'token':   token,
        'user':    user_model.to_dict(user)
    }), 201


# ── Sign In ───────────────────────────────────
@auth_bp.route('/signin', methods=['POST'])
def signin():
    data     = request.get_json()
    email    = data.get('email',    '').strip().lower()
    password = data.get('password', '').strip()

    if not email or not password:
        return jsonify({'message': 'Email and password are required!'}), 400

    user = user_model.find_by_email(email)

    if not user:
        return jsonify({'message': 'No account found with this email!'}), 404

    if not check_password_hash(user['password'], password):
        return jsonify({'message': 'Incorrect password!'}), 401

    token = create_access_token(identity=str(user['_id']))

    return jsonify({
        'message': 'Login successful!',
        'token':   token,
        'user':    user_model.to_dict(user)
    }), 200
