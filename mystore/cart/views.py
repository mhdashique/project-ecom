from django.shortcuts import render,redirect,get_object_or_404
from adminside.models import Variant,Products,Category
from .models import Cart,Checkout,Wishlist
from orders.models import Coupon
from django.contrib import messages
from django.http import JsonResponse
import json
from django.views.decorators.http import require_POST
from user.models import CustomUser
from userprofile.models import Address
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
# Create your views here.
from django.views.decorators.cache import cache_control
from django.core.paginator import Paginator     
from django.db.models import Q,Count
from django.contrib.messages import get_messages
import razorpay



@login_required
def wishlist(request):
    wishlist_items = Wishlist.objects.filter(user=request.user)
    print(list.variant_size for list in wishlist_items)
    return render(request, 'wishlist.html', {'wishlist_items': wishlist_items})

@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Products, id=product_id)

    size = request.GET.get('size')
    print(size)
    available_variant = Variant.objects.filter(product=product, size=size, quantity__gt=0).first()
    
    if not available_variant:
        messages.error(request, "This size is out of stock and cannot be added to your wishlist.")
        return redirect('product_detail', id=product_id)
    
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)

    if created: 
        wishlist_item.variant_size = size
        wishlist_item.save()
        messages.success(request, f"{product.name} (Size: {size}) added to your wishlist.")
    else:
        messages.info(request, f"{product.name} (Size: {size}) is already in your wishlist.")
    
    return redirect('wishlist')


@login_required
def remove_from_wishlist(request, product_id):
    product = get_object_or_404(Products, id=product_id)
    wishlist_item = Wishlist.objects.filter(user=request.user, product=product)
    
    if wishlist_item.exists():
        wishlist_item.delete()
        messages.success(request, f"{product.name} removed from your wishlist.")
    else:
        messages.error(request, "Product not found in your wishlist.")
    
    return redirect('wishlist')


# @login_required
# def add_to_cart(request, product_id):
    product = get_object_or_404(Products, id=product_id)
    
    cart_item, created = Cart.objects.get_or_create(user=request.user, variant__product=product)
    
    if created:
        messages.success(request, f"{product.name} added to your cart.")
    else:
        messages.info(request, f"{product.name} is already in your cart.")
    
    Wishlist.objects.filter(user=request.user, product=product).delete()

    return redirect('wishlist')


@login_required(login_url="login")
def shop(request): 
    categories = Category.objects.filter(is_listed=True)
    category_id = request.GET.get('category')
    if category_id:
        products = Products.objects.filter(category__id=category_id, category__is_listed=True)
    else:
        products = Products.objects.filter(category__in=categories)     

    sort_by = request.GET.get('sort')
    if sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    elif sort_by == 'latest':
        products= products.order_by('-priority')   
    elif sort_by == 'aA-zZ':
        products= products.order_by('name')   
    elif sort_by == 'zZ-aA':
        products= products.order_by('-name')   
    elif sort_by == 'stock':
        products = Products.objects.all().annotate(
                        available_variants=Count('variant', filter=Q(variant__quantity__gt=0)))
     
        products = products.exclude(Q(variant__size=None) | Q(available_variants=0))

    
    
    paginator=Paginator(products,12)
    page_num=request.GET.get('page') 
    page_obj=paginator.get_page(page_num)
    context = {
        "page_obj":page_obj,
        "categories": categories,
        "selected_category": category_id,
        "selected_sort": sort_by
    }

    return render(request, 'shop.html',context)

@login_required(login_url="login")
def product_detail(request,id):
    product = Products.objects.get(id=id)
    related_products = Products.objects.exclude(id=id).order_by('?')[:12]
    variants = product.variant_set.all().exclude(quantity=0).order_by("-size")
   
    sizes = [variant.size for variant in variants]
    if not sizes:
        sizes=None

    context = {
        'product':product,
        'products':related_products,
        "sizes":sizes,
        
    }
    return render(request, 'product_detail.html',context)

@login_required(login_url="login")
def cart(request):
    cart_items = Cart.objects.all().order_by('-created_at')
    cart_subtotal = 0
    quantity_ranges = {}
    any_out_of_stock = False 

    if cart_items.exists(): 
        for item in cart_items:
            offer_price = item.variant.product.get_offer_price()
            if offer_price:
                item.total_price = offer_price * item.quantity
            else:    
                item.total_price = item.get_total()
            cart_subtotal += float(item.total_price)
            
            original_qty = item.variant.quantity

            if original_qty == 0:
                quantity_ranges[item.id] = None
                any_out_of_stock = True  
            elif original_qty < 10 and original_qty > 0:
                quantity_ranges[item.id] = range(1, original_qty + 1) 
            else:
                quantity_ranges[item.id] = range(1, 11)
    else:
        
        quantity_ranges = {}

    context = {
        'cart_items': cart_items,
        'cart_subtotal': cart_subtotal,
        'cart_total': cart_subtotal,
        'quantity_ranges': quantity_ranges,
        'any_out_of_stock': any_out_of_stock 
    }
    return render(request, 'cart.html', context)

