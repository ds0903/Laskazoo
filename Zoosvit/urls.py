"""
URL configuration for Zoosvit project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from Zoosvit import views
from django.conf import settings
from django.conf.urls.static import static
from django.templatetags.static import static as static_url
from django.views.generic.base import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('categories/', include('apps.products.urls')),
    path('users/', include(('apps.users.urls','users'), namespace='users')),
    path('orders/',     include('apps.orders.urls',     namespace='orders')),
    path('favourites/', include('apps.favourites.urls', namespace='favourites')),
    path('stores/', views.stores_map, name='stores_map'),
    path('info/<slug:slug>/', views.info_page, name='info_page'),
    path("api/torgsoft/", include("apps.ts_ftps.urls")),
    path("favicon.ico",RedirectView.as_view(url=static_url("zoosvit/img/favicon.ico"), permanent=True)),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)