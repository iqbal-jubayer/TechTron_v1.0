from django.shortcuts import render, HttpResponse, redirect
from manager.models import *
from django.db.models import Sum
from django.db.models import Prefetch
from django.db.models import F
from decimal import Decimal, ROUND_HALF_UP

WEBSITE_NAME = "TechTron"

def ifNotLoggedIn(req):
    if 'user_id' not in req.session:
        return redirect('/')

def ifLoggedIn(req):
    if 'user_id' in req.session:
        return redirect('/')
    
def handleNavbarLogged(req, context):
    if 'user_id' in req.session:
        context['logged_in'] = True
        user = User.objects.get(email=req.session['user_id'])
        context['user_name'] = user.first_name + " " + user.last_name
        return user

# Create your views here.
def home(req):
    product_prefetch = Prefetch(
    'belongto_category_set',  # reverse FK from Category → BelongTo_Category
    queryset=BelongTo_Category.objects.select_related('product').annotate(
        total_quantity=Sum('product__inventory__quantity')
    ),
    to_attr='products_with_quantity')
    
    categories = Category.objects.prefetch_related(product_prefetch)
    
    category_data = {}
    for cat in categories:
        category_data[cat.category_name] = []
        for bc in cat.products_with_quantity:
            category_data[cat.category_name].append({
                'product_id': bc.product.product_id,
                'product_name': bc.product.product_name,
                'brand': bc.product.brand,
                'model':bc.product.model_number,
                'price': bc.product.price,
                'total_quantity': bc.total_quantity or 0
            })

    context = {"mytitle":WEBSITE_NAME, "category_data":category_data}
    if 'user_id' in req.session:
        context['logged_in'] = True
        user = User.objects.get(email=req.session['user_id'])
        context['user_name'] = user.first_name + " " + user.last_name
    return render(req, "frontview/home.html", context)

def login(req):
    context = {"mytitle":WEBSITE_NAME}
    if 'user_id' in req.session:
        return redirect('/')
    if req.method == "POST":
        user_email = req.POST.get("email")
        user_password = req.POST.get("password")
        users = User.objects.filter(email=user_email)
        
        if len(users) > 0 and user_password == users[0].password:
            req.session['user_id'] = users[0].email
            return redirect('/')
        else:
            print("Username or Password is incorrect")
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
        if len(User.objects.filter(email=usr_email)) == 0:
            user = User.objects.create(            
            first_name = usr_first_name,
            last_name = usr_last_name,
            email = usr_email,
            password = usr_password,
            user_type = "customer")
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
    
    product = Product.objects.annotate(total_quantity=Sum('inventory__quantity')).get(product_id = id)
    if product.total_quantity is None:
        product.total_quantity = 0
    context["product"] = product
    
    if req.method == "POST":
        print(req.POST.get('qty'))
        
    handleNavbarLogged(req, context)
    return render(req, "frontview/product_details.html", context)

def place_order(req):
    if 'user_id' not in req.session:
        return redirect('/login')
    
    context = {"mytitle":WEBSITE_NAME}
    if req.method == "POST":
        qty = req.POST.get('qty')
        id = req.POST.get('id')
    
    product = Product.objects.annotate(total_quantity=Sum('inventory__quantity')).get(product_id = id)
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
            "total_product_price": int(q) * product.price
        })
    
    product_weight_cost = Decimal(qty) * product.weight * Decimal(0.1)
    product_weight_cost = product_weight_cost.quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
    context["delivery_cost"] = 70 * len(inv) + product_weight_cost
    context["total_cost"] = context["total_product_price"] + context["delivery_cost"]
    
    user = handleNavbarLogged(req, context)
    
    context["user"] = user
    
    return render(req, "frontview/place_order.html", context)

def handleInventory(product_id, qty):
    qty = int(qty)
    dat = Inventory.objects.filter(product_id=product_id, quantity__gt=0).order_by('-quantity')
    total = sum(p.quantity for p in dat)
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
    
    product = Product.objects.get(product_id=product_id)
    user = User.objects.get(email=req.session['user_id'])
    
    invent = handleInventory(product_id, qty)
    
    if user.address is None:
        return redirect('/')
    
    order = Order.objects.create(user_id = user.user_id)
    order_item = Order_Item.objects.create(order_item_id=1, quantity=qty, order_id=order.order_id, product_id=product_id)
    for inv, q in invent:
        inventory_id = inv.inventory_id
        address = user.address  
        cost = product.price * q + 70
        shipment = Shipment.objects.create(order=order, inventory=inv, shipment_address=address, shipping_cost=cost, quantity = q)
        Inventory.objects.filter(inventory_id=inventory_id).update(quantity=F('quantity')-q)
    
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
        order = Order.objects.get(order_id=id, user_id=user.user_id)
        shipments = Shipment.objects.filter(order_id=id)
        for shipment in shipments:
            inventory = Inventory.objects.get(inventory_id = shipment.inventory.inventory_id)
            inventory.quantity += shipment.quantity
            inventory.save()
        order.status = "CANCELLED"
        order.save()
    except Exception as e:
        print(e)
    return redirect('/dashboard/')


