# routes/auth_routes.py
# ─────────────────────────────────────────────
# POST /api/signup
# POST /api/signin
# ─────────────────────────────────────────────

from flask               import Blueprint, request, jsonify
from flask_jwt_extended  import create_access_token
from werkzeug.security   import generate_password_hash, check_password_hash
from extensions          import db
from models.user         import User
from models.user_settings import UserSettings

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
    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email already registered!'}), 409

    # Create user
    hashed = generate_password_hash(password)
    user   = User(name=name, email=email, password=hashed)
    db.session.add(user)
    db.session.flush()          # get user.id before commit

    # Auto-create default settings row for this user
    settings = UserSettings(user_id=user.id)
    db.session.add(settings)
    db.session.commit()

    token = create_access_token(identity=str(user.id))

    return jsonify({
        'message': 'Account created successfully!',
        'token':   token,
        'user':    user.to_dict()
    }), 201


# ── Sign In ───────────────────────────────────
@auth_bp.route('/signin', methods=['POST'])
def signin():
    data     = request.get_json()
    email    = data.get('email',    '').strip().lower()
    password = data.get('password', '').strip()

    if not email or not password:
        return jsonify({'message': 'Email and password are required!'}), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({'message': 'No account found with this email!'}), 404

    if not check_password_hash(user.password, password):
        return jsonify({'message': 'Incorrect password!'}), 401

    token = create_access_token(identity=str(user.id))

    return jsonify({
        'message': 'Login successful!',
        'token':   token,
        'user':    user.to_dict()
    }), 200