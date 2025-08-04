from django.db import models
from django.urls import reverse

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
    slug = models.SlugField(max_length=255, unique=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name     = models.CharField(max_length=255)
    slug     = models.SlugField(max_length=255, unique=True)
    sku      = models.CharField("Артикул", max_length=64)
    price    = models.DecimalField(max_digits=10, decimal_places=2)
    image    = models.ImageField(upload_to='products/', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    brand    = models.ForeignKey(Brand,    on_delete=models.CASCADE, related_name='products')
    description = models.TextField("Опис", blank=True)

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
    product   = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    sku       = models.CharField("Артикул",max_length=255)
    price     = models.DecimalField("Ціна",max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    weight    = models.DecimalField("Вага",max_digits=10, decimal_places=2)
    stock     = models.IntegerField("Наявність")
    color = models.CharField("Колір", max_length=32, blank=True, null=True)
    size = models.CharField("Розмір", max_length=32, blank=True, null=True)

    class Meta:
        unique_together = (('product', 'sku'),)
        ordering = ['product', 'sku']
        verbose_name = "Варіант товару"
        verbose_name_plural = "Варіанти товарів"

    def __str__(self):
        return f"{self.product.name} — {self.sku}"