from django.shortcuts import render, HttpResponse

# Create your views here.
def dashboard(req):
    return render(req, './manager/dashboard.html')

def manage_warehouse(req):
    return render(req, './manager/manage_warehouse.html')