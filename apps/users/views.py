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
        return render(request, self.template_name, {'login_form': self.form_class()})

    def post(self, request):
        form = self.form_class(request.POST)
        error = None
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password']
            )
            if user:
                login(request, user)
                request.session.save()  # Явне збереження сесії

                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'redirect_url': '/'})
                return redirect('/')
            error = _('Невірний логін або пароль')
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
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Подвійна перевірка унікальності безпосередньо перед створенням
                    from .models import CustomUser
                    from django.db import connection
                    
                    username = form.cleaned_data['username']
                    email = form.cleaned_data['email']
                    
                    # Використовуємо пряме SQL для точної перевірки
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "SELECT COUNT(*) FROM users_customuser WHERE username = %s",
                            [username]
                        )
                        username_count = cursor.fetchone()[0]
                        
                        cursor.execute(
                            "SELECT COUNT(*) FROM users_customuser WHERE email = %s",
                            [email]
                        )
                        email_count = cursor.fetchone()[0]
                    
                    # Якщо знайдено дублікати - зупиняємо
                    if username_count > 0:
                        logger.warning(f'Username {username} вже існує (SQL count: {username_count})')
                        form.add_error('username', _('Користувач з таким логіном вже існує.'))
                        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                            return render(request, 'zoosvit/users/register_form.html', {'form': form}, status=400)
                        return render(request, 'zoosvit/users/register.html', {'form': form})
                    
                    if email_count > 0:
                        logger.warning(f'Email {email} вже існує (SQL count: {email_count})')
                        form.add_error('email', _('Користувач з таким email вже існує.'))
                        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                            return render(request, 'zoosvit/users/register_form.html', {'form': form}, status=400)
                        return render(request, 'zoosvit/users/register.html', {'form': form})
                    
                    # Якщо все ОК - створюємо користувача
                    user = form.save()
                    login(request, user)
                    request.session.save()  # Явне збереження сесії
                    logger.info(f'Успішна реєстрація користувача: {user.username}')
                    
                    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                        return JsonResponse({'success': True, 'redirect_url': '/'})
                    return redirect('home')
            
            except IntegrityError as e:
                logger.error(f'Помилка реєстрації (повторна): {str(e)}')
                # Якщо все ж помилка на рівні БД - обробляємо
                if 'username' in str(e):
                    form.add_error('username', _('Користувач з таким логіном вже існує.'))
                elif 'email' in str(e):
                    form.add_error('email', _('Користувач з таким email вже існує.'))
                else:
                    form.add_error(None, _('Виникла помилка під час реєстрації.'))
                
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return render(request, 'zoosvit/users/register_form.html', {'form': form}, status=400)
                return render(request, 'zoosvit/users/register.html', {'form': form})
            
            except Exception as e:
                logger.error(f'Неочікувана помилка реєстрації: {str(e)}')
                form.add_error(None, _('Виникла технічна помилка. Спробуйте пізніше.'))
                
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return render(request, 'zoosvit/users/register_form.html', {'form': form}, status=500)
                return render(request, 'zoosvit/users/register.html', {'form': form})
        else:
            logger.warning(f'Невалідна форма реєстрації: {form.errors}')
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return render(request, 'zoosvit/users/register_form.html', {'form': form}, status=400)
            return render(request, 'zoosvit/users/register.html', {'form': form})

    else:
        form = CustomUserCreationForm()

    return render(request, 'zoosvit/users/register.html', {'form': form})

@login_required
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
        if 'username' in str(e):
            form.add_error('username', _('Користувач з таким логіном вже існує.'))
        else:
            messages.error(request, _('Помилка збереження даних.'))
    except Exception as e:
        logger.error(f'Неочікувана помилка профілю: {str(e)}')
        messages.error(request, _('Технічна помилка. Спробуйте пізніше.'))
        
    return render(request, 'zoosvit/users/profile.html', {'form': form})
