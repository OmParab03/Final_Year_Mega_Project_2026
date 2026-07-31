# models/user.py
# ─────────────────────────────────────────────
# User table — stores login info + profile data
# ─────────────────────────────────────────────

from extensions import db
from datetime   import datetime

class User(db.Model):
    __tablename__ = 'users'

    # ── Primary Key ───────────────────────────
    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    # ── Auth Fields (already exist) ───────────
    name     = db.Column(db.String(100), nullable=False)
    email    = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    # ── New Profile Fields ────────────────────
    phone    = db.Column(db.String(20),  nullable=True, default=None)
    dob      = db.Column(db.Date,        nullable=True, default=None)
    photo_url = db.Column(db.Text,       nullable=True, default=None)

    # ── Timestamps ────────────────────────────
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # ── Relationships ─────────────────────────
    settings = db.relationship(
        'UserSettings',
        backref='user',
        uselist=False,          # one-to-one
        cascade='all, delete-orphan'
    )
    analyses = db.relationship(
        'SkinAnalysis',
        backref='user',
        lazy=True,
        cascade='all, delete-orphan'
    )

    # ── Serializer ────────────────────────────
    def to_dict(self):
        return {
            'id':        self.id,
            'name':      self.name,
            'email':     self.email,
            'phone':     self.phone    or '',
            'dob':       str(self.dob) if self.dob else '',
            'photo_url': self.photo_url or '',
        }

    def __repr__(self):
        return f'<User {self.email}>'