from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone
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
    
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Готівка при отриманні'),
        ('card_online', 'Картка онлайн'),
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
    
    # Нова Пошта дані
    city = models.CharField(max_length=100, blank=True, default='')  # Назва міста
    city_ref = models.CharField(max_length=100, blank=True, default='')  # Ref міста Нової Пошти
    warehouse_ref = models.CharField(max_length=100, blank=True, default='')  # Ref відділення Нової Пошти
    novaposhta_ttn = models.CharField(max_length=100, blank=True, default='')  # ТТН (номер накладної)
    
    # Оплата
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash')
    payment_status = models.CharField(max_length=20, default='pending')  # pending, paid, failed
    payment_id = models.CharField(max_length=255, blank=True, null=True)  # ID транзакції від платіжного сервісу
    
    # Для експорту
    exported = models.BooleanField(default=False)
    exported_at = models.DateTimeField(null=True, blank=True)

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


class PaymentTransaction(models.Model):
    """
    Модель для логування всіх платіжних транзакцій
    Зберігає історію взаємодій з платіжними системами
    """
    TRANSACTION_TYPE_CHOICES = [
        ('payment', 'Оплата'),
        ('refund', 'Повернення'),
        ('callback', 'Callback'),
    ]
    
    TRANSACTION_STATUS_CHOICES = [
        ('initiated', 'Ініційовано'),
        ('processing', 'В обробці'),
        ('success', 'Успішно'),
        ('failed', 'Помилка'),
        ('cancelled', 'Скасовано'),
    ]
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='Замовлення'
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPE_CHOICES,
        default='payment',
        verbose_name='Тип транзакції'
    )
    status = models.CharField(
        max_length=20,
        choices=TRANSACTION_STATUS_CHOICES,
        default='initiated',
        verbose_name='Статус'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Сума'
    )
    currency = models.CharField(
        max_length=3,
        default='UAH',
        verbose_name='Валюта'
    )
    
    # Дані від платіжної системи
    payment_system = models.CharField(
        max_length=50,
        default='portmone',
        verbose_name='Платіжна система'
    )
    external_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='ID в платіжній системі'
    )
    
    # Request/Response для дебагу
    request_data = models.JSONField(
        blank=True,
        null=True,
        verbose_name='Дані запиту'
    )
    response_data = models.JSONField(
        blank=True,
        null=True,
        verbose_name='Дані відповіді'
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        verbose_name='Повідомлення про помилку'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Створено'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Оновлено'
    )
    completed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Завершено'
    )
    
    class Meta:
        verbose_name = 'Транзакція'
        verbose_name_plural = 'Транзакції'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order', '-created_at']),
            models.Index(fields=['external_id']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"Транзакція {self.id} | Замовлення #{self.order.order_number or self.order.id} | {self.amount} {self.currency}"
    
    def mark_as_success(self, response_data=None):
        """Позначити транзакцію як успішну"""
        self.status = 'success'
        self.completed_at = timezone.now()
        if response_data:
            self.response_data = response_data
        self.save()
    
    def mark_as_failed(self, error_message=None, response_data=None):
        """Позначити транзакцію як невдалу"""
        self.status = 'failed'
        self.completed_at = timezone.now()
        if error_message:
            self.error_message = error_message
        if response_data:
            self.response_data = response_data
        self.save()
