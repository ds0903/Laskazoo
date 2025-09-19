import json
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from apps.orders.models import Order, OrderItem


class Command(BaseCommand):
    help = 'Експортує замовлення в JSON файл для TorgSoft'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Перезаписати файл, навіть якщо він існує',
        )

    def handle(self, *args, **options):
        # Визначаємо папку для експорту з налаштувань або використовуємо за замовчуванням
        export_dir = getattr(settings, 'TS_LOCAL_INCOMING_DIR', '/home/torgsoft/incoming')
        
        # Для локальної розробки використовуємо папку в проекті
        if not os.path.exists(export_dir):
            export_dir = os.path.join(settings.BASE_DIR, 'exports')
            os.makedirs(export_dir, exist_ok=True)
        
        # Ім'я файлу з датою
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'orders_{timestamp}.json'
        filepath = os.path.join(export_dir, filename)
        
        # Також створюємо файл з фіксованою назвою для постійного перезапису
        fixed_filepath = os.path.join(export_dir, 'orders_current.json')
        
        # Отримуємо замовлення для експорту
        # Беремо замовлення зі статусом "в процесі" та ті, що ще не були експортовані
        # АБО ті, що були експортовані, але статус ще не "в дорозі" (не опрацьовані менеджером)
        orders = Order.objects.filter(
            status__in=[Order.STATUS_IN_PROCESS, Order.STATUS_PROCESSING]
        ).exclude(
            status=Order.STATUS_SHIPPED  # Не беремо ті, що вже в дорозі
        )
        
        if not orders.exists():
            self.stdout.write(self.style.WARNING('Немає замовлень для експорту'))
            return
        
        # Формуємо JSON структуру
        export_data = []
        
        for order in orders:
            order_data = {
                "Client": {
                    "Name": order.full_name,
                    "MPhone": order.phone,
                    "CPhone": "",  # Додатковий телефон (не використовуємо)
                    "ZIP": "",  # Поштовий індекс (не використовуємо)
                    "Country": "Україна",
                    "Region": "",  # Можна додати пізніше
                    "Місто": "",  # Витягується з адреси
                    "Address": order.delivery_address,
                    "EMail": order.email
                },
                "Options": {
                    "SaleType": order.sale_type,
                    "Comment": order.comment or "",
                    "OrderNumber": order.order_number or str(order.id),
                    "DeliveryCondition": order.get_delivery_condition_display(),
                    "DeliveryAddress": order.delivery_address,
                    "OrderDate": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "CurrencyInternationalCode": "UAH"
                },
                "Goods": []
            }
            
            # Додаємо товари
            for item in order.items.all():
                # Визначаємо ID товару - для варіанту беремо SKU, для продукту - ID
                if item.variant:
                    good_id = item.variant.sku or f"V{item.variant.id}"
                else:
                    good_id = str(item.product.id)
                
                good_data = {
                    "GoodID": good_id,
                    "Price": str(item.retail_price),
                    "Count": str(item.quantity)
                }
                order_data["Goods"].append(good_data)
            
            export_data.append(order_data)
        
        # Зберігаємо в JSON файли
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        with open(fixed_filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        # Оновлюємо статус замовлень на "обробляється"
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
                f'Експортовано {len(export_data)} замовлень в {filepath}\n'
                f'Оновлено статус для {updated_count} замовлень'
            )
        )
