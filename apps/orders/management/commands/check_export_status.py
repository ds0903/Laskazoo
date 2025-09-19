from django.core.management.base import BaseCommand
from apps.orders.models import Order
from django.utils import timezone
from datetime import timedelta
import os
from django.conf import settings


class Command(BaseCommand):
    help = 'Перевіряє стан системи експорту замовлень'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Стан системи експорту замовлень ===\n'))
        
        # Статистика замовлень по статусах
        statuses = [
            (Order.STATUS_CART, 'У кошику'),
            (Order.STATUS_IN_PROCESS, 'В процесі (нові)'),
            (Order.STATUS_PROCESSING, 'Обробляється (в JSON)'),
            (Order.STATUS_SHIPPED, 'В дорозі'),
            (Order.STATUS_COMPLETED, 'Виконані'),
            (Order.STATUS_CANCELED, 'Скасовані'),
        ]
        
        self.stdout.write('📊 Статистика замовлень:')
        for status_code, status_name in statuses:
            count = Order.objects.filter(status=status_code).count()
            if count > 0:
                self.stdout.write(f'  {status_name}: {count}')
        
        # Замовлення для експорту
        export_orders = Order.objects.filter(
            status__in=[Order.STATUS_IN_PROCESS, Order.STATUS_PROCESSING]
        )
        self.stdout.write(f'\n📤 Замовлень для експорту: {export_orders.count()}')
        
        if export_orders.exists():
            self.stdout.write('  Деталі:')
            for order in export_orders[:5]:  # Показуємо перші 5
                self.stdout.write(
                    f'    #{order.id} - {order.full_name} - '
                    f'{order.get_status_display()} - '
                    f'{order.created_at.strftime("%Y-%m-%d %H:%M")}'
                )
            if export_orders.count() > 5:
                self.stdout.write(f'    ... і ще {export_orders.count() - 5}')
        
        # Перевірка папки експорту
        export_dir = getattr(settings, 'TS_LOCAL_INCOMING_DIR', None)
        if not export_dir or not os.path.exists(export_dir):
            export_dir = os.path.join(settings.BASE_DIR, 'exports')
        
        self.stdout.write(f'\n📁 Папка експорту: {export_dir}')
        
        if os.path.exists(export_dir):
            json_files = [f for f in os.listdir(export_dir) if f.endswith('.json')]
            self.stdout.write(f'  JSON файлів: {len(json_files)}')
            
            if json_files:
                # Показуємо останні 3 файли
                json_files.sort(reverse=True)
                self.stdout.write('  Останні файли:')
                for file in json_files[:3]:
                    file_path = os.path.join(export_dir, file)
                    mtime = os.path.getmtime(file_path)
                    mtime_str = timezone.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
                    self.stdout.write(f'    {file} - {mtime_str}')
        else:
            self.stdout.write('  ❌ Папка не існує')
        
        # Останні експортовані замовлення
        recent_exported = Order.objects.filter(
            exported=True,
            exported_at__gte=timezone.now() - timedelta(hours=24)
        ).order_by('-exported_at')[:5]
        
        if recent_exported:
            self.stdout.write(f'\n⏰ Експортовано за останню добу: {recent_exported.count()}')
            for order in recent_exported:
                self.stdout.write(
                    f'  #{order.id} - {order.exported_at.strftime("%Y-%m-%d %H:%M")}'
                )
        
        # Рекомендації
        self.stdout.write('\n💡 Рекомендації:')
        
        in_process_count = Order.objects.filter(status=Order.STATUS_IN_PROCESS).count()
        if in_process_count > 0:
            self.stdout.write(f'  • Є {in_process_count} нових замовлень - запустіть експорт')
            
        processing_count = Order.objects.filter(status=Order.STATUS_PROCESSING).count()
        if processing_count > 10:
            self.stdout.write(f'  • Багато замовлень ({processing_count}) в статусі "Обробляється" - перевірте роботу менеджера')
            
        if not json_files:
            self.stdout.write('  • Немає JSON файлів - система експорту може не працювати')
        
        self.stdout.write('\n✅ Перевірка завершена')
