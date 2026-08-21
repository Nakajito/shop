from .base import *  # noqa: F401, F403

DEBUG = False

SECRET_KEY = "test-secret-key-not-for-production"  # noqa: S105

ALLOWED_HOSTS = ["localhost", "testserver"]

# django-axes requires a real request in authenticate() (see accounts/forms.py
# CustomUserLoginForm); Django's test Client.login() helper calls
# authenticate() without one, which would 500 every test that uses it. Axes'
# own lockout behavior gets dedicated coverage via @override_settings in
# accounts/tests.py, which re-enables it and drives the real login view.
AXES_ENABLED = False

# In-memory SQLite for fast tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Faster password hashing for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Dummy cache
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# Celery runs tasks synchronously in tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Console email backend
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Disable logging noise during tests
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "handlers": ["null"],
    },
}
