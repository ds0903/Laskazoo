from django.contrib import admin
from .models import Main_Categories, Category, Brand, Product, PopularProduct

@admin.register(Main_Categories)
class MainCategoriesAdmin(admin.ModelAdmin):
    list_display = ('name','slug')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name','slug','main_category')

admin.site.register(Brand)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'brand', 'category', 'type', 'retail_price', 'warehouse_quantity', 'is_active')
    list_filter = ('type', 'brand', 'category', 'is_active')
    search_fields = ('name', 'sku', 'barcode')
    list_editable = ('type',)

# @admin.register(PopularProduct)
# class PopularProductAdmin(admin.ModelAdmin):
#     list_display  = ('id', 'product', 'position', 'is_active', 'label', 'created_at')
#     list_editable = ('position', 'is_active', 'label')
#     search_fields = ('product__name', 'product__sku', 'product__slug')
#     autocomplete_fields = ('product',)
#     ordering = ('position',)