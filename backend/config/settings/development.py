"""
Django development settings for ESG Platform.
"""
import os

from .base import *  # noqa: F401, F403

# --------------------------------------------------------------------------
# Debug
# --------------------------------------------------------------------------
DEBUG = True

# --------------------------------------------------------------------------
# Allowed hosts
# --------------------------------------------------------------------------
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0').split(',')

# --------------------------------------------------------------------------
# CORS
# --------------------------------------------------------------------------
_cors_origins = os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173')
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in _cors_origins.split(',') if origin.strip()]
CORS_ALLOW_CREDENTIALS = True
