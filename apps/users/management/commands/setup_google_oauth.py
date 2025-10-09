from django.core.management.base import BaseCommand
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Налаштовує Google OAuth автоматично без адмінки'

    def add_arguments(self, parser):
        parser.add_argument(
            '--domain',
            type=str,
            default='localhost:8000',
            help='Домен для Site (за замовчуванням: localhost:8000)',
        )

    def handle(self, *args, **kwargs):
        domain = kwargs['domain']
        client_id = os.getenv('GOOGLE_OAUTH_CLIENT_ID', '')
        client_secret = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET', '')
        
        if not client_id or not client_secret:
            self.stdout.write(self.style.WARNING(
                'Google OAuth credentials не знайдено в .env файлі.\n'
                'Додайте GOOGLE_OAUTH_CLIENT_ID та GOOGLE_OAUTH_CLIENT_SECRET'
            ))
            return
        
        # Отримуємо або створюємо сайт
        site, created = Site.objects.get_or_create(
            pk=1,
            defaults={'domain': domain, 'name': domain}
        )
        
        # Якщо сайт існує, але домен інший - оновлюємо
        if not created and site.domain != domain:
            site.domain = domain
            site.name = domain
            site.save()
            self.stdout.write(self.style.SUCCESS(f'Оновлено сайт: {site.domain}'))
        elif created:
            self.stdout.write(self.style.SUCCESS(f'Створено сайт: {site.domain}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Сайт вже існує: {site.domain}'))
        
        # Отримуємо або створюємо Google SocialApp
        social_app, created = SocialApp.objects.get_or_create(
            provider='google',
            defaults={
                'name': 'Google OAuth',
                'client_id': client_id,
                'secret': client_secret,
            }
        )
        
        # Оновлюємо credentials якщо вони змінилися
        if not created:
            updated = False
            if social_app.client_id != client_id:
                social_app.client_id = client_id
                updated = True
            if social_app.secret != client_secret:
                social_app.secret = client_secret
                updated = True
            if updated:
                social_app.save()
                self.stdout.write(self.style.SUCCESS('Оновлено Google OAuth credentials'))
        else:
            self.stdout.write(self.style.SUCCESS('Створено Google OAuth додаток'))
        
        # Додаємо сайт до додатку
        if site not in social_app.sites.all():
            social_app.sites.add(site)
            self.stdout.write(self.style.SUCCESS(f'Додано сайт {site.domain} до Google OAuth'))
        
        self.stdout.write(self.style.SUCCESS(
            '\n✅ Google OAuth налаштовано успішно!\n'
            f'Домен: {site.domain}\n'
            'Тепер можна використовувати Google login на сайті.\n'
        ))
        
        # Показуємо що потрібно додати в Google Console
        if domain == 'localhost:8000':
            self.stdout.write(self.style.WARNING(
                '📝 Переконайтесь що в Google Console додано Authorized redirect URIs:\n'
                '   - http://localhost:8000/accounts/google/login/callback/\n'
                '   - http://127.0.0.1:8000/accounts/google/login/callback/\n'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f'📝 Переконайтесь що в Google Console додано Authorized redirect URI:\n'
                f'   - https://{domain}/accounts/google/login/callback/\n'
            ))
