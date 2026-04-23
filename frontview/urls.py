from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home),
    path('login/', views.login),
    path('signup/', views.signup),
    path('logout/', views.logout),
    path('product/product_no_<int:id>/', views.product_details),
    path('place_order/', views.place_order),
    path('order_completion/', views.order_completion),
    path('dashboard/', views.dashboard),
    path('help/', views.help),
    path('order/<int:id>/cancel/', views.cancelOrder),
    path('account_settings', views.accountSettings),
    path('update_account_info/', views.updateAccountInfo),
]
