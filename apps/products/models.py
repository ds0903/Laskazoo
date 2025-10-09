from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.db.models.functions import Now
from decimal import Decimal
from unidecode import unidecode

def slugify_smart(value: str, *, allow_unicode=False) -> str:
    """
    Транслітерація у латиницю + slugify.
    Напр.: "Лапи Преміум" -> "lapy-premium"
    """
    if not value:
        return ""
    s = str(value)
    if unidecode:
        s = unidecode(s)  # кирилиця -> латиниця
    return slugify(s, allow_unicode=allow_unicode)  # зазвич. ASCII

def slug_base(*parts: str, fallback: str = "item") -> str:
    """
    Склеює непорожні частини, латинізує та slugify.
    """
    cleaned = [str(p).strip() for p in parts if p and str(p).strip()]
    if cleaned:
        return slugify_smart("-".join(cleaned))
    return fallback

def unique_slugify(model_cls, base_slug, pk=None, slug_field='slug'):
    """
    Генерує унікальний slug: base, base-2, base-3, ...
    Ігнорує поточний запис за pk (для оновлень).
    """
    slug = base_slug or "item"
    i = 2
    qs = model_cls.objects.all()
    if pk:
        qs = qs.exclude(pk=pk)
    while qs.filter(**{slug_field: slug}).exists():
        slug = f"{base_slug}-{i}" if base_slug else f"item-{i}"
        i += 1
    return slug

class Main_Categories(models.Model):
    """ 08.07.2024 Danylo Fedorenko
        В цій моделі вказані 6 головних моделей (коти, собаки, гризуни, і тд...)
    """
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    is_active = models.BooleanField(
        default=True,
        db_index=True,
        db_default=True,
    )

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

    is_active = models.BooleanField(
        default=True,
        db_index=True,
        db_default=True,
    )

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

    is_active = models.BooleanField(
        default=True,
        db_index=True,
        db_default=True,
    )

    def __str__(self):
        return self.name

