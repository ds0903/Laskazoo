from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = 'Створює групу Менеджер для доступу до кабінету менеджера'

    def handle(self, *args, **options):
        group, created = Group.objects.get_or_create(name='Менеджер')
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('Групу "Менеджер" успішно створено!')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Група "Менеджер" вже існує')
            )
