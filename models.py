from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    _tablename_ = "users"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    full_name = db.Column(db.String(160), nullable=False)
    email = db.Column(db.String(255), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    uploads = db.relationship("Upload", backref="user", lazy=True)

class Upload(db.Model):
    _tablename_ = "uploads"
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    result_label = db.Column(db.String(16), nullable=False)      # "REAL" or "FAKE"
    confidence = db.Column(db.Float, nullable=False)             # 0..100
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)  # nullable for guests
    guest_session_id = db.Column(db.String(64), nullable=True)                 # for guests
