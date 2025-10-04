# =====================================================
# ПРИКЛАД НАЛАШТУВАНЬ ДЛЯ settings.py
# Додай ці рядки у файл Laskazoo/settings.py
# =====================================================

import os
from pathlib import Path
from dotenv import load_dotenv

# Завантажуємо змінні з .env файлу
load_dotenv()

# =====================================================
# PORTMONE НАЛАШТУВАННЯ
# =====================================================

# Дані для інтеграції з Portmone
PORTMONE_PAYEE_ID = os.getenv('PORTMONE_PAYEE_ID', '')
PORTMONE_LOGIN = os.getenv('PORTMONE_LOGIN', '')
PORTMONE_PASSWORD = os.getenv('PORTMONE_PASSWORD', '')

# URL для callback від Portmone
PORTMONE_CALLBACK_URL = os.getenv('SITE_URL', 'http://localhost:8000') + '/orders/payment/callback/'

# Перевірка підпису від Portmone (рекомендовано на продакшені)
PORTMONE_SIGNATURE_VERIFICATION = os.getenv('DEBUG', 'True') == 'False'

# =====================================================
# GOOGLE PAY НАЛАШТУВАННЯ
# =====================================================

GOOGLE_PAY_MERCHANT_ID = os.getenv('GOOGLE_PAY_MERCHANT_ID', '')
GOOGLE_PAY_ENVIRONMENT = os.getenv('GOOGLE_PAY_ENVIRONMENT', 'TEST')  # TEST або PRODUCTION

# =====================================================
# EMAIL НАЛАШТУВАННЯ
# =====================================================

EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')

DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@laskazoo.com')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@laskazoo.com')

# =====================================================
# БЕЗПЕКА (для продакшену)
# =====================================================

# HTTPS налаштування
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False') == 'True'
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False') == 'True'
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', 'False') == 'True'

# SameSite cookies
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# =====================================================
# ЛОГУВАННЯ ТРАНЗАКЦІЙ
# =====================================================

PAYMENT_LOGGING_ENABLED = os.getenv('PAYMENT_LOGGING_ENABLED', 'True') == 'True'

# Логування в файл
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'payment.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'apps.orders.payment_views': {
            'handlers': ['file', 'console'],
            'level': os.getenv('LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
    },
}

# =====================================================
# ДОДАТКОВІ НАЛАШТУВАННЯ
# =====================================================

# URL сайту (для callback та email посилань)
SITE_URL = os.getenv('SITE_URL', 'http://localhost:8000')

# Часовий пояс
TIME_ZONE = os.getenv('TIME_ZONE', 'Europe/Kiev')

# Мова
LANGUAGE_CODE = os.getenv('LANGUAGE_CODE', 'uk')

# =====================================================
# ВСТАНОВЛЕННЯ PYTHON-DOTENV
# =====================================================
# Якщо у тебе ще немає python-dotenv, встанови:
#
#   pip install python-dotenv
#
# І додай у requirements.txt:
#   python-dotenv==1.0.0

# =====================================================
# ПЕРЕВІРКА НАЛАШТУВАНЬ
# =====================================================
# Для перевірки що все працює, запусти в терміналі:
#
#   python manage.py shell
#   >>> from django.conf import settings
#   >>> print(settings.PORTMONE_PAYEE_ID)
#   >>> print(settings.EMAIL_HOST)

# =====================================================
# ВАЖЛИВО ДЛЯ ПРОДАКШЕНУ
# =====================================================
# 1. Створи файл .env на сервері з реальними даними
# 2. Додай .env у .gitignore (щоб не потрапив у git)
# 3. Встанови DEBUG=False
# 4. Використовуй HTTPS (SECURE_SSL_REDIRECT=True)
# 5. Налаштуй firewall для захисту callback URL
