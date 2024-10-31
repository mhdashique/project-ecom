from django.shortcuts import render,redirect,get_object_or_404,reverse
from django.contrib import messages
from user.models import CustomUser
from .models import Address, Wallet, WalletTransaction
from django.db import transaction
from django.contrib.auth.decorators import login_required
from orders.models import Order,OrderedProducts
from decimal import Decimal
import decimal
import razorpay
from django.conf import settings
from django.http import HttpResponse
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
# Create your views here.

@login_required(login_url="login")
def profile(request):
    if "email" in request.session:
        email = request.session.get("email")
        user = get_object_or_404(CustomUser,email=email)
        address = Address.objects.filter(user=user , is_available=True)
        orders = Order.objects.filter(user=user).order_by("-id")
        wallet ,created= Wallet.objects.get_or_create(user=request.user)
        transactions = wallet.transactions.all().order_by('-timestamp')
    
   
    context = {
        "user" : user,
        "address" : address,
        "orders":orders,
        'wallet': wallet,
        'transactions': transactions
        
    }
    return render(request, 'profile.html',context)



@login_required(login_url="login")
def edit_profile(request):
    gender_choices= CustomUser.GENDER_CHOICES
    context = {
        "gender_choices" : gender_choices,
    }
    if request.method == "POST":
        user = request.user
        user.username = request.POST.get('full_name')
        user.phone = request.POST.get('phone')
        user.dob = request.POST.get('dob')
        user.gender = request.POST.get('gender')
        

        if not user.username.strip():
            messages.error(request,"please enter the fullname")
            return redirect('edit_profile')
        
        if not  user.phone.strip():
            messages.error(request,"please enter the phone number")
            return redirect('edit_profile')
        
        if not  user.phone.isdigit() or len( user.phone) != 10:
            messages.error(request, "Please enter a valid 10-digit phone number")
            return redirect('edit_profile')
    
        if not  user.dob.strip():
            messages.error(request,"please enter the date of birth")
            return redirect('edit_profile')
        
        if not  user.gender.strip():
            messages.error(request,"please select the gender")
            return redirect('edit_profile')
        
        user.save()
        messages.success(request, "Profile updated successfully.")
        return redirect('profile')
    
    return render(request, 'edit_profile.html',context)

