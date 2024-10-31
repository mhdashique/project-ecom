from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login,authenticate,logout 
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from .models import Products,Variant,Category,Product_Offer,Category_Offer
from userprofile.models import Address,Wallet,WalletTransaction
from user.models import CustomUser
from orders.models import Order,OrderedProducts,Coupon
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from PIL import Image
from django.core.files.images import get_image_dimensions
import os
from decimal import Decimal
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Sum,Count,Value,F,Q
from django.db.models.functions import Coalesce, TruncDate
from django.db.models import DecimalField
# from weasyprint import HTML 
from django.template.loader import render_to_string
from django.http import HttpResponse

# Create your views here.


def adminlogin(request):
       
    if request.method == 'POST':
        username = request.POST.get("username")
        password = request.POST.get("password")

        if not username.strip() and not password.strip():
                messages.error(request,"please enter the username and password")
                return redirect("adminlogin")

        elif not username.strip():
                messages.error(request,"please enter the username")
                return redirect("adminlogin")

        elif  not password.strip():
                messages.error(request,"please enter the password")
                return redirect("adminlogin")
        
        user = authenticate(username=username,password=password)
       
        if user is not None and user.is_superuser:
            login(request, user)  
            request.session['username1'] = username  
            messages.success(request, "You logged in successfully")
            return redirect('admin_home')  

        messages.error(request, "Username or Password is invalid")

    return render(request,'admin_login.html')


@never_cache
def adminlogout(request):
    if request.user.is_authenticated:
        logout(request)
    return redirect('adminlogin')
    


