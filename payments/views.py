# Import necessary Django modules and functions
from django.shortcuts import render, redirect  # For rendering templates and redirecting users
from .models import Payment # Import custom Payment and UserWallet models
from django.conf import settings  # To access Django settings (like PAYSTACK_PUBLIC_KEY)
from django.contrib import messages  # For displaying flash messages to users
import json  # For handling JSON data
from store.utils import *
from base.models import *  # Import all models from base app
from receipts.utils import generate_receipt_after_verification




def initiate_payment(request):
    data = cartData(request)
    
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']
    
    if len(items) == 0:
        messages.error(request, "Your cart is empty")
        return redirect('cart')

    if request.method == "POST":
        email = request.POST['email']  # Get email from POST data
        
        # Calculate amount based on what type order is
        if isinstance(order, dict):
            amount = order['get_cart_total']  # Dictionary access
        else:
            amount = order.get_cart_total  # Object property access
        
        try:
            # For guest users (order is a dictionary), create an actual Order first
            if isinstance(order, dict):
                # Either create a guest customer or use the existing one
                if request.user.is_authenticated:
                    customer = request.user.customer
                else:
                    # Create a guest customer based on email
                    customer, created = Customer.objects.get_or_create(email=email)
                
                # Create a real Order object from the order dictionary
                actual_order = Order.objects.create(
                    customer=customer,
                    complete=False
                )
                
                # Add the items to the order
                for item in items:
                    product = Product.objects.get(id=item['id'])
                    OrderItem.objects.create(
                        product=product,
                        order=actual_order,
                        quantity=item['quantity']
                    )
                
                # Update the total
                actual_order.save()
                
            else:
                # For logged-in users, use the existing order object
                actual_order = order
            
            # Create payment with the actual Order object
            payment = Payment.objects.create(
                amount=amount,
                email=email,
                payment_order=actual_order,  # Now this is always an Order instance
                # session_id=request.session.session_key 
                # or 'session_' + str(uuid.uuid4())
            )
            
            context = {
                'payment': payment,
                'paystack_pub_key': settings.PAYSTACK_PUBLIC_KEY,
                'amount_value': payment.amount_value(),
                'order': order,
                'items': items,
                'cartItems': cartItems
            }
            
            response = render(request, 'make_payment.html', context)
            response.set_cookie('payment_ref', payment.ref, httponly=True)
            return response

        except Exception as e:
            # Handle any errors during payment creation
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('cart')

    # If not POST, render initial payment form
    return render(request, 'payment.html', {'order': order, 'items': items})







