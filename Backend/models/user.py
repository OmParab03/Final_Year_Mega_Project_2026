# models/user.py
# ─────────────────────────────────────────────
# users collection — login info + profile data
# ─────────────────────────────────────────────

from extensions import db
from datetime   import datetime
from bson       import ObjectId


def create_user(name, email, password_hash):
    now = datetime.utcnow()
    result = db.users.insert_one({
        'name':       name,
        'email':      email,
        'password':   password_hash,
        'phone':      None,
        'dob':        None,
        'photo_url':  None,
        'created_at': now,
        'updated_at': now,
    })
    return find_by_id(result.inserted_id)


def find_by_email(email):
    return db.users.find_one({'email': email})


def find_by_id(user_id):
    try:
        oid = user_id if isinstance(user_id, ObjectId) else ObjectId(user_id)
    except Exception:
        return None
    return db.users.find_one({'_id': oid})


def update_user(user_id, updates: dict):
    updates = {**updates, 'updated_at': datetime.utcnow()}
    db.users.update_one({'_id': ObjectId(user_id)}, {'$set': updates})
    return find_by_id(user_id)


def to_dict(user):
    if not user:
        return None
    dob = user.get('dob')
    return {
        'id':        str(user['_id']),
        'name':      user.get('name', ''),
        'email':     user.get('email', ''),
        'phone':     user.get('phone') or '',
        'dob':       dob.strftime('%Y-%m-%d') if dob else '',
        'photo_url': user.get('photo_url') or '',
    }
