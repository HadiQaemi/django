from .base import *

DEBUG = False

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "13.40.122.107", "13.40.122.107:8000"]

CORS_ALLOW_ALL_ORIGINS = True

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

INSTALLED_APPS += [
    "django_extensions",
    # "debug_toolbar",
]
# MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE

INTERNAL_IPS = [
    "127.0.0.1",
]

CELERY_TASK_ALWAYS_EAGER = True

REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    "anon": "1000/day",
    "user": "10000/day",
}

AXES_ENABLED = False

LOGGING["loggers"]["django"]["level"] = "DEBUG"
LOGGING["loggers"]["core"]["level"] = "DEBUG"

EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
EMAIL_FILE_PATH = os.path.join(BASE_DIR, "sent_emails")
