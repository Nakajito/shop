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

# Session via cache with DB fallback — plain "cache" backend raises
# SessionInterrupted if anything calls cache.clear() mid-request (e.g. the
# post_save cache-invalidation signals in shop/signals.py) since it wipes the
# in-flight request's own session out of the same LocMemCache store.
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
