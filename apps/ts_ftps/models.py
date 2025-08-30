from django.db import models

class TSGoods(models.Model):
    # унікальний ключ
    good_id = models.CharField(max_length=64, unique=True, db_index=True)

    # текстові
    good_name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    country = models.CharField(max_length=128, blank=True, null=True)
    articul = models.CharField(max_length=128, blank=True, null=True)
    category = models.CharField(max_length=255, blank=True, null=True)
    display = models.CharField(max_length=32, blank=True, null=True)  # залишимо як текст прапор/мітка
    the_size = models.CharField(max_length=64, blank=True, null=True)
    color = models.CharField(max_length=64, blank=True, null=True)
    material = models.CharField(max_length=128, blank=True, null=True)
    fashion_name = models.CharField(max_length=255, blank=True, null=True)
    sex = models.CharField(max_length=16, blank=True, null=True)
    short_name = models.CharField(max_length=255, blank=True, null=True)
    good_type_full = models.CharField(max_length=255, blank=True, null=True)
    producer_collection_full = models.CharField(max_length=255, blank=True, null=True)
    season = models.CharField(max_length=64, blank=True, null=True)
    barcode = models.CharField(max_length=255, blank=True, null=True)
    pack = models.CharField(max_length=64, blank=True, null=True)
    pack_size = models.CharField(max_length=64, blank=True, null=True)
    power_supply = models.CharField(max_length=64, blank=True, null=True)
    age = models.CharField(max_length=64, blank=True, null=True)
    measure = models.CharField(max_length=64, blank=True, null=True)
    measure_unit = models.CharField(max_length=32, blank=True, null=True)
    equal_currency_name = models.CharField(max_length=32, blank=True, null=True)
    supplier_code = models.CharField(max_length=64, blank=True, null=True)
    analogs = models.TextField(blank=True, null=True)

    # числові/булеві
    retail_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    wholesale_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    retail_price_with_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    min_quantity_for_order = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    height = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    width = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    warehouse_quantity = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    count_units_per_box = models.IntegerField(default=0)
    closeout = models.BooleanField(default=False)

    retail_price_per_unit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    wholesale_price_per_unit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    equal_sale_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    equal_wholesale_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    prime_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "TSGoods (сирі дані Торгсофт)"
        verbose_name_plural = "TSGoods (сирі дані Торгсофт)"
        db_table = "ts_goods"

    def __str__(self):
        return f"{self.good_id} — {self.good_name or ''}".strip()
