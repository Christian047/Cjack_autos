import json
from .models import *
from base.models import Products  # Make sure to use Products model with 's'

def cookieCart(request):
    """
    Create a cart for non-logged in users based on cookies
    """
    # Try to get the cart from cookies
    try:
        cart = json.loads(request.COOKIES.get('cart', '{}'))
    except:
        cart = {}
        print('CART:', cart)

    # Initialize empty values
    items = []
    order = {'get_cart_total': 0, 'get_cart_items': 0, 'shipping': False}
    cartItems = 0
    
    # Process items in the cart
    for i in cart:
        # We use try block to prevent errors if a product has been deleted
        try:
            # Only process items with positive quantities
            if cart[i]['quantity'] > 0:
                cartItems += cart[i]['quantity']
                
                # Get the product
                product = Products.objects.get(id=i)
                total = (product.price * cart[i]['quantity'])
                
                # Update order totals
                order['get_cart_total'] += total
                order['get_cart_items'] += cart[i]['quantity']
                
                # Create item dictionary that closely matches the OrderItem model structure
                item = {
                    'id': product.id,
                    'product': product,  # Use the actual product object
                    'quantity': cart[i]['quantity'],
                    'get_total': total,
                }
                items.append(item)
        except Exception as e:
            print(f"Error processing cart item {i}: {e}")
            pass
            
    return {'cartItems': cartItems, 'order': order, 'items': items}

def cartData(request):
    """
    Get cart data for both logged in and guest users
    """
    if request.user.is_authenticated:
        # Get the logged-in customer's cart
        try:
            customer = request.user.customer
        except:
            # Create customer if not exists
            customer = Customer.objects.create(
                user=request.user,
                name=request.user.username,
                email=request.user.email
            )
            
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
    else:
        # Get guest cart from cookies
        cookieData = cookieCart(request)
        cartItems = cookieData['cartItems']
        order = cookieData['order']
        items = cookieData['items']

    return {'cartItems': cartItems, 'order': order, 'items': items}

def guestOrder(request, data):
    """
    Create an order for guest users
    """
    name = data['form']['name']
    email = data['form']['email']

    cookieData = cookieCart(request)
    items = cookieData['items']

    customer, created = Customer.objects.get_or_create(
        email=email,
    )
    customer.name = name
    customer.save()

    order = Order.objects.create(
        customer=customer,
        complete=False,
    )

    for item in items:
        product = Products.objects.get(id=item['id'])
        orderItem = OrderItem.objects.create(
            product=product,
            order=order,
            quantity=item['quantity'],
        )
    return customer, order









# import json
# from .models import *

# def cookieCart(request):

# 	#Create empty cart for now for non-logged in user
# 	try:
# 		cart = json.loads(request.COOKIES['cart'])
# 	except:
# 		cart = {}
# 		print('CART:', cart)

# 	items = []
# 	order = {'get_cart_total':0, 'get_cart_items':0, 'shipping':False}
# 	cartItems = order['get_cart_items']

# 	for i in cart:
# 		#We use try block to prevent items in cart that may have been removed from causing error
# 		try:	
# 			if(cart[i]['quantity']>0): #items with negative quantity = lot of freebies  
# 				cartItems += cart[i]['quantity']

# 				product = Product.objects.get(id=i)
# 				total = (product.price * cart[i]['quantity'])

# 				order['get_cart_total'] += total
# 				order['get_cart_items'] += cart[i]['quantity']

# 				item = {
# 				'id':product.id,
# 				'product':{'id':product.id,'name':product.name, 'price':product.price, 
# 				'imageURL':product.imageURL}, 'quantity':cart[i]['quantity'],
# 				'digital':product.digital,'get_total':total,
# 				}
# 				items.append(item)

# 				if product.digital == False:
# 					order['shipping'] = True
# 		except:
# 			pass
			
# 	return {'cartItems':cartItems ,'order':order, 'items':items}

# def cartData(request):
# 	if request.user.is_authenticated:
# 		customer = request.user.customer
# 		order, created = Order.objects.get_or_create(customer=customer, complete=False)
# 		items = order.orderitem_set.all()
# 		cartItems = order.get_cart_items
# 	else:
# 		cookieData = cookieCart(request)
# 		cartItems = cookieData['cartItems']
# 		order = cookieData['order']
# 		items = cookieData['items']

# 	return {'cartItems':cartItems ,'order':order, 'items':items}

	
# def guestOrder(request, data):
# 	name = data['form']['name']
# 	email = data['form']['email']

# 	cookieData = cookieCart(request)
# 	items = cookieData['items']

# 	customer, created = Customer.objects.get_or_create(
# 			email=email,
# 			)
# 	customer.name = name
# 	customer.save()

# 	order = Order.objects.create(
# 		customer=customer,
# 		complete=False,
# 		)

# 	for item in items:
# 		product = Product.objects.get(id=item['id'])
# 		orderItem = OrderItem.objects.create(
# 			product=product,
# 			order=order,
# 			quantity=(item['quantity'] if item['quantity']>0 else -1*item['quantity']), # negative quantity = freebies
# 		)
# 	return customer, order

