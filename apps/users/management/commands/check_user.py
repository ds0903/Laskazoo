from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction


class Command(BaseCommand):
    help = 'Перевіряє конкретного користувача в базі даних'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username для перевірки')

    def handle(self, *args, **options):
        username = options['username']
        User = get_user_model()
        
        self.stdout.write(f'Перевіряємо користувача: {username}')
        self.stdout.write('-' * 50)
        
        # Перевірка 1: exists()
        exists = User.objects.filter(username=username).exists()
        self.stdout.write(f'User.objects.filter(username="{username}").exists(): {exists}')
        
        # Перевірка 2: count()
        count = User.objects.filter(username=username).count()
        self.stdout.write(f'User.objects.filter(username="{username}").count(): {count}')
        
        # Перевірка 3: get() з обробкою помилок
        try:
            user = User.objects.get(username=username)
            self.stdout.write(f'User.objects.get(username="{username}"): {user} (ID: {user.id})')
        except User.DoesNotExist:
            self.stdout.write(f'User.objects.get(username="{username}"): НЕ ЗНАЙДЕНО')
        except User.MultipleObjectsReturned:
            self.stdout.write(f'User.objects.get(username="{username}"): ЗНАЙДЕНО КІЛЬКА!')
            users = User.objects.filter(username=username)
            for u in users:
                self.stdout.write(f'  - {u} (ID: {u.id})')
        
        # Перевірка 4: В транзакції
        self.stdout.write('\n--- В atomic транзакції ---')
        try:
            with transaction.atomic():
                exists_atomic = User.objects.filter(username=username).exists()
                self.stdout.write(f'В транзакції exists(): {exists_atomic}')
        except Exception as e:
            self.stdout.write(f'Помилка в транзакції: {e}')
        
        # Перевірка 5: Пряме SQL
        from django.db import connection
        self.stdout.write('\n--- Пряме SQL ---')
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, username FROM users_customuser WHERE username = %s",
                    [username]
                )
                rows = cursor.fetchall()
                if rows:
                    for row in rows:
                        self.stdout.write(f'SQL result: ID={row[0]}, username={row[1]}')
                else:
                    self.stdout.write('SQL result: НЕ ЗНАЙДЕНО')
        except Exception as e:
            self.stdout.write(f'Помилка SQL: {e}')
