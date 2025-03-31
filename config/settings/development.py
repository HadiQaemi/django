"""
Development settings for the REBORN API project.
"""

from .base import *

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True

# Turn off secure settings that might cause issues in development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Additional installed apps for development
INSTALLED_APPS += [
    "django_extensions",
    "debug_toolbar",
]

# Add debug toolbar middleware
MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE

# Debug toolbar settings
INTERNAL_IPS = [
    "127.0.0.1",
]

# Make celery work synchronously in development for easier debugging
CELERY_TASK_ALWAYS_EAGER = True

# Set higher rate limit for testing
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    "anon": "1000/day",
    "user": "10000/day",
}

# Reduce security settings for development
AXES_ENABLED = False

# More verbose logging for development
LOGGING["loggers"]["django"]["level"] = "DEBUG"
LOGGING["loggers"]["core"]["level"] = "DEBUG"

# Add a file-based email backend for development
EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
EMAIL_FILE_PATH = os.path.join(BASE_DIR, "sent_emails")
