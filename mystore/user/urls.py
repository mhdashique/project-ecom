from django.urls import path
from . import views

urlpatterns = [
    path('userlogin/', views.userlogin, name='login'),
    path('userregister/', views.signup, name='signup'),
    path('', views.Home, name='home'),
   
    path('set_new_password/<int:user_id>/', views.set_new_password, name='set_new_password'),
    path('verify_email/', views.forgot_verify_email, name='verify_email'),
    path('forgot_verify_otp/<int:user_id>/', views.forgot_verify_otp, name='forgot_verify_otp'),
    path('new_resend_otp/<int:user_id>/', views.new_resend_otp, name='new_resend_otp'),

    path('verify_otp/<int:user_id>/', views.verify_otp, name='verify_otp'),
    path('resend_otp/<int:user_id>/', views.resend_otp, name='resend_otp'),
    path('userlogout/', views.userlogout, name='logout'),
]
