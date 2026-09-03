# extensions.py
# ─────────────────────────────────────────────
# All Flask extensions are created here ONCE.
# Import from here everywhere else.
# This avoids circular imports.
# ─────────────────────────────────────────────

from flask_jwt_extended import JWTManager
from flask_cors         import CORS
from pymongo             import MongoClient

jwt  = JWTManager()
cors = CORS()

# Set by init_mongo() once the app config is available.
mongo_client = None
db           = None


def init_mongo(app):
    """Connect to MongoDB and ensure the indexes this app relies on exist."""
    global mongo_client, db

    mongo_client = MongoClient(app.config['MONGODB_URI'])
    db = mongo_client[app.config['MONGODB_DB_NAME']]

    db.users.create_index('email', unique=True)
    db.user_settings.create_index('user_id', unique=True)
    db.skin_analyses.create_index('user_id')

    return db
