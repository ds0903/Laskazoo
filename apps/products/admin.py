from django.contrib import admin
from .models import Main_Categories, Category, Brand, Product

@admin.register(Main_Categories)
class MainCategoriesAdmin(admin.ModelAdmin):
    list_display = ('name','slug')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name','slug','main_category')

admin.site.register(Brand)
admin.site.register(Product)

