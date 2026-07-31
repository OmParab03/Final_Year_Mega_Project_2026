# config.py
# ─────────────────────────────────────────────
# All configuration in one place.
# Change values here only — nowhere else.
# ─────────────────────────────────────────────

import os

class Config:
    # ── Database ──────────────────────────────
    DB_USER     = 'root'
    DB_PASSWORD = 'manager'
    DB_HOST     = 'localhost'
    DB_PORT     = '3306'
    DB_NAME     = 'toxiscan'

    SQLALCHEMY_DATABASE_URI = (
        f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}'
        f'@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── JWT ───────────────────────────────────
    JWT_SECRET_KEY = 'toxiscan-secret-key-change-in-production'

    # ── File Upload ───────────────────────────
    UPLOAD_FOLDER        = os.path.join(os.getcwd(), 'uploads', 'profiles')
    MAX_CONTENT_LENGTH   = 5 * 1024 * 1024          # 5 MB max upload
    ALLOWED_EXTENSIONS   = {'jpg', 'jpeg', 'png', 'webp'}