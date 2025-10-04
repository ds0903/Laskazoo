from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Product, Main_Categories, Category, Brand


class ProductSitemap(Sitemap):
    """Sitemap для сторінок товарів"""
    changefreq = "daily"
    priority = 0.9

    def items(self):
        return Product.objects.filter(is_active=True).select_related(
            'category__main_category', 'brand'
        )

    def location(self, obj):
        return obj.get_absolute_url()

    def lastmod(self, obj):
        # Якщо у тебе є поле updated_at, можна використати його
        return None


class MainCategorySitemap(Sitemap):
    """Sitemap для головних категорій (коти, собаки, гризуни тощо)"""
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Main_Categories.objects.filter(is_active=True)

    def location(self, obj):
        return f"/categories/{obj.slug}/"


class CategorySitemap(Sitemap):
    """Sitemap для підкатегорій"""
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Category.objects.filter(
            is_active=True,
            main_category__is_active=True
        ).select_related('main_category')

    def location(self, obj):
        return f"/categories/{obj.main_category.slug}/{obj.slug}/"


class BrandSitemap(Sitemap):
    """Sitemap для брендів"""
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return Brand.objects.filter(is_active=True)

    def location(self, obj):
        return f"/categories/brand/{obj.brand_slug}/"


class StaticPagesSitemap(Sitemap):
    """Sitemap для статичних сторінок"""
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        return [
            'home',
            'stores_map',
            'products:catalog',
        ]

    def location(self, item):
        return reverse(item)


class InfoPagesSitemap(Sitemap):
    """Sitemap для інформаційних сторінок"""
    changefreq = "monthly"
    priority = 0.4
    
    def items(self):
        return [
            'public-offer',
            'payment-delivery',
            'returns',
            'privacy',
            'contacts',
        ]
    
    def location(self, item):
        return f"/info/{item}/"
