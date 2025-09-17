from django.core.management.base import BaseCommand
from django.core.management import call_command
import os
from django.conf import settings


class Command(BaseCommand):
    help = 'Швидке перезапуск з SQLite - робить міграції та створює тестові дані'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-fixtures',
            action='store_true',
            help='Не завантажувати тестові дані',
        )

    def handle(self, *args, **options):
        self.stdout.write('Налаштовуємо проект з SQLite...')
        
        try:
            # Міграції
            self.stdout.write('Застосовуємо міграції...')
            call_command('migrate', verbosity=0)
            
            # Компілюємо переклади
            self.stdout.write('Компілюємо переклади...')
            try:
                call_command('compile_translations', verbosity=0)
            except:
                self.stdout.write(
                    self.style.WARNING('Не вдалося скомпілювати переклади, продовжуємо...')
                )
            
            # Створюємо суперкористувача якщо немає
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            if not User.objects.filter(is_superuser=True).exists():
                self.stdout.write('Створюємо тестового суперкористувача...')
                User.objects.create_superuser(
                    username='admin',
                    email='admin@test.com',
                    password='admin123'
                )
                self.stdout.write(
                    self.style.SUCCESS('Створено admin/admin123')
                )
            
            # Створюємо тестового користувача
            if not User.objects.filter(username='testuser').exists():
                self.stdout.write('Створюємо тестового користувача...')
                User.objects.create_user(
                    username='testuser',
                    email='test@test.com',
                    password='test123'
                )
                self.stdout.write(
                    self.style.SUCCESS('Створено testuser/test123')
                )
            
            self.stdout.write(
                self.style.SUCCESS('Готово! Можете запускати runserver')
            )
            self.stdout.write('Доступні користувачі:')
            self.stdout.write('  Адмін: admin / admin123')
            self.stdout.write('  Тест: testuser / test123')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Помилка налаштування: {e}')
            )
