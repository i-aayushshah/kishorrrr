import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-.env")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///unmask_ai.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

    # Email configuration
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "aayushshah983@gmail.com")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "svlhlqbjmcqxmfly")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "aayushshah983@gmail.com")
