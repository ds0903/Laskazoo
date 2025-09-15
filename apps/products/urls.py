from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path("search/quick/", views.quick_search, name="quick_search"),
    path("search/suggest/", views.search_suggest, name="search_suggest"),
    path('categories/brand/<slug:brand_slug>/', views.catalog_by_brand, name='brand'),
    path('categories/country/<slug:country_slug>/', views.catalog_by_country, name='country'),
    path(
        '',
        views.catalog,
        name='catalog'
    ),

    path(
        '<slug:main_slug>/',
        views.subcategory_list,
        name='subcategory_list'
    ),

    path(
        '<slug:main_slug>/<slug:slug>/',
        views.category_list,
        name='category_products'
    ),

    path(
      '<slug:main_slug>/<slug:slug>/<slug:product_slug>/',
      views.product_detail,
      name='product_detail'
    ),
]

