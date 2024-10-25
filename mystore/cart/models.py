from django.db import models
from user.models import CustomUser
from adminside.models import Variant,Products

# Create your models here.

class Cart(models.Model):
    user_id =models.ForeignKey(CustomUser,on_delete=models.CASCADE,null=True)
    variant = models.ForeignKey(Variant, on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField(default=1)
    sub_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_total(self):
        return self.quantity * self.variant.product.price
    
    def calculate_cart_total(self):
        return self.sub_total 

class Checkout(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    coupon = models.CharField()
    sub_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True)
    discount = models.IntegerField(null=True)

    def discount_total(self):
        return self.sub_total - self.discount


class Wishlist(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    variant_size = models.CharField(null=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user}'s wishlist item: {self.product.name}"