@login_required(login_url="adminlogin")
@never_cache
def home(request):
    if not request.user.is_superuser:
        return redirect('adminlogin')
    
    time_period = request.GET.get('time_period', 'year') 

    # Define the date range based on the time period
    now = timezone.now()
    if time_period == 'day':
        start_date = now - timedelta(days=1)
        date_trunc = 'hour'
    elif time_period == 'week':
        start_date = now - timedelta(weeks=1)
        date_trunc = 'day'
    elif time_period == 'month': 
        start_date = now - timedelta(days=30)
        date_trunc = 'day'
    else:  # Default to year
        start_date = now - timedelta(days=365)
        date_trunc = 'month'

    sales_data = Order.objects.filter(order_date__gte=start_date)

    distinct_order_ids = OrderedProducts.objects.filter(
        status='Delivered', 
        order__order_date__gte=start_date
    ).values('order_id').distinct()

    total_sales = Order.objects.filter(
        id__in=distinct_order_ids
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    total_orders = sales_data.count()
    avg_order_value = total_sales / total_orders if total_orders > 0 else 0
    
    returning_customers = OrderedProducts.objects.filter(
        status="Returned",
        order__order_date__gte=start_date 
    ).count() / total_orders * 100 if total_orders > 0 else 0

    top_products = (
        Products.objects
        .annotate(total_sold=Coalesce(Sum('variant__orderedproducts__quantity', 
            filter=Q(variant__orderedproducts__status='Delivered', 
                    variant__orderedproducts__order__order_date__gte=start_date)), Value(0)))
        .annotate(revenue=F('price') * F('total_sold'))
        .order_by('-total_sold')[:3]
    )

    category_sales = Category.objects.annotate(
    total_sales=Coalesce(
        Sum(
            'products__variant__orderedproducts__total_amount',
            filter=Q(products__variant__orderedproducts__status='Delivered',
                      products__variant__orderedproducts__order__order_date__gte=start_date)
        ),
        Value(0),
        output_field=DecimalField()  
    )
    )

    # Sales over time
    sales_over_time = Order.objects.filter(
        order_date__gte=start_date,
        orderedproducts__status='Delivered'
    ).annotate(
        date=TruncDate('order_date', tzinfo=timezone.get_current_timezone())
    ).values('date').annotate(
        total_sales=Sum('total_amount')
    ).order_by('date')

    # Orders over time
    orders_over_time = Order.objects.filter(
        order_date__gte=start_date
    ).annotate(
        date=TruncDate('order_date', tzinfo=timezone.get_current_timezone())
    ).values('date').annotate(
        total_orders=Count('id')
    ).order_by('date')

    order_status = {
        'completed': OrderedProducts.objects.filter( status='Delivered',order__order_date__gte=start_date).count(),
        'pending': OrderedProducts.objects.filter(status='Shipped',order__order_date__gte=start_date  ).count(),
        'canceled': OrderedProducts.objects.filter(status='Cancelled', order__order_date__gte=start_date ).count(),
    }

    # Payment methods breakdown within the filtered sales data
    payment_methods = Order.objects.filter(orderedproducts__status='Delivered',orderedproducts__order__order_date__gte=start_date 
    ).values('payment_method').annotate(total_orders=Count('id'),total_amount=Sum('total_amount'))
    

    context = {
        'time_period': time_period, 
        'total_sales': total_sales,
        'total_orders': total_orders,
        'avg_order_value': avg_order_value,
        'returning_customers': returning_customers,
        'top_products': top_products,
        'category_sales': category_sales,
        'sales_over_time': list(sales_over_time),
        'orders_over_time': list(orders_over_time),
        'order_status': order_status,
        'payment_methods': payment_methods,
    }
    
    return render(request, 'admin_home.html', context)




@login_required(login_url="adminlogin")
def user_list(request):
    if not request.user.is_superuser:
        return redirect('adminlogin')

    users = CustomUser.objects.filter(is_superuser=False).order_by('id') 
    paginator = Paginator(users,9)  
    page_number = request.GET.get('page', 1)

    try:
        page_users = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_users = paginator.get_page(1)
    except EmptyPage:
        page_users = paginator.get_page(paginator.num_pages)

    context = {'users': page_users}  
    return render(request, 'admin_customer.html', context)

@login_required(login_url="adminlogin")
def user_manage(request ,id):
    if not request.user.is_superuser:
        return redirect('adminlogin')
    
    user = CustomUser.objects.get(pk=id)
    if user.is_blocked:
        user.is_blocked = False
    else:
        user.is_blocked = True 

    user.save()
    return redirect('admin_customer')


@login_required(login_url="adminlogin")
def products_manage(request):
    if not request.user.is_superuser:
        return redirect('adminlogin')
    
    search = request.GET.get('search')
    
    if search:
        products = Products.objects.filter(name__istartswith=search).select_related("category")
        disable_pagination = True
    else:
        products = Products.objects.select_related("category").all().order_by('-id')
        disable_pagination = False

    if disable_pagination:
        page_products = products  # No pagination, show all results
    else:
        paginator = Paginator(products, 9)  # 9 items per page
        page = request.GET.get('page', 1)

        try:
            page_products = paginator.get_page(page)
        except PageNotAnInteger:
            page_products = paginator.get_page(1)
        except EmptyPage:
            page_products = paginator.get_page(paginator.num_pages)

    context = {
        "products": page_products,
        "disable_pagination": disable_pagination,
    }

    return render(request, 'admin_products.html', context)
   
def product_list(request,id): 
    product = Products.objects.get(id=id)
    product.is_listed = not product.is_listed
    product.save    
    return redirect("admin_product")

@login_required(login_url="adminlogin")
@csrf_exempt
def add_product(request):
    if not request.user.is_superuser:
        return redirect('adminlogin')
    
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode('utf-8'))
        except ValueError:
            # Fallback to accessing form data if JSON parsing fails
            data = request.POST
        
        # Initialize an empty list to collect error messages
        errors = []

        name = data.get("name").strip()
        description = data.get("description")
        category_name = data.get("category")
        priority = data.get("priority")

        original_price = None
        price = None
        if data.get("original_price"):
            try:
                original_price = float(data.get("original_price"))
            except ValueError:
                        errors.append("Original price must be a valid number.")
        else:
            errors.append("Original price is required.")

        if data.get("price"):
            try:
                price = float(data.get("price"))
            except ValueError:
                errors.append("Price must be a valid number.")
        else:
            errors.append("Price is required.")

        # Validate category existence
        if not Category.objects.filter(id=category_name).exists():
            errors.append("Please select category.")
        
        cat = Category.objects.get(id=category_name)

        # Perform other validations and collect error messages
        if name.isdigit():
            errors.append('Please enter a valid product name (should not be a number)')
        
        if not name.strip():
            errors.append("Please enter valid product name")

        if not description.strip():
            errors.append("Please enter Product description")
        
        if not priority.strip():
            errors.append("Please enter valid priority")

        if not category_name.strip():
            errors.append("Please Select Category for product")

        if original_price is not None and float(original_price) < 0:
            errors.append("Original price must be greater than zero.")

        if original_price is not None and price is not None and float(original_price) <= float(price):
            errors.append('Price must be less than the original price.')

        if price is not None and float(price) < 0:
            errors.append("Price must be greater than zero.")

        if Products.objects.filter(name__iexact=name).exists():
            errors.append(f'Product with name "{name}" already exists!')

        if errors:
            return JsonResponse({"errors": errors}, status=400)

        
        img_blobs = {key: request.FILES.get(key) for key in ["img1", "img2", "img3", "img4"]}
        images = {}
        for img_key, img_blob in img_blobs.items():
            if img_blob:
                try:
                    # Convert blob to Django InMemoryUploadedFile
                    image_file = ContentFile(img_blob.read(), f"{img_key}.png")
                    images[img_key] = image_file
                except Exception as e:
                    errors.append(f"Failed to process {img_key}: {str(e)}")
                    return JsonResponse({"errors": errors}, status=400)
            
        product = Products(
            name=name,
            description=description,
            category=cat,
            original_price=original_price,
            price=price,
            priority=priority,
            img1=images.get("img1"),
            img2=images.get("img2"),
            img3=images.get("img3"),
            img4=images.get("img4"),
        )
        product.save()

        return JsonResponse({"success": True, "message": f'"{product.name}" is added Successfully'})
        

    else:
        category = Category.objects.filter(is_listed=True)
        context = {"categories": category}
        return render(request, "add_product.html", context)



