from django.core.management.base import BaseCommand
from django.db import transaction
from apps.users.models import CustomUser
from django.db.models import Count
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Очищає дублікати користувачів за username'

    def handle(self, *args, **options):
        with transaction.atomic():
            # Знаходимо дублікати по username
            duplicates = (
                CustomUser.objects
                .values('username')
                .annotate(count=Count('id'))
                .filter(count__gt=1)
            )

            total_removed = 0
            
            for dup in duplicates:
                username = dup['username']
                users = CustomUser.objects.filter(username=username).order_by('date_joined')
                
                # Залишаємо найстаршого користувача, видаляємо решту
                users_to_delete = users[1:]  # всі крім першого
                
                self.stdout.write(
                    f"Username '{username}': знайдено {users.count()} дублікатів"
                )
                
                for user in users_to_delete:
                    self.stdout.write(
                        f"  Видаляємо користувача ID {user.id} (створений {user.date_joined})"
                    )
                    user.delete()
                    total_removed += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f'Успішно видалено {total_removed} дублікатів користувачів'
                )
            )
