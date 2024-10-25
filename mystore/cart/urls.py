from django.urls import path
from . import views


urlpatterns = [
    path('cart/', views.cart, name='cart'),
    path('update_cart/<int:itemid>/', views.update_cart, name='update_cart'),
    path('remove_cart/<int:id>/', views.cart_remove, name='cart_remove'),
    path('cart_clear/', views.cart_clear, name='cart_clear'),
    path('checkout/', views.checkout, name='checkout'),
    path('add_cart/<int:id>/', views.add_cart, name='add_cart'),
    path('shop/', views.shop, name='shop'),
    path('product/<int:id>/', views.product_detail, name='product_detail'),
    path('apply_coupon/', views.apply_coupon, name='apply_coupon'),
    path('remove_coupon/', views.remove_coupon, name='remove_coupon'),

    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    # path('wishlist/add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),

]