@login_required(login_url="adminlogin")
def edit_product(request,id):
    if not request.user.is_superuser:
        return redirect('adminlogin')

    product = Products.objects.get(id=id)
    categories = Category.objects.all()
    context = {"product": product, 'all_categories': categories}

    if request.method == "POST":
        name = request.POST.get("name").strip()
        desc = request.POST.get("description")
        category_name = request.POST.get("category")

        try:
            cat = Category.objects.get(name=category_name)
        except:
            cat = None

        original_price = request.POST.get("original_price")
        price = request.POST.get("price")
        priority = request.POST.get("priority")
        img1 = request.FILES.get("img1")
        img2 = request.FILES.get("img2")
        img3 = request.FILES.get("img3")
        img4 = request.FILES.get("img4")

        if name.isdigit():
            messages.error(request,'Please enter a valid product name (should not be a number)')
            return redirect('edit_product',id)
        
        if name.strip() == "":
            messages.error(request, "Please enter valid product name")
            return redirect('edit_product',id)

        if desc.strip() == "":
            messages.error(request, "Please enter Product description")
            return redirect('edit_product',id)

        if category_name.strip() == "":
            messages.error(request, "Please Select Category for product")
            return redirect('edit_product',id)

        if float(original_price) < 0:
            messages.error(request, "Not a Valid Amount")
            return redirect('edit_product',id)

        if float(price) < 0:
            messages.error(request, "Not a Valid Amount")
            return redirect('edit_product',id)
        
        if float(original_price) < float(price):
            messages.error(request, 'Price should less than Original Price')
            return redirect('edit_product',id)

        if Products.objects.filter(name__iexact=name).exclude(id=id).exists():
            messages.error(request, f'Product with name "{name}" already exists!')
            return redirect('edit_product',id)

        def is_image(file):
            try:
                img = Image.open(file)
                img.verify()
                get_image_dimensions(file)
                return True
            except Exception:
                return False

        if any(file and not is_image(file) for file in [img1, img2, img3, img4]):
            messages.error(request, "Please upload valid image files.")
            return render(request, "edit_product.html", context)

        obj = Products.objects.get(id=id)
        obj.name = name
        obj.description = desc
        obj.category = cat
        obj.original_price = original_price
        obj.price = price
        obj.priority = priority
        if img1:
            if obj.img1:
                os.remove(obj.img1.path)
            obj.img1 = img1
        if img2:
            if obj.img2:
                os.remove(obj.img2.path)
            obj.img2 = img2
        if img3:
            if obj.img3:
                os.remove(obj.img3.path)
            obj.img3 = img3
        if img4:
            if obj.img4:
                os.remove(obj.img4.path)
            obj.img4 = img4
        obj.save()

        messages.success(request, "Product details updated")
        return redirect("admin_product")

    return render(request, "edit_product.html" ,context)


 
