from django.urls import path
from . import views

app_name = 'favourites'

urlpatterns = [
    path('', views.favourite_list, name='list'),
    path('toggle/<int:pk>/', views.toggle, name='toggle'),
    path('api/count/', views.api_count, name='api_count'),
]
