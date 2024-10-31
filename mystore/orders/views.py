from django.shortcuts import render,redirect
from django.urls import reverse
from .models import Order,OrderedProducts,Coupon
from userprofile.models import Address,Wallet,WalletTransaction
from django.contrib import messages
from django.views.decorators.cache import never_cache
from cart.models import Cart,Checkout
from adminside.models import Variant
from django.contrib.auth.decorators import login_required
import razorpay 
import json
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from decimal import Decimal
# from .signals import return_requested
# Create your views here.




@login_required(login_url="login")
def order_view(request,id):
    order = Order.objects.get(id=id)
    ord_products = OrderedProducts.objects.filter(order=order)

    context={
        "ord_products":ord_products,
        "order":order,
    }
    return render(request,'order_view.html',context)


@never_cache
def place_order(request):
    if request.method == 'POST':
        # try:
            if 'order_placed' in request.session:
                return redirect('order_confirm')

            address_id =request.POST.get('selected_address')
            total_amount =float(request.POST.get('order_total'))
            order_subtotal =float(request.POST.get('order_subtotal'))
            order_coupon =request.POST.get('order_coupon')
            payment_method =request.POST.get('payment_method')

            try:
                coupon = Coupon.objects.get(code=order_coupon)
            except:
                coupon = None
                
            if not address_id :
                messages.error(request,"please select shipping address.")
                return redirect('checkout')
            
            if not payment_method :
                messages.error(request,"please select payment method.")
                return redirect('checkout')
            
            if total_amount <=0:
                messages.error(request,"invalid order.")
                return redirect('checkout')
            
            if total_amount >=1000:
                messages.error(request,"please choose other payment method for purchase above 1000.")
                return redirect('checkout')
            
            if order_subtotal <=0:
                messages.error(request,"invalid order.")
                return redirect('checkout')
            
            address=Address.objects.get(id=address_id)
            formatted_address = f"""\
                {address.name},
                {address.street_address},
                {address.city}, {address.state}, {address.pincode},
                {address.country}.
                Mobile: {address.phone}
                """
            
            order  = Order.objects.create(
                user = request.user,
                address=formatted_address,
                total_amount=total_amount,
                sub_total=order_subtotal,
                discount=coupon.discount if coupon else 0,
                payment_method=payment_method,
                payment_status = "Pending",
            )


            user=request.user    
            cart_objects = Cart.objects.filter(user_id=user)

            for cart_obj in cart_objects:
                var = Variant.objects.get(product=cart_obj.variant.product,
                    size=cart_obj.variant.size,
                )
                var.quantity= var.quantity - cart_obj.quantity
                var.save()
                prd_total = cart_obj.variant.product.price * cart_obj.quantity
    

                OrderedProducts.objects.create(
                    order=order,
                    user=user,
                    variant=cart_obj.variant,
                    size=cart_obj.variant.size,
                    quantity=cart_obj.quantity,
                    total_amount=prd_total,
                    status="Order confirmed",
                )

            
            order_id=order.id
            request.session['order_placed'] = True
            request.session['order_id'] = order_id

            item = Cart.objects.filter(user_id =user)
            item.delete()
            coupon_applied = Checkout.objects.filter(user=user).first()
            if coupon_applied:
                coupon_applied.delete()

            messages.success(request, 'Your order has been placed successfully!')
            return redirect('order_confirm')

        # except Exception as e:
        #     messages.error(request, 'An error occurred while placing your order.')
        #     return redirect('checkout')
        
    return redirect('checkout')   



