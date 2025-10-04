from django.urls import path
from . import views

app_name = 'manager'

urlpatterns = [
    path('', views.manager_dashboard, name='dashboard'),
    path('users/', views.manager_users, name='users'),
    path('orders/', views.manager_orders, name='orders'),
    path('orders/<int:order_id>/', views.manager_order_detail, name='order_detail'),
    path('import/', views.manager_import_products, name='import_products'),
    
    # Банери
    path('banners/', views.manager_banners, name='banners'),
    path('banners/add/', views.banner_add, name='banner_add'),
    path('banners/<int:banner_id>/update/', views.banner_update, name='banner_update'),
    path('banners/<int:banner_id>/delete/', views.banner_delete, name='banner_delete'),
    
    # Популярні товари
    path('popular-products/', views.manager_popular_products, name='popular_products'),
    path('popular-products/add/', views.popular_product_add, name='popular_product_add'),
    path('popular-products/<int:popular_id>/update/', views.popular_product_update, name='popular_product_update'),
    path('popular-products/<int:popular_id>/delete/', views.popular_product_delete, name='popular_product_delete'),
    
    # Популярні категорії
    path('popular-categories/', views.manager_popular_categories, name='popular_categories'),
    path('popular-categories/add/', views.popular_category_add, name='popular_category_add'),
    path('popular-categories/<int:popular_id>/update/', views.popular_category_update, name='popular_category_update'),
    path('popular-categories/<int:popular_id>/delete/', views.popular_category_delete, name='popular_category_delete'),
    
    # API endpoints
    path('api/search-ts-goods/', views.search_ts_goods, name='search_ts_goods'),
    path('api/create-products/', views.create_products_from_ts, name='create_products'),
    path('api/categories-brands/', views.get_categories_and_brands, name='categories_brands'),
    path('api/reorder-banners/', views.reorder_banners, name='reorder_banners'),
    path('api/reorder-popular-products/', views.reorder_popular_products, name='reorder_popular_products'),
    path('api/reorder-popular-categories/', views.reorder_popular_categories, name='reorder_popular_categories'),
]
