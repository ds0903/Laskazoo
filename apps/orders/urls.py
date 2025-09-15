from django.urls import path
from .views import order_list, order_detail
from . import views

app_name = 'orders'

urlpatterns = [
    path('',      order_list,   name='list'),
    path('<int:pk>/', order_detail, name='detail'),
    path('add/<int:product_id>/', views.add_to_cart, name='add'),
    path('add-variant/<int:variant_id>/', views.add_variant_to_cart, name='add_variant'),
    path('cart/', views.cart_detail, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('history/', views.orders_list, name='history'),

    path('api/cart-modal/', views.cart_modal, name='cart_modal'),
    path('api/cart-count/', views.api_cart_summary, name='api_cart_summary'),

    path('item/<int:item_id>/inc/', views.cart_item_inc, name='item_inc'),
    path('item/<int:item_id>/dec/', views.cart_item_dec, name='item_dec'),
    path('item/<int:item_id>/remove/', views.cart_item_remove, name='item_remove'),
    path('item/<int:item_id>/set-qty/', views.item_set_qty, name='item_set_qty'),
    path('clear/', views.cart_clear, name='clear'),
]