@login_required(login_url="login")
def add_address(request,id):

    user = get_object_or_404(CustomUser,id=id)
    
    if request.method == "POST":
        fullname = request.POST.get('full_name')
        phone = request.POST.get('phone_number')
        street_address = request.POST.get('street_address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        pincode = request.POST.get('pin_code')
        country = request.POST.get('country')

        if not fullname.strip():
            messages.error(request,"please enter the fullname")
            return redirect('add_address', id=id)
        
        if not phone.strip():
            messages.error(request,"please enter the phone number")
            return redirect('add_address', id=id)
        
        if not phone.isdigit() or len(phone) != 10:
            messages.error(request, "Please enter a valid 10-digit phone number")
            return redirect('add_address', id=id)
        
        if not street_address.strip():
            messages.error(request,"please enter the street_address")
            return redirect('add_address', id=id)
        
        if not city.strip():
            messages.error(request,"please enter the city")
            return redirect('add_address', id=id)
        
        if not state.strip():
            messages.error(request,"please enter the state")
            return redirect('add_address', id=id)
        
        if not pincode.strip():
            messages.error(request,"please enter the postal_code")
            return redirect('add_address', id=id)
        
        if  not pincode.isdigit() or len(pincode) != 6:
            messages.error(request,"please enter the valid postal_code")
            return redirect('add_address', id=id)
       
        if not country.strip():
            messages.error(request,"please enter the country")
            return redirect('add_address', id=id)
        
        Address.objects.create(
            user=user,
            name=fullname,
            phone=phone,
            street_address=street_address,
            city=city,
            state=state,
            pincode=pincode,
            country=country,      
        )
        
        messages.success(request, "Address added successfully.")
        return_url = request.GET.get('return_url', 'profile') 
        if return_url == 'checkout':
            return redirect('checkout') 
        else:
            return redirect('profile') 
        

    return render(request, 'add_address.html')

@login_required(login_url="login")
def edit_address(request,id):

    address = Address.objects.get(id=id)
    context = {
        "address" : address,
    }

    if request.method == "POST":
        fullname = request.POST.get('full_name')
        phone = request.POST.get('phone_number')
        street_address = request.POST.get('street_address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        pincode = request.POST.get('pin_code')
        country = request.POST.get('country')

        if not fullname.strip():
            messages.error(request,"please enter the fullname")
            return redirect('edit_address', id=id)
        
        if not phone.strip():
            messages.error(request,"please enter the phone number")
            return redirect('edit_address', id=id)
        
        if not phone.isdigit() or len(phone) != 10:
            messages.error(request, "Please enter a valid 10-digit phone number")
            return redirect('edit_address', id=id)
        
        if not street_address.strip():
            messages.error(request,"please enter the street_address")
            return redirect('edit_address', id=id)
        
        if not city.strip():
            messages.error(request,"please enter the city")
            return redirect('edit_address', id=id)
        
        if not state.strip():
            messages.error(request,"please enter the state")
            return redirect('edit_address', id=id)
        
        if not pincode.strip():
            messages.error(request,"please enter the postal_code")
            return redirect('edit_address', id=id)
        
        if  not pincode.isdigit() or len(pincode) != 6:
            messages.error(request,"please enter the valid postal_code")
            return redirect('edit_address', id=id)
       
        if not country.strip():
            messages.error(request,"please enter the country")
            return redirect('edit_address', id=id)
        
        address.name = fullname
        address.phone = phone
        address.street_address = street_address
        address.city = city
        address.state = state
        address.pincode = pincode
        address.country = country
        address.save()
        
        messages.success(request, "Address updated successfully.")
        return redirect('profile')
    
    return render(request, 'edit_address.html',context)

@login_required(login_url="login")
def delete_address(request,id):
    address = get_object_or_404(Address, id=id)
    address.delete()

    return redirect('profile')


@login_required(login_url="login")
def change_pasword(request):
    if "email" in request.session:
        if request.method == 'POST':
            email = request.session.get("email")
            current_password =request.POST.get("current_password")
            new_password =request.POST.get("new_password")
            confirm_password =request.POST.get("confirm_password")
            
            try:
                user = CustomUser.objects.get(email=email)
            except:
                messages.error(request, "User is not found")
                return redirect("login")

            if current_password.strip() == "":
                messages.error(request, "current password field is Empty")
                return redirect("change_pasword")

            if new_password.strip() == "":
                messages.error(request, "New password field is Empty")
                return redirect("change_pasword")

            if confirm_password.strip() == "":
                messages.error(request, "Confrim password field is Empty")
                return redirect("change_pasword")

            if not user.check_password(current_password):
                messages.error(request, "Current password is incorrect")
                return redirect("change_password")

            if user.password == new_password:
                messages.error(request, "current Password and new password are the same")
                return redirect("change_pasword")

            if new_password != confirm_password:
                messages.error(request, "Passwords do not match")
                return redirect("change_pasword")

            if len(new_password) < 6:
                messages.error(request, "Password should be atleast 6 charaters long")
                return redirect("change_pasword")

        
            user.set_password(new_password)
            user.save()

            messages.success(
                request, "Password changed successfully.  Please login again."
            )
            request.session.clear()
            return redirect("login")

    return render(request, 'change_pswd.html')


client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def add_fund_wallet(request):
    if request.method == 'POST':
        amount = float(request.POST.get('amount'))
        if amount <= 0:
            return JsonResponse({'error': 'Invalid amount!'}, status=400)

        # Create Razorpay order
        razorpay_order = client.order.create(dict(
            amount=int(amount * 100), 
            currency="INR",
            payment_capture='0' 
        ))

        request.session['razorpay_order_id'] = razorpay_order['id']
        request.session['wallet_amount'] = str(amount)

        return JsonResponse({
            'order_id': razorpay_order['id'],
            'amount': amount,
            'razorpay_merchant_key': settings.RAZORPAY_KEY_ID,
        })

    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
def razorpay_wallet_callback(request):
    if request.method == "POST":
        try:
            payment_id = request.POST.get('razorpay_payment_id', '')
            razorpay_order_id = request.POST.get('razorpay_order_id', '')
            signature = request.POST.get('razorpay_signature', '')

            # Verify payment signature
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            client.utility.verify_payment_signature(params_dict)

            amount = Decimal(request.session.get('wallet_amount', 0))
            client.payment.capture(payment_id, int(amount * 100))

            wallet = Wallet.objects.get(user=request.user)
            with transaction.atomic():
                wallet.balance += amount
                wallet.save()

                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='credit',
                    amount=amount,
                    description="Funds added to wallet"
                )

            messages.success(request, f"Successfully added {amount} to your wallet!")
            return redirect('profile')

        except:
            messages.error(request, "Payment failed. Please try again.")
            return redirect('profile')

    return HttpResponse(status=400)


def invoice(request,id):
    ord_product = OrderedProducts.objects.get(id=id)
    order = Order.objects.get(orderedproducts=ord_product)
    ord_pro_count = OrderedProducts.objects.filter(order=order).count()
    each_pro_discount = order.discount/ord_pro_count 
    invoice_total = ord_product.total_amount - Decimal(each_pro_discount) 
    context={
         "product":ord_product,
         "order":order,
         "each_pro_discount":each_pro_discount,
         "invoice_total":invoice_total,
    }
    return render(request, "invoice.html",context)