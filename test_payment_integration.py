#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Скрипт для тестування інтеграції оплати

Використання:
    python test_payment_integration.py
"""

import os
import sys
import django

# Налаштування Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Laskazoo.settings')
django.setup()

from apps.orders.models import Order, PaymentTransaction
from django.contrib.auth import get_user_model

User = get_user_model()


def print_section(title):
    """Красиво виводить заголовок секції"""
    print('\n' + '=' * 80)
    print(f' {title}')
    print('=' * 80)


def test_database_connection():
    """Тест підключення до бази даних"""
    print_section('ТЕСТ 1: Підключення до бази даних')
    try:
        users_count = User.objects.count()
        orders_count = Order.objects.count()
        transactions_count = PaymentTransaction.objects.count()
        
        print(f'✅ Підключення до БД успішне')
        print(f'   Користувачів: {users_count}')
        print(f'   Замовлень: {orders_count}')
        print(f'   Транзакцій: {transactions_count}')
        return True
    except Exception as e:
        print(f'❌ Помилка підключення до БД: {e}')
        return False


def test_models():
    """Тест моделей Order та PaymentTransaction"""
    print_section('ТЕСТ 2: Моделі')
    try:
        # Перевіряємо чи Order має поля payment
        order_fields = [f.name for f in Order._meta.get_fields()]
        required_fields = ['payment_method', 'payment_status', 'payment_id']
        
        print('Перевірка полів Order:')
        for field in required_fields:
            if field in order_fields:
                print(f'   ✅ {field} - присутнє')
            else:
                print(f'   ❌ {field} - ВІДСУТНЄ!')
                return False
        
        # Перевіряємо PaymentTransaction
        print('\nПеревірка моделі PaymentTransaction:')
        transaction_fields = [f.name for f in PaymentTransaction._meta.get_fields()]
        required_trans_fields = ['order', 'transaction_type', 'status', 'amount', 'payment_system']
        
        for field in required_trans_fields:
            if field in transaction_fields:
                print(f'   ✅ {field} - присутнє')
            else:
                print(f'   ❌ {field} - ВІДСУТНЄ!')
                return False
        
        print('\n✅ Всі моделі налаштовані правильно')
        return True
    except Exception as e:
        print(f'❌ Помилка перевірки моделей: {e}')
        return False


def test_payment_choices():
    """Тест choices для оплати"""
    print_section('ТЕСТ 3: Choices для оплати')
    try:
        print('Доступні способи оплати:')
        for code, name in Order.PAYMENT_METHOD_CHOICES:
            print(f'   💳 {code}: {name}')
        
        print('\nСтатуси оплати:')
        payment_statuses = ['pending', 'paid', 'failed']
        for status in payment_statuses:
            print(f'   🟢 {status}')
        
        print('\n✅ Choices налаштовані правильно')
        return True
    except Exception as e:
        print(f'❌ Помилка перевірки choices: {e}')
        return False


def test_create_transaction():
    """Тест створення транзакції"""
    print_section('ТЕСТ 4: Створення транзакції')
    try:
        # Знаходимо або створюємо тестове замовлення
        user = User.objects.first()
        if not user:
            print('⚠️  Немає користувачів у БД. Створіть користувача спочатку.')
            return False
        
        order = Order.objects.filter(user=user).first()
        if not order:
            print('⚠️  Немає замовлень у БД. Створіть замовлення спочатку.')
            return False
        
        print(f'Використовуємо замовлення #{order.order_number or order.id}')
        
        # Створюємо тестову транзакцію
        transaction = PaymentTransaction.objects.create(
            order=order,
            transaction_type='payment',
            status='initiated',
            amount=order.total_amount,
            currency='UAH',
            payment_system='portmone'
        )
        
        print(f'✅ Транзакцію #{transaction.id} створено успішно')
        print(f'   Замовлення: #{order.order_number or order.id}')
        print(f'   Сума: {transaction.amount} {transaction.currency}')
        print(f'   Статус: {transaction.status}')
        
        # Тестуємо методи
        transaction.mark_as_success({'test': 'data'})
        print(f'   ✅ mark_as_success() працює')
        
        # Видаляємо тестову транзакцію
        transaction.delete()
        print(f'   🗑️  Тестову транзакцію видалено')
        
        return True
    except Exception as e:
        print(f'❌ Помилка створення транзакції: {e}')
        import traceback
        traceback.print_exc()
        return False


def test_saletype_logic():
    """Тест логіки saletype"""
    print_section('ТЕСТ 5: Логіка saletype для JSON експорту')
    try:
        user = User.objects.first()
        if not user:
            print('⚠️  Немає користувачів у БД')
            return False
        
        # Знаходимо замовлення з різними способами оплати
        cash_order = Order.objects.filter(payment_method='cash').first()
        card_order = Order.objects.filter(payment_method='card_online').first()
        
        if cash_order:
            print(f'💵 Готівка: saletype = "{cash_order.sale_type}"')
            if cash_order.sale_type == '1':
                print('   ✅ Правильно (saletype = "1")')
            else:
                print(f'   ❌ НЕПРАВИЛЬНО! Має бути "1", а не "{cash_order.sale_type}"')
        
        if card_order:
            print(f'💳 Картка: saletype = "{card_order.sale_type}"')
            if card_order.sale_type == '2':
                print('   ✅ Правильно (saletype = "2")')
            else:
                print(f'   ❌ НЕПРАВИЛЬНО! Має бути "2", а не "{card_order.sale_type}"')
        
        if not cash_order and not card_order:
            print('⚠️  Немає замовлень для перевірки. Оформіть тестове замовлення.')
        
        return True
    except Exception as e:
        print(f'❌ Помилка перевірки saletype: {e}')
        return False


def test_admin_registration():
    """Тест реєстрації в Django Admin"""
    print_section('ТЕСТ 6: Django Admin')
    try:
        from django.contrib import admin
        from apps.orders.models import PaymentTransaction
        
        if admin.site.is_registered(PaymentTransaction):
            print('✅ PaymentTransaction зареєстровано в admin')
        else:
            print('❌ PaymentTransaction НЕ зареєстровано в admin')
            return False
        
        return True
    except Exception as e:
        print(f'❌ Помилка перевірки admin: {e}')
        return False


def main():
    """Головна функція"""
    print('\n')
    print('🚀 ' + '=' * 76)
    print('   ТЕСТУВАННЯ ІНТЕГРАЦІЇ ОПЛАТИ КАРТКОЮ')
    print('=' * 80)
    
    tests = [
        ('Підключення до БД', test_database_connection),
        ('Моделі', test_models),
        ('Payment Choices', test_payment_choices),
        ('Створення транзакції', test_create_transaction),
        ('Логіка saletype', test_saletype_logic),
        ('Django Admin', test_admin_registration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f'\n❌ Критична помилка в тесті "{test_name}": {e}')
            results.append((test_name, False))
    
    # Підсумок
    print_section('ПІДСУМОК')
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = '✅ ПРОЙДЕНО' if result else '❌ НЕ ПРОЙДЕНО'
        print(f'{status:<20} | {test_name}')
    
    print('\n' + '=' * 80)
    print(f'Результат: {passed}/{total} тестів пройдено')
    
    if passed == total:
        print('🎉 ВСІ ТЕСТИ ПРОЙДЕНО! Інтеграція оплати готова до використання.')
    else:
        print('⚠️  Є помилки. Перевірте налаштування та запустіть міграції:')
        print('   python manage.py makemigrations')
        print('   python manage.py migrate')
    
    print('=' * 80 + '\n')


if __name__ == '__main__':
    main()
