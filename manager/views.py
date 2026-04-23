from django.shortcuts import render, HttpResponse, redirect
from manager.models import *
from django.db import connection

CAN_DELETE = False

WEBSITE_NAME = "TechTron"

def checkAuthentication(req, context):
    if "user_id" not in req.session:
        return redirect('/')
    try:
        user_email = req.session['user_id']
        user = User.objects.raw(
            '''
            SELECT
            *
            FROM manager_user
            WHERE email=%s AND user_type=%s
            ''', [user_email,"manager"]
        )[0]
        context['logged_in'] = True
        context['user_name'] = user.first_name + " " + user.last_name
    except Exception as e:
        print(e)
        return redirect('/')

# Create your views here.
def dashboard(req):
    context = {"mytitle":WEBSITE_NAME}
    checkAuthentication(req, context)
        
    selected_filter = req.GET.get("filter")
    contents = None
    if(selected_filter == "warehouse" or selected_filter is None):
        warehouses = Warehouse.objects.raw(
            '''
            SELECT
            w.warehouse_id,
            name,
            CONCAT(area, ', ', district) as location, 
            COUNT(i.inventory_id) as total_inventory,
            SUM(quantity) as stock 
            FROM manager_warehouse w
            LEFT JOIN manager_inventory i ON w.warehouse_id = i.warehouse_id 
            GROUP BY w.warehouse_id;
            ''')
        contents = warehouses
        
    elif(selected_filter == "inventory"):
        inventory = Inventory.objects.raw('''
            SELECT
            inventory_id,
            location,
            quantity,
            w.name as warehouse_name,
            district,
            area,
            product_name,
            brand,
            model_number,
            specs,
            price,
            weight,
            s.name as supplier_name
            FROM manager_inventory i JOIN manager_warehouse w ON i.warehouse_id = w.warehouse_id 
            JOIN manager_product p ON p.product_id = i.product_id
            JOIN manager_supplier s ON p.supplier_id = s.supplier_id 
            ORDER BY i.quantity;
            ''')
        contents = inventory
        
    elif(selected_filter == "customers"):
        customers = User.objects.raw(
            '''
            SELECT
            u.user_id,
            u.first_name,
            u.last_name,
            u.email,
            u.address,
            COUNT(o.order_id) as total_order,
            0 as cancelled,
            0 as pending,
            0 as confirmed,
            0 as processing,
            0 as completed
            FROM manager_user u
            LEFT JOIN manager_order o ON u.user_id = o.user_id
            GROUP BY u.user_id;
            '''
        )
        
        for customer in customers:
            status_ = Order.objects.raw(
                '''
                SELECT
                order_id,
                status,
                count(*) as count_status
                FROM manager_order
                WHERE user_id = %s GROUP BY status;
                ''', [customer.user_id]
            )
            for stat in  status_:
                if stat.status == "PENDING":
                    customer.pending = stat.count_status
                elif stat.status == "COMPLETED":
                    customer.completed = stat.count_status
                elif stat.status == "PROCESSING":
                    customer.processing = stat.count_status
                elif stat.status == "CANCELLED":
                    customer.cancelled = stat.count_status
                elif stat.status == "CONFIRMED":
                    customer.confirmed = stat.count_status
        
        contents = customers
        
    elif selected_filter == "suppliers":
        suppliers = Supplier.objects.raw(
            '''
            SELECT
            *
            FROM manager_supplier;
            '''
            )
        contents = suppliers
        
    elif selected_filter == "categories":
        category = Category.objects.raw('''
            SELECT 
                c.category_id,
                c.category_name,
                COUNT(DISTINCT bc.product_id) AS products
            FROM manager_category c
            LEFT JOIN manager_belongto_category bc ON c.category_id = bc.category_id
            GROUP BY c.category_id, c.category_name;
            ''')
        contents = category
        
    elif selected_filter == "products":
        products = Product.objects.raw(
            '''
            SELECT 
            p.product_id,
            product_name,
            brand,
            model_number,
            specs,
            price,
            weight,
            s.name as supplier_name
            FROM manager_product p 
            LEFT JOIN manager_supplier s ON p.supplier_id = s.supplier_id;
            ''')
        product_list = []
        for product in products:
            p_dict = {
                "product":product,
                "categories":BelongTo_Category.objects.raw(
                    '''
                    SELECT id,
                    c.category_id,
                    category_name 
                    FROM manager_belongto_category bc 
                    JOIN manager_product p ON bc.product_id = p.product_id 
                    JOIN manager_category c ON c.category_id = bc.category_id 
                    WHERE p.product_id = %s;''', [product.product_id]
                )
            }
            product_list.append(p_dict)
        contents = product_list
        
    elif selected_filter == "orders":        
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
            SUM(shipping_cost) as total_cost,
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
            GROUP BY o.order_id
            ORDER BY order_date ASC;
            ''')
        contents = orders
        
    
    context['contents'] = contents
    context["selected_filter"] = selected_filter
    return render(req, "manager/dashboard.html", context)

def updateOrders(req):
    context = {"mytitle":WEBSITE_NAME}
    
    checkAuthentication(req, context)
    
    order_id = req.POST.get('order_id')
    status = req.POST.get('status')
    address = req.POST.get('address')
    try:
        order = Order.objects.raw(
            '''
            SELECT 
            *
            FROM manager_order
            WHERE order_id=%s
            ''', [order_id]
        )[0]
        
        shipments = Shipment.objects.raw(
            '''
            SELECT
            *
            FROM manager_shipment
            WHERE order_id = %s;
            ''', [order_id]
        )
        
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
                    inventory_id = shipment.inventory.inventory_id
                    inventory = Inventory.objects.raw(
                        '''
                        SELECT
                        *
                        FROM manager_inventory
                        WHERE inventory_id = %s
                        ''', [inventory_id]
                    )[0]
                    inventory.quantity += shipment.quantity
                    with connection.cursor() as cursor:
                        cursor.execute(
                            '''
                            UPDATE manager_inventory
                            SET quantity=%s
                            WHERE inventory_id=%s
                            ''', [inventory.quantity, inventory_id]
                        )
                    # inventory.save()
            order.status = status
            with connection.cursor() as cursor:
                cursor.execute(
                    '''
                    UPDATE manager_order
                    SET status=%s
                    WHERE order_id=%s
                    ''', [status, order.order_id]
                )
    except Exception as e:
        print(e)
    return redirect(f'/manager/dashboard/?filter=orders#{order_id   }')


def editWarehouse(req,id):
    context = {"mytitle":WEBSITE_NAME}
    
    checkAuthentication(req,context)
    
    warehouse = Warehouse.objects.raw(
        '''
        SELECT
        *
        FROM manager_warehouse
        WHERE warehouse_id=%s
        ''', [id]
    )[0]
    context["warehouse"] = warehouse
    
    return render(req, "manager/edit_warehouse.html", context)

def updateWarehouse(req):
    context = {"mytitle":WEBSITE_NAME}
    
    checkAuthentication(req, context)
    
    if req.method == "POST":
        warehouse_id = req.POST.get("warehouse_id")
        name = req.POST.get("warehouse_name")
        area = req.POST.get("area")
        district = req.POST.get("district")
    
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                UPDATE manager_warehouse
                SET name=%s,
                area=%s,
                district=%s
                WHERE warehouse_id=%s
                ''', [name, area, district, warehouse_id]
            )
    
    return redirect(f"/manager/dashboard/?filter=warehouse")

