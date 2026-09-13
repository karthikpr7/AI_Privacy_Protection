import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = "dev-secret-key-change-in-production"
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "storage", "uploads")
    PROCESSED_FOLDER = os.path.join(BASE_DIR, "storage", "processed")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB upload limit
    ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}