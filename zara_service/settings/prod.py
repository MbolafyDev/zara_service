# zara_service/settings/prod.py
from .base import *
import os

DEBUG = False

ALLOWED_HOSTS = ["zaraservice.pythonanywhere.com"]
CSRF_TRUSTED_ORIGINS = ["https://zaraservice.pythonanywhere.com"]

# MySQL (variables d'environnement à définir dans le WSGI ou la config PA)
DB_NAME = os.environ.get("DB_NAME", "zaraservice$default")  # adapte si différent
DB_USER = os.environ.get("DB_USER", "zaraservice")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "Zara@586#")
DB_HOST = os.environ.get("DB_HOST", "zaraservice.mysql.pythonanywhere-services.com")
DB_PORT = os.environ.get("DB_PORT", "3306")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": DB_NAME,
        "USER": DB_USER,
        "PASSWORD": DB_PASSWORD,
        "HOST": DB_HOST,
        "PORT": DB_PORT,
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Sécurité (HTTPS sur PythonAnywhere)
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
# Active HSTS quand tu es prêt
SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# Logging un peu plus strict
LOGGING["root"]["level"] = "WARNING"
LOGGING["loggers"] = {
    "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": True},
}