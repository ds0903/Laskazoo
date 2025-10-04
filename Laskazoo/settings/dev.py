from .settings import *
import os

DEBUG = True
from pathlib import Path

# Якщо BASE_DIR не імпортовано, то:
BASE_DIR = Path(__file__).resolve().parent.parent

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


SECRET_KEY = os.getenv('SECRET_KEY')

ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '*').split(',')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': os.getenv('PG_HOST', '127.0.0.1'),
        'PORT': os.getenv('PG_PORT', '5432'),
        'NAME': os.getenv('PG_NAME', 'laska_db'),
        'USER': os.getenv('PG_USER', 'danil'),
        'PASSWORD': os.getenv('PG_PASS', ''),
        'CONN_MAX_AGE': 60,
    }
}

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0

LOGGING = {}
