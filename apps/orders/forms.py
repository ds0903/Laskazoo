from django import forms
from .models import Order

class OrderCheckoutForm(forms.ModelForm):
    # Тип доставки
    DELIVERY_CHOICES = [
        ('nova_poshta', 'Нова Пошта'),
        ('ukrposhta', 'Укрпошта'),
    ]
    
    delivery_type = forms.ChoiceField(
        choices=DELIVERY_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'delivery-radio'}),
        label='Спосіб доставки *',
        initial='nova_poshta',  # За замовчуванням Нова Пошта
        required=True
    )
    
    class Meta:
        model = Order
        fields = ['full_name', 'phone', 'email', 'delivery_address', 'comment']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # ПІБ - ОБОВ'ЯЗКОВЕ
        self.fields['full_name'].widget.attrs.update({
            'placeholder': 'Прізвище Ім\'я По-батькові',
            'required': True,
            'class': 'form-control'
        })
        self.fields['full_name'].label = 'ПІБ *'
        self.fields['full_name'].required = True
        
        # ТЕЛЕФОН - ОБОВ'ЯЗКОВИЙ
        self.fields['phone'].widget.attrs.update({
            'placeholder': '+380XXXXXXXXX',
            'required': True,
            'class': 'form-control'
        })
        self.fields['phone'].label = 'Телефон *'
        self.fields['phone'].required = True
        
        # EMAIL - ОБОВ'ЯЗКОВИЙ
        self.fields['email'].widget.attrs.update({
            'placeholder': 'your@email.com',
            'required': True,
            'class': 'form-control'
        })
        self.fields['email'].label = 'Email *'
        self.fields['email'].required = True
        
        # АДРЕСА ДОСТАВКИ - ОБОВ'ЯЗКОВА
        self.fields['delivery_address'].widget = forms.Textarea(attrs={
            'rows': 2,
            'placeholder': 'Вкажіть адресу доставки',
            'class': 'form-control',
            'required': True
        })
        self.fields['delivery_address'].label = 'Адреса доставки *'
        self.fields['delivery_address'].required = True
        
        # Коментар - НЕ обов'язковий
        self.fields['comment'].widget = forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Код під\'їзду, побажання...',
            'class': 'form-control'
        })
        self.fields['comment'].label = 'Коментар до замовлення'
        self.fields['comment'].required = False
        
    def clean_full_name(self):
        full_name = self.cleaned_data.get('full_name')
        if not full_name or not full_name.strip():
            raise forms.ValidationError('Поле ПІБ є обов\'язковим для заповнення')
        return full_name.strip()
        
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone or not phone.strip():
            raise forms.ValidationError('Поле телефон є обов\'язковим для заповнення')
        return phone.strip()
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email or not email.strip():
            raise forms.ValidationError('Поле email є обов\'язковим для заповнення')
        return email.strip()
        
    def clean_delivery_address(self):
        delivery_address = self.cleaned_data.get('delivery_address')
        if not delivery_address or not delivery_address.strip():
            raise forms.ValidationError('Поле адреса доставки є обов\'язковим для заповнення')
        return delivery_address.strip()
        
    def clean(self):
        cleaned_data = super().clean()
        delivery_type = cleaned_data.get('delivery_type')
        
        # Перевіряємо, що тип доставки вибраний
        if not delivery_type:
            raise forms.ValidationError('Виберіть тип доставки')
            
        return cleaned_data