@login_required(login_url="login")
def add_cart(request,id):
    if request.method == "POST":
        size = request.POST.get("size")

        try:
            variant = Variant.objects.get(product__id=id,size=size)
        except Variant.DoesNotExist:
            messages.error(request, "This Product is not available.")
            return redirect('product_detail', id=id) 
            
        if variant.quantity == 0:
            messages.error(request, "This product is out of stock.")
            return redirect('product_detail', id=id)
        
        if Cart.objects.filter(variant=variant, user_id=request.user).exists():
            messages.error(request, "Product is already exists in Cart")
            return redirect("product_detail", id=id)
        
        item=Cart(
            user_id = request.user ,
            variant=variant,
        )
        item.save()
        messages.success(request, "Product added to cart")
        Wishlist.objects.filter(user=request.user, product=variant.product, variant_size=size).delete()

    return redirect('product_detail', id=id)


@login_required(login_url="login")
@require_POST
def update_cart(request, itemid):
    
    item = get_object_or_404(Cart, id=itemid)
    data = json.loads(request.body)
    new_quantity = int(data.get('quantity'))
    item.quantity = new_quantity
    item.save()

    cart_items = Cart.objects.all()
    cart_subtotal = sum(item.get_total() for item in cart_items)
    

    return JsonResponse({
        'success': True,
        'item_total': float(item.get_total()),
        'cart_subtotal': float(cart_subtotal),
        'cart_total': float(cart_subtotal)
    })



  
@login_required(login_url="login")
def cart_remove(request, id):
     item = get_object_or_404(Cart,id=id)
     item.delete()
     messages.success(request,f'Item {item.variant.product.name} of {item.variant.size} removed from your cart.')
     return redirect("cart")

@login_required(login_url="login")
def cart_clear(request):
     item = Cart.objects.all()
     item.delete()
     messages.success(request, 'All Items removed from your cart.')
     return redirect("cart")


@login_required(login_url="login")
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@never_cache
def checkout(request):
    if "email" in request.session:
        email = request.session.get("email")
        user = CustomUser.objects.get(email=email)
        address = Address.objects.filter(user=user, is_available=True)

        cart_items = Cart.objects.all()
        cart_subtotal = 0
        for item in cart_items:
            offer_price = item.variant.product.get_offer_price()
            if offer_price:
                item.total_price = offer_price * item.quantity
            else:
                item.total_price = item.get_total() 
            cart_subtotal += float(item.total_price)

        coupons = Coupon.objects.filter(is_active=True)
        applied_coupon = Checkout.objects.filter(user=user).first() 
        cart_total = cart_subtotal - (applied_coupon.discount if applied_coupon else 0)
        

        client = razorpay.Client(auth=('rzp_test_jIotm3SaZbXO9x', 'dwZipHebtZ6PN2XDbEKyygS9'))
        try:
            razorpay_order = client.order.create({
            'amount': int(cart_total * 100),  
            'currency': 'INR',
            'payment_capture': '1' 
            })
        except:
            messages.error(request,"cart is empty")
            return redirect("cart")       

        context = {
            "user": user,
            "address": address,
            'cart_items': cart_items,
            'order_subtotal': cart_subtotal,
            'order_total': cart_total,
            'coupons': coupons, 
            "applied_coupon": applied_coupon,
            "razorpay_order_id": razorpay_order['id'],
            "razorpay_merchant_key": 'rzp_test_jIotm3SaZbXO9x',
            "razorpay_amount": int(cart_total * 100),
            "currency": 'INR',
        }    
        return render(request, 'checkout.html', context)


def apply_coupon(request):
    if request.method == "POST":
        coupon_code = request.POST.get("coupon_code")
        coupon_selected =Coupon.objects.get(code=coupon_code)
        cart_items= Cart.objects.filter(user_id=request.user)
        cart_subtotal = 0
        for item in cart_items:
            item.total_price=item.get_total()
            cart_subtotal += item.total_price
        
        if cart_subtotal < coupon_selected.min_price:
            messages.error(request,"you purchase price does not agrees coupon criteria.")
            return redirect("checkout")
        
        Checkout.objects.create(
            user=request.user,
            coupon=coupon_code,
            sub_total=cart_subtotal,
            discount = coupon_selected.discount
        )
        messages.success(request,"coupon applied")
        coupon_selected.usage_limit -=1
        coupon_selected.save()

        return redirect("checkout")
        

def remove_coupon(request):
    if request.method == "POST":
        applied_coupon = Checkout.objects.get(user=request.user)
        coupon_code = Coupon.objects.get(code=applied_coupon.coupon)
        applied_coupon.delete()
        coupon_code.usage_limit += 1
        coupon_code.save()
        messages.success(request,"coupon removed")
    return redirect("checkout")