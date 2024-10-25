from django.db import models
from user.models import CustomUser
from adminside.models import Variant,Products,Category
from userprofile.models import Address
from django.utils import timezone

# Create your models here.
class Order(models.Model):
    PAYMENT_CHOICES = (
        ("Paid","Paid"),
        ("Pending","Pending"),
        ("Failed","Failed"),
    )
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    sub_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, null=True)
    discount = models.IntegerField(null=True ,blank=True)
    payment_method = models.CharField(max_length=10)
    order_date = models.DateTimeField(auto_now_add=True)
    return_request = models.BooleanField(default=False)
    payment_status =models.CharField(choices=PAYMENT_CHOICES,null=True)


    def __str__(self) -> str:
        return f"{self.user}'s Order {self.id}"
    
    
class OrderedProducts(models.Model):
    STATUS_CHOICES = (
        ("Order confirmed", "Order confirmed"),
        ("Shipped", "Shipped"),
        ("Delivered", "Delivered"),
        ("Cancelled", "Cancelled"),
        ("Returned", "Returned"),
    )
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True )
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    variant = models.ForeignKey(Variant, on_delete=models.SET_NULL, null=True, blank=True)
    size = models.CharField(max_length=5,null=True, blank=True)
    quantity = models.PositiveIntegerField(default=0, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, null=True)
    delivery_date = models.DateField(null=True, blank=True) 
    status = models.CharField(choices=STATUS_CHOICES,null=True)  
    return_request = models.BooleanField(default=False)


    def __str__(self) -> str:
        return f"Orderedproduct-{self.id}({self.variant})" 
    


class Coupon(models.Model):
    code = models.CharField(max_length=50)
    description = models.CharField(max_length=150)
    expiry_date = models.DateField()
    min_price = models.IntegerField()
    discount = models.IntegerField()    
    usage_limit = models.IntegerField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['expiry_date']

    def __str__(self) -> str:
        return self.code