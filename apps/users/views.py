from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.views import View
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from .forms import CustomUserCreationForm, LoginForm, ProfileForm
from django.contrib.auth.decorators import login_required
from django.db import transaction, IntegrityError
import logging

logger = logging.getLogger(__name__)


class UserLoginView(View):
    form_class = LoginForm
    template_name = 'zoosvit/users/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('/')
        return render(request, self.template_name, {'login_form': self.form_class()})

    def post(self, request):
        form = self.form_class(request.POST)
        error = None
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )
            if user:
                login(request, user, backend='apps.users.backends.EmailBackend')
                request.session.save()

                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'redirect_url': '/'})
                return redirect('/')
            error = _('Невірний email або пароль')
        else:
            error = _('Будь ласка, виправте помилки у формі')

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return render(
                request,
                'zoosvit/users/login_form.html',
                {'login_form': form, 'error': error},
                status=400
            )

        return render(request, self.template_name, {
            'login_form': form,
            'error': error
        })


class UserLogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('/')


def register(request):
    if request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'redirect_url': '/'})
        return redirect('/')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        
        # Перевіряємо валідність форми
        if not form.is_valid():
            logger.warning(f'Невалідна форма реєстрації: {form.errors}')
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return render(request, 'zoosvit/users/register_form.html', {'form': form}, status=400)
            return render(request, 'zoosvit/users/register.html', {'form': form})
        
        # Форма валідна - створюємо користувача
        try:
            with transaction.atomic():
                user = form.save()
                logger.info(f'Успішна реєстрація користувача: {user.username} ({user.email})')
                
                # Логінимо користувача
                login(request, user, backend='apps.users.backends.EmailBackend')
                request.session.save()
                
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'redirect_url': '/'})
                return redirect('home')
        
        except IntegrityError as e:
            logger.error(f'IntegrityError при реєстрації: {str(e)}')
            form.add_error('email', _('Користувач з таким email вже існує.'))
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return render(request, 'zoosvit/users/register_form.html', {'form': form}, status=400)
            return render(request, 'zoosvit/users/register.html', {'form': form})
        
        except Exception as e:
            logger.error(f'Неочікувана помилка при реєстрації: {str(e)}')
            form.add_error(None, _('Виникла технічна помилка. Спробуйте пізніше.'))
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return render(request, 'zoosvit/users/register_form.html', {'form': form}, status=500)
            return render(request, 'zoosvit/users/register.html', {'form': form})
    
    else:
        form = CustomUserCreationForm()

    return render(request, 'zoosvit/users/register.html', {'form': form})


@login_required(login_url='/users/login/')
def profile_view(request):
    try:
        form = ProfileForm(request.POST or None, instance=request.user)
        if form.is_valid():
            with transaction.atomic():
                form.save()
                messages.success(request, _('Дані оновлено ✔️'))
                return redirect('users:profile')
    except IntegrityError as e:
        logger.error(f'Помилка оновлення профілю: {str(e)}')
        if 'email' in str(e):
            form.add_error('email', _('Користувач з таким email вже існує.'))
        else:
            messages.error(request, _('Помилка збереження даних.'))
    except Exception as e:
        logger.error(f'Неочікувана помилка профілю: {str(e)}')
        messages.error(request, _('Технічна помилка. Спробуйте пізніше.'))
        
    return render(request, 'zoosvit/users/profile.html', {'form': form})
