from django.urls import path, include
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard),
    path('dashboard/edit/warehouse/', views.editWarehouse),
    path('dashboard/update/orders/', views.updateOrders),
]
