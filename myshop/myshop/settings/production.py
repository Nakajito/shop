import dj_database_url
from decouple import config

from .base import *  # noqa: F401, F403

DEBUG = False

# No default: fail closed rather than risk a predictable key reaching prod.
SECRET_KEY = config("SECRET_KEY")

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS", cast=lambda v: [s.strip() for s in v.split(",")]
)

# Database - PostgreQSL for development
DATABASES = {
    "default": dj_database_url.config(
        default=config("DATABASE_URL"),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Cache - Redis for production
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": config("REDIS_CACHE_URL", default="redis://localhost:6379/2"),
    }
}

# Session via cache with DB fallback (prevents session loss if Redis restarts)
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

# Security
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", cast=Csv())
SESSION_COOKIE_SAMESITE = "Lax"

# WhiteNoise for static files
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")  # noqa: F405
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Media files — persistent volume mount in Coolify
MEDIA_ROOT = BASE_DIR.parent / "media"  # /app/media

# Sentry
SENTRY_DSN = config("SENTRY_DSN", default="")
if SENTRY_DSN:
    import sentry_sdk

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=0.1,
        send_default_pii=False,
    )

CELERY_BROKER_URL = config("REDIS_CACHE_URL", default="redis://redis:6379/0")
CELERY_RESULT_BACKEND = config("REDIS_CACHE_URL", default="redis://redis:6379/0")

ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"

# Transactional email via Resend
INSTALLED_APPS.append("anymail")  # noqa: F405
EMAIL_BACKEND = "anymail.backends.resend.EmailBackend"
ANYMAIL = {"RESEND_API_KEY": config("RESEND_API_KEY")}
