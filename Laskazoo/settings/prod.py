from .settings import *

import os

DEBUG = False


SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')


ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',')


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
    }
}


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = os.getenv('EMAIL_PORT')
EMAIL_HOST_USER = os.getenv('EMAIL_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_PASSWORD')
EMAIL_USE_TLS = True


SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

LOGGING = {}
# LOGGING = {
#     'version': 1,
#     'handlers': {
#         'file': {
#             'class': 'logging.FileHandler',
#             'filename': BASE_DIR / 'logs' / 'app.log',
#         },
#     },
#     'root': {
#         'handlers': ['file'],
#         'level': 'WARNING',
#     },
# }
