"""Production settings (Vercel + Neon)."""

from config.settings.base import *  # noqa: F401,F403
from config.settings.base import env

DEBUG = False

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[".vercel.app"])

CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=["https://*.vercel.app"])

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Serverless has no collectstatic step, so use non-manifest static storage.
# The API is JSON-only; static assets only back the admin and API docs pages.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

# Tokens are signed with SECRET_KEY, so production refuses to start with the public default or a short key.
if SECRET_KEY.startswith("django-insecure") or len(SECRET_KEY) < 40:  # noqa: F405
    from django.core.exceptions import ImproperlyConfigured

    raise ImproperlyConfigured("Set SECRET_KEY to a long random value in production.")

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"
