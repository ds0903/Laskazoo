# apps/orders/urls.py
from django.urls import path
from .views import order_list, order_detail

app_name = 'orders'

urlpatterns = [
    path('',      order_list,   name='list'),
    path('<int:pk>/', order_detail, name='detail'),
]
