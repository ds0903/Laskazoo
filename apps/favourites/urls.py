from django.urls import path
from . import views

app_name = 'favourites'

urlpatterns = [
    path('', views.favourite_list, name='list'),
]
