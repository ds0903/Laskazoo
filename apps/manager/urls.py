from django.urls import path
from . import views

app_name = 'manager'

urlpatterns = [
    path('', views.manager_dashboard, name='dashboard'),
    path('users/', views.manager_users, name='users'),
    path('orders/', views.manager_orders, name='orders'),
    path('orders/<int:order_id>/', views.manager_order_detail, name='order_detail'),
    path('import/', views.manager_import_products, name='import_products'),
    
    # API endpoints
    path('api/search-ts-goods/', views.search_ts_goods, name='search_ts_goods'),
    path('api/create-products/', views.create_products_from_ts, name='create_products'),
    path('api/categories-brands/', views.get_categories_and_brands, name='categories_brands'),
]
