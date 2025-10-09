from django.urls import path
from .views import UserLoginView, UserLogoutView, register
from . import views

app_name = 'users'

urlpatterns = [
    path('login/',    UserLoginView.as_view(),  name='login'),
    path('logout/',   UserLogoutView.as_view(), name='logout'),
    path('register/', register,                 name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('password-reset-confirm/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('check-auth/', views.check_auth, name='check_auth'),
]
