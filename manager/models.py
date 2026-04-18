from django.db import models

# Create your models here.
class Warehouse(models.Model):
    warehouse_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    district = models.CharField(max_length=255)
    area = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    

class Supplier(models.Model):
    supplier_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    email = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    password = models.CharField(max_length=255)
    address = models.CharField(max_length=255, blank=True, null=True)

    class UserType(models.TextChoices):
        MANAGER = "manager"
        CUSTOMER = "customer"
        STUFF = "stuff"
    user_type = models.CharField(max_length=50, choices=UserType.choices, default=UserType.CUSTOMER)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}, {self.user_type}"

class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=255)
    brand = models.CharField(max_length=255)
    model_number = models.CharField(max_length=255)
    specs = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    weight = models.DecimalField(max_digits=10, decimal_places=2, default= 100)
    
    def __str__(self):
        return self.product_name

class Category(models.Model):
    category_id = models.AutoField(primary_key=True)
    category_name = models.CharField(max_length=50)
    
    def __str__(self):
        return self.category_name

class BelongTo_Category(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("category", "product")

class Order(models.Model):
    order_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_date = models.DateTimeField(auto_now_add=True)
    
    class Type(models.TextChoices):
        PENDING = "PENDING"
        CONFIRMED = "CONFIRMED"
        PROCESSING = "PROCESSING"
        ON_HOLD = "ON_HOLD"
        CANCELLED = "CANCELLED"
        COMPLETED = "COMPLETED"
        FAILED = "FAILED"
    status = models.CharField(max_length=50, choices=Type.choices, default=Type.PENDING)

class Order_Item(models.Model):
    order_item_id = models.IntegerField()
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()

    class Meta:
        unique_together = ("order", "order_item_id")

class Shipment_Carriers(models.Model):
    carrier_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name
    
class Inventory(models.Model):
    inventory_id = models.AutoField(primary_key=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    location = models.CharField(max_length=200, blank=True, null=True)
    quantity = models.IntegerField()
    
    def __str__(self):
        return f"{self.inventory_id}, {self.product}, {self.warehouse}" 

class Shipment(models.Model):
    shipment_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    
    shipment_date = models.DateTimeField(blank=True, null=True)
    delivery_date = models.DateTimeField(blank=True, null=True)
    carrier_partner = models.ForeignKey(Shipment_Carriers, on_delete=models.SET_NULL, blank=True, null=True)
    carrier_phone = models.CharField(max_length=20, blank=True, null=True)
    
    shipment_address = models.CharField(max_length=300)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=0)
    class Type(models.TextChoices):
        PENDING = "PENDING"
        READY_TO_SHIP = "READY_TO_SHIP"
        PICKED_UP = "PICKED_UP"
        IN_TRANSIT = "IN_TRANSIT"
        OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
        DELIVERED = "DELIVERED"
        FAILED_DELIVERY = "FAILED_DELIVERY"
        LOST = "LOST"
        
    status = models.CharField(max_length=50, choices=Type.choices, default=Type.PENDING)