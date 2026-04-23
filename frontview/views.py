from django.shortcuts import render, HttpResponse, redirect
from manager.models import *

from django.db import connection
from datetime import datetime



WEBSITE_NAME = "TechTron"
    
def handleNavbarLogged(req, context):
    if 'user_id' in req.session:
        context['logged_in'] = True
        email = req.session['user_id']
        user = User.objects.raw(
            f'''
            SELECT * FROM manager_user WHERE email="{email}";
            '''
        )[0]
        context['user_name'] = user.first_name + " " + user.last_name
        return user

# Create your views here.
def home(req):
    context = {"mytitle":WEBSITE_NAME}
    
    if 'user_id' in req.session:
        user_email = req.session['user_id']
        context['logged_in'] = True
        user = User.objects.raw(
            f'''
            SELECT * FROM manager_user WHERE email="{user_email}"
            '''
        )[0]
        context['user_name'] = user.first_name + " " + user.last_name
            
    categories = Category.objects.raw('''
                                        SELECT * FROM manager_category;
                                        ''') # To scap the categories
    categories_data = []
    for cat in categories:
        product_details = BelongTo_Category.objects.raw(f'''
                                                        SELECT id, 
                                                        p.product_id,
                                                        product_name,
                                                        brand, 
                                                        model_number,
                                                        price,
                                                        weight,
                                                        sum(quantity) as total_quantity 
                                                        FROM manager_belongto_category bc 
                                                        JOIN manager_category c ON bc.category_id = c.category_id 
                                                        JOIN manager_product p ON bc.product_id = p.product_id 
                                                        LEFT JOIN manager_inventory i ON i.product_id = p.product_id 
                                                        WHERE bc.category_id = {cat.category_id} GROUP BY id;
                                                        ''') # Getting product and inventory info for each category
        categories_data.append([cat, product_details])
        
    context["category_data"] = categories_data

    return render(req, "frontview/home.html", context)

def login(req):
    context = {"mytitle":WEBSITE_NAME}
    if 'user_id' in req.session:
        return redirect('/')
    
    if req.method == "POST":
        user_email = req.POST.get("email")
        user_password = req.POST.get("password")
        users = User.objects.raw(
            f'''
            SELECT * FROM manager_user WHERE email='{user_email}'
            ''')[0]
        
        if user_password == users.password:
            req.session['user_id'] = users.email
            return redirect('/')
        else:
            context["login_error"] = "Username or Password is incorrect"
    return render(req, "frontview/login.html", context)