@login_required(login_url="adminlogin")     
def manage_category(request):
     if not request.user.is_superuser:
        return redirect('adminlogin')
    #  if "email" in request.session:
    #     return redirect("error_page")

     categories = Category.objects.all().order_by('name')
     context = {"categories": categories}
    
     return render(request,'admin_category.html',context)  
 
@login_required(login_url="adminlogin") 
def add_category(request):
    if not request.user.is_superuser:
        return redirect('adminlogin')
    
    if request.method == "POST":
        category_name = request.POST.get("name")
        is_listed = request.POST.get("is_listed")

        if category_name.strip() == "":
            messages.error(request, "Please enter Category Name")
            return redirect('add_category')

        if Category.objects.filter(name__icontains=category_name).exists():
            messages.error(
                request, f'Category with name "{category_name}" already exists!'
            )
            return redirect("add_category")

        Subdata = Category(name=category_name, is_listed=is_listed)
        Subdata.save()
        messages.success(request, f"{category_name} added ")
        return redirect("admin_category")

    return render(request,'add_category.html')   



@login_required(login_url="adminlogin")
def edit_category(request,id):
    if not request.user.is_superuser:
        return redirect('adminlogin')
    
    if request.method == "POST":
        name = request.POST.get("name")
        is_listed = request.POST.get("is_listed")

        if name.strip() == "":
            messages.error(request, "Please enter Category Name")
            return redirect('edit_category', id)

        obj = Category.objects.get(id=id)
        obj.name = name
        obj.is_listed = is_listed
        obj.save()
        messages.success(request, f"{name} edited")
        return redirect("admin_category")
    obj1 = Category.objects.get(id=id)
    context = {"category": obj1}
    return render(request, "edit_category.html", context)

@login_required(login_url="adminlogin")
def variant(request,id):
    if not request.user.is_superuser:
        return redirect('adminlogin')
    
    variants = Variant.objects.select_related('product').filter(product_id=id).order_by('-size')
  
    context={
        "variants":variants,
        "product_id": id
       
    }
    return render(request,'variant.html',context)   