def verify_payment(request, ref):
    print("\n========== PAYMENT VERIFICATION DEBUG ==========")
    print(f"PAYMENT REF: {ref}")
    print(f"USER: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
    
    # Debug all cookies
    print("\nALL COOKIES:")
    for key, value in request.COOKIES.items():
        print(f"  {key}: {value[:50]}{'...' if len(value) > 50 else ''}")
    
    # Debug all session data
    print("\nALL SESSION DATA:")
    for key, value in request.session.items():
        value_str = str(value)
        print(f"  {key}: {value_str[:50]}{'...' if len(value_str) > 50 else ''}")
    
    # Get payment reference from cookie
    payment_ref = request.COOKIES.get('payment_ref')
    print(f"\nRetrieved payment_ref from cookie: {payment_ref}")

    # Validate payment reference
    if not payment_ref or payment_ref != ref:
        print("ERROR: Invalid payment reference!")
        messages.error(request, "Invalid payment reference")
        return redirect('cart')

    try:
        # Get payment object and verify it
        payment = Payment.objects.get(ref=ref)
        print(f"Payment object found: ID={payment.id}, Amount={payment.amount}")

        # Verify the payment
        verified = payment.verify_payment()
        print(f"\nPayment verification result: {verified}")
        
        if not verified:
            print("ERROR: Payment verification failed.")
            messages.error(request, "Payment verification failed")
            return render(request, "failure.html")

        # Check if this payment has already been processed
        existing_order = Order.objects.filter(transaction_id=payment.ref).first()
        if existing_order:
            print(f"FOUND: Payment already processed for Order #{existing_order.id}")
            
            # Clear cookies and show success page
            response = render(request, "success.html", {
                'message': "Payment already verified successfully!",
                'order': existing_order
            })
            
            # Clear cookies and session data
            return clear_cart_and_return_response(request, response)
        
        # Get cart data from cookies or session
        cart = request.COOKIES.get('cart')
        if not cart:
            cart = request.session.get('cart')
            
        print(f"Retrieved cart data: {cart[:100] if cart else 'None'}")
        
        if not cart:
            print("ERROR: No cart data found in cookies or session")
            messages.error(request, "No items found in cart")
            return redirect('cart')
        
        # Parse cart data
        import json
        cart_data = json.loads(cart)
        print(f"Parsed cart contains {len(cart_data)} items")
        
        # Create the order
        customer = request.user.customer if request.user.is_authenticated else None
        
        order = Order.objects.create(
            customer=customer,
            complete=True,
            transaction_id=payment.ref
        )
        print(f"Created new order with ID: {order.id}")
        
        # Create order items from cart data
        print("Creating order items from cart data...")
        total_price = 0
        for product_id, item_data in cart_data.items():
            try:
                product = Product.objects.get(id=product_id)
                quantity = item_data.get('quantity', 1)
                
                # Create order item
                OrderItem.objects.create(
                    product=product,
                    order=order,
                    quantity=quantity
                )
                
                # Add to total price
                item_price = product.price * quantity
                total_price += item_price
                
                print(f"Added item: {product.name}, Qty: {quantity}, Price: {item_price}")
                
            except Product.DoesNotExist:
                print(f"Warning: Product with ID {product_id} not found, skipping")
        
        # Update order total
        order.total_price = total_price
        order.save()
        print(f"Updated order total price to: {total_price}")
        
        # For logged-in users, mark all their other incomplete orders as complete
        if request.user.is_authenticated:
            try:
                other_orders = Order.objects.filter(
                    customer=request.user.customer, 
                    complete=False
                ).exclude(id=order.id)
                
                updated_count = other_orders.update(complete=True)
                print(f"Marked {updated_count} additional incomplete orders as complete")
            except Exception as e:
                print(f"Error updating other orders: {str(e)}")
        
        # Try to generate receipt
        try:
            print("Generating receipt for the order...")
            receipt = generate_receipt_after_verification(order)
            print("Receipt generated successfully")
        except Exception as e:
            print(f"ERROR: Failed to generate receipt: {str(e)}")
            # Continue anyway, this shouldn't block the order process
        
        # Clear cookies and show success page
        print("Rendering success page...")
        response = render(request, "success.html", {
            'message': "Payment verified successfully!",
            'order': order
        })
        
        # Clear cart and return response
        return clear_cart_and_return_response(request, response)

    except Payment.DoesNotExist:
        print(f"ERROR: Payment record with ref {ref} not found.")
        messages.error(request, "Payment not found")
        return redirect('cart')

    except Exception as e:
        print(f"CRITICAL ERROR: An unexpected exception occurred")
        print(f"Exception type: {type(e).__name__}")
        print(f"Exception message: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('cart')

def clear_cart_and_return_response(request, response):
    """Helper function to clear cart data from cookies and session"""
    # Clear cookies
    cookies_to_delete = ['cart', 'payment_ref', 'pending_order_id', 'shipping_info']
    for cookie in cookies_to_delete:
        if cookie in request.COOKIES:
            response.delete_cookie(cookie)
            print(f"Deleted cookie: {cookie}")
    
    # Clear session data
    session_keys_to_delete = ['pending_order_id', 'cart']
    for key in session_keys_to_delete:
        if key in request.session:
            del request.session[key]
            print(f"Deleted session key: {key}")
    
    request.session.modified = True
    print("Session marked as modified")
    
    return response
    print("\n========== PAYMENT VERIFICATION DEBUG ==========")
    print(f"REQUEST PATH: {request.path}")
    print(f"PAYMENT REF: {ref}")
    print(f"USER: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
    
    # Debug all cookies
    print("\nALL COOKIES:")
    for key, value in request.COOKIES.items():
        print(f"  {key}: {value[:50]}{'...' if len(value) > 50 else ''}")
    
    # Debug all session data
    print("\nALL SESSION DATA:")
    for key, value in request.session.items():
        value_str = str(value)
        print(f"  {key}: {value_str[:50]}{'...' if len(value_str) > 50 else ''}")
    
    # Get payment reference from cookie
    payment_ref = request.COOKIES.get('payment_ref')
    print(f"\nRetrieved payment_ref from cookie: {payment_ref}")

    # Validate payment reference
    if not payment_ref or payment_ref != ref:
        print("ERROR: Invalid payment reference!")
        print(f"Cookie payment_ref: {payment_ref}")
        print(f"URL ref parameter: {ref}")
        messages.error(request, "Invalid payment reference")
        return redirect('cart')

    try:
        # Get payment object and verify it
        print(f"\nFetching payment object for ref: {ref}")
        payment = Payment.objects.get(ref=ref)
        print(f"Payment object details:")
        print(f"  ID: {payment.id}")
        print(f"  Amount: {payment.amount}")
        print(f"  Email: {payment.email}")
        print(f"  Verified: {payment.verified}")
        print(f"  Date Created: {payment.date_created}")

        # Verify the payment first - we only want to process verified payments
        verified = payment.verify_payment()
        print(f"\nPayment verification result: {verified}")
        
        if not verified:
            print("\nERROR: Payment verification failed.")
            messages.error(request, "Payment verification failed")
            return render(request, "failure.html")

        # Get the pending order ID from cookie or session
        pending_order_id = request.COOKIES.get('pending_order_id')
        session_pending_order_id = request.session.get('pending_order_id')
        
        print(f"\nPending order ID from cookie: {pending_order_id}")
        print(f"Pending order ID from session: {session_pending_order_id}")
        
        # Use whichever is available
        pending_order_id = pending_order_id or session_pending_order_id
        print(f"Final pending order ID being used: {pending_order_id}")
        
        # First check if this payment has already been processed
        existing_order = Order.objects.filter(transaction_id=payment.ref).first()
        if existing_order:
            print(f"\nFOUND: Payment already processed for Order #{existing_order.id}")
            
            # Clear cookies and show success page
            response = render(request, "success.html", {
                'message': "Payment already verified successfully!",
                'order': existing_order
            })
            
            # Clear cookies
            cookies_to_delete = ['cart', 'payment_ref', 'pending_order_id', 'shipping_info']
            for cookie in cookies_to_delete:
                if cookie in request.COOKIES:
                    response.delete_cookie(cookie)
                    print(f"Deleted cookie: {cookie}")
            
            # Clear session data
            session_keys_to_delete = ['pending_order_id', 'cart']
            for key in session_keys_to_delete:
                if key in request.session:
                    del request.session[key]
                    print(f"Deleted session key: {key}")
            
            request.session.modified = True
            print("Session marked as modified")
            return response
        
        # Check for pending order or confirmed order with this ID
        pending_order = None
        order = None
        
        # Try to find the pending order first
        if pending_order_id:
            try:
                pending_order = PendingOrder.objects.get(id=pending_order_id)
                print(f"\nFound pending order with ID: {pending_order.id}")
            except PendingOrder.DoesNotExist:
                print(f"Pending order with ID {pending_order_id} not found, checking Order table...")
                try:
                    order = Order.objects.get(id=pending_order_id)
                    print(f"Found order in Order table with ID: {order.id}")
                except Order.DoesNotExist:
                    print(f"Order with ID {pending_order_id} not found in either table!")
                    pending_order_id = None
                    
        # If still no pending order ID, try to find a recent pending order for this user or email
        if not pending_order and not order:
            print("\nAttempting to recover order based on user/email...")
            
            # Try to find by user first if authenticated
            if request.user.is_authenticated:
                try:
                    recent_pending_orders = PendingOrder.objects.filter(
                        customer=request.user.customer,
                        complete=False
                    ).order_by('-date_ordered')[:5]
                    
                    print(f"Found {recent_pending_orders.count()} recent pending orders for user.")
                    if recent_pending_orders.exists():
                        pending_order = recent_pending_orders.first()
                        print(f"Recovered pending order with ID: {pending_order.id}")
                except Exception as e:
                    print(f"Error finding orders by user: {str(e)}")
            
            # If not found, try by email
            if not pending_order and payment.email:
                try:
                    # Try to match by email from the payment
                    from django.db.models import Q
                    recent_pending_orders = PendingOrder.objects.filter(
                        Q(customer__email=payment.email) | 
                        Q(customer__user__email=payment.email)
                    ).filter(complete=False).order_by('-date_ordered')[:5]
                    
                    print(f"Found {recent_pending_orders.count()} recent pending orders by email.")
                    if recent_pending_orders.exists():
                        pending_order = recent_pending_orders.first()
                        print(f"Recovered pending order with ID: {pending_order.id}")
                except Exception as e:
                    print(f"Error finding orders by email: {str(e)}")
            
            # If still nothing found, we can't proceed
            if not pending_order and not order:
                print("ABORT: Failed to find any relevant order for this payment")
                messages.error(request, "No order found for this payment")
                return redirect('cart')
        
        # Process the payment based on whether we have a pending order or confirmed order
        if pending_order:
            # Process the pending order
            print("\nProcessing a pending order...")
            
            # Set transaction ID on pending order
            pending_order.transaction_id = payment.ref
            pending_order.save()
            print(f"Updated pending order with transaction ID: {payment.ref}")
            
            # Check if this pending order already has a confirmed order
            if hasattr(pending_order, 'confirmed_order') and pending_order.confirmed_order:
                print(f"This pending order already has a confirmed order with ID: {pending_order.confirmed_order.id}")
                order = pending_order.confirmed_order
                
                # Make sure it's marked as complete
                order.complete = True
                order.transaction_id = payment.ref
                order.save()
                print("Updated existing confirmed order")
            else:
                # Convert pending order to confirmed order
                print("\nCONVERTING: Pending order to confirmed order...")
                
                # Use convert_to_order method if it exists
                if hasattr(pending_order, 'convert_to_order') and callable(getattr(pending_order, 'convert_to_order')):
                    order = pending_order.convert_to_order()
                    print(f"Used convert_to_order() to create Order #{order.id}")
                else:
                    # Create order manually if method doesn't exist
                    order = Order(
                        pending_order=pending_order,
                        customer=pending_order.customer,
                        product=pending_order.product,
                        width=pending_order.width,
                        height=pending_order.height,
                        dimension_unit=pending_order.dimension_unit,
                        design_file=pending_order.design_file,
                        special_instructions=pending_order.special_instructions,
                        total_price=pending_order.total_price,
                        transaction_id=payment.ref,
                        complete=True
                    )
                    order.save()
                    print(f"Manually created Order #{order.id}")
                
                # Set the bidirectional relationship
                order.pending_order = pending_order
                order.complete = True
                order.transaction_id = payment.ref
                order.save()
                print(f"Updated Order #{order.id} with complete=True, transaction_id={payment.ref}")
                
                # Copy specifications from pending order to confirmed order
                print("\nCopying specifications from pending order...")
                specs_copied = 0
                
                for pending_spec in pending_order.specifications.all():
                    # Create new OrderSpecification for the confirmed order
                    order_spec = OrderSpecification(
                        order=order,
                        field_name=pending_spec.field_name,
                        field_value=pending_spec.field_value
                    )
                    
                    # Copy file if exists
                    if pending_spec.field_file:
                        try:
                            print(f"  Copying file for spec '{pending_spec.field_name}'")
                            from django.core.files.base import ContentFile
                            file_content = pending_spec.field_file.read()
                            pending_spec.field_file.seek(0)  # Reset file pointer
                            order_spec.field_file.save(
                                pending_spec.field_file.name,
                                ContentFile(file_content),
                                save=True
                            )
                        except Exception as e:
                            print(f"Error copying file: {str(e)}")
                    
                    order_spec.save()
                    specs_copied += 1
                
                print(f"Successfully copied {specs_copied} specifications to confirmed order")
                
                # Mark pending order as complete
                pending_order.complete = True
                pending_order.save()
                print("Pending order marked as complete")
        
        elif order:
            # Process the already created order
            print("\nProcessing an existing order...")
            
            # Update the order with payment information
            order.transaction_id = payment.ref
            order.complete = True
            order.save()
            print(f"Updated existing order with transaction ID: {payment.ref}")
            
            # Check if this order has a related pending order
            if order.pending_order:
                # Update pending order too
                order.pending_order.complete = True
                order.pending_order.transaction_id = payment.ref
                order.pending_order.save()
                print(f"Updated related pending order #{order.pending_order.id}")
        
        # For logged-in users, mark all their other incomplete orders as complete
        if request.user.is_authenticated:
            other_orders = Order.objects.filter(
                customer=request.user.customer, 
                complete=False
            ).exclude(id=order.id)
            
            updated_count = other_orders.update(complete=True)
            print(f"Marked {updated_count} additional incomplete orders as complete")
        
        try:
            # Generate receipt
            print("\nGenerating receipt for the order...")
            receipt = generate_receipt_after_verification(order)
            print(f"Receipt generated successfully")
        except Exception as e:
            print(f"ERROR: Failed to generate receipt: {str(e)}")
            print(f"Exception type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            # We continue anyway since this shouldn't block the order process
        
        # Clear cookies and show success page
        print("\nRendering success page...")
        response = render(request, "success.html", {
            'message': "Payment verified successfully!",
            'order': order
        })
        
        # Clear cookies
        cookies_to_delete = ['cart', 'payment_ref', 'pending_order_id', 'shipping_info']
        for cookie in cookies_to_delete:
            if cookie in request.COOKIES:
                response.delete_cookie(cookie)
                print(f"Deleted cookie: {cookie}")
        
        # Clear session data
        session_keys_to_delete = ['pending_order_id', 'cart']
        for key in session_keys_to_delete:
            if key in request.session:
                del request.session[key]
                print(f"Deleted session key: {key}")
        
        request.session.modified = True
        print("Session marked as modified")
        
        print("DEBUG COMPLETE: Returning success response.")
        print("==========================================\n")
        return response

    except Payment.DoesNotExist:
        print(f"\nERROR: Payment record with ref {ref} not found.")
        messages.error(request, "Payment not found")
        return redirect('cart')

    except Exception as e:
        print(f"\nCRITICAL ERROR: An unexpected exception occurred")
        print(f"Exception type: {type(e).__name__}")
        print(f"Exception message: {str(e)}")
        print(f"Exception traceback:")
        import traceback
        traceback.print_exc()
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('cart')