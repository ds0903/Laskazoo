from .settings import *

DEBUG = True

# Секретний ключ для локальної роботи, але не в репозиторії
SECRET_KEY = 'django-insecure-…локальний-ключ…'

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# База даних: SQLite для швидкого старту
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Пошта в консоль
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Логи — повний дебаг
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}