@login_required(login_url="adminlogin")
def add_variant(request,id):
    if not request.user.is_superuser:
        return redirect('adminlogin')
    
    size_choices = Variant.SIZE_CHOICES
    context ={}
    if request.method == "POST":
        qty = request.POST.get("Quantity")
        size = request.POST.get("size")

        if Variant.objects.filter(size=size, product_id=id).exists():
            messages.error(request, f'Variant with size "{size}" already exists for this product!')
            return redirect('add_variant',id=id)

        if not qty.strip():
            messages.error(request,"Please enter the product quantity")
            return redirect('add_variant',id=id)
        
        if int(qty) < 0:
            messages.error(request,"Please enter valid product quantity")
            return redirect('add_variant',id=id)

        if not size.strip():
            messages.error(request,"Please select the size")
            return redirect('add_variant',id=id)

        product = get_object_or_404(Products,id=id)
       
         
        data=Variant(
            product=product,
            size=size,
            quantity=qty
        )
        data.save() 
      
        messages.success(request, f'"{product.name}" variant is added Successfully') 
        return redirect('variant',id=id)
    
    context = {
        "size_choices": size_choices,
        "product_id" : id
        } 
    return render(request,'add_variants.html',context)   

@login_required(login_url="adminlogin")
def edit_variant(request,id):
    if not request.user.is_superuser:
        return redirect('adminlogin')
    
    variant=Variant.objects.get(id=id)
    product=variant.product
    
    if request.method == "POST":
        qty = request.POST.get("Quantity")
        
        if int(qty) < 0:
            messages.error(request,"Please enter valid product quantity")
            return redirect('edit_variant',id=id)
        
        variant.quantity = qty
        variant.save()
       
        messages.success(request, f'"{product.name}" variant is updated Successfully') 
        return redirect('variant',id=product.id)
    
    context = {
        "variant":variant,
        "product_id" : product.id
    }
    return render(request,'edit_variant.html',context)  

@login_required(login_url="adminlogin")
def order(request):
    if not request.user.is_superuser:
        return redirect('adminlogin')
     
    orders = Order.objects.all().order_by("-id")
    
    context={
        "orders":orders,
    }
    return render(request , 'admin_order.html',context)

@login_required(login_url="adminlogin")
def order_detail(request,id):
    if not request.user.is_superuser:
        return redirect('adminlogin')
    
    order = Order.objects.get(id=id)
    ord_products = OrderedProducts.objects.filter(order=order).order_by('variant__product__name')
    context={
        "order":order,
        "ord_products":ord_products,
    }
    return render(request,'order_detail.html',context)


def update_product_status(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        new_status = request.POST.get('status')
        
    try:
        product= OrderedProducts.objects.get(id=product_id)
    
        product.status = new_status
        if product.order.payment_method == "cod" and new_status == "Delivered":
            product.payment_status = "Paid"
        if new_status =="Returned" :
            order = Order.objects.get(orderedproducts=product)
            ord_pro_count = OrderedProducts.objects.filter(order=order).count()
            each_pro_discount = order.discount/ord_pro_count
            wallet = Wallet.objects.get(user=product.order.user)
            return_amount = product.total_amount- Decimal(each_pro_discount)
            wallet.balance += return_amount
            wallet.save()

            WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type='credit',
            amount=return_amount,
            description="Funds added to wallet (return order)"
            )
            product.order.return_request = False 
            product.order.save()
        product.save()
        
        order_id = product.order.id

        messages.success(request, f"Status updated to '{new_status}' for product '{product.variant.product.name}'.")
        return redirect(reverse('order_detail', kwargs={'id': order_id}))  
    except OrderedProducts.DoesNotExist:
        messages.error(request, "Product not found.")
        return redirect(reverse('order_detail', kwargs={'id': order_id}))  


def coupon_list(request):
    coupons = Coupon.objects.all()
    return render(request,"admin_coupon.html",{"coupons":coupons})

def coupon_activation(request,id):
    coupon1 = Coupon.objects.get(id =id)
    coupon1.is_active = not coupon1.is_active
    coupon1.save()
    return redirect("admin_coupon")

