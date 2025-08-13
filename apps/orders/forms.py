from django import forms
from .models import Order

class OrderCheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name', 'phone', 'city']  # додай сюди інші поля адреси/оплати
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'Ваше ім’я'}),
            'phone':      forms.TextInput(attrs={'placeholder': 'Телефон'}),
            'city':       forms.TextInput(attrs={'placeholder': 'Місто або індекс'}),
        }
