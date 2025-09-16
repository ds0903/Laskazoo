from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Показує всіх користувачів в базі даних'

    def handle(self, *args, **options):
        User = get_user_model()
        
        users = User.objects.all()
        
        if not users.exists():
            self.stdout.write(
                self.style.WARNING('В базі даних немає жодного користувача')
            )
            return
            
        self.stdout.write(f'Знайдено {users.count()} користувачів:')
        self.stdout.write('-' * 50)
        
        for user in users:
            status = "✅ Активний" if user.is_active else "❌ Неактивний"
            superuser = "👑 Суперкористувач" if user.is_superuser else ""
            
            self.stdout.write(
                f'ID: {user.id:3} | {user.username:15} | {user.email:25} | {status} {superuser}'
            )
            
        # Перевіряємо конкретного користувача
        problematic_users = ['danilus15', 'danilus123', 'testuser']
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write('Перевірка проблемних користувачів:')
        
        for username in problematic_users:
            exists = User.objects.filter(username=username).exists()
            user_count = User.objects.filter(username=username).count()
            status = f"EXISTS ({user_count} записів)" if exists else "НЕ ІСНУЄ"
            self.stdout.write(f'{username:15} | {status}')