def add_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('code')
        discount = request.POST.get('discount')
        expiry_date = request.POST.get('expiry_date')
        usage_limit = request.POST.get('usage_limit')
        description = request.POST.get('description')
        min_price = float(request.POST.get('min_price')) 
        is_active = request.POST.get('is_active')

        if not code :
            messages.error(request,"code is empty.")
            return redirect('add_coupon')
        if not discount :
            messages.error(request,"please enter discount amount.")
            return redirect('add_coupon')
        if not expiry_date :
            messages.error(request,"please select expiry date .")
            return redirect('add_coupon')
        if not usage_limit :
            messages.error(request,"please enter usage limit .")
        if not min_price :
            messages.error(request,"please enter min_price.")
            return redirect('add_coupon')
        if not description :
            messages.error(request,"please write description.")
            return redirect('add_coupon')
        
        coupon_new = Coupon.objects.create(
            code=code,
            description= description,
            discount=discount,
            expiry_date=expiry_date,
            usage_limit=usage_limit,
            min_price=min_price,
            is_active=is_active

        )

        messages.success(request,f'you added new coupon "{coupon_new}"')
        return redirect("admin_coupon")
        
    return render(request,"add_coupon.html")

def edit_coupon(request,coupon_id):
    coupon1 = Coupon.objects.get(id=coupon_id)
    if request.method == 'POST':
        code = request.POST.get('code')
        discount = request.POST.get('discount')
        expiry_date = request.POST.get('expiry_date')
        usage_limit = request.POST.get('usage_limit')
        description = request.POST.get('description')
        min_price = float(request.POST.get('min_price'))
        is_active = request.POST.get('is_active')

        if not code :
            messages.error(request,"code is empty.")
            return redirect('edit_coupon',coupon_id)
        if not discount :
            messages.error(request,"please enter discount amount.")
            return redirect('edit_coupon',coupon_id)
        if not expiry_date :
            messages.error(request,"please select expiry date .")
            return redirect('edit_coupon',coupon_id)
        if not usage_limit :
            messages.error(request,"please enter usage limit .")
        if not min_price :
            messages.error(request,"please enter min_price.")
            return redirect('edit_coupon',coupon_id)
        if not description :
            messages.error(request,"please write description.")
            return redirect('edit_coupon',coupon_id)
        
        
        
        coupon1.code=code
        coupon1.description= description
        coupon1.discount=discount
        
        coupon1.usage_limit=usage_limit
        coupon1.min_price=min_price
        coupon1.is_active=is_active
        if expiry_date:
            coupon1.expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()

        coupon1.save()

        messages.success(request,f'you edited coupon "{coupon1}"')
        return redirect("admin_coupon")
    
    context ={
        "coupon":coupon1,
    }   
    return render(request,"edit_coupon.html",context )


def delete_coupon(request,coupon_id):
    coupon1 = Coupon.objects.get(id=coupon_id)
    coupon1.delete()
    messages.success(request,"coupon deleted")
    return redirect("admin_coupon")

def product_offer_list(request):
    context = {}
    context["products"] = Products.objects.all()
    offers = Product_Offer.objects.all().select_related('product_id')

    search_query = request.GET.get('search')
    if search_query:
        offers = offers.filter(product_id__name=search_query)
        context['disable_pagination'] = True
    else:
        paginator = Paginator(offers, 5)
        page_number = request.GET.get('page', 1)
        context["offers"] = paginator.get_page(page_number)

    return render(request, 'pro_offer.html', context)


