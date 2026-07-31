# models/user_settings.py
# ─────────────────────────────────────────────
# One row per user — stores all toggle settings
# ─────────────────────────────────────────────

from extensions import db
from datetime   import datetime

class UserSettings(db.Model):
    __tablename__ = 'user_settings'

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
        nullable=False,
        unique=True             # one row per user
    )

    # ── Settings Fields ───────────────────────
    email_notifications  = db.Column(db.Boolean, default=True,  nullable=False)
    save_analysis_history = db.Column(db.Boolean, default=True,  nullable=False)
    dark_mode            = db.Column(db.Boolean, default=False, nullable=False)

    # ── Timestamps ────────────────────────────
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # ── Serializer ────────────────────────────
    def to_dict(self):
        return {
            'emailNotifications':  self.email_notifications,
            'saveAnalysisHistory': self.save_analysis_history,
            'darkMode':            self.dark_mode,
        }

    def __repr__(self):
        return f'<UserSettings user_id={self.user_id}>'