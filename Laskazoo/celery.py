import os
from celery import Celery
from celery.schedules import crontab

# Встановлюємо налаштування Django для Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Laskazoo.settings.local')

app = Celery('Laskazoo')

# Використовуємо налаштування з Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматично знаходимо та реєструємо tasks
app.autodiscover_tasks()

# Налаштування періодичних завдань
app.conf.beat_schedule = {
    'export-orders-every-15-minutes': {
        'task': 'apps.orders.tasks.export_orders_task',
        'schedule': crontab(minute='*/15'),  # Кожні 15 хвилин
    },
}

# Для тестування можна використовувати:
# 'schedule': 60.0,  # Кожні 60 секунд