@login_required(login_url="adminlogin")
def add_product_offer(request):
    now_date = timezone.now().date()

    if request.method == "POST":
        product_id = request.POST.get("productName")
        percentage = request.POST.get("percentage")
        start_date_str = request.POST.get("start_date")
        end_date_str = request.POST.get("end_date")

        try:
            product = Products.objects.get(id=product_id)

            if not 1 <= float(percentage) < 100:
                messages.error(request, "Percentage must be between 1 and 100.")
                return redirect("pro_offer") 

            percentage = float(percentage)

            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

            if Product_Offer.objects.filter(product_id=product).exists():
                messages.error(request, f'Offer Already exists with "{product}"')
                return redirect("pro_offer") 

            if end_date < start_date:
                messages.error(request, "End date must be after start date.")
                return redirect("pro_offer") 

            if now_date > end_date:
                messages.error(
                    request, "The end date for the Offer cannot be in the past."
                )
                return redirect("pro_offer") 

            Product_Offer.objects.create(
                product_id=product,
                percentage=percentage,
                start_date=start_date,
                end_date=end_date,
            )

            messages.success(request, f"'{product}' added '{percentage}%' offer ")
            return redirect("pro_offer") 

        except Products.DoesNotExist:
            messages.error(request, "Invalid product selected.")
            return redirect("pro_offer") 

    products = Products.objects.all()  
    return render(request, "add_pro_offer.html", {"products": products})

@login_required(login_url="adminlogin")
def edit_product_offer(request, id):
    now_date = timezone.now().date()
    offer = Product_Offer.objects.get(id=id)

    if request.method == "POST":
        percentage = request.POST.get("percentage")
        start_date_str = request.POST.get("start_date")
        end_date_str = request.POST.get("end_date")

        try:
            offer = Product_Offer.objects.get(id=id)
            if not 0 <= float(percentage) < 100:
                messages.error(request, "Percentage must be between 0 and 100.")
                return redirect("pro_offer")

            percentage = float(percentage)

            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

            if end_date < start_date:
                messages.error(request, "End date must be after start date.")
                return redirect("pro_offer")

            if now_date > end_date:
                messages.error(
                    request, "The end date for the Offer cannot be in the past."
                )
                return redirect("product_offers")

            offer.percentage = percentage
            offer.start_date = start_date
            offer.end_date = end_date
            offer.save()

            messages.success(request, f"'{offer}' Updated with '{percentage}%' offer ")
            return redirect("pro_offer")

        except Products.DoesNotExist:
            messages.error(request, "Invalid product selected.")

    return render(request, "add_pro_offer.html")

def toggle_offer_status(request, id):
    offer = get_object_or_404(Product_Offer, id=id)
    offer.is_active = not offer.is_active
    offer.save()
    return redirect('pro_offer')

def category_offer_list(request):
    return render(request,'cat_offer.html')

def sales_report(request):
    time_period = request.GET.get('time_period', 'year')  # Default to 'year'
    now = timezone.now()

    # Define the date range based on the time period
    if time_period == 'year':
        start_date = now - timedelta(days=365)
    elif time_period == 'month':
        start_date = now - timedelta(days=30)
    elif time_period == 'week':
        start_date = now - timedelta(weeks=1)
    elif time_period == 'today':
        start_date = now - timedelta(days=1)
    else:
        start_date = now  

    distinct_order_ids = OrderedProducts.objects.filter(
        status='Delivered', 
        order__order_date__gte=start_date
    ).values('order_id').distinct()

    orders = Order.objects.filter(
        id__in=distinct_order_ids)    

    context = {
        "orders": orders,
        "time_period": time_period,
    }
    return render(request,"sales_report.html",context)

# def download_pdf(request):
#     time_period = request.GET.get('time_period', 'year')
#     now = timezone.now()

#     if time_period == 'year':
#         start_date = now - timedelta(days=365)
#     elif time_period == 'month':
#         start_date = now - timedelta(days=30)
#     elif time_period == 'week':
#         start_date = now - timedelta(weeks=1)
#     else:
#         start_date = now

#     orders = Order.objects.filter(order_date__gte=start_date).order_by("-id")

#     context = {
#         "orders": orders,
#         "time_period": time_period,
#     }

#     # Render the HTML to a string
#     html_string = render_to_string('sales_report_pdf.html', context)

#     # Create a PDF response
#     response = HttpResponse(content_type='application/pdf')
#     response['Content-Disposition'] = 'attachment; filename="sales_report.pdf"'
    
#     # Generate PDF
#     HTML(string=html_string).write_pdf(response)

#     return response