def addWarehouse(req):
    context = {"mytitle":WEBSITE_NAME}
    checkAuthentication(req, context)
    return render(req, "manager/add_warehouse.html",context)

def createWarehouse(req):
    context = {"mytitle":WEBSITE_NAME}
    
    checkAuthentication(req, context)
    
    if req.method == "POST":
        name = req.POST.get("name")
        area = req.POST.get("area")
        district = req.POST.get("district")
        
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                INSERT INTO manager_warehouse(name, area, district)
                VALUES(%s, %s, %s);
                ''', [name, area, district]
            )
    
    return redirect(f"/manager/dashboard/?filter=warehouse")

def deleteWarehouse(req,id):
    context = {"mytitle":WEBSITE_NAME}
    checkAuthentication(req,context)
    
    if not CAN_DELETE:
        return redirect(f"/manager/dashboard/?filter=warehouse")
    
    with connection.cursor() as cursor:
        cursor.execute(
            '''
            DELETE FROM manager_warehouse 
            WHERE warehouse_id=%s;
            ''', [id]
        )
    
    return redirect(f"/manager/dashboard/?filter=warehouse")


def editSupplier(req, id):
    context = {"mytitle":WEBSITE_NAME}
    checkAuthentication(req, context)
    
    supplier = Supplier.objects.raw(
        '''
        SELECT
        *
        FROM manager_supplier
        WHERE supplier_id=%s;
        ''', [id]
    )[0]
    
    context["supplier"] = supplier
    
    return render(req, "manager/edit_supplier.html",context)

def updateSupplier(req):
    context = {"mytitle":WEBSITE_NAME}
    checkAuthentication(req, context)
    if req.method == "POST":
        id = req.POST.get("supplier_id")
        name = req.POST.get("name")
        email = req.POST.get("email")
        address = req.POST.get("address")
        contact_person = req.POST.get("contact_person")
        
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                UPDATE manager_supplier
                SET name=%s,
                email=%s,
                address=%s,
                contact_person=%s
                WHERE supplier_id=%s;
                ''', [name, email, address, contact_person, id]
            )
    
    return redirect("/manager/dashboard/?filter=suppliers")

