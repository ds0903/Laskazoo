from django.core.management.base import BaseCommand
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site


class Command(BaseCommand):
    help = 'Перевіряє налаштування Google OAuth'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('\n🔍 Перевірка налаштувань Google OAuth...\n'))
        
        # Перевірка Sites
        sites = Site.objects.all()
        self.stdout.write(f'📍 Знайдено Sites: {sites.count()}')
        for site in sites:
            self.stdout.write(f'  - ID: {site.pk}, Domain: {site.domain}, Name: {site.name}')
        
        # Перевірка SocialApp
        social_apps = SocialApp.objects.filter(provider='google')
        self.stdout.write(f'\n🔑 Знайдено Google OAuth додатків: {social_apps.count()}')
        
        if social_apps.exists():
            for app in social_apps:
                self.stdout.write(f'\n  Назва: {app.name}')
                self.stdout.write(f'  Provider: {app.provider}')
                self.stdout.write(f'  Client ID: {app.client_id[:20]}...' if len(app.client_id) > 20 else f'  Client ID: {app.client_id}')
                self.stdout.write(f'  Secret: {"*" * 10}')
                self.stdout.write(f'  Прив\'язані сайти:')
                for site in app.sites.all():
                    self.stdout.write(f'    - {site.domain}')
        else:
            self.stdout.write(self.style.ERROR('\n  ❌ Не знайдено Google OAuth додатків!'))
            self.stdout.write(self.style.WARNING('  Запустіть: python manage.py setup_google_oauth'))
        
        self.stdout.write('\n')
