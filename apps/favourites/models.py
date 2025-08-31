# apps/favourites/models.py
from django.db import models
from django.conf import settings

class Favourite(models.Model):
    user     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favourites')
    product  = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    variant  = models.ForeignKey('products.Product_Variant', on_delete=models.CASCADE, null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # було: ('user', 'product')
        unique_together = ('user', 'product', 'variant')
        indexes = [
            models.Index(fields=['user', 'variant']),
        ]
        ordering = ['-added_at']

    def __str__(self):
        base = f"{self.user_id} → {self.product_id}"
        return f"{base} (v={self.variant_id or '-'})"

