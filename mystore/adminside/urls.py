from django.urls import path
from . import views

urlpatterns = [
    path('admin/', views.home, name='admin_home'),
    path('login/', views.adminlogin, name='adminlogin'),
    path('logout/',views.adminlogout, name='adminlogout'),
   
    path('customer/', views.user_list, name='admin_customer'),
    path('customer/<int:id>/', views.user_manage, name='user_manage'),
   
    path('products/', views.products_manage, name='admin_product'),
    path('product_list/<int:id>', views.product_list, name='product_list'),
    path('add_products/', views.add_product, name='add_product'),
    path('edit_products/<int:id>/', views.edit_product, name='edit_product'),

    path('category/', views.manage_category, name='admin_category'),
    path('add_category/', views.add_category, name='add_category'),
    path('edit_category/<int:id>/', views.edit_category, name='edit_category'),

    path('variant/<int:id>/', views.variant, name='variant'),
    path('add_variant/<int:id>/', views.add_variant, name='add_variant'),
    path('edit_variant/<int:id>/', views.edit_variant, name='edit_variant'),

    path('order/', views.order, name='admin_order'),
    path('order_detail/<int:id>/', views.order_detail, name='order_detail'),
    path('update_product_status/',  views.update_product_status, name='update_product_status'),
    
    path('coupon/', views.coupon_list, name='admin_coupon'),
    path('coupon_activation/<int:id>/', views.coupon_activation, name='coupon_activation'),
    path('add_coupon/', views.add_coupon, name='add_coupon'),
    path('edit_coupon/<int:coupon_id>/', views.edit_coupon, name='edit_coupon'),
    path('delete_coupon/<int:coupon_id>/', views.delete_coupon, name='delete_coupon'),

    path('pro_offer/', views.product_offer_list, name='pro_offer'),
    path("add_product_offer/", views.add_product_offer, name="add_product_offer"),
    path('edit_product_offer/<int:id>/', views.edit_product_offer, name="edit_product_offer"),
    path('toggle_offer_status/<int:id>/', views.toggle_offer_status, name='toggle_offer_status'),


    path('cat_offer/', views.category_offer_list,  name='cat_offer'),
    
    path('sales_report/', views.sales_report,  name='sales_report'),
    
]