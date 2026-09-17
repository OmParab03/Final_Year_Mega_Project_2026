# models/product_scan.py
# ─────────────────────────────────────────────
# scan_history collection — one doc per product scan
# ─────────────────────────────────────────────

from extensions import db
from datetime   import datetime
from bson       import ObjectId


def create_scan(user_id, doc: dict):
    record = {
        'user_id':    ObjectId(user_id),
        'created_at': datetime.utcnow(),
        **doc,
    }
    result = db.scan_history.insert_one(record)
    record['_id'] = result.inserted_id
    return record


def get_history(user_id, page=1, per_page=10):
    oid   = ObjectId(user_id)
    query = {'user_id': oid}

    total = db.scan_history.count_documents(query)
    skip  = max(page - 1, 0) * per_page

    cursor = (
        db.scan_history.find(query)
        .sort('created_at', -1)
        .skip(skip)
        .limit(per_page)
    )
    items = list(cursor)
    pages = (total + per_page - 1) // per_page if per_page else 1
    return items, total, pages


def delete_scan(scan_id, user_id):
    try:
        oid = ObjectId(scan_id)
    except Exception:
        return False
    result = db.scan_history.delete_one({'_id': oid, 'user_id': ObjectId(user_id)})
    return result.deleted_count > 0


def to_dict(record):
    return {
        'id':                    str(record['_id']),
        'userId':                str(record['user_id']),
        'imageUrl':              record.get('image_url', ''),
        'score':                 record.get('score', 0),
        'score_label':           record.get('score_label', ''),
        'score_summary':         record.get('score_summary', ''),
        'harmful_ingredients':   record.get('harmful_ingredients', []),
        'beneficial_ingredients':record.get('beneficial_ingredients', []),
        'ai_summary':            record.get('ai_summary', ''),
        'potential_issues':      record.get('potential_issues', {}),
        'recommended_alternatives': record.get('recommended_alternatives', []),
        # Legacy
        'ingredients':           record.get('ingredients', []),
        'analysis':              record.get('analysis', []),
        'createdAt':             record['created_at'].isoformat(),
    }
