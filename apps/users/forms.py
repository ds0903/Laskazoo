from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.translation import gettext_lazy as _
from .models import CustomUser

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
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone_number']
        labels = {
            'username': _('ПІБ'),
            'email': _('Email'),
            'phone_number': _('Телефон'),
        }
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': _('Ваше ПІБ')}),
            'email': forms.EmailInput(attrs={'placeholder': _('Ваша пошта')}),
            'phone_number': forms.TextInput(attrs={'placeholder': _('Ваш телефон')}),
        }
        error_messages = {
            'username': {
                'required': _('Введіть ПІБ')
            },
            'email': {
                'required': _('Введіть email'),
                'invalid': _('Введіть коректну email адресу'),
                'unique': _('Користувач з таким email вже існує')
            }
        }
