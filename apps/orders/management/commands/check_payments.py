# -*- coding: utf-8 -*-
"""
Management команда для перевірки та синхронізації статусів оплат
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.orders.models import Order
import requests


class Command(BaseCommand):
    help = 'Перевіряє статус оплат через Portmone API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--order-id',
            type=int,
            help='Перевірити конкретне замовлення за ID'
        )
        parser.add_argument(
            '--pending-only',
            action='store_true',
            help='Перевірити тільки замовлення зі статусом "очікує оплати"'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Кількість днів для перевірки (за замовчуванням 7)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔍 Починаємо перевірку статусів оплат...'))
        
        # Фільтруємо замовлення
        queryset = Order.objects.filter(payment_method='card_online')
        
        if options['order_id']:
            queryset = queryset.filter(id=options['order_id'])
            self.stdout.write(f"Перевіряємо замовлення #{options['order_id']}")
        elif options['pending_only']:
            queryset = queryset.filter(payment_status='pending')
            self.stdout.write(f"Перевіряємо тільки замовлення зі статусом 'pending'")
        else:
            # Перевіряємо за останні N днів
            days = options['days']
            date_from = timezone.now() - timezone.timedelta(days=days)
            queryset = queryset.filter(created_at__gte=date_from)
            self.stdout.write(f"Перевіряємо замовлення за останні {days} днів")
        
        queryset = queryset.order_by('-created_at')
        total = queryset.count()
        
        if total == 0:
            self.stdout.write(self.style.WARNING('⚠️  Замовлень для перевірки не знайдено'))
            return
        
        self.stdout.write(f"Знайдено замовлень: {total}")
        self.stdout.write('-' * 80)
        
        # Статистика
        stats = {
            'checked': 0,
            'paid': 0,
            'pending': 0,
            'failed': 0,
            'updated': 0,
        }
        
        for order in queryset:
            stats['checked'] += 1
            
            # Статистика по статусам
            if order.payment_status == 'paid':
                stats['paid'] += 1
                status_icon = '🟢'
            elif order.payment_status == 'pending':
                stats['pending'] += 1
                status_icon = '🟡'
            else:
                stats['failed'] += 1
                status_icon = '🔴'
            
            # Виводимо інформацію
            self.stdout.write(
                f"{status_icon} Замовлення #{order.order_number or order.id} | "
                f"Клієнт: {order.full_name} | "
                f"Сума: {order.total_amount} грн | "
                f"Статус: {order.payment_status} | "
                f"Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}"
            )
            
            # Тут можна додати запит до Portmone API для перевірки статусу
            # if order.payment_status == 'pending':
            #     new_status = self.check_payment_status_with_portmone(order)
            #     if new_status and new_status != order.payment_status:
            #         order.payment_status = new_status
            #         order.save()
            #         stats['updated'] += 1
            #         self.stdout.write(self.style.SUCCESS(f"  ✅ Оновлено статус на: {new_status}"))
        
        # Виводимо статистику
        self.stdout.write('-' * 80)
        self.stdout.write(self.style.SUCCESS('\n📊 СТАТИСТИКА:'))
        self.stdout.write(f"Перевірено замовлень: {stats['checked']}")
        self.stdout.write(self.style.SUCCESS(f"🟢 Оплачено: {stats['paid']}"))
        self.stdout.write(self.style.WARNING(f"🟡 Очікує оплати: {stats['pending']}"))
        self.stdout.write(self.style.ERROR(f"🔴 Не пройшла: {stats['failed']}"))
        if stats['updated'] > 0:
            self.stdout.write(self.style.SUCCESS(f"✨ Оновлено статусів: {stats['updated']}"))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Перевірка завершена!'))

    def check_payment_status_with_portmone(self, order):
        """
        Перевіряє статус оплати через Portmone API
        Повертає новий статус або None
        """
        # TODO: Реалізувати запит до Portmone API
        # Приклад:
        # response = requests.post(
        #     'https://www.portmone.com.ua/gateway/status',
        #     data={
        #         'payee_id': settings.PORTMONE_PAYEE_ID,
        #         'shop_order_number': order.order_number,
        #     }
        # )
        # if response.status_code == 200:
        #     data = response.json()
        #     return 'paid' if data.get('status') == 'success' else 'failed'
        return None
