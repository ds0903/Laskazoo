from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.translation import gettext_lazy as _
from .models import CustomUser
import re

class CustomUserCreationForm(forms.ModelForm):
    username = forms.CharField(
        required=True,
        label=_("ПІБ"),
        error_messages={
            'required': _('Будь ласка, введіть ПІБ.')
        },
        widget=forms.TextInput(attrs={'placeholder': _('Введіть ПІБ')})
    )
    
    email = forms.EmailField(
        required=True, 
        label=_("Email"), 
        error_messages={
            'required': _('Будь ласка, введіть email.'),
            'invalid': _('Введіть коректну email адресу.')
        },
        widget=forms.EmailInput(attrs={'placeholder': _('Введіть email')})
    )

    password = forms.CharField(
        label=_("Пароль"),
        widget=forms.PasswordInput(attrs={'placeholder': _('Введіть пароль')}),
        error_messages={
            'required': _('Пароль є обов\'язковим.')
        },
        help_text=_('Ваш пароль повинен містити щонайменше 4 символи.')
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password']
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError(_('Email є обов\'язковим.'))
        
        email_lower = email.lower().strip()
        
        # Перевіряємо чи існує користувач з таким email
        if CustomUser.objects.filter(email__iexact=email_lower).exists():
            raise forms.ValidationError(_('Користувач з таким email вже існує.'))
        
        return email_lower
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.set_password(self.cleaned_data['password'])
        
        if commit:
            user.save()
        return user

class AdminUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email')

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'phone_number')

class LoginForm(forms.Form):
    email = forms.EmailField(
        label=_("Email"),
        error_messages={
            'required': _('Введіть email'),
            'invalid': _('Введіть коректну email адресу')
        },
        widget=forms.EmailInput(attrs={'placeholder': _('Введіть email')})
    )
    password = forms.CharField(
        label=_("Пароль"), 
        widget=forms.PasswordInput(attrs={'placeholder': _('Введіть пароль')}),
        error_messages={'required': _('Введіть пароль')}
    )

class ProfileForm(forms.ModelForm):
    phone_number = forms.CharField(
        required=False,
        label=_('Телефон'),
        widget=forms.TextInput(attrs={
            'placeholder': '+380XXXXXXXXX',
            'class': 'phone-input',
            'maxlength': '13'
        })
    )
    
    class Meta:
        model = CustomUser
        fields = ['username', 'phone_number']
        labels = {
            'username': _('ПІБ'),
            'phone_number': _('Телефон'),
        }
        widgets = {
            'username': forms.TextInput(attrs={
                'placeholder': _('Ваше ПІБ'),
                'class': 'profile-input'
            }),
        }
        error_messages = {
            'username': {
                'required': _('Введіть ПІБ')
            }
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Видаляємо email з форми, щоб його не можна було змінювати
        if 'email' in self.fields:
            del self.fields['email']
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number', '').strip()
        
        if not phone:
            return ''
        
        # Видаляємо всі символи крім цифр і +
        phone = re.sub(r'[^\d+]', '', phone)
        
        # Якщо номер не починається з +, додаємо +38
        if phone and not phone.startswith('+'):
            if phone.startswith('380'):
                phone = '+' + phone
            elif phone.startswith('80'):
                phone = '+3' + phone
            elif phone.startswith('0'):
                phone = '+38' + phone
            else:
                phone = '+380' + phone
        
        # Перевіряємо формат українського номера
        if phone and not re.match(r'^\+380\d{9}$', phone):
            raise forms.ValidationError(_('Введіть коректний український номер телефону у форматі +380XXXXXXXXX'))
        
        return phone
