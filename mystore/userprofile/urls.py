from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.profile, name='profile'),
    
    path('add_address/<int:id>', views.add_address, name='add_address'),
    path('edit_address/<int:id>', views.edit_address, name='edit_address'),
    path('delete_address/<int:id>', views.delete_address, name='delete_address'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('change_pasword/', views.change_pasword, name='change_pasword'),
    path('add_fund_wallet/', views.add_fund_wallet, name='add_fund_wallet'),
    path('razorpay-wallet-callback/', views.razorpay_wallet_callback, name='razorpay_wallet_callback'),

    path('invoice/<int:id>', views.invoice, name='invoice'),
]    