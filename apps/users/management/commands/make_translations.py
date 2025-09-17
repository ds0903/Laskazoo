from django.core.management.base import BaseCommand
import os
import subprocess
from django.conf import settings


class Command(BaseCommand):
    help = 'Генерує файли перекладу для української мови'

    def handle(self, *args, **options):
        self.stdout.write('Генеруємо файли перекладу...')
        
        try:
            # Створюємо директорію для української мови
            uk_locale_dir = os.path.join(settings.BASE_DIR, 'locale', 'uk', 'LC_MESSAGES')
            os.makedirs(uk_locale_dir, exist_ok=True)
            
            # Генеруємо .po файл
            os.chdir(settings.BASE_DIR)
            subprocess.run([
                'python', 'manage.py', 'makemessages', 
                '-l', 'uk', 
                '--extension=html,py',
                '--ignore=.venv'
            ], check=True)
            
            self.stdout.write(
                self.style.SUCCESS('Файли перекладу успішно створені!')
            )
            self.stdout.write(
                'Відредагуйте файл locale/uk/LC_MESSAGES/django.po і запустіте:'
            )
            self.stdout.write(
                'python manage.py compilemessages'
            )
            
        except subprocess.CalledProcessError as e:
            self.stdout.write(
                self.style.ERROR(f'Помилка при створенні файлів перекладу: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Неочікувана помилка: {e}')
            )