class Product(models.Model):
    TYPE_CHOICES = [
        ('package', 'В упаковці'),
        ('weight', 'На вагу'),
        ('pouch', 'Паучі'),
        ('can', 'Консерва'),
        ('treats_package', 'Смаколики в упаковці'),
        ('treats_weight', 'Смаколики на вагу'),
        ('treats_piece', 'Смаколики поштучно'),
    ]
    
    torgsoft_id = models.CharField(max_length=64, unique=True, null=True, blank=True)
    barcode = models.CharField(max_length=128, blank=True, null=True)
    name     = models.CharField(max_length=255, blank=True, null=True)
    sku       = models.CharField("Артикул", max_length=255, blank=True, null=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True)
    image    = models.ImageField(upload_to='products/', blank=True, null=True)
    weight = models.PositiveIntegerField("Вага (г)", validators=[MinValueValidator(1)], db_default=0)
    color = models.CharField("Колір", max_length=32, blank=True, null=True)
    size = models.CharField("Розмір", max_length=32, blank=True, null=True)
    type = models.CharField("Тип", max_length=32, choices=TYPE_CHOICES, blank=True, null=True, db_index=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    brand    = models.ForeignKey(Brand,    on_delete=models.CASCADE, related_name='products')
    description = models.TextField("Опис", blank=True, null=True)
    # prime_cost = models.DecimalField("Собівартість", max_digits=10, decimal_places=2, default=Decimal('0.00'))
    retail_price = models.DecimalField("Ціна роздрібна", max_digits=10, decimal_places=2, db_default=Decimal('0.00'))
    # wholesale_price = models.DecimalField("Оптова ціна", max_digits=10, decimal_places=2, default=Decimal('0.00'))
    retail_price_with_discount = models.DecimalField("Ціна роздрібна зі знижкою", max_digits=10, decimal_places=2, db_default=Decimal('0.00'))
    original_bag_weight_kg = models.DecimalField(
        "Оригінальна вага мішка, кг",
        max_digits=6, decimal_places=3,
        null=True, blank=True
    )
    warehouse_quantity = models.IntegerField("Наявність", db_default=0)


    is_active = models.BooleanField(
        default=True,
        db_index=True,
        db_default=True,
    )

    def rebuild_slug(self):
        base = slug_base(self.name, self.sku) or slug_base(self.torgsoft_id) or slug_base(self.barcode)
        self.slug = unique_slugify(Product, base, pk=self.pk)

    def weight_kg(self):
        return self.weight / 1000

    def weight_label(self):
        # 500 → "500g", 1000 → "1kg", 1500 → "1.5kg"
        g = self.weight
        return f"{g}g" if g < 1000 or g % 1000 != 0 else f"{g // 1000}kg"

    def save(self, *args, **kwargs):
        # Генеруємо тільки якщо порожній
        # if not self.slug:
        base = slug_base(self.name, self.sku)
        if base == "item":  # якщо і name, і sku порожні
            base = slug_base(self.torgsoft_id) if self.torgsoft_id else slug_base(self.barcode)
        self.slug = unique_slugify(Product, base, pk=self.pk)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_url(self, name):
        return reverse(name, args=[self.slug])

    def get_absolute_url(self):
        cat = getattr(self, 'category', None)
        main = getattr(cat, 'main_category', None)
        if not (self.slug and cat and cat.slug and main and getattr(main, 'slug', None)):
            return ''  # ← важливо: не викликаємо reverse з порожніми значеннями
        return reverse(
            'products:product_detail',
            args=[main.slug, cat.slug, self.slug]
        )

class Product_Variant(models.Model):
    torgsoft_id = models.CharField(max_length=64, unique=True, null=True, blank=True)
    barcode = models.CharField(max_length=128, blank=True, null=True)
    name     = models.CharField(max_length=255, blank=True, null=True)
    sku       = models.CharField("Артикул", max_length=255, blank=True, null=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True)
    product   = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    weight = models.PositiveIntegerField("Вага (г)", validators=[MinValueValidator(1)], db_default=0)
    color = models.CharField("Колір", max_length=32, blank=True, null=True)
    size = models.CharField("Розмір", max_length=32, blank=True, null=True)
    # prime_cost = models.DecimalField("Собівартість", max_digits=10, decimal_places=2, default=Decimal('0.00'))
    retail_price = models.DecimalField("Ціна роздрібна", max_digits=10, decimal_places=2, db_default=Decimal('0.00'))
    # wholesale_price = models.DecimalField("Оптова ціна", max_digits=10, decimal_places=2, default=Decimal('0.00'))
    retail_price_with_discount = models.DecimalField("Ціна роздрібна зі знижкою", max_digits=10, decimal_places=2, db_default=Decimal('0.00'))
    original_bag_weight_kg = models.DecimalField(
        "Оригінальна вага мішка, кг",
        max_digits=6, decimal_places=3,
        null=True, blank=True
    )
    warehouse_quantity = models.IntegerField("Наявність", db_default=0)

    is_active = models.BooleanField(
        default=True,
        db_index=True,
        db_default=True,
    )

    def rebuild_slug(self):
        base = slug_base(
            self.product.name if self.product_id and getattr(self, 'product', None) and self.product.name else None,
            self.weight, self.color, self.size, self.sku
        )
        if base == "item":
            base = slug_base(self.barcode) if self.barcode else slug_base(self.torgsoft_id, fallback="variant")
        self.slug = unique_slugify(Product_Variant, base, pk=self.pk)

    def weight_kg(self):
        return self.weight / 1000

    def weight_label(self):
        # 500 → "500g", 1000 → "1kg", 1500 → "1.5kg"
        g = self.weight
        return f"{g}g" if g < 1000 or g % 1000 != 0 else f"{g // 1000}kg"

    def save(self, *args, **kwargs):
        # if not self.slug:
        base = slug_base(
            self.product.name if self.product_id and getattr(self, 'product', None) and self.product.name else None,
            self.weight, self.color, self.size, self.sku
        )
        if base == "item":
            base = slug_base(self.barcode) if self.barcode else slug_base(self.torgsoft_id, fallback="variant")
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
    is_active = models.BooleanField(default=True, db_index=True, db_default=True)
    label     = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False,
                                      db_default=Now())
    updated_at = models.DateTimeField(default=timezone.now,
                                      db_default=Now())

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

class PopularCategory(models.Model):
    """
    Мінімальна обгортка над Category для блоку 'Популярні категорії':
    тільки увімкнено/вимкнено + timestamps.
    """
    category   = models.OneToOneField(
        Category,
        on_delete=models.CASCADE,
        related_name='popular_category'   # одна категорія = один запис у популярних
    )
    is_active = models.BooleanField(default=True, db_index=True, db_default=True)
    position  = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now, editable=False,
                                      db_default=Now())
    updated_at = models.DateTimeField(default=timezone.now,
                                      db_default=Now())

    class Meta:
        db_table = 'products_popular_categories'
        ordering = ['position', '-created_at']
        verbose_name = 'Популярна категорія'
        verbose_name_plural = 'Популярні категорії'
        indexes = [
            models.Index(fields=['is_active', 'position']),
        ]

    def __str__(self):
        return f"{self.category.name} ({'ON' if self.is_active else 'OFF'})"

    @property
    def url(self):
        """/categories/<main>/<category>/ — під твій роутінг."""
        main = self.category.main_category.slug
        cat  = self.category.slug
        return f"/categories/{main}/{cat}/"

    @property
    def image(self):
        """Картинка беремо з Category (фолбек у шаблоні)."""
        return self.category.image

    @property
    def title(self):
        return self.category.name