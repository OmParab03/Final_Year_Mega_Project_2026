# models/skin_analysis.py
# ─────────────────────────────────────────────
# skin_analyses collection — one doc per scan
# ─────────────────────────────────────────────

from extensions import db
from datetime   import datetime
from bson       import ObjectId


def create_analysis(user_id, doc: dict):
    record = {
        'user_id':    ObjectId(user_id),
        'created_at': datetime.utcnow(),
        **doc,
    }
    result = db.skin_analyses.insert_one(record)
    record['_id'] = result.inserted_id
    return record


def get_history(user_id, page=1, per_page=10):
    oid   = ObjectId(user_id)
    query = {'user_id': oid}

    total = db.skin_analyses.count_documents(query)
    skip  = max(page - 1, 0) * per_page

    cursor = (
        db.skin_analyses.find(query)
        .sort('created_at', -1)
        .skip(skip)
        .limit(per_page)
    )
    items = list(cursor)
    pages = (total + per_page - 1) // per_page if per_page else 1
    return items, total, pages


def delete_analysis(analysis_id, user_id):
    try:
        oid = ObjectId(analysis_id)
    except Exception:
        return False
    result = db.skin_analyses.delete_one({'_id': oid, 'user_id': ObjectId(user_id)})
    return result.deleted_count > 0


def to_dict(record):
    conditions = record.get('conditions') or []
    condition_summary = ', '.join(c['label'] for c in conditions) if conditions else 'No issues detected'

    return {
        'id':         str(record['_id']),
        'userId':     str(record['user_id']),
        'imageUrl':   record.get('image_url', ''),
        'skinType':   record.get('skin_type', ''),
        'conditions': conditions,
        'result':     f"{record.get('skin_type', '')} • {condition_summary}",
        'severity':   record.get('severity', 'low'),
        'score':      record.get('score', 0),
        'aiResponse': {
            'classifier': record.get('raw_classifier_response'),
            'yolo':       record.get('raw_yolo_response'),
        },
        'createdAt':  record['created_at'].isoformat(),
    }
