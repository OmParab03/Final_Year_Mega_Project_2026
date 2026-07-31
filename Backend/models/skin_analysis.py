# models/skin_analysis.py
# ─────────────────────────────────────────────
# Stores each skin scan result
# Your colleague will fill in the AI logic
# ─────────────────────────────────────────────

from extensions import db
from datetime   import datetime
import json

class SkinAnalysis(db.Model):
    __tablename__ = 'skin_analyses'

    # ── Primary Key ───────────────────────────
    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    # ── Foreign Key → users ───────────────────
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False
    )

    # ── Analysis Data ─────────────────────────
    image_url    = db.Column(db.Text,    nullable=False)
    result       = db.Column(db.Text,    nullable=True)
    severity     = db.Column(
        db.Enum('low', 'medium', 'high'),
        default='low',
        nullable=False
    )

    # Store AI response as JSON string
    ai_response  = db.Column(db.Text,    nullable=True)

    # ── Timestamp ─────────────────────────────
    created_at   = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # ── Serializer ────────────────────────────
    def to_dict(self):
        ai_data = None
        if self.ai_response:
            try:
                ai_data = json.loads(self.ai_response)
            except Exception:
                ai_data = {}

        return {
            'id':         self.id,
            'userId':     self.user_id,
            'imageUrl':   self.image_url,
            'result':     self.result,
            'severity':   self.severity,
            'aiResponse': ai_data,
            'createdAt':  self.created_at.isoformat(),
        }

    def __repr__(self):
        return f'<SkinAnalysis id={self.id} user={self.user_id}>'