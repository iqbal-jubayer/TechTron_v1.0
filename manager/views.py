from django.shortcuts import render, HttpResponse, redirect
from manager.models import *

WEBSITE_NAME = "TechTron"

# Create your views here.
def dashboard(req):
    context = {"mytitle":WEBSITE_NAME}
    if "user_id" not in req.session:
        return redirect('/')
    try:
        user = User.objects.get(email = req.session['user_id'], user_type="manager")
        context['logged_in'] = True
        context['user_name'] = user.first_name + " " + user.last_name
    except Exception as e:
        return redirect('/')
        
    selected_filter = req.GET.get("filter")
    contents = None
    if(selected_filter == "warehouse" or selected_filter is None):
        warehouses = Warehouse.objects.raw('''SELECT w.warehouse_id, name, CONCAT(area, ', ', district) as location, 
                                           COUNT(i.inventory_id) as total_inventory, SUM(quantity) as stock 
                                           FROM manager_warehouse w LEFT JOIN manager_inventory i ON w.warehouse_id = i.warehouse_id GROUP BY w.warehouse_id;''')
        contents = warehouses
        
    elif(selected_filter == "inventory"):
        inventory = Inventory.objects.raw("SELECT inventory_id, location, quantity, w.name as warehouse_name, district, area, product_name, brand, model_number, specs, price, weight, s.name as supplier_name FROM manager_inventory i JOIN manager_warehouse w ON i.warehouse_id = w.warehouse_id JOIN manager_product p ON p.product_id = i.product_id JOIN manager_supplier s ON p.supplier_id = s.supplier_id ORDER BY i.quantity;")
        contents = inventory
        
    elif(selected_filter == "customers"):
        customers = User.objects.raw('''SELECT u.user_id, first_name, last_name, email, address,\
            COUNT(o.order_id) as total_order, \
            (SELECT COUNT(*) FROM manager_user u1 JOIN manager_order o1 ON u1.user_id = o1.user_id WHERE o1.status = "CANCELLED" AND u1.user_id = u.user_id) as cancelled,\
            (SELECT COUNT(*) FROM manager_user u1 JOIN manager_order o1 ON u1.user_id = o1.user_id WHERE o1.status = "PENDING" AND u1.user_id = u.user_id) as pending,\
            (SELECT COUNT(*) FROM manager_user u1 JOIN manager_order o1 ON u1.user_id = o1.user_id WHERE o1.status = "CONFIRMED" AND u1.user_id = u.user_id) as confirmed,\
            (SELECT COUNT(*) FROM manager_user u1 JOIN manager_order o1 ON u1.user_id = o1.user_id WHERE o1.status = "PROCESSING" AND u1.user_id = u.user_id) as processing,\
            (SELECT COUNT(*) FROM manager_user u1 JOIN manager_order o1 ON u1.user_id = o1.user_id WHERE o1.status = "COMPLETED" AND u1.user_id = u.user_id) as completed\
            FROM manager_user u LEFT JOIN manager_order o ON u.user_id = o.user_id GROUP BY u.user_id;''')
        contents = customers
        
    elif selected_filter == "suppliers":
        suppliers = Supplier.objects.filter()
        contents = suppliers
        
    elif selected_filter == "categories":
        category = Category.objects.raw('''
        SELECT 
            c.category_id,
            c.category_name,
            COUNT(DISTINCT bc.product_id) AS products
        FROM manager_category c
        LEFT JOIN manager_belongto_category bc 
            ON c.category_id = bc.category_id
        GROUP BY c.category_id, c.category_name;
        ''')
        contents = category
        
    elif selected_filter == "products":
        products = Product.objects.raw('''SELECT p.product_id, product_name, brand, model_number, specs, price, weight, s.name as supplier_name
                                        FROM manager_product p LEFT JOIN manager_supplier s ON p.supplier_id = s.supplier_id;''')
        product_list = []
        for product in products:
            p_dict = {
                "product":product,
                "categories":BelongTo_Category.objects.raw(f'''SELECT id, c.category_id, category_name FROM manager_belongto_category bc JOIN manager_product p ON bc.product_id = p.product_id JOIN manager_category c ON c.category_id = bc.category_id WHERE p.product_id = {product.product_id};''')
            }
            product_list.append(p_dict)
        contents = product_list
        
    elif selected_filter == "orders":
        products = Product.objects.raw('''SELECT p.product_id, product_name, brand, model_number, specs, price, weight, s.name as supplier_name
                                        FROM manager_product p LEFT JOIN manager_supplier s ON p.supplier_id = s.supplier_id;''')
        product_list = []
        for product in products:
            p_dict = {
                "product":product,
                "categories":BelongTo_Category.objects.raw(f'''SELECT id, c.category_id, category_name FROM manager_belongto_category bc JOIN manager_product p ON bc.product_id = p.product_id JOIN manager_category c ON c.category_id = bc.category_id WHERE p.product_id = {product.product_id};''')
            }
            product_list.append(p_dict)
        
        orders = Order.objects.raw('''
                                    SELECT
                                    id, 
                                    oi.quantity as total_quantity,
                                    oi.order_id,
                                    oi.product_id,
                                    order_date,
                                    o.status as order_status,
                                    first_name,
                                    last_name,
                                    u.email,
                                    shipment_address as address,
                                    shipping_cost,
                                    w.name as warehouse,
                                    product_name,
                                    brand,
                                    model_number,
                                    price,
                                    weight,
                                    sp.name as supplier_name,
                                    sp.email as supplier_email,
                                    contact_person
                                    FROM manager_order_item oi 
                                    JOIN manager_order o ON oi.order_id = o.order_id 
                                    JOIN manager_user u ON o.user_id = u.user_id
                                    JOIN manager_shipment sh ON sh.order_id = o.order_id
                                    JOIN manager_inventory i ON i.inventory_id = sh.inventory_id
                                    JOIN manager_warehouse w ON w.warehouse_id = i.warehouse_id
                                    JOIN manager_product p ON p.product_id = oi.product_id
                                    JOIN manager_supplier sp ON sp.supplier_id = p.supplier_id
                                    ORDER BY order_date DESC;
                                   ''')
        contents = orders
        
    
    context['contents'] = contents
    context["selected_filter"] = selected_filter
    return render(req, "manager/dashboard.html", context)

