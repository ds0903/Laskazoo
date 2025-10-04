#!/usr/bin/env python
"""
Автоматичне виправлення таблиці orders_order
"""
import os
import sys
import django

# Додаємо шлях до проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Налаштовуємо Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Laskazoo.settings.settings')
django.setup()

from django.db import connection

def fix_orders_table():
    """Додаємо відсутні поля в таблицю orders_order"""
    
    print("Додаємо нові поля в таблицю orders_order...")
    
    with connection.cursor() as cursor:
        # SQL команди для додавання полів
        sql_commands = [
            "ALTER TABLE orders_order ADD COLUMN IF NOT EXISTS full_name VARCHAR(255) DEFAULT ''",
            "ALTER TABLE orders_order ADD COLUMN IF NOT EXISTS email VARCHAR(254) DEFAULT ''",
            "ALTER TABLE orders_order ADD COLUMN IF NOT EXISTS sale_type VARCHAR(10) DEFAULT '1'",
            "ALTER TABLE orders_order ADD COLUMN IF NOT EXISTS delivery_condition VARCHAR(50) DEFAULT 'nova_poshta'",
            "ALTER TABLE orders_order ADD COLUMN IF NOT EXISTS delivery_address TEXT DEFAULT ''",
            "ALTER TABLE orders_order ADD COLUMN IF NOT EXISTS comment TEXT",
            "ALTER TABLE orders_order ADD COLUMN IF NOT EXISTS order_number VARCHAR(50)",
            "ALTER TABLE orders_order ADD COLUMN IF NOT EXISTS exported BOOLEAN DEFAULT false",
            "ALTER TABLE orders_order ADD COLUMN IF NOT EXISTS exported_at TIMESTAMP",
        ]
        
        for sql in sql_commands:
            try:
                cursor.execute(sql)
                print(f"✓ Виконано: {sql[:50]}...")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"• Поле вже існує: {sql[:50]}...")
                else:
                    print(f"✗ Помилка: {e}")
        
        # Оновлюємо дані для існуючих записів
        print("\nОновлюємо існуючі записи...")
        
        update_commands = [
            "UPDATE orders_order SET full_name = COALESCE(first_name, 'Не вказано') WHERE full_name = '' OR full_name IS NULL",
            "UPDATE orders_order SET email = 'no-email@example.com' WHERE email = '' OR email IS NULL",
            "UPDATE orders_order SET delivery_address = COALESCE(city, 'Адреса не вказана') WHERE delivery_address = '' OR delivery_address IS NULL",
        ]
        
        for sql in update_commands:
            try:
                cursor.execute(sql)
                print(f"✓ Оновлено: {sql[:50]}...")
            except Exception as e:
                print(f"• Пропущено: {e}")
        
        # Перевіряємо структуру таблиці
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'orders_order'
            ORDER BY ordinal_position
        """)
        
        print("\n=== Структура таблиці orders_order ===")
        for column in cursor.fetchall():
            print(f"  {column[0]}: {column[1]}")
    
    print("\n✓ Таблиця виправлена!")
    print("\nТепер виконайте:")
    print("  python manage.py migrate orders --fake")
    print("  python manage.py runserver")

if __name__ == '__main__':
    try:
        fix_orders_table()
    except Exception as e:
        print(f"\n✗ Помилка: {e}")
        print("\nСпробуйте виконати SQL команди вручну через pgAdmin або psql")
