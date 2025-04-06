# cart.py (Handles Cart Logic)

import json  # Import JSON module for handling cart data stored as cookies
from .models import *  # Import all models (Product, Order, OrderItem, Customer)

def cookieCart(request):
    try:
        cart = json.loads(request.COOKIES['cart'])
    except:
        cart = {}  # Empty cart for guests
        print('CART:', cart)  # Debugging: Print empty cart when no cookie found

    # Initialize cart details
    items = []  # List to hold cart items
    order = {'get_cart_total': 0, 'get_cart_items': 0, 'shipping': False}  # Default order structure
    cartItems = order['get_cart_items']  # Total number of items in the cart

    # Iterate through the cart to process each item
    for i in cart:
        try:  
            if cart[i]['quantity'] > 0:  # Ignore items with negative quantity (prevents freebies)
                cartItems += cart[i]['quantity']  # Add quantity to total cart items

                product = Product.objects.get(id=i)  # Retrieve product from database
                total = product.price * cart[i]['quantity']  # Calculate total price for this item

                # Update order totals
                order['get_cart_total'] += total
                order['get_cart_items'] += cart[i]['quantity']

                # Create dictionary for this cart item
                item = {
                    'id': product.id,
                    'product': {
                        'id': product.id,
                        'name': product.name,
                        'price': product.price,
                        'imageURL': product.imageURL
                    },
                    'quantity': cart[i]['quantity'],
                    'digital': product.digital,
                    'get_total': total,  # Total price for this product
                }
                items.append(item)  # Add item to the cart list

                # Check if product requires shipping (i.e., not digital)
                if product.digital == False:
                    order['shipping'] = True  # If any item requires shipping, set it to True

        except:
            pass  # If a product is deleted from the database, ignore it

    # Return cart summary
    return {'cartItems': cartItems, 'order': order, 'items': items}


def cartData(request):
    """
    Retrieves cart data based on whether the user is logged in or a guest.
    Returns order, cart items, and total quantity.
    """

    if request.user.is_authenticated:
        # Get the logged-in customer's cart
        try:
             customer = request.user.customer  # Get the customer linked to the user
        except AttributeError:
            customer = Customer.objects.create(user=request.user, name=request.user.username, email=request.user.email)  # Create a new customer if not found
        order, created = Order.objects.get_or_create(customer=customer, complete=False)  # Get or create an open order
        items = order.orderitem_set.all()  # Retrieve all items in the order
        cartItems = order.get_cart_items  # Get the total number of items in the cart

    else:
        # Retrieve cart from cookies for guests
        cookieData = cookieCart(request)
        cartItems = cookieData['cartItems']
        order = cookieData['order']
        items = cookieData['items']

    return {'cartItems': cartItems, 'order': order, 'items': items}  # Return cart details


def guestOrder(request, data):
    """
    Handles orders for guest users who are not logged in.
    Associates their order with an email and creates an Order record.
    """

    # Extract name and email from form submission
    name = data['form']['name']
    email = data['form']['email']

    # Retrieve cart items from cookies
    cookieData = cookieCart(request)
    items = cookieData['items']

    # Check if the customer already exists (based on email)
    customer, created = Customer.objects.get_or_create(email=email)
    customer.name = name  # Update customer name
    customer.save()  # Save to database

    # Create a new order for the guest user
    order = Order.objects.create(
        customer=customer,
        complete=False,  # Mark as incomplete until payment is made
    )

    # Add each cart item to the order
    for item in items:
        product = Product.objects.get(id=item['id'])  # Retrieve the product
        orderItem = OrderItem.objects.create(
            product=product,
            order=order,
            quantity=(item['quantity'] if item['quantity'] > 0 else -1 * item['quantity']),  
            # If quantity is negative, convert it to positive (to handle freebies)
        )

    return customer, order  # Return the created customer and order



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

