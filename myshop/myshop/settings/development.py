from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Database
# myproject/settings.py

# Database - PostgreQSL for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Email - use console backend for development
# EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Cache - local memory for development
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Sessions en caché (mucho más rápido que DB)
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
