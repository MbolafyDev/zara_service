# zara_service/settings/dev.py
from .base import *
import os

DEBUG = True

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
CSRF_TRUSTED_ORIGINS = ["http://127.0.0.1", "http://localhost"]

# Base de données locale : SQLite (simple)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Emails en console pour les tests
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
