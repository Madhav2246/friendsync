import os
from dotenv import load_dotenv

load_dotenv()

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-secret')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(base_dir, 'instance', 'friends.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── Sessions: filesystem instead of Redis ──────────────────────────────
    SESSION_TYPE              = 'filesystem'
    SESSION_FILE_DIR          = os.path.join(base_dir, 'flask_sessions')
    SESSION_PERMANENT         = True
    SESSION_USE_SIGNER        = True
    PERMANENT_SESSION_LIFETIME = 604800  # 7 days

    # ── Cache: in-memory instead of Redis ─────────────────────────────────
    CACHE_TYPE            = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300

    # ── Rate limiter: in-memory instead of Redis ───────────────────────────
    RATELIMIT_STORAGE_URL = 'memory://'

    # ── Mail ───────────────────────────────────────────────────────────────
    MAIL_SERVER   = 'smtp.gmail.com'
    MAIL_PORT     = 587
    MAIL_USE_TLS  = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')

    # ── Uploads ────────────────────────────────────────────────────────────
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}