from django.shortcuts import render
from django.http import JsonResponse
import json
import datetime
from .models import * 
from base.models import Products
from .utils import cookieCart, cartData, guestOrder
from django.shortcuts import redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from .models import OrderItem, Order
from django.views.decorators.csrf import csrf_exempt

def store(request):
	data = cartData(request)

	cartItems = data['cartItems']
 
#  --------------------------------------------------------------------------------------------------------------------------------------------------
	order = data['order']
	items = data['items']

	products = Products.objects.all()
	context = {'products':products, 'cartItems':cartItems}
	return render(request, 'store/store.html', context)


def cart(request):
	data = cartData(request)

	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	context = {'items':items, 'order':order, 'cartItems':cartItems}
	return render(request, 'store/cart.html', context)

def checkout(request):
	data = cartData(request)
	
	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	context = {'items':items, 'order':order, 'cartItems':cartItems}
	return render(request, 'store/checkout.html', context)








@csrf_exempt
def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']

    customer = request.user.customer
    product = Products.objects.get(id=productId)
    order, created = Order.objects.get_or_create(customer=customer, complete=False)

    orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

    if action == 'add':
        orderItem.quantity = (orderItem.quantity + 1)
    elif action == 'remove':
        orderItem.quantity = (orderItem.quantity - 1)

    orderItem.save()

    if orderItem.quantity <= 0:
        orderItem.delete()

    # Get the current cart count
    cart_count = order.get_cart_items if hasattr(order, 'get_cart_items') else order.orderitem_set.all().count()

    # Return JSON response with cart count
    return JsonResponse({
        'message': 'Item was added',
        'cart_count': cart_count
    }, safe=False)
















def processOrder(request):
	transaction_id = datetime.datetime.now().timestamp()
	data = json.loads(request.body)

	if request.user.is_authenticated:
		customer = request.user.customer
		order, created = Order.objects.get_or_create(customer=customer, complete=False)
	else:
		customer, order = guestOrder(request, data)

	total = float(data['form']['total'])
	order.transaction_id = transaction_id

	if total == order.get_cart_total:
		order.complete = True
	order.save()

	if order.shipping == True:
		ShippingAddress.objects.create(
		customer=customer,
		order=order,
		address=data['shipping']['address'],
		city=data['shipping']['city'],
		state=data['shipping']['state'],
		zipcode=data['shipping']['zipcode'],
		)

	return JsonResponse('Payment submitted..', safe=False)
# --------------------------------------------------------------------------------------------------




def update_quantity(request):
    """
    Update the quantity of a specific product in the cart
    """
    data = json.loads(request.body)
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1))
    
    try:
        # Get the product
        product = Products.objects.get(id=product_id)
        
        # Get the customer's order
        if request.user.is_authenticated:
            customer = request.user.customer
            order, created = Order.objects.get_or_create(customer=customer, complete=False)
        else:
            # Handle for non-authenticated users if you support guest checkout
            device = request.COOKIES.get('device')
            customer, created = Customer.objects.get_or_create(device=device)
            order, created = Order.objects.get_or_create(customer=customer, complete=False)
        
        # Get or create order item
        order_item, created = OrderItem.objects.get_or_create(order=order, product=product)
        
        # Update quantity
        if quantity > 0 and quantity <= 100:
            order_item.quantity = quantity
            order_item.save()
            
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        print(e)
        return JsonResponse({'status': 'error', 'message': str(e)})

def remove_from_cart(request, product_id):
    """
    Remove a specific product from the cart
    """
    try:
        # Get the product
        product = Products.objects.get(id=product_id)
        
        # Get the customer's order
        if request.user.is_authenticated:
            customer = request.user.customer
            order, created = Order.objects.get_or_create(customer=customer, complete=False)
        else:
            # Handle for non-authenticated users if you support guest checkout
            device = request.COOKIES.get('device')
            customer, created = Customer.objects.get_or_create(device=device)
            order, created = Order.objects.get_or_create(customer=customer, complete=False)
        
        # Get the order item and delete it
        order_item = OrderItem.objects.filter(order=order, product=product).first()
        
        if order_item:
            order_item.delete()
            
    except Exception as e:
        print(e)
        
    return HttpResponseRedirect(reverse('cart'))

def clear_cart(request):
    """
    Clear all items from the cart
    """
    try:
        # Get the customer's order
        if request.user.is_authenticated:
            customer = request.user.customer
            order, created = Order.objects.get_or_create(customer=customer, complete=False)
        else:
            # Handle for non-authenticated users if you support guest checkout
            device = request.COOKIES.get('device')
            customer, created = Customer.objects.get_or_create(device=device)
            order, created = Order.objects.get_or_create(customer=customer, complete=False)
        
        # Delete all order items
        OrderItem.objects.filter(order=order).delete()
        
    except Exception as e:
        print(e)
        
    return HttpResponseRedirect(reverse('cart'))
