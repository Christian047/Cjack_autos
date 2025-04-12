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

    if request.user.is_authenticated:
        # Existing logic for authenticated users
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

        cart_count = order.get_cart_items
    else:
        # Logic for guest users using cookies
        try:
            cart = json.loads(request.COOKIES.get('cart', '{}'))
        except json.JSONDecodeError:
            cart = {}
        
        # Convert productId to string (as cart keys are strings)
        productId = str(productId)

        # Initialize product in cart if not exists
        if productId not in cart:
            cart[productId] = {'quantity': 0}

        # Update quantity based on action
        if action == 'add':
            cart[productId]['quantity'] += 1
        elif action == 'remove':
            cart[productId]['quantity'] -= 1

        # Remove item if quantity is 0 or less
        if cart[productId]['quantity'] <= 0:
            del cart[productId]

        # Calculate cart count for guest
        cart_count = sum(item['quantity'] for item in cart.values())

        # Prepare response with updated cart
        response = JsonResponse({
            'message': 'Item was added',
            'cart_count': cart_count
        }, safe=False)

        # Use separators to minimize unnecessary whitespace and escaping
        response.set_cookie('cart', json.dumps(cart, separators=(',', ':')))
        return response

    # Return JSON response with cart count for authenticated users
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




@csrf_exempt
def update_quantity(request):
    """
    Handle cart item quantity updates for both authenticated and guest users
    """
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        
        # Validate input
        if not product_id:
            return JsonResponse({'status': 'error', 'message': 'Product ID is required'})
        
        if quantity < 1:
            return JsonResponse({'status': 'error', 'message': 'Quantity must be at least 1'})
        
        # Check if product exists
        try:
            product = Products.objects.get(id=product_id)
        except Products.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Product not found'})
            
        # For authenticated users
        if request.user.is_authenticated:
            customer = request.user.customer
            order, created = Order.objects.get_or_create(customer=customer, complete=False)
            
            orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)
            orderItem.quantity = quantity
            orderItem.save()
            
            return JsonResponse({'status': 'success'})
        
        # For guest users, manage cart via cookies
        else:
            # Get current cart from cookies
            try:
                cart_str = request.COOKIES.get('cart', '{}')
                # Handle double-encoded cookies
                if cart_str.startswith('"') and cart_str.endswith('"'):
                    cart_str = cart_str[1:-1].replace('\\"', '"').replace('\\\\', '\\')
                cart = json.loads(cart_str)
            except json.JSONDecodeError:
                cart = {}    
                
            # Ensure product_id is a string for dictionary key
            product_id = str(product_id)
            
            # Log received cart for debugging
            print(f"Received cart cookie: {cart}")
            
            # Update ONLY the specified product's quantity, preserving all other items
            cart[product_id] = {'quantity': quantity}
            
            # Calculate updated cart totals by processing all items
            cart_total = 0
            cart_items = 0
            
            # Properly calculate cart totals from all items
            for p_id, item_data in cart.items():
                item_quantity = item_data.get('quantity', 0)
                if item_quantity > 0:
                    try:
                        p = Products.objects.get(id=p_id)
                        cart_total += float(p.price * item_quantity)
                        cart_items += item_quantity
                    except Products.DoesNotExist:
                        # Skip if product doesn't exist
                        pass
            
            # Prepare response
            response = JsonResponse({
                'status': 'success',
                'cart_items': cart_items,
                'cart_total': cart_total
            })
            
            # Set the updated cart cookie
            response.set_cookie('cart', json.dumps(cart, separators=(',', ':')))
            
            # Log response for debugging
            print(f"Setting cart cookie: {json.dumps(cart, separators=(',', ':'))}")
            
            return response
            
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON in request'})
    except ValueError as e:
        return JsonResponse({'status': 'error', 'message': f'Value error: {str(e)}'})
    except Exception as e:
        print(f"Error updating cart: {e}")
        return JsonResponse({
            'status': 'error', 
            'message': f'Server error: {str(e)}'
        })



def remove_from_cart(request, product_id):
    """
    Remove a specific product from the cart
    """
    try:
        # Get the product
        product = Products.objects.get(id=product_id)
        
        # For authenticated users
        if request.user.is_authenticated:
            customer = request.user.customer
            order, created = Order.objects.get_or_create(customer=customer, complete=False)
            
            # Get the order item and delete it
            order_item = OrderItem.objects.filter(order=order, product=product).first()
            
            if order_item:
                order_item.delete()
        else:
            # For guest users, modify the cart in the cookie
            import json
            
            # Get existing cart from cookie
            cart_cookie = request.COOKIES.get('cart', '{}')
            try:
                cart = json.loads(cart_cookie)
            except json.JSONDecodeError:
                cart = {}
            
            # Remove the specific product
            if str(product_id) in cart:
                del cart[str(product_id)]
            
            # Prepare response
            response = HttpResponseRedirect(reverse('cart'))
            
            # Set updated cart back to cookie
            response.set_cookie('cart', json.dumps(cart))
            
            return response

    except Exception as e:
        print(f"Error removing from cart: {e}")

    return HttpResponseRedirect(reverse('cart'))




def clear_cart(request):
    """
    Clear all items from the cart
    """
    try:
        if request.user.is_authenticated:
            # For authenticated users, clear their cart
            customer = request.user.customer
            order, created = Order.objects.get_or_create(customer=customer, complete=False)
            OrderItem.objects.filter(order=order).delete()
        else:
            # For guest users, clear the cart and reset cookies
            response = HttpResponseRedirect(reverse('cart'))
            response.delete_cookie('device')  # Remove the guest device cookie
            response.delete_cookie('cart')    # Remove any cart-related cookies

            return response

    except Exception as e:
        print(f"Error clearing cart: {e}")

    return HttpResponseRedirect(reverse('cart'))
    """
    Clear all items from the cart
    """
    try:
        # Get the customer's order
        if request.user.is_authenticated:
            customer = request.user.customer
            order, created = Order.objects.get_or_create(customer=customer, complete=False)
        else:
            # Handle for non-authenticated users
            # Instead of using 'device', use a different approach
            device = request.COOKIES.get('device')
            customer, created = Customer.objects.get_or_create(
                user=None,  # Or use another unique identifier
                email=None,  # You might want to add a unique constraint or identifier
                defaults={
                    'name': f'Guest-{device}' if device else 'Anonymous Guest'
                }
            )
            order, created = Order.objects.get_or_create(customer=customer, complete=False)

        # Delete all order items
        OrderItem.objects.filter(order=order).delete()

    except Exception as e:
        print(f"Error clearing cart: {e}")

    return HttpResponseRedirect(reverse('cart'))