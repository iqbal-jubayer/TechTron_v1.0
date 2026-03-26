from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.dashboard),
    path('manage_warehouse', views.manage_warehouse),
]
