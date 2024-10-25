def razorpay_callback(request):
    if request.method == "POST":
        try:
            # Get order details
            address_id = request.POST.get('address_id')
            total_amount = float(request.POST.get('order_total'))
            order_subtotal = float(request.POST.get('order_subtotal'))
            payment_status = request.POST.get('payment_status', 'PENDING')
            
            # Validate basic requirements
            if not address_id or not request.POST.get('payment_method'):
                return JsonResponse({
                    'error': 'Missing required fields',
                    'redirect_url': '/checkout/'
                }, status=400)

            if total_amount <= 0 or order_subtotal <= 0:
                return JsonResponse({
                    'error': 'Invalid order amount',
                    'redirect_url': '/checkout/'
                }, status=400)

            # Get or validate coupon
            order_coupon = request.POST.get('order_coupon')
            coupon = None
            if order_coupon:
                try:
                    coupon = Coupon.objects.get(code=order_coupon)
                except Coupon.DoesNotExist:
                    coupon = None

            # Format address
            address = Address.objects.get(id=address_id)
            formatted_address = f"""{address.name},
                {address.street_address},
                {address.city}, {address.state}, {address.pincode},
                {address.country}.
                Mobile: {address.phone}"""

            # Create order
            order = Order.objects.create(
                user=request.user,
                address=formatted_address,
                total_amount=total_amount,
                sub_total=order_subtotal,
                discount=coupon.discount if coupon else 0,
                payment_method=request.POST.get('payment_method'),
                payment_status='PENDING'  # Default to pending
            )

            # Process cart items
            user = request.user
            cart_objects = Cart.objects.filter(user_id=user)

            for cart_obj in cart_objects:
                var = Variant.objects.get(
                    product=cart_obj.variant.product,
                    size=cart_obj.variant.size,
                )
                var.quantity -= cart_obj.quantity
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
                    payment_status="PENDING"  # Set to pending initially
                )

            # Handle payment verification
            payment_id = request.POST.get('razorpay_payment_id')
            razorpay_order_id = request.POST.get('razorpay_order_id')
            signature = request.POST.get('razorpay_signature')

            if payment_status == 'SUCCESS' and payment_id and razorpay_order_id and signature:
                try:
                    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                    params_dict = {
                        'razorpay_order_id': razorpay_order_id,
                        'razorpay_payment_id': payment_id,
                        'razorpay_signature': signature
                    }
                    client.utility.verify_payment_signature(params_dict)

                    # Update order and ordered products status
                    order.payment_status = "PAID"
                    order.razorpay_payment_id = payment_id
                    order.razorpay_order_id = razorpay_order_id
                    order.save()

                    OrderedProducts.objects.filter(order=order).update(payment_status="PAID")

                    # Clear cart and applied coupon
                    Cart.objects.filter(user_id=user).delete()
                    Checkout.objects.filter(user=user).delete()

                    request.session['order_placed'] = True
                    request.session['order_id'] = order.id

                    return JsonResponse({
                        'status': 'success',
                        'message': 'Payment successful',
                        'redirect_url': '/order_confirm/'
                    })
                except Exception as e:
                    print(f"Payment verification failed: {e}")
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Payment verification failed',
                        'redirect_url': f'/order_details/{order.id}/'  # Redirect to order details for retry
                    })
            else:
                # Payment was not attempted or failed
                return JsonResponse({
                    'status': 'pending',
                    'message': 'Order placed successfully. Payment pending.',
                    'redirect_url': f'/order_details/{order.id}/'  # Redirect to order details for payment
                })

        except Exception as e:
            print(f"Order processing error: {e}")
            return JsonResponse({
                'status': 'error',
                'message': 'Error processing order',
                'redirect_url': '/checkout/'
            }, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)