def updateOrders(req):
    context = {"mytitle":WEBSITE_NAME}
    if "user_id" not in req.session:
        return redirect('/')
    
    try:
        user = User.objects.get(email = req.session['user_id'], user_type="manager")
        context['logged_in'] = True
        context['user_name'] = user.first_name + " " + user.last_name
    except Exception as e:
        return redirect('/')
    
    order_id = req.POST.get('order_id')
    status = req.POST.get('status')
    address = req.POST.get('address')
    try:
        order = Order.objects.get(order_id=order_id)
        shipments = Shipment.objects.filter(order_id=order_id)
        for shipment in shipments:
            if shipment.shipment_address != address:
                shipment.shipment_address = address
                shipment.save()
        if status == "1":
            status = "PENDING"
        elif status == "2":
            status = "PROCESSING"
        elif status == "3":
            status = "CONFIRMED"
        elif status == "4":
            status = "COMPLETED"
        elif status == "5":
            status = "CANCELLED"
        if(order.status != status):
            if status == "CANCELLED":
                for shipment in shipments:
                    inventory = Inventory.objects.get(inventory_id = shipment.inventory.inventory_id)
                    inventory.quantity += shipment.quantity
                    inventory.save()
            order.status = status
            order.save()
    except Exception as e:
        print(e)
    return redirect(f'/manager/dashboard/?filter=orders#{order_id   }')


def editWarehouse(req):
    context = {"mytitle":WEBSITE_NAME}
    if "user_id" not in req.session:
        return redirect('/')
    try:
        user = User.objects.get(email = req.session['user_id'], user_type="manager")
        context['logged_in'] = True
        context['user_name'] = user.first_name + " " + user.last_name
    except Exception as e:
        return redirect('/')
    
    
    warehouse_id = req.POST.get("warehouse_id")
    warehouse = Warehouse.objects.get(warehouse_id=warehouse_id)
    inventories = Inventory.objects.filter(warehouse_id=warehouse_id)
    context["warehouse"] = warehouse
    context["inventories"] = inventories
    return render(req, "manager/edit_warehouse.html", context)