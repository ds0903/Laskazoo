# -*- coding: utf-8 -*-
"""
Management команда для генерації звітів по оплатах
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, Sum, Q
from apps.orders.models import Order
from decimal import Decimal


class Command(BaseCommand):
    help = 'Генерує звіт по оплатах за період'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Період у днях (за замовчуванням 30)'
        )
        parser.add_argument(
            '--export',
            type=str,
            help='Експортувати звіт у файл (вкажіть шлях)'
        )

    def handle(self, *args, **options):
        days = options['days']
        date_from = timezone.now() - timezone.timedelta(days=days)
        
        self.stdout.write(self.style.SUCCESS(f'\n📊 ЗВІТ ПО ОПЛАТАХ'))
        self.stdout.write(self.style.SUCCESS(f'Період: {date_from.strftime("%d.%m.%Y")} - {timezone.now().strftime("%d.%m.%Y")}'))
        self.stdout.write('=' * 80)
        
        # Загальна статистика
        orders = Order.objects.filter(
            created_at__gte=date_from
        ).exclude(status=Order.STATUS_CART)
        
        total_orders = orders.count()
        
        # По способах оплати
        cash_orders = orders.filter(payment_method='cash').count()
        card_orders = orders.filter(payment_method='card_online').count()
        
        # По статусах оплати
        paid_orders = orders.filter(payment_status='paid').count()
        pending_orders = orders.filter(payment_status='pending').count()
        failed_orders = orders.filter(payment_status='failed').count()
        
        # Суми
        total_amount = sum(order.total_amount for order in orders)
        
        cash_amount = sum(
            order.total_amount 
            for order in orders.filter(payment_method='cash')
        )
        
        card_paid_amount = sum(
            order.total_amount 
            for order in orders.filter(payment_method='card_online', payment_status='paid')
        )
        
        card_pending_amount = sum(
            order.total_amount 
            for order in orders.filter(payment_method='card_online', payment_status='pending')
        )
        
        # Виводимо звіт
        self.stdout.write(f'\n📦 ЗАГАЛЬНА СТАТИСТИКА:')
        self.stdout.write(f'  Всього замовлень: {total_orders}')
        self.stdout.write(f'  Загальна сума: {total_amount:.2f} грн')
        
        self.stdout.write(f'\n💰 ПО СПОСОБАХ ОПЛАТИ:')
        self.stdout.write(f'  💵 Готівка: {cash_orders} замовлень ({cash_amount:.2f} грн)')
        self.stdout.write(f'  💳 Картка: {card_orders} замовлень')
        
        if card_orders > 0:
            self.stdout.write(f'\n💳 СТАТУС ОПЛАТ КАРТКОЮ:')
            self.stdout.write(self.style.SUCCESS(
                f'  🟢 Оплачено: {paid_orders} замовлень ({card_paid_amount:.2f} грн)'
            ))
            self.stdout.write(self.style.WARNING(
                f'  🟡 Очікує: {pending_orders} замовлень ({card_pending_amount:.2f} грн)'
            ))
            self.stdout.write(self.style.ERROR(
                f'  🔴 Не пройшла: {failed_orders} замовлень'
            ))
            
            # Конверсія
            if card_orders > 0:
                conversion_rate = (paid_orders / card_orders) * 100
                self.stdout.write(f'\n📈 КОНВЕРСІЯ ОПЛАТ:')
                self.stdout.write(f'  Успішних оплат: {conversion_rate:.1f}%')
        
        # Щоденна статистика (останні 7 днів)
        self.stdout.write(f'\n📅 ДИНАМІКА ОСТАННІХ 7 ДНІВ:')
        self.stdout.write('-' * 80)
        
        for i in range(7):
            day = timezone.now() - timezone.timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            day_orders = orders.filter(created_at__range=[day_start, day_end])
            day_count = day_orders.count()
            day_amount = sum(order.total_amount for order in day_orders)
            
            day_paid = day_orders.filter(
                payment_method='card_online', 
                payment_status='paid'
            ).count()
            
            self.stdout.write(
                f"{day.strftime('%d.%m.%Y (%A)'):<25} | "
                f"Замовлень: {day_count:>3} | "
                f"Сума: {day_amount:>10.2f} грн | "
                f"Оплат карткою: {day_paid:>2}"
            )
        
        self.stdout.write('=' * 80)
        
        # Топ 5 найбільших оплат
        top_orders = orders.order_by('-total_amount')[:5]
        if top_orders:
            self.stdout.write(f'\n💎 ТОП 5 НАЙБІЛЬШИХ ЗАМОВЛЕНЬ:')
            for idx, order in enumerate(top_orders, 1):
                payment_icon = '💳' if order.payment_method == 'card_online' else '💵'
                status_icon = '🟢' if order.payment_status == 'paid' else '🟡'
                self.stdout.write(
                    f"  {idx}. {payment_icon} {status_icon} "
                    f"#{order.order_number or order.id} | "
                    f"{order.full_name} | "
                    f"{order.total_amount:.2f} грн | "
                    f"{order.created_at.strftime('%d.%m.%Y')}"
                )
        
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(self.style.SUCCESS('✅ Звіт сформовано!\n'))
        
        # Експорт у файл
        if options['export']:
            self.export_to_file(options['export'], orders, {
                'total_orders': total_orders,
                'total_amount': total_amount,
                'cash_orders': cash_orders,
                'card_orders': card_orders,
                'paid_orders': paid_orders,
                'pending_orders': pending_orders,
                'failed_orders': failed_orders,
            })
    
    def export_to_file(self, filepath, orders, stats):
        """Експортує звіт у текстовий файл"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('=' * 80 + '\n')
                f.write('ЗВІТ ПО ОПЛАТАХ\n')
                f.write(f"Дата: {timezone.now().strftime('%d.%m.%Y %H:%M')}\n")
                f.write('=' * 80 + '\n\n')
                
                f.write('СТАТИСТИКА:\n')
                f.write(f"Всього замовлень: {stats['total_orders']}\n")
                f.write(f"Загальна сума: {stats['total_amount']:.2f} грн\n")
                f.write(f"Готівка: {stats['cash_orders']} замовлень\n")
                f.write(f"Картка: {stats['card_orders']} замовлень\n")
                f.write(f"  - Оплачено: {stats['paid_orders']}\n")
                f.write(f"  - Очікує: {stats['pending_orders']}\n")
                f.write(f"  - Не пройшла: {stats['failed_orders']}\n\n")
                
                f.write('=' * 80 + '\n')
                f.write('ДЕТАЛІ ЗАМОВЛЕНЬ:\n')
                f.write('=' * 80 + '\n\n')
                
                for order in orders:
                    f.write(f"Замовлення #{order.order_number or order.id}\n")
                    f.write(f"Клієнт: {order.full_name}\n")
                    f.write(f"Телефон: {order.phone}\n")
                    f.write(f"Спосіб оплати: {order.get_payment_method_display()}\n")
                    f.write(f"Статус оплати: {order.payment_status}\n")
                    f.write(f"Сума: {order.total_amount:.2f} грн\n")
                    f.write(f"Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n")
                    f.write('-' * 40 + '\n\n')
            
            self.stdout.write(self.style.SUCCESS(f'✅ Звіт експортовано у файл: {filepath}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Помилка експорту: {e}'))