def signup(req):
    context = {"mytitle":WEBSITE_NAME}
    
    if 'user_id' in req.session:
        return redirect('/')
    
    if req.method == "POST":
        usr_first_name = req.POST.get("firstname")
        usr_last_name = req.POST.get("lastname")
        usr_email = req.POST.get("email")
        usr_password = req.POST.get("password")
        user = User.objects.raw(
            f'''
            SELECT * FROM manager_user WHERE email = "{usr_email}"
            ''')
        if len(user) == 0:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO manager_user (first_name, last_name, email, password, user_type)
                    VALUES (%s, %s, %s, %s, %s);
                    """, (usr_first_name, usr_last_name, usr_email, usr_password, "customer"))
            print("Account Created!")
            return redirect('/login')
        else:
            context["account_exist"] = True
            print("Already Exists!")
    return render(req, "frontview/signup.html", context)

def logout(req):
    req.session.flush()
    return redirect('/')

def product_details(req, id):
    context = {"mytitle":WEBSITE_NAME}
    product = Product.objects.raw(f'''
                                  SELECT p.product_id,
                                  p.product_name,
                                  brand,
                                  model_number,
                                  price,
                                  weight,
                                  s.name as supplier_name,
                                  SUM(quantity) as total_quantity
                                  FROM manager_product p
                                  LEFT JOIN manager_inventory i ON i.product_id = p.product_id 
                                  LEFT JOIN manager_supplier s ON s.supplier_id = p.product_id 
                                  WHERE p.product_id = {id} GROUP BY p.product_id;
                                  ''')[0]
    
    context["product"] = product
    
    if product.total_quantity is None:
        product.total_quantity = 0
        
    handleNavbarLogged(req, context)
    
    return render(req, "frontview/product_details.html", context)

def place_order(req):
    if 'user_id' not in req.session:
        return redirect('/login')
    
    context = {"mytitle":WEBSITE_NAME}
    
    user = handleNavbarLogged(req, context)
    context["user"] = user
    
    if req.method == "POST":
        qty = req.POST.get('qty')
        id = req.POST.get('id')
        
    product = Product.objects.raw(
        '''
        SELECT 
        p.product_id,
        p.product_name,
        p.brand,
        p.model_number,
        p.specs,
        p.price,
        p.supplier_id,
        p.weight,
        SUM(i.quantity) as total_quantity
        FROM manager_product p 
        LEFT JOIN manager_inventory i ON i.product_id = p.product_id 
        WHERE p.product_id = %s GROUP BY p.product_id;
        ''', [id]
        )[0]
    
    if product.total_quantity is None:
        product.total_quantity = 0
        
    context["product"] = product
    context["qty"] = qty
    context["total_product_price"] = int(qty) * product.price
    
    inv = handleInventory(product.product_id, qty)
    
    context["prods"] = []
    
    for i, q in inv:
        context["prods"].append({
            "qty":q,
            "total_product_price": float(q) * float(product.price)
        })
        
    product_weight_cost = float(product.weight) * float(qty) * 0.1
    context["delivery_cost"] = 70 * len(inv) + product_weight_cost
    context["total_cost"] = float(context["total_product_price"]) + float(context["delivery_cost"])
    
    return render(req, "frontview/place_order.html", context)

def handleInventory(product_id, qty):
    qty = int(qty)
    
    dat = Inventory.objects.raw(
        '''
        SELECT
        *
        FROM manager_inventory 
        WHERE product_id = %s AND quantity > 0
        ORDER BY quantity DESC;
        ''', [product_id]
    )
    
    inv = []
    for p in dat:
        if p.quantity - qty >= 0:
            inv.append([p, qty])
            break
        else:
            inv.append([p, p.quantity])
            qty -= p.quantity
            
    return inv

def order_completion(req):
    if 'user_id' not in req.session:
        return redirect('/')
    
    product_id = req.POST.get('product_id')
    qty = int(req.POST.get('product_qty'))
    
    product = Product.objects.raw(
        '''
        SELECT
        *
        FROM manager_product
        WHERE product_id = %s;
        ''', [product_id]
    )[0]
    
    user_email = req.session['user_id']
    user = User.objects.raw(
        '''
        SELECT
        *
        FROM manager_user
        WHERE email = %s;
        ''', [user_email]
    )[0]
    
    invent = handleInventory(product_id, qty)
    
    if user.address is None:
        return redirect('/')
    
    with connection.cursor() as cursor:
        cursor.execute(
            '''
            INSERT INTO manager_order(user_id, order_date, status)
            VALUES(%s, %s, %s);
            ''', (user.user_id, datetime.now(), "PENDING"))
        order_id = cursor.lastrowid
    
    with connection.cursor() as cursor:
        cursor.execute(
            '''
            INSERT INTO manager_order_item(order_item_id, quantity, order_id, product_id)
            VALUES(%s, %s, %s, %s);
            ''', (1, qty, order_id, product_id))
        
    for inv, q in invent:
        inventory_id = inv.inventory_id
        address = user.address  
        cost = product.price * q + 70
        
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                INSERT INTO manager_shipment (order_id, inventory_id, shipment_address, shipping_cost, quantity, status)
                VALUES (%s, %s, %s, %s, %s, %s);
                ''', (order_id,inventory_id,address,cost,q, "PENDING"))
        
        inventory = Inventory.objects.raw(
            f'''
            SELECT 
            inventory_id,
            quantity 
            FROM manager_inventory WHERE inventory_id={inventory_id};
            '''
        )[0]
        inventory.quantity -= q
        with connection.cursor() as cursor:
            cursor.execute(
                f'''
                UPDATE manager_inventory
                SET quantity={inventory.quantity}
                WHERE inventory_id={inventory_id}
                '''
            )
    
    return redirect('/')

def dashboard(req):
    context = {"mytitle":WEBSITE_NAME}
    if 'user_id' not in req.session:
        return redirect('/')
    
    user = handleNavbarLogged(req,context)
    orders = Order.objects.raw(f'''
                            SELECT
                            ordr.order_id as order_id,
                            order_date,
                            ordr.status as status,
                            delivery_date,
                            carrier_phone,
                            SUM(shipping_cost) as total_cost,
                            shipment_address as address,
                            oi.quantity, 
                            p.product_id,
                            product_name,
                            brand,
                            model_number,
                            specs,
                            price,
                            weight,
                            name as supplier_name
                            FROM manager_order ordr 
                            JOIN manager_shipment shipment ON ordr.order_id = shipment.order_id 
                            JOIN manager_order_item oi ON ordr.order_id = oi.order_id 
                            JOIN manager_product p ON oi.product_id = p.product_id 
                            JOIN manager_supplier splr ON splr.supplier_id = p.supplier_id 
                            WHERE user_id = {user.user_id} 
                            GROUP BY ordr.order_id, shipment.delivery_date, carrier_phone, shipment_address, oi.quantity, p.product_id
                            ORDER BY order_date DESC;''')
        
    context["total_order"] = len(orders)
    context["pending_order"] = 0
    context["confirmed_order"] = 0
    context["completed_order"] = 0
    context["cancelled_order"] = 0
    
    for order in orders:
        stat = order.status.lower()
        if stat == "pending":
            context["pending_order"] += 1
        elif stat == "confirmed":
            context["confirmed_order"] += 1
        elif stat == "completed":
            context["completed_order"] += 1
        elif stat == "cancelled":
            context["cancelled_order"] += 1
            
    context["selected_filter"] = req.GET.get("filter")
    context["orders"] = orders
    context["user"] = user
    
    return render(req, "frontview/dashboard.html", context)

def help(req):
    context = {"mytitle":WEBSITE_NAME}
    handleNavbarLogged(req, context)
    return render(req, "frontview/help.html", context)

def cancelOrder(req,id): 
    if 'user_id' not in req.session:
        return redirect('/login')
    context = {"mytitle":WEBSITE_NAME}
    user = handleNavbarLogged(req, context)
    try:
        order = Order.objects.raw(
            f'''
            SELECT * FROM manager_order WHERE order_id={id} AND user_id={user.user_id}
            '''
        )[0]
        shipments = Shipment.objects.raw(
            f'''
            SELECT * FROM manager_shipment WHERE order_id = {id}
            '''
        )
        for shipment in shipments:
            inventory = Inventory.objects.raw(
                f'''
                SELECT * FROM manager_inventory WHERE inventory_id = {shipment.inventory.inventory_id}
                '''
            )[0]
            inventory.quantity += shipment.quantity
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    UPDATE manager_inventory 
                    SET quantity = {inventory.quantity}
                    WHERE inventory_id = {inventory.inventory_id};
                    """)
        order.status = "CANCELLED"
        with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    UPDATE manager_order 
                    SET status = "{order.status}"
                    WHERE order_id = {order.order_id};
                    """)
    except Exception as e:
        print(e)
    return redirect('/dashboard/')


