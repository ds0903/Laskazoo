from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.template.exceptions import TemplateDoesNotExist
from django.http import JsonResponse


class SessionExpiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        # Перехоплюємо помилку TemplateDoesNotExist для login
        if isinstance(exception, TemplateDoesNotExist):
            if 'login' in str(exception):
                # Якщо це AJAX запит, повертаємо JSON з помилкою
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'error': _('Будь ласка, увійдіть в свій акаунт'),
                        'redirect_url': '/users/login/'
                    }, status=401)
                
                # Редірект на сторінку входу з повідомленням
                messages.warning(request, _('Будь ласка, увійдіть в свій акаунт'))
                next_url = request.GET.get('next', request.path)
                return redirect(f'/users/login/?next={next_url}')
        
        # Якщо користувач не залогінений і намагається отримати доступ до захищеної сторінки
        if not request.user.is_authenticated:
            # Перевіряємо чи це запит до захищеної сторінки
            if request.path.startswith('/users/profile/') or request.path.startswith('/orders/'):
                # Якщо це AJAX запит
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'error': _('Будь ласка, увійдіть в свій акаунт'),
                        'redirect_url': '/users/login/'
                    }, status=401)
                
                messages.warning(request, _('Будь ласка, увійдіть в свій акаунт'))
                return redirect(f'/users/login/?next={request.path}')
        
        return None
