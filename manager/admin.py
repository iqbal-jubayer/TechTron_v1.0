from django.contrib import admin
from .models import Warehouse, Supplier, User, Product, Category, BelongTo_Category, Order, Order_Item, Shipment_Carriers, Shipment, Inventory

# Register your models here.
admin.site.register(Warehouse)
admin.site.register(Product)
admin.site.register(Supplier)
admin.site.register(User)
admin.site.register(Category)
admin.site.register(BelongTo_Category)
admin.site.register(Order)
admin.site.register(Order_Item)
admin.site.register(Shipment_Carriers)
admin.site.register(Shipment)
admin.site.register(Inventory)