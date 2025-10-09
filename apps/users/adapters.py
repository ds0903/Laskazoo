from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter
from django.shortcuts import redirect
from django.contrib import messages


class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        if sociallogin.is_existing:
            return
        
        if 'email' not in sociallogin.account.extra_data:
            return
            
        email = sociallogin.account.extra_data['email']
        
        try:
            from apps.users.models import CustomUser
            user = CustomUser.objects.get(email__iexact=email)
            sociallogin.connect(request, user)
            messages.success(request, f'Ваш Google акаунт успішно підключено!')
        except CustomUser.DoesNotExist:
            pass
    
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        
        if sociallogin.account.provider == 'google':
            if 'name' in data:
                user.username = data['name']
            elif 'given_name' in data and 'family_name' in data:
                user.username = f"{data['given_name']} {data['family_name']}"
            elif 'given_name' in data:
                user.username = data['given_name']
            else:
                user.username = data.get('email', '').split('@')[0]
        
        return user
    
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        messages.success(request, f'Вітаємо, {user.username}! Ваш акаунт успішно створено.')
        return user


class MyAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return True
