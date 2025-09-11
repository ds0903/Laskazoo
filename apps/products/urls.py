# apps/products/urls.py
from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path("search/quick/", views.quick_search, name="quick_search"),
    path("search/suggest/", views.search_suggest, name="search_suggest"),
    path('categories/brand/<slug:brand_slug>/', views.catalog_by_brand, name='brand'),
    path('categories/country/<slug:country_slug>/', views.catalog_by_country, name='country'),
    # 1) /categories/ — головні категорії
    path(
        '',
        views.catalog,
        name='catalog'
    ),

    # 2) /categories/cats/ — підкатегорії для головної "cats"
    path(
        '<slug:main_slug>/',
        views.subcategory_list,
        name='subcategory_list'
    ),

    # 3) /categories/cats/cats_food/ — продукти підкатегорії "cats_food"
    path(
        '<slug:main_slug>/<slug:slug>/',
        views.category_list,
        name='category_products'
    ),

    # 4) /categories/<main_slug>/<slug>/<product_slug>/ — детально про товар
    path(
      '<slug:main_slug>/<slug:slug>/<slug:product_slug>/',
      views.product_detail,
      name='product_detail'
    ),
]

