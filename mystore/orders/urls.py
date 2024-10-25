from django.urls import path
from . import views


urlpatterns = [
    path('order_view/<int:id>', views.order_view, name='order_view'),
    path('place_order/', views.place_order, name='place_order'),
    path('order_confirm/', views.order_confirm, name='order_confirm'),
    path('repay_order/<int:id>', views.repay_order, name='repay_order'),
    path('order_failed/', views.order_failed, name='order_failed'),
    path('order_cancel/', views.cancel_order, name='cancel_order'),
    path('return_order/', views.return_order, name='return_order'),
    path('razorpay_callback/', views.razorpay_callback, name='razorpay_callback'),
    path('wallet_payment/', views.wallet_payment, name='wallet_payment'),
    path('repay_success/', views.repay_success, name='repay_success'),   
]