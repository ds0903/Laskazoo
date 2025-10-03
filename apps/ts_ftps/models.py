from django.db import models

class TSGoods(models.Model):
    # унікальний ключ
    good_id = models.CharField(max_length=64, unique=True, db_index=True)

    good_name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    new_description = models.TextField(blank=True, null=True)
    articul = models.CharField(max_length=128, blank=True, null=True)
    good_type_full = models.CharField(max_length=255, blank=True, null=True)
    barcode = models.CharField(max_length=255, blank=True, null=True)
    wholesale_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    warehouse_quantity = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    closeout = models.BooleanField(default=False)
    equal_sale_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    equal_wholesale_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "TSGoods (сирі дані Торгсофт)"
        verbose_name_plural = "TSGoods (сирі дані Торгсофт)"
        db_table = "ts_goods"

    def __str__(self):
        return f"{self.good_id} — {self.good_name or ''}".strip()
