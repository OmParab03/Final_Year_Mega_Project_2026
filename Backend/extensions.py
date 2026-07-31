# extensions.py
# ─────────────────────────────────────────────
# All Flask extensions are created here ONCE.
# Import from here everywhere else.
# This avoids circular imports.
# ─────────────────────────────────────────────

from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS

db  = SQLAlchemy()
jwt = JWTManager()
cors = CORS()