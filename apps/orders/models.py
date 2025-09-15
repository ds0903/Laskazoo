from decimal import Decimal
from django.db import models
from django.conf import settings
from apps.products.models import Product, Product_Variant

class Order(models.Model):
    STATUS_CART = 'cart'
    STATUS_NEW = 'new'
    STATUS_PROCESSING = 'processing'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELED = 'canceled'

    STATUS_CHOICES = [
        (STATUS_CART, 'У кошику'),
        (STATUS_NEW, 'Нове'),
        (STATUS_PROCESSING, 'В обробці'),
        (STATUS_COMPLETED, 'Виконане'),
        (STATUS_CANCELED, 'Скасоване'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='orders')
    status = models.CharField(max_length=20,
                              choices=STATUS_CHOICES,
                              default=STATUS_CART)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    first_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=100, blank=True)



    def __str__(self):
        return f"Order #{self.id} ({self.get_status_display()})"


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
