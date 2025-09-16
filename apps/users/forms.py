from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True, 
        label=_("Email"), 
        error_messages={
            'required': _('Будь ласка, введіть email.'),
            'invalid': _('Введіть коректну email адресу.')
        }
    )

    password1 = forms.CharField(
        label=_("Пароль"),
        widget=forms.PasswordInput(attrs={'placeholder': _('Введіть пароль')}),
        error_messages={
            'required': _('Пароль є обов\'язковим.')
        },
        help_text=_('Ваш пароль повинен містити щонайменше 4 символи.')
    )

    password2 = forms.CharField(
        label=_("Повторіть пароль"),
        widget=forms.PasswordInput(attrs={'placeholder': _('Повторіть пароль')}),
        error_messages={
            'required': _('Підтвердіть пароль.')
        },
        help_text=_('Введіть той самий пароль для підтвердження.')
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']
        labels = {
            'username': _('Логін'),
        }
        error_messages = {
            'username': {
                'required': _('Введіть логін'),
                'unique': _('Такий логін вже існує'),
                'invalid': _('Логін може містити тільки букви, цифри та символи @/./+/-/_')
            }
        }
        
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_('Паролі не співпадають.'))
        return password2
        
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError(_('Користувач з таким логіном вже існує.'))
        return username
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError(_('Користувач з таким email вже існує.'))
        return email

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'phone_number')

class LoginForm(forms.Form):
    username = forms.CharField(
        label=_("Логін"),
        error_messages={'required': _('Введіть логін')}
    )
    password = forms.CharField(
        label=_("Пароль"), 
        widget=forms.PasswordInput,
        error_messages={'required': _('Введіть пароль')}
    )

class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone_number']
        labels = {
            'username': _('Логін'),
            'email': _('Email'),
            'phone_number': _('Телефон'),
        }
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': _('Ваш логін')}),
            'email': forms.EmailInput(attrs={'placeholder': _('Ваша пошта')}),
            'phone_number': forms.TextInput(attrs={'placeholder': _('Ваш телефон')}),
        }
        error_messages = {
            'username': {
                'required': _('Введіть логін'),
                'unique': _('Такий логін вже існує')
            },
            'email': {
                'required': _('Введіть email'),
                'invalid': _('Введіть коректну email адресу'),
                'unique': _('Користувач з таким email вже існує')
            }
        }
