import json
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from apps.orders.models import Order


class Command(BaseCommand):
    help = 'Періодично експортує нові замовлення кожні 15 хвилин'

    def handle(self, *args, **options):
        # Визначаємо папку для експорту
        export_dir = getattr(settings, 'TS_LOCAL_INCOMING_DIR', None)
        
        # Для локальної розробки використовуємо папку в проекті
        if not export_dir or not os.path.exists(export_dir):
            export_dir = os.path.join(settings.BASE_DIR, 'exports')
            os.makedirs(export_dir, exist_ok=True)
        
        # Ім'я файлу з датою
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'orders_{timestamp}.json'
        filepath = os.path.join(export_dir, filename)
        
        # Отримуємо замовлення для експорту
        # Замовлення в статусі "in_process" (щойно оформлені) - додаємо в JSON
        # Замовлення в статусі "processing" (вже в JSON, але ще не "shipped") - теж додаємо
        orders = Order.objects.filter(
            status__in=[Order.STATUS_IN_PROCESS, Order.STATUS_PROCESSING]
        )
        
        if not orders.exists():
            self.stdout.write('Немає нових замовлень для експорту')
            return
        
        # Формуємо JSON структуру
        export_data = []
        
        for order in orders:
            # Визначаємо назву способу доставки
            delivery_display = ""
            if order.delivery_condition == 'nova_poshta':
                delivery_display = "Нова Пошта"
            elif order.delivery_condition == 'ukrposhta':
                delivery_display = "Укр Пошта"
            else:
                delivery_display = order.get_delivery_condition_display()
            
            order_data = {
                "Client": {
                    "Name": order.full_name or "Покупець",
                    "MPhone": order.phone or "",
                    "CPhone": "",  # Додатковий телефон
                    "ZIP": "",  # Поштовий індекс
                    "Country": "Україна",
                    "Region": "",  # Область
                    "Місто": "",  # Місто
                    "Address": order.delivery_address or "",
                    "EMail": order.email or ""
                },
                "Options": {
                    "SaleType": order.sale_type or "1",
                    "Comment": order.comment or "",
                    "OrderNumber": order.order_number or str(order.id),
                    "DeliveryCondition": delivery_display,
                    "DeliveryAddress": order.delivery_address or "",
                    "ReserveDate": "",  # Дата резерву (пустий)
                    "BonusPay": "0",  # Бонуси (пустий)
                    "GiftCertificate": "",  # Сертифікати (пустий)
                    "OrderDate": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "CurrencyInternationalCode": "UAH"
                },
                "Goods": []
            }
            
            # Додаємо товари
            for item in order.items.all():
                # Для варіантів використовуємо їх ID, для продуктів - ID продукту
                if item.variant:
                    good_id = str(item.variant.id)
                else:
                    good_id = str(item.product.id)
                
                good_data = {
                    "GoodID": good_id,
                    "Price": str(item.retail_price or 0),
                    "Count": str(item.quantity or 1)
                }
                order_data["Goods"].append(good_data)
            
            export_data.append(order_data)
        
        # Зберігаємо JSON файл
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        # Оновлюємо статуси - тільки для тих, що були "in_process"
        updated_count = 0
        for order in orders:
            if order.status == Order.STATUS_IN_PROCESS:
                order.status = Order.STATUS_PROCESSING
                order.exported = True
                order.exported_at = timezone.now()
                order.save()
                updated_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Експортовано {len(export_data)} замовлень в {filename}\\n'
                f'Оновлено статус для {updated_count} нових замовлень'
            )
        )
        
        # Виводимо шлях до файлу для налагодження
        self.stdout.write(f'Файл збережено: {filepath}')