def addSupplier(req):
    context = {"mytitle":WEBSITE_NAME}
    checkAuthentication(req, context)
    return render(req, "manager/add_supplier.html",context)

def createSupplier(req):
    context = {"mytitle":WEBSITE_NAME}
    checkAuthentication(req, context)
    
    if req.method == "POST":
        name = req.POST.get("name")
        email = req.POST.get("email")
        address = req.POST.get("address")
        contact_person = req.POST.get("contact_person")
        
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                INSERT INTO manager_supplier (name, address, email, contact_person)
                VALUES(%s, %s, %s, %s);
                ''', [name, email, address, contact_person]
            )
    
    return redirect("/manager/dashboard/?filter=suppliers")

def deleteSupplier(req, id):
    context = {"mytitle":WEBSITE_NAME}
    checkAuthentication(req, context)
    
    if not CAN_DELETE:
        print("Cannot Delete")
        return redirect("/manager/dashboard/?filter=suppliers")
    
    with connection.cursor() as cursor:
        cursor.execute(
            '''
            DELETE FROM manager_supplier 
            WHERE supplier_id=%s;
            ''', [id]
        )
    
    return redirect("/manager/dashboard/?filter=suppliers")



def editProducts(req, id):
    context = {"mytitle":WEBSITE_NAME}
    checkAuthentication(req, context)
    
    product = Product.objects.raw(
        '''
        SELECT
        *,
        name as supplier_name
        FROM manager_product p
        JOIN manager_supplier s ON p.supplier_id = s.supplier_id
        WHERE p.product_id=%s;
        ''', [id]
    )[0]
    context["product"] = product
    
    suppliers = Supplier.objects.raw(
        '''
        SELECT *
        FROM manager_supplier;
        '''
    )
    context["suppliers"] = suppliers
    
    available_categories = Category.objects.raw(
        '''
        SELECT
        *
        FROM manager_category;
        '''
    )
    context["available_categories"] = available_categories
    
    product_category = Category.objects.raw(
        '''
        SELECT
        *
        FROM manager_belongto_category
        WHERE product_id=%s;
        ''', [id]
    )
    context["product_category"] = product_category[0]
    return render(req, "manager/edit_product.html",context)

def updateProducts(req):
    context = {"mytitle":WEBSITE_NAME}
    checkAuthentication(req, context)
    
    if req.method == "POST":
        product_id = req.POST.get("product_id")
        name = req.POST.get("name")
        brand = req.POST.get("brand")
        model = req.POST.get("model")
        specs = req.POST.get("specs")
        weight = req.POST.get("weight")
        price = req.POST.get("price")
        supplier = req.POST.get("supplier")
        
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                UPDATE manager_product
                SET product_name=%s,
                brand=%s,
                model_number=%s,
                specs=%s,
                weight=%s,
                price=%s,
                supplier_id=%s
                WHERE product_id=%s;
                ''', [name, brand, model, specs, weight, price, supplier, product_id]
            )
    
    return redirect("/manager/dashboard/?filter=products")

def addProducts(req):
    context = {"mytitle":WEBSITE_NAME}
    checkAuthentication(req, context)
    suppliers = Supplier.objects.raw(
        '''
        SELECT *
        FROM manager_supplier;
        '''
    )
    context["suppliers"] = suppliers
    return render(req, "manager/add_product.html", context)

def createProducts(req):
    context = {"mytitle":WEBSITE_NAME}
    checkAuthentication(req, context)
    
    if req.method == "POST":
        name = req.POST.get("name")
        brand = req.POST.get("brand")
        model = req.POST.get("model")
        specs = req.POST.get("specs")
        weight = req.POST.get("weight")
        price = req.POST.get("price")
        supplier = req.POST.get("supplier")
        
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                INSERT INTO manager_product(product_name, brand, model_number, specs, weight, price, supplier_id)
                VALUES(%s, %s, %s, %s, %s, %s, %s);
                ''', [name, brand, model, specs, weight, price, supplier]
            )
    
    return redirect("/manager/dashboard/?filter=products")

def deleteProducts(req, id):
    context = {"mytitle":WEBSITE_NAME}
    checkAuthentication(req, context)
    
    return HttpResponse("Delete Products")