from django.urls import path, include
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard),
    
    path('dashboard/edit/warehouse/<int:id>', views.editWarehouse),
    path('dashboard/update/warehouse/', views.updateWarehouse),
    path('dashboard/add/warehouse/', views.addWarehouse),
    path('dashboard/create/warehouse/', views.createWarehouse),
    path('dashboard/delete/warehouse/<int:id>', views.deleteWarehouse),
    
    path('dashboard/edit/suppliers/<int:id>', views.editSupplier),
    path('dashboard/update/suppliers/', views.updateSupplier),
    path('dashboard/add/suppliers/', views.addSupplier),
    path('dashboard/create/suppliers/', views.createSupplier),
    path('dashboard/delete/suppliers/<int:id>', views.deleteSupplier),
    
    path('dashboard/edit/products/<int:id>', views.editProducts),
    path('dashboard/update/products/', views.updateProducts),
    path('dashboard/add/products/', views.addProducts),
    path('dashboard/create/products/', views.createProducts),
    path('dashboard/delete/products/<int:id>', views.deleteProducts),
    
    path('dashboard/update/orders/', views.updateOrders),
]
