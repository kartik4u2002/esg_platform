"""
Django production settings for ESG Platform.
"""
import os

from .base import *  # noqa: F401, F403

# --------------------------------------------------------------------------
# Debug
# --------------------------------------------------------------------------
DEBUG = False

# --------------------------------------------------------------------------
# Security
# --------------------------------------------------------------------------
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# --------------------------------------------------------------------------
# Allowed hosts (must be set via env in production)
# --------------------------------------------------------------------------
ALLOWED_HOSTS = [host.strip() for host in os.environ.get('ALLOWED_HOSTS', '').split(',') if host.strip()]
# Allow local and internal Docker network hostnames
ALLOWED_HOSTS += ['web', 'localhost', '127.0.0.1']

# --------------------------------------------------------------------------
# CORS
# --------------------------------------------------------------------------
_cors_origins = os.environ.get('CORS_ALLOWED_ORIGINS', '')
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in _cors_origins.split(',') if origin.strip()]
CORS_ALLOW_CREDENTIALS = True
