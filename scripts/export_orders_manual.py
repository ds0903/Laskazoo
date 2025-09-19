#!/usr/bin/env python
"""
Ручний запуск експорту замовлень для тестування
Використання: python scripts/export_orders_manual.py
"""

import os
import sys
import django

# Додаємо шлях до проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Налаштовуємо Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Laskazoo.settings.settings')
django.setup()

# Тепер можемо викликати команду
from django.core.management import call_command

if __name__ == '__main__':
    print("Запуск експорту замовлень...")
    try:
        call_command('export_orders', '--force')
        print("Експорт завершено успішно!")
    except Exception as e:
        print(f"Помилка експорту: {e}")
