from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.views import View
from allauth.socialaccount.models import SocialAccount
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from .forms import CustomUserCreationForm, LoginForm, ProfileForm, PasswordResetRequestForm, SetNewPasswordForm
from django.contrib.auth.decorators import login_required
from django.db import transaction, IntegrityError
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from .models import CustomUser
from django.utils import timezone
import logging
import secrets

logger = logging.getLogger(__name__)


class UserLoginView(View):
    form_class = LoginForm
    template_name = 'zoosvit/users/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('/')
        return render(request, self.template_name, {
            'login_form': self.form_class(),
            'register_form': CustomUserCreationForm()
        })

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

                # Перевіряємо чи є Google акаунт прив'язаний
                next_url = '/'
                if not SocialAccount.objects.filter(user=user, provider='google').exists():
                    # Якщо немає Google акаунту - пропонуємо прив'язати
                    pass

                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'redirect_url': next_url})
                return redirect(next_url)
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
            'register_form': CustomUserCreationForm(),
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
        
        if not form.is_valid():
            logger.warning(f'Невалідна форма реєстрації: {form.errors}')
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return render(request, 'zoosvit/users/register_form.html', {'form': form}, status=400)
            return render(request, 'zoosvit/users/register.html', {'form': form})
        
        try:
            with transaction.atomic():
                user = form.save()
                logger.info(f'Успішна реєстрація користувача: {user.username} ({user.email})')
                
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
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                    messages.success(request, _('Дані успішно оновлено! ✔️'))
                    logger.info(f'Користувач {request.user.email} оновив профіль')
                    return redirect('users:profile')
            except Exception as e:
                logger.error(f'Помилка при збереженні профілю: {str(e)}')
                messages.error(request, _('Виникла помилка при збереженні. Спробуйте ще раз.'))
        else:
            logger.warning(f'Невалідна форма профілю для {request.user.email}: {form.errors}')
            messages.error(request, _('Будь ласка, виправте помилки у формі.'))
    else:
        form = ProfileForm(instance=request.user)
    
    has_google = SocialAccount.objects.filter(user=request.user, provider='google').exists()
    
    return render(request, 'zoosvit/users/profile.html', {
        'form': form,
        'has_google': has_google
    })


def password_reset_request(request):
    """View для запиту на відновлення пароля"""
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        
        if form.is_valid():
            email = form.cleaned_data['email']
            user = CustomUser.objects.get(email__iexact=email)
            
            # Генеруємо одноразовий токен
            token = secrets.token_urlsafe(32)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Зберігаємо токен в базі
            user.password_reset_token = token
            user.password_reset_token_created = timezone.now()
            user.password_reset_token_used = False
            user.save()
            
            # Формуємо посилання для відновлення
            reset_url = request.build_absolute_uri(
                f'/users/password-reset-confirm/{uid}/{token}/'
            )
            
            try:
                send_mail(
                    subject='Відновлення пароля - Laskazoo',
                    message=f'Перейдіть за посиланням для відновлення пароля:\n\n{reset_url}\n\nПосилання дійсне протягом 30 хвилин і може бути використане лише один раз.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                logger.info(f'Відправлено лист для відновлення пароля на {email}')
                
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': 'Лист відправлено на вашу пошту'})
                
                messages.success(request, 'Інструкції для відновлення пароля відправлено на вашу пошту')
                return redirect('users:login')
                
            except Exception as e:
                logger.error(f'Помилка при відправці email: {str(e)}')
                
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': 'Помилка при відправці листа'}, status=500)
                
                messages.error(request, 'Виникла помилка при відправці листа')
        
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False, 
                    'errors': form.errors
                }, status=400)
    
    return JsonResponse({'success': False, 'message': 'Невірний запит'}, status=400)


def password_reset_confirm(request, uidb64, token):
    """View для підтвердження відновлення пароля та встановлення нового"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None
    
    if user is not None and user.is_token_valid(token):
        if request.method == 'POST':
            form = SetNewPasswordForm(request.POST)
            
            if form.is_valid():
                user.set_password(form.cleaned_data['password1'])
                user.mark_token_as_used()
                
                logger.info(f'Користувач {user.email} успішно змінив пароль')
                messages.success(request, 'Пароль успішно змінено! Тепер ви можете увійти з новим паролем.')
                return redirect('users:login')
            
            return render(request, 'zoosvit/users/password_reset_confirm.html', {
                'form': form,
                'validlink': True
            })
        
        else:
            form = SetNewPasswordForm()
            return render(request, 'zoosvit/users/password_reset_confirm.html', {
                'form': form,
                'validlink': True
            })
    
    else:
        return render(request, 'zoosvit/users/password_reset_confirm.html', {
            'validlink': False
        })


def check_auth(request):
    """Перевірка чи користувач авторизований"""
    return JsonResponse({
        'authenticated': request.user.is_authenticated
    })
