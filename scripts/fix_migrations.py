#!/usr/bin/env python
"""
Скрипт для відновлення міграцій
"""
import os
import sys

# Додаємо шлях до проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Інструкції
print("""
=================================================
ІНСТРУКЦІЇ ДЛЯ ВИПРАВЛЕННЯ МІГРАЦІЙ:
=================================================

1. ЗУПИНІТЬ сервер Django (Ctrl+C)

2. Виконайте команди в цій послідовності:

# Видаліть файли старих міграцій (якщо вони є в БД):
python manage.py migrate orders 0001 --fake

# Застосуйте нові міграції:
python manage.py migrate orders

3. Якщо виникає помилка про відсутність таблиці, виконайте:
python manage.py migrate --fake-initial

4. Перевірте статус міграцій:
python manage.py showmigrations orders

5. Запустіть сервер:
python manage.py runserver

=================================================
ЯКЩО ПОМИЛКИ ПРОДОВЖУЮТЬСЯ:
=================================================

1. Підключіться до PostgreSQL:
psql -U danil -d laska_db

2. Виконайте SQL команди для додавання полів вручну:

ALTER TABLE orders_order 
ADD COLUMN IF NOT EXISTS full_name VARCHAR(255) DEFAULT '',
ADD COLUMN IF NOT EXISTS email VARCHAR(254) DEFAULT '', 
ADD COLUMN IF NOT EXISTS sale_type VARCHAR(10) DEFAULT '1',
ADD COLUMN IF NOT EXISTS delivery_condition VARCHAR(50) DEFAULT 'nova_poshta',
ADD COLUMN IF NOT EXISTS delivery_address TEXT DEFAULT '',
ADD COLUMN IF NOT EXISTS comment TEXT,
ADD COLUMN IF NOT EXISTS order_number VARCHAR(50) UNIQUE,
ADD COLUMN IF NOT EXISTS exported BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS exported_at TIMESTAMP;

3. Позначте міграції як виконані:
python manage.py migrate orders --fake

=================================================
""")
