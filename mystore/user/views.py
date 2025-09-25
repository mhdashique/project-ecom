from django.shortcuts import render,redirect
from django.contrib.auth import authenticate,login,logout
from . import models
from .models import CustomUser
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.core.mail import send_mail
# from mystore.settings import EMAIL_HOST_USER
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib import messages
import random
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from adminside.models import Variant,Products,Category
from django.conf import settings

email_user = settings.EMAIL_HOST_USER



# user login
def userlogin(request):
    if "email" in request.session:
        return redirect("home")

    errors = {}

    if request.method == "POST":
        identifier = request.POST.get("username")
        password = request.POST.get("password")

        if not identifier.strip():
            errors['general'] = "Please enter your username/password"
        if not password.strip():
            errors['password'] = "Please enter your password"

        email_validator = EmailValidator()

        # Check if the identifier is an email or a username
        try:
            email_validator(identifier)
            is_email = True
        except ValidationError:
            is_email = False
       
        if not errors:
            if is_email:
                user = authenticate(email=identifier, password=password)
            else:
                user = authenticate(username=identifier, password=password)

            if user is not None:
                if user.is_blocked:
                    errors['general'] = f"{identifier} is blocked"
                    
                else:
                    if user.is_verified:
                        login(request, user)
                        request.session["email"] = user.email  
                        return redirect("home")
                    else:
                        generate_otp(user)
                        return redirect(reverse('verify_otp', kwargs={'user_id':user.id}))
            else:
                errors['general'] = "Invalid username/email or password"

        return render(request, 'user_login.html', {'errors': errors, 'identifier': identifier})
    
    return render(request, 'user_login.html')


# user signup
def signup(request):

    if "email" in request.session:
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        email_validator = EmailValidator()
        errors = {}

        # Validate email
        try:
            email_validator(email)
        except ValidationError:
            errors['email'] = "Invalid email address"

        if not username.strip() :
            errors['username'] = "Please enter your Username"

        if not email.strip() :
            errors['email'] = "Please enter your Email"

        if not password1.strip():
            errors['password1'] = "Please enter your Password"

        if not password2.strip() :
            errors['password2'] = "Please enter your Confirm Password"

        if  password1 != password2:
            errors['password2'] = "Both passwords are not the same!"
        
        if len(password1) < 6:
             errors['password1'] = "Password should be at least 6 characters"


        if CustomUser.objects.filter(username=username).exists():
            errors['username'] = "Username is already taken"

        if CustomUser.objects.filter(email=email).exists():
            errors['email'] = "Email is already taken"

        if errors:
            return render(request, 'user_register.html', {'errors': errors})
        
        user = CustomUser(
              username=username,
              email=email
            )
        user.set_password(password1)
        user.save()

        generate_otp(user)
        return redirect("verify_otp",user.id)
        
    return render(request, 'user_register.html')

def generate_otp(user):
    otp = random.randint(100000, 999999)  # Generate a 6-digit OTP
    user.otp_field = otp
    user.otp_generated_at = timezone.now()
    user.save()
    
    # Send OTP to the user's email
    send_mail(
        'Your OTP Code',
        f'Your OTP code is {otp}.',
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
 
def verify_otp(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    error = None

    if request.method == "POST":
        otp = request.POST.get("otp", "").strip()

        if user.otp_field == otp:
            otp_age = timezone.now() - user.otp_generated_at
            if otp_age.total_seconds() <= 300: 
                user.is_verified = True
                user.otp_field = None
                user.save()
                messages.success(request, "Your account has been verified.")
                return redirect('login')
            else:
                error = "OTP has expired."
        else:
            error = "Invalid OTP."

    return render(request, 'otp_verification.html', {'error': error, 'user_id': user.id})


def resend_otp(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    generate_otp(user)
    messages.success(request, "A new OTP has been sent to your email.")
    return redirect('verify_otp', user_id=user.id)


def userlogout(request):
    if "email" in request.session:
        del request.session["email"]

    logout(request)
    return redirect('login')


@login_required(login_url='login')
@never_cache
def Home(request):
    featured_products = Products.objects.filter(priority=1)[:7]
    context = {
        "products":featured_products,
    }
    return render(request, 'home.html',context)


def forgot_verify_email(request):
    errors = {}
    if request.method == "POST":
        identifier = request.POST.get("identifier")
        
        if not identifier:
            errors['identifier'] = "Please enter your username or email"
        else:
            email_validator = EmailValidator()
            try:
                email_validator(identifier)
                is_email = True
            except ValidationError:
                is_email = False

            # Now handle either email or username check
            try:
                if is_email:
                    user = CustomUser.objects.get(email=identifier)
                else:
                    user = CustomUser.objects.get(username=identifier)
            except CustomUser.DoesNotExist:
                errors['identifier'] = "Invalid username or email"

        if not errors:
            # If no errors, generate OTP and redirect
            generate_otp(user)
            return redirect(reverse('forgot_verify_otp', kwargs={'user_id': user.id}))

    # Context with errors to render in the template
    context = {
        "errors": errors,
    }
    return render(request, "verify_email.html", context)


def forgot_verify_otp(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    error = None

    if request.method == "POST":
        otp = request.POST.get("otp_code", "").strip()
    
        if user.otp_field == otp:
            otp_age = timezone.now() - user.otp_generated_at
            if otp_age.total_seconds() <= 300: 
                user.otp_field = None
                user.save()
                messages.success(request, "Your username/email has been verified.")
                return redirect(reverse('set_new_password', kwargs={'user_id': user.id}))
            else:
                error = "OTP has expired."
        else:
            error = "Invalid OTP."

    return render(request, 'forgot_otp_verify.html', {'error': error, 'user_id': user.id})

def new_resend_otp(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    generate_otp(user)
    messages.success(request, "A new OTP has been sent to your email.")
    return redirect('forgot_verify_otp', user_id=user.id)

# User = get_user_model()  # If you're using a custom user model


def set_new_password(request, user_id):
    errors = {}
    user = get_object_or_404(CustomUser, id=user_id)  # Retrieve user by ID or other means
    if request.method == "POST":
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")
        
        # Basic password validation
        if not new_password or not confirm_password:
            errors['password'] = "Please enter both password fields."
        elif new_password != confirm_password:
            errors['password'] = "Passwords do not match."
        else:
            # Use Django's built-in set_password method to hash and set the new password
            user.set_password(new_password)
            user.save()  # Don't forget to save the user after setting the password
            
            # Optionally log the user in again after password change
            return redirect(reverse('login'))  # Redirect to login or other page

    context = {
        'errors': errors
    }
    return render(request, 'set_new_password.html', context)

