from django.db import models
from django.core.validators import FileExtensionValidator
from decimal import Decimal
from datetime import date





    
# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=200)
    is_listed = models.BooleanField(default=True)

    def __str__(self):
        return self.name   

 
    
class Products(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE,null=True, blank=True)
    priority = models.IntegerField(default=1)
    img1 = models.ImageField(upload_to='media/', validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])],null=True, blank=True)
    img2 = models.ImageField(upload_to='media/', validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])],null=True, blank=True)
    img3 = models.ImageField(upload_to='media/', validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])],null=True, blank=True)
    img4 = models.ImageField(upload_to='media/', validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])],null=True, blank=True)
    

    def get_images(self):
        return [self.img1, self.img2, self.img3, self.img4]
    
    def get_offer_price(self):
     
        # Get the active offers for this product
        active_offer = Product_Offer.objects.filter(
            product_id=self,
            is_active=True,
            start_date__lte=date.today(),
            end_date__gte=date.today()
        ).first()
        if active_offer:
            # Calculate discount amount
            discount_amount = (float(self.price) * active_offer.percentage) / 100
            return round(float(self.price) - discount_amount, 2)
        return None
    
    # def discounted_price(self):
    #     pro_offer = self.product_offer_set.first()
    #     cat_offer = self.category.category_offer_set.first()

    #     if pro_offer and cat_offer:
    #         if pro_offer.is_active == True and cat_offer.is_active == True:
    #             pro_discount = self.selling_price * (
    #                 Decimal(pro_offer.percentage) / 100
    #             )
    #             cat_discount = self.selling_price * (
    #                 Decimal(cat_offer.percentage) / 100
    #             )
    #             offer = min(pro_discount, cat_discount)
    #             return int(self.selling_price - offer)

    #         elif pro_offer.is_active == True and cat_offer.is_active == False:
    #             offer = self.selling_price * (Decimal(pro_offer.percentage) / 100)
    #             return int(self.selling_price - offer)

    #         elif pro_offer.is_active == False and cat_offer.is_active == True:
    #             offer = self.selling_price * (Decimal(cat_offer.percentage) / 100)
    #             return int(self.selling_price - offer)

    #         else:
    #             return int(self.selling_price)

    #     elif pro_offer and pro_offer.is_active == True:
    #         offer = self.selling_price * (Decimal(pro_offer.percentage) / 100)
    #         return int(self.selling_price - offer)

    #     elif cat_offer and cat_offer.is_active == True:
    #         offer = self.selling_price * (Decimal(cat_offer.percentage) / 100)
    #         return int(self.selling_price - offer)

    #     else:
    #         return int(self.selling_price)



    def __str__(self):
        return self.name
    

class Variant(models.Model):
    SIZE_CHOICES = [("S", "Small"), ("M", "Medium"), ("L", "Large")]

    product = models.ForeignKey(Products,on_delete=models.CASCADE)
    size = models.CharField(max_length=5,choices=SIZE_CHOICES,null=True,blank=True)
    quantity = models.PositiveIntegerField(default=0,blank=True,null=True)  


    def __str__(self):
        return f"{self.product.name} - {self.size}"



class Product_Offer(models.Model):
    product_id = models.ForeignKey(Products, on_delete=models.SET_NULL, null=True)
    percentage = models.FloatField(null=True, blank=True, default=0)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateField(auto_now_add=True)


class Category_Offer(models.Model):
    category_id = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    percentage = models.FloatField(null=True, blank=True, default=0)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateField(auto_now_add=True)