@csrf_exempt
def razorpay_callback(request):
    if request.method == "POST":
        try:
            address_id = request.POST.get('address_id')
            total_amount =float(request.POST.get('order_total'))
            order_subtotal =float(request.POST.get('order_subtotal')) 
            order_coupon =request.POST.get('order_coupon')
            payment_method =request.POST.get('payment_method')
            
            coupon = None
            if order_coupon:
                try:
                    coupon = Coupon.objects.get(code=order_coupon)
                except Coupon.DoesNotExist:
                    coupon = None
                
            if not address_id :
                messages.error(request,"please select shipping address.")
                return redirect('checkout')
            
            if not payment_method :
                messages.error(request,"please select payment method.")
                return redirect('checkout')
            
            if total_amount <=0:
                messages.error(request,"invalid order.")
                return redirect('checkout')
            
            if order_subtotal <=0:
                messages.error(request,"invalid order.")
                return redirect('checkout')
            
            address=Address.objects.get(id=address_id)
            formatted_address = f"""\
                {address.name},
                {address.street_address},
                {address.city}, {address.state}, {address.pincode},
                {address.country}.
                Mobile: {address.phone}
                """
            order  = Order.objects.create(
                user = request.user,
                address=formatted_address,
                total_amount=total_amount,
                sub_total=order_subtotal,
                discount=coupon.discount if coupon else 0,
                payment_method=payment_method,
                payment_status = "Failed",
            )
            user=request.user    
            cart_objects = Cart.objects.filter(user_id=user)

            for cart_obj in cart_objects:
                var = Variant.objects.get(product=cart_obj.variant.product,
                    size=cart_obj.variant.size,
                )
                var.quantity= var.quantity - cart_obj.quantity
                var.save()
                prd_total = cart_obj.variant.product.price * cart_obj.quantity
    

                OrderedProducts.objects.create(
                    order=order,
                    user=user,
                    variant=cart_obj.variant,
                    size=cart_obj.variant.size,
                    quantity=cart_obj.quantity,
                    total_amount=prd_total,
                    status="Order confirmed",
                    
                )
            order_id=order.id    
            request.session['order_id'] = order_id
            request.session['order_placed'] = True
            item = Cart.objects.filter(user_id =user)
            item.delete()
            coupon_applied = Checkout.objects.filter(user=user).first()
            if coupon_applied:
                coupon_applied.delete()

            payment_id = request.POST.get('razorpay_payment_id', '')
            razorpay_order_id = request.POST.get('razorpay_order_id', '')
            signature = request.POST.get('razorpay_signature', '')

            if payment_id and razorpay_order_id and signature:
                try:
                    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                    params_dict = {
                        'razorpay_order_id': razorpay_order_id,
                        'razorpay_payment_id': payment_id,
                        'razorpay_signature': signature
                    }
                    client.utility.verify_payment_signature(params_dict) 

                    order.payment_status = "Paid"
                    order.save()
                    messages.success(request, 'Your order has been placed successfully!')
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Payment successful',
                        'redirect_url': '/order_confirm/'
                    })
                except Exception as e:
                    return JsonResponse({
                        'status': 'failure',
                        'message': 'Payment verification failed',
                        'redirect_url': f'/order_failed/'  # Redirect to order details for retry
                    })
            else:
                # Payment was not attempted or failed
                return JsonResponse({
                    'status': 'success',
                    'message': 'Order placed successfully. Payment pending.',
                    'redirect_url': f'/order_failed/'  # Redirect to order details for payment
                })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': 'Error processing order',
                'redirect_url': '/checkout/'
            }, status=500)
    return redirect('checkout')

def order_failed(request):
    if 'order_placed' in request.session:
        order_id = request.session['order_id']
        del request.session['order_placed']
        del request.session['order_id']
        context = {'order_id': order_id}
        return render(request, 'order_failed.html',context)
    else:
        return redirect('shop')
    
def repay_order(request,id):
    try:
        order = Order.objects.get(id=id, user=request.user)
        
        if order.payment_status == 'PAID':
            messages.info(request, 'This order has already been paid for.')
            return redirect('order_view', order_id=id)

        # Create new Razorpay order
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        payment_data = {
            'amount': int(order.total_amount * 100),  # Convert to paise
            'currency': 'INR',
            'payment_capture': 1
        }
        
        razorpay_order = client.order.create(data=payment_data)  
        context = {
            'order': order,
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_merchant_key': settings.RAZORPAY_KEY_ID,
            'razorpay_amount': payment_data['amount'],
            'currency': payment_data['currency'],
            'callback_url': '/razorpay_callback/'
        }
        
        return render(request, 'repay_order.html', context)
    
    except Order.DoesNotExist:
        messages.error(request, 'Order not found.')
        return redirect('profile')
    except Exception as e:
        messages.error(request, 'Error processing payment retry.')
        return redirect('order_view', order_id=id)

def repay_success(request):
    if request.method == "POST":
        order_id = request.POST.get('order_id')
        order = Order.objects.get(id=order_id, user=request.user)
        order.payment_status = "Paid"
        order.save()
        messages.success(request, 'Payment completed.')
        return JsonResponse({
            'status': 'success',
            'message': 'Payment successful',
            'redirect_url': f'/order_view/{order.id}'
        })   

def wallet_payment(request):
    
    if request.method == 'POST':
        try:
            if 'order_placed' in request.session:
                return redirect('order_confirm')

            address_id =request.POST.get('address_id')
            total_amount =float(request.POST.get('order_total'))
            order_subtotal =float(request.POST.get('order_subtotal'))
            order_coupon =request.POST.get('order_coupon')
            payment_method =request.POST.get('payment_method')
            wallet = Wallet.objects.get(user=request.user)
            
            try:
                coupon = Coupon.objects.get(code=order_coupon)
            except:
                coupon = None
   

            if not address_id :
                messages.error(request,"please select shipping address.")
                return redirect('checkout')
            
            if not payment_method :
                messages.error(request,"please select payment method.")
                return redirect('checkout')
            
            if total_amount <=0:
                messages.error(request,"invalid order.")
                return redirect('checkout')
            
            if order_subtotal <=0:
                messages.error(request,"invalid order.")
                return redirect('checkout')

            
            address=Address.objects.get(id=address_id)
        
            formatted_address = (
                f"{address.name},\n"
                f"{address.street_address},\n"
                f"{address.city}, {address.state}, {address.pincode},\n"
                f"{address.country}.\n"
                f"Mobile: {address.phone}"
            )
           
            user=request.user    
            cart_objects = Cart.objects.filter(user_id=user)

            if wallet.balance >= total_amount:
                new_balance = wallet.balance - int(total_amount)
                wallet.balance = new_balance
                wallet.save()
                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='debit',
                    amount=total_amount,
                    description='Order payment'
                )

            order  = Order.objects.create(
                user = request.user,
                address=formatted_address,
                total_amount=total_amount,
                sub_total=order_subtotal,
                discount=coupon.discount if coupon else 0,
                payment_method=payment_method,
                payment_status = "Paid",
            )

            for cart_obj in cart_objects:
                var = Variant.objects.get(product=cart_obj.variant.product,
                    size=cart_obj.variant.size,
                )
                var.quantity= var.quantity - cart_obj.quantity
                var.save()
                prd_total = cart_obj.variant.product.price * cart_obj.quantity
    

                OrderedProducts.objects.create(
                    order=order,
                    user=user,
                    variant=cart_obj.variant,
                    size=cart_obj.variant.size,
                    quantity=cart_obj.quantity,
                    total_amount=prd_total,
                    status="Order confirmed",
                )

        
                order_id=order.id
                request.session['order_placed'] = True
                request.session['order_id'] = order_id

                item = Cart.objects.filter(user_id =user)
                item.delete()
                coupon_applied = Checkout.objects.filter(user=user).first()
                if coupon_applied:
                    coupon_applied.delete()

                messages.success(request, 'Your order has been placed successfully!')
                data = {"redirect_url": "/order_confirm/"}

            return JsonResponse(data)
        except:
            # If we reach here, payment failed
            messages.error(request,'you order is failed ')
            return redirect('checkout')
    return redirect('checkout')     


@never_cache
def order_confirm(request):

    if 'order_placed' in request.session:
        order_id = request.session['order_id']
        del request.session['order_placed']
        del request.session['order_id']
        
        context = {'order_id': order_id}
        return render(request, 'order_confirm.html',context)
    else:
        return redirect('shop')
    
@never_cache
def cancel_order(request):
    if request.method == 'POST':
        order_product_id = request.POST.get('order_product_id')
        if order_product_id:
            try:
                order_product = OrderedProducts.objects.get(id=order_product_id, user=request.user)
                order = Order.objects.get(orderedproducts=order_product)
                ord_pro_count = OrderedProducts.objects.filter(order=order).count()
                each_pro_discount = order.discount/ord_pro_count 
                order_product.variant.quantity += order_product.quantity
                order_product.variant.save()
                if order_product.payment_status == "Paid":
                    wallet = Wallet.objects.get(user=request.user)
                    return_amount = order_product.total_amount- Decimal(each_pro_discount)
                    wallet.balance += return_amount
                    wallet.save()

                    WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='credit',
                    amount=return_amount,
                    description="Funds added to wallet (order cancel)"
                )
                order_product.status = 'Cancelled' 
                order_product.save()
                order_id = order_product.order.id
                messages.success(request, 'Your order has been cancelled successfully.')
            except OrderedProducts.DoesNotExist:
                messages.error(request, 'Order not found or you do not have permission to cancel it.')
        else:
            messages.error(request, 'Invalid request.')
        return redirect(reverse('order_view', kwargs={'id': order_id}))
    


def return_order(request):
    if request.method == 'POST':
        order_product_id = request.POST.get('order_product_id')
        if order_product_id:
            try:
                order_product = OrderedProducts.objects.get(id=order_product_id, user=request.user)
                order_id = order_product.order.id
                order_product.order.return_request=True
                order_product.order.save()
                order_product.return_request=True
                order_product.save()
                # return_requested.send(sender=order_product)
                messages.success(request, 'Your order has requested return.')
            except OrderedProducts.DoesNotExist:
                messages.error(request, 'Order not found or you do not have permission to return it.')
        else:
            messages.error(request, 'Invalid request.')
        return redirect(reverse('order_view', kwargs={'id': order_id}))