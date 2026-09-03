# models/user_settings.py
# ─────────────────────────────────────────────
# user_settings collection — one doc per user
# ─────────────────────────────────────────────

from extensions import db
from datetime   import datetime
from bson       import ObjectId

_DEFAULTS = {
    'email_notifications':   True,
    'save_analysis_history': True,
    'dark_mode':             False,
}


def get_or_create_settings(user_id):
    oid = ObjectId(user_id)
    settings = db.user_settings.find_one({'user_id': oid})
    if settings:
        return settings

    doc = {'user_id': oid, **_DEFAULTS, 'updated_at': datetime.utcnow()}
    db.user_settings.insert_one(doc)
    return doc


def update_settings(user_id, updates: dict):
    """Assumes get_or_create_settings() has already been called for this user."""
    oid = ObjectId(user_id)
    patch = {'updated_at': datetime.utcnow()}

    if 'emailNotifications' in updates:
        patch['email_notifications'] = bool(updates['emailNotifications'])
    if 'saveAnalysisHistory' in updates:
        patch['save_analysis_history'] = bool(updates['saveAnalysisHistory'])
    if 'darkMode' in updates:
        patch['dark_mode'] = bool(updates['darkMode'])

    db.user_settings.update_one({'user_id': oid}, {'$set': patch})
    return db.user_settings.find_one({'user_id': oid})


def to_dict(settings):
    return {
        'emailNotifications':  settings.get('email_notifications', True),
        'saveAnalysisHistory': settings.get('save_analysis_history', True),
        'darkMode':            settings.get('dark_mode', False),
    }
