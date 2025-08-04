from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email", error_messages={
        'required': 'Будь ласка, введіть email.'
    })

    password1 = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={'placeholder': 'Введіть пароль'}),
        error_messages={
            'required': 'Пароль є обовʼязковим.'
        }
    )

    password2 = forms.CharField(
        label="Повторіть пароль",
        widget=forms.PasswordInput(attrs={'placeholder': 'Повторіть пароль'}),
        error_messages={
            'required': 'Підтвердіть пароль.'
        }
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']
        labels = {
            'username': 'Логін',
        }
        error_messages = {
            'username': {
                'required': 'Введіть логін',
                'unique': 'Такий логін вже існує'
            }
        }

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'phone_number')

class LoginForm(forms.Form):
    username = forms.CharField(label="Логін")
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone_number']
        labels = {
            'username': 'Логін',
            'email':    'Email',
            'phone_number': 'Телефон',
        }
        widgets = {
            'username':     forms.TextInput(attrs={'placeholder': 'Ваш логін'}),
            'email':        forms.EmailInput(attrs={'placeholder': 'Ваша пошта'}),
            'phone_number': forms.TextInput(attrs={'placeholder': 'Ваш телефон'}),
        }