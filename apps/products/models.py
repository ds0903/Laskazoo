from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import MinValueValidator
from decimal import Decimal

def unique_slugify(model_cls, base_slug, pk=None, slug_field='slug'):
    """
    Генерує унікальний slug: base, base-2, base-3, ...
    Ігнорує поточний запис за pk (для оновлень).
    """
    slug = base_slug
    i = 2
    qs = model_cls.objects.all()
    if pk:
        qs = qs.exclude(pk=pk)
    while qs.filter(**{slug_field: slug}).exists():
        slug = f"{base_slug}-{i}"
        i += 1
    return slug

class Main_Categories(models.Model):
    """ 08.07.2024 Danylo Fedorenko
        В цій моделі вказані 6 головних моделей (коти, собаки, гризуни, і тд...)
    """
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    class Meta:
        verbose_name_plural = "Main_Categories"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_detail', args=[self.slug])

class Category(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    main_category = models.ForeignKey(Main_Categories, on_delete=models.CASCADE, related_name='categories')

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

    def get_url(self, name):
        return reverse(name, args=[self.slug])

class Brand(models.Model):
    name = models.CharField(max_length=255)
    brand_slug = models.SlugField(max_length=255, unique=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    country_slug = models.SlugField(max_length=255)
    country = models.CharField(max_length=255)
    def __str__(self):
        return self.name

class Product(models.Model):
    torgsoft_id = models.CharField(max_length=64, unique=True, null=True, blank=True)
    barcode = models.CharField(max_length=128, blank=True, null=True)
    name     = models.CharField(max_length=255)
    sku      = models.CharField("Артикул", max_length=64)
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True)
    image    = models.ImageField(upload_to='products/', blank=True, null=True)
    weight = models.PositiveIntegerField("Вага (г)", validators=[MinValueValidator(1)], default=0)
    color = models.CharField("Колір", max_length=32, blank=True, null=True)
    size = models.CharField("Розмір", max_length=32, blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    brand    = models.ForeignKey(Brand,    on_delete=models.CASCADE, related_name='products')
    description = models.TextField("Опис", blank=True, null=True)
    prime_cost = models.DecimalField("Собівартість", max_digits=10, decimal_places=2, default=Decimal('0.00'))
    retail_price = models.DecimalField("Ціна роздрібна", max_digits=10, decimal_places=2, default=Decimal('0.00'))
    wholesale_price = models.DecimalField("Оптова ціна", max_digits=10, decimal_places=2, default=Decimal('0.00'))
    retail_price_with_discount = models.DecimalField("Ціна роздрібна зі знижкою", max_digits=10, decimal_places=2, default=Decimal('0.00'))
    warehouse_quantity = models.IntegerField("Наявність", default=0)

    def weight_kg(self):
        return self.weight / 1000

    def weight_label(self):
        # 500 → "500g", 1000 → "1kg", 1500 → "1.5kg"
        g = self.weight
        return f"{g}g" if g < 1000 or g % 1000 != 0 else f"{g // 1000}kg"

    def save(self, *args, **kwargs):
        # Генеруємо тільки якщо порожній або якщо змінили name/sku (опц.)
        if not self.slug:
            base = slugify(f"{self.name}-{self.sku}") if self.sku else slugify(self.name)
            self.slug = unique_slugify(Product, base, pk=self.pk)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_url(self, name):
        return reverse(name, args=[self.slug])

    def get_absolute_url(self):
        return reverse(
            'products:product_detail',
            args=[
                self.category.main_category.slug,
                self.category.slug,
                self.slug
            ]
        )

class Product_Variant(models.Model):
    torgsoft_id = models.CharField(max_length=64, unique=True, null=True, blank=True)
    barcode = models.CharField(max_length=128, blank=True, null=True)
    sku       = models.CharField("Артикул",max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True)
    product   = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    weight = models.PositiveIntegerField("Вага (г)", validators=[MinValueValidator(1)], default=0)
    color = models.CharField("Колір", max_length=32, blank=True, null=True)
    size = models.CharField("Розмір", max_length=32, blank=True, null=True)
    prime_cost = models.DecimalField("Собівартість", max_digits=10, decimal_places=2, default=Decimal('0.00'))
    retail_price = models.DecimalField("Ціна роздрібна", max_digits=10, decimal_places=2, default=Decimal('0.00'))
    wholesale_price = models.DecimalField("Оптова ціна", max_digits=10, decimal_places=2, default=Decimal('0.00'))
    retail_price_with_discount = models.DecimalField("Ціна роздрібна зі знижкою", max_digits=10, decimal_places=2, default=Decimal('0.00'))
    warehouse_quantity = models.IntegerField("Наявність", default=0)

    def weight_kg(self):
        return self.weight / 1000

    def weight_label(self):
        # 500 → "500g", 1000 → "1kg", 1500 → "1.5kg"
        g = self.weight
        return f"{g}g" if g < 1000 or g % 1000 != 0 else f"{g // 1000}kg"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_parts = [self.product.name, self.weight or '', self.color or '', self.size or '']
            base = slugify("-".join([p for p in base_parts if p]))
            self.slug = unique_slugify(Product_Variant, base, pk=self.pk)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['product', 'sku']
        verbose_name = "Варіант товару"
        verbose_name_plural = "Варіанти товарів"

    def __str__(self):
        return f"{self.product.name} — {self.sku}"

class PopularProduct(models.Model):
    product   = models.OneToOneField(
        Product, on_delete=models.CASCADE, related_name='popular'
    )
    position  = models.PositiveIntegerField(default=0, help_text='Чим менше — тим вище')
    is_active = models.BooleanField(default=True)
    label     = models.CharField(max_length=30, blank=True)  # напр., «Хіт»
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products_popular'
        ordering = ['position', '-created_at']
        verbose_name = 'Популярний товар'
        verbose_name_plural = 'Популярні товари'
        indexes = [
            models.Index(fields=['is_active', 'position']),
        ]

    def __str__(self):
        return f'{self.product} (#{self.position})'