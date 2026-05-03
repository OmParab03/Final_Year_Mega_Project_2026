from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# ================== CONFIGURATION ==================

# MySQL Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:manager@localhost:3306/skincare_user_profiles_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your-secret-key-here-change-in-production'

# Initialize Extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:4200"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email
        }

# Create Database
with app.app_context():
    db.create_all()
    print("✅ MySQL Database connected and tables created!")

# Home Route
@app.route('/')
def home():
    return "Your Flask app is running with MySQL 🚀"

# ================== AUTH ROUTES ==================

# Sign Up Route
@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not name or not email or not password:
        return jsonify({'message': 'All fields are required!'}), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'message': 'Email already exists!'}), 409

    hashed_password = generate_password_hash(password)
    new_user = User(name=name, email=email, password=hashed_password)
    
    db.session.add(new_user)
    db.session.commit()

    access_token = create_access_token(identity=str(new_user.id))

    return jsonify({
        'message': 'Account created successfully!',
        'token': access_token,
        'user': new_user.to_dict()
    }), 201

# Sign In Route
@app.route('/api/signin', methods=['POST'])
def signin():
    data = request.get_json()

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Email and password are required!'}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'message': 'User not found!'}), 404

    if not check_password_hash(user.password, password):
        return jsonify({'message': 'Invalid password!'}), 401

    access_token = create_access_token(identity=str(user.id))

    return jsonify({
        'message': 'Login successful!',
        'token': access_token,
        'user': user.to_dict()
    }), 200

# Profile Route
@app.route('/api/profile', methods=['GET'])
@jwt_required()
def profile():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))

    if not user:
        return jsonify({'message': 'User not found!'}), 404

    return jsonify(user.to_dict()), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)