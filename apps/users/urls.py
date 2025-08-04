# users/urls.py
from django.urls import path
from .views import UserLoginView, UserLogoutView, register
from . import views

urlpatterns = [
    path('login/',    UserLoginView.as_view(),  name='login'),
    path('logout/',   UserLogoutView.as_view(), name='logout'),
    path('register/', register,                 name='register'),
    path('profile/', views.profile_view, name='profile'),
]
