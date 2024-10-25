from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


# user model

class CustomUser(AbstractUser):
    username = models.CharField(max_length=100,default="")
    phone = models.BigIntegerField(unique=True,blank=True,null=True)
    email = models.EmailField(max_length=100,unique=True)
    password = models.CharField(max_length=100)
    dob = models.DateField(null=True,blank=True)
    GENDER_CHOICES = (
        ('m','Male'),
        ('F','Female'),
        ('O','Other'),
    )
    gender = models.CharField(max_length=1,choices=GENDER_CHOICES,null=True,blank=True)
    date_joined = models.DateField(default=timezone.now)
    otp_field = models.CharField(max_length=6, null=True, blank=True)
    otp_generated_at = models.DateTimeField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)

    USERNAME_FIELD='email'
    REQUIRED_FIELDS=['username']

    def __str__(self):
        return self.username if self.username else self.email
    
   