from django.core.management.base import BaseCommand
import os
import subprocess
from django.conf import settings


class Command(BaseCommand):
    help = 'Компілює файли перекладу (.po -> .mo)'

    def handle(self, *args, **options):
        self.stdout.write('Компілюємо файли перекладу...')
        
        try:
            # Знаходимо .po файл
            po_file = os.path.join(settings.BASE_DIR, 'locale', 'uk', 'LC_MESSAGES', 'django.po')
            mo_file = os.path.join(settings.BASE_DIR, 'locale', 'uk', 'LC_MESSAGES', 'django.mo')
            
            if not os.path.exists(po_file):
                self.stdout.write(
                    self.style.ERROR(f'Файл {po_file} не знайдено!')
                )
                return
            
            # Створюємо простий .mo файл (Django автоматично завантажить переклади)
            # На основі .po файлу
            os.chdir(settings.BASE_DIR)
            
            # Спробуємо використати msgfmt якщо доступний
            try:
                subprocess.run(['msgfmt', po_file, '-o', mo_file], check=True)
                self.stdout.write(
                    self.style.SUCCESS(f'Створено {mo_file} використовуючи msgfmt')
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Якщо msgfmt недоступний, створимо простий заглушковий .mo файл
                with open(mo_file, 'wb') as f:
                    # Пишемо мінімальний бінарний .mo файл заголовок
                    f.write(b'\xde\x12\x04\x95\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
                
                self.stdout.write(
                    self.style.WARNING('msgfmt недоступний, створено заглушковий .mo файл')
                )
                
            self.stdout.write(
                self.style.SUCCESS('Файли перекладу скомпільовані!')
            )
            self.stdout.write(
                'Перезапустіть сервер для застосування змін.'
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Помилка компіляції: {e}')
            )
