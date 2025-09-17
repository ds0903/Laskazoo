from decimal import Decimal
from django.db import models
from django.conf import settings
from apps.products.models import Product, Product_Variant

class Order(models.Model):
    STATUS_CART = 'cart'
    STATUS_NEW = 'new'
    STATUS_IN_PROCESS = 'in_process'
    STATUS_PROCESSING = 'processing'
    STATUS_SHIPPED = 'shipped'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELED = 'canceled'

    STATUS_CHOICES = [
        (STATUS_CART, 'У кошику'),
        (STATUS_NEW, 'Нове'),
        (STATUS_IN_PROCESS, 'В процесі'),
        (STATUS_PROCESSING, 'Обробляється'),
        (STATUS_SHIPPED, 'В дорозі'),
        (STATUS_COMPLETED, 'Виконане'),
        (STATUS_CANCELED, 'Скасоване'),
    ]
    
    SALE_TYPE_CHOICES = [
        ('1', 'Роздріб'),
        ('2', 'Опт'),
    ]
    
    DELIVERY_CHOICES = [
        ('nova_poshta', 'Нова Пошта'),
        ('ukrposhta', 'Укрпошта'),
        ('pickup', 'Самовивіз'),
        ('courier', 'Кур\'єр'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='orders')
    status = models.CharField(max_length=20,
                              choices=STATUS_CHOICES,
                              default=STATUS_CART)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Клієнт
    full_name = models.CharField(max_length=255, blank=True, default='')
    phone = models.CharField(max_length=20, blank=True, default='')
    email = models.EmailField(blank=True, default='')
    
    # Опції доставки
    sale_type = models.CharField(max_length=10, choices=SALE_TYPE_CHOICES, default='1')
    delivery_condition = models.CharField(max_length=50, choices=DELIVERY_CHOICES, default='nova_poshta')
    delivery_address = models.TextField(blank=True, default='')
    comment = models.TextField(blank=True, null=True)
    order_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    
    # Для експорту
    exported = models.BooleanField(default=False)
    exported_at = models.DateTimeField(null=True, blank=True)
    
    # Старі поля для сумісності (видалимо пізніше)
    first_name = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)



    @property
    def total_amount(self):
        return sum(item.line_total for item in self.items.all())
    
    def save(self, *args, **kwargs):
        if not self.order_number and self.status != self.STATUS_CART:
            # Генеруємо унікальний номер замовлення
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            self.order_number = f"{timestamp}{self.id or ''}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Order #{self.order_number or self.id} ({self.get_status_display()})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order,
                              related_name='items',
                              on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product',
                                on_delete=models.CASCADE)
    variant = models.ForeignKey(Product_Variant, null=True, blank=True, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    retail_price = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):

        if self.variant and self.variant.product_id != self.product_id:
            raise ValueError('Variant does not belong to product')
        super().save(*args, **kwargs)

    @property
    def line_total(self):
        retail_price = self.retail_price or Decimal('0')
        return retail_price * self.quantity

    def __str__(self):
        suffix = f' / {self.variant.sku}' if self.variant_id else ''
        return f'{self.product.name}{suffix} ×{self.quantity}'
