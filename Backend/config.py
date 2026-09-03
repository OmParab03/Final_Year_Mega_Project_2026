# config.py
# ─────────────────────────────────────────────
# All configuration in one place.
# Change values here only — nowhere else.
# ─────────────────────────────────────────────

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ── Database (MongoDB) ────────────────────
    MONGODB_URI     = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017')
    MONGODB_DB_NAME = os.environ.get('MONGODB_DB_NAME', 'toxiscan')

    # ── JWT ───────────────────────────────────
    JWT_SECRET_KEY = os.environ.get(
        'JWT_SECRET_KEY',
        'toxiscan-secret-key-change-in-production'
    )

    # ── File Upload ───────────────────────────
    UPLOAD_FOLDER        = os.path.join(os.getcwd(), 'uploads', 'profiles')
    SKIN_SCAN_FOLDER     = os.path.join(os.getcwd(), 'uploads', 'skin_scans')
    MAX_CONTENT_LENGTH   = 5 * 1024 * 1024          # 5 MB max upload
    ALLOWED_EXTENSIONS   = {'jpg', 'jpeg', 'png', 'webp'}

    # ── Hugging Face Spaces (skin analysis) ───
    HF_SKIN_CLASSIFIER_SPACE = os.environ.get(
        'HF_SKIN_CLASSIFIER_SPACE', 'Omkarrrrr/SkinClassifierSpace'
    )
    HF_SKIN_CONDITION_SPACE = os.environ.get(
        'HF_SKIN_CONDITION_SPACE', 'Omkarrrrr/yolo'
    )
    # Optional but strongly recommended: without it, calls share the public
    # anonymous-usage quota (easy to exhaust) instead of the token's own quota.
    HF_TOKEN = os.environ.get('HF_TOKEN', '')
