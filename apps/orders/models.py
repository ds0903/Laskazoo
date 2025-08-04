# apps/orders/models.py
from django.db import models
from django.conf import settings

class Order(models.Model):
    STATUS_NEW        = 'new'
    STATUS_PROCESSING = 'processing'
    STATUS_SHIPPED    = 'shipped'
    STATUS_COMPLETED  = 'completed'

    STATUS_CHOICES = [
        (STATUS_NEW,        'Нове'),
        (STATUS_PROCESSING, 'В обробці'),
        (STATUS_SHIPPED,    'Відправлене'),
        (STATUS_COMPLETED,  'Завершене'),
    ]

    user       = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    status     = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_NEW
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name        = 'Замовлення'
        verbose_name_plural = 'Замовлення'

    def __str__(self):
        return f"#{self.pk} — {self.get_status_display()}"
