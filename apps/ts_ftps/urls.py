from django.urls import path
from .views import TorgsoftNotifyView

urlpatterns = [
    path("notify/", TorgsoftNotifyView.as_view(), name="ts-notify"),
]
