from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    full_name = db.Column(db.String(160), nullable=False)
    email = db.Column(db.String(255), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    verification_code = db.Column(db.String(6), nullable=True)
    verification_code_expires = db.Column(db.DateTime, nullable=True)
    reset_token = db.Column(db.String(64), nullable=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    uploads = db.relationship("Upload", backref="user", lazy=True)

    def generate_verification_code(self):
        """Generate a 6-digit verification code valid for 15 minutes"""
        import random
        self.verification_code = f"{random.randint(100000, 999999)}"
        self.verification_code_expires = datetime.utcnow() + timedelta(minutes=15)
        return self.verification_code

    def generate_reset_token(self):
        """Generate a reset token valid for 1 hour"""
        import secrets
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        return self.reset_token

    def is_verification_code_valid(self, code):
        """Check if verification code is valid and not expired"""
        if not self.verification_code or not self.verification_code_expires:
            return False
        if datetime.utcnow() > self.verification_code_expires:
            return False
        return self.verification_code == code

    def is_reset_token_valid(self, token):
        """Check if reset token is valid and not expired"""
        if not self.reset_token or not self.reset_token_expires:
            return False
        if datetime.utcnow() > self.reset_token_expires:
            return False
        return self.reset_token == token

class Upload(db.Model):
    __tablename__ = "uploads"
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    result_label = db.Column(db.String(16), nullable=False)      # "REAL" or "FAKE"
    confidence = db.Column(db.Float, nullable=False)             # 0..100
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)  # nullable for guests
    guest_session_id = db.Column(db.String(64), nullable=True)                 # for guests
