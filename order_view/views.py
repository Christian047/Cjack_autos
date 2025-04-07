from base.models import  Products
from store.models import Order
import logging




from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone
from django.contrib import messages
from datetime import timedelta
from django.db import connection
import json

# Import your models
from store.models import Order
from payments.models import Payment  # Adjust app name as needed

# @login_required
def debug_order_view(request):
    """Debug view to diagnose payment data issues"""
    
    # Get orders with debugging info
    orders = Order.objects.all().order_by('-date_ordered')[:10]  # Just get 10 most recent orders
    
    # Debug info to display
    debug_info = {
        'order_count': orders.count(),
        'queries': [],
        'payment_count': 0,
        'orders_data': [],
    }
    
    # Try to count payments
    try:
        debug_info['payment_count'] = Payment.objects.count()
        debug_info['payment_linked_count'] = Payment.objects.filter(payment_order__isnull=False).count()
    except Exception as e:
        debug_info['payment_error'] = str(e)
    
    # Check each order for payment data
    for order in orders:
        order_data = {
            'id': order.id,
            'customer': str(order.customer),
            'date': order.date_ordered.strftime('%Y-%m-%d %H:%M'),
            'complete': order.complete,
            'transaction_id': order.transaction_id,
            'items_count': order.get_cart_items,
            'cart_total': order.get_cart_total,
        }
        
        # Try to get payments for this order
        try:
            payments = list(order.myorder.all().values('id', 'amount', 'ref', 'email', 'verified'))
            order_data['payments'] = payments
            order_data['has_payment'] = len(payments) > 0
        except Exception as e:
            order_data['payment_error'] = str(e)
            order_data['has_payment'] = False
        
        debug_info['orders_data'].append(order_data)
    
    # Record queries that were executed
    debug_info['queries'] = connection.queries
    
    context = {
        'debug_info': debug_info,
        'raw_json': json.dumps(debug_info, indent=2, default=str)
    }
    
    return render(request, 'order_view/debug.html', context)
# @login_required
def admin_dashboard(request):
    """Main admin dashboard with overview statistics and real-time data"""
    
    # Get only orders with transaction IDs
    orders = Order.objects.filter(
        transaction_id__isnull=False,  # Only orders with transaction IDs
        complete=True                  # Only completed orders
    ).prefetch_related('orderitem_set')
    
    # Calculate total revenue from verified orders using the property method
    total_revenue = sum(order.get_cart_total for order in orders)
    
    # Calculate time-based statistics
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    this_week_start = today - timedelta(days=today.weekday())
    this_month_start = today.replace(day=1)
    
    # Filter orders by different time periods
    today_orders = [order for order in orders if order.date_ordered.date() == today]
    yesterday_orders = [order for order in orders if order.date_ordered.date() == yesterday]
    this_week_orders = [order for order in orders if order.date_ordered.date() >= this_week_start]
    this_month_orders = [order for order in orders if order.date_ordered.date() >= this_month_start]
    
    # Calculate revenue for different time periods
    today_revenue = sum(order.get_cart_total for order in today_orders)
    yesterday_revenue = sum(order.get_cart_total for order in yesterday_orders)
    this_week_revenue = sum(order.get_cart_total for order in this_week_orders)
    this_month_revenue = sum(order.get_cart_total for order in this_month_orders)
    
    # Calculate revenue change percentage
    revenue_change = (today_revenue - yesterday_revenue) / yesterday_revenue * 100 if yesterday_revenue else 0
    
    # Calculate completed vs processing orders
    completed_orders = orders
    processing_orders = Order.objects.filter(complete=False)
    
    # Calculate recent orders (last 24 hours)
    last_24h = timezone.now() - timedelta(hours=24)
    recent_24h_orders = [order for order in orders if order.date_ordered >= last_24h]
    
    # Get top products - will need to be calculated differently
    # This is a simplified approach
    top_products = []
    product_counts = {}
    
    for order in orders:
        for item in order.orderitem_set.all():
            product_id = item.product.id
            if product_id in product_counts:
                product_counts[product_id] += item.quantity
            else:
                product_counts[product_id] = item.quantity
    
    # Convert to a list of (product, count) tuples and sort
    product_count_pairs = [(Products.objects.get(id=pid), count) 
                          for pid, count in product_counts.items()]
    top_products = sorted(product_count_pairs, key=lambda x: x[1], reverse=True)[:5]
    
    # Get recent orders
    recent_orders = sorted(orders, key=lambda x: x.date_ordered, reverse=True)[:5]
    
    context = {
        'recent_orders': recent_orders,
        'verified_count': len(orders),
        'total_revenue': total_revenue,
        
        # Today's data
        'today_orders': len(today_orders),
        'today_revenue': today_revenue,
        
        # Yesterday's data
        'yesterday_orders': len(yesterday_orders),
        'yesterday_revenue': yesterday_revenue,
        
        # This week's data
        'this_week_orders': len(this_week_orders),
        'this_week_revenue': this_week_revenue,
        
        # This month's data
        'this_month_orders': len(this_month_orders),
        'this_month_revenue': this_month_revenue,
        
        # Change metrics
        'revenue_change': revenue_change,
        'orders_change': ((len(today_orders) - len(yesterday_orders)) / len(yesterday_orders) * 100) if len(yesterday_orders) else 0,
        
        # Last 24 hours
        'recent_24h_count': len(recent_24h_orders),
        
        # Order status counts
        'completed_count': completed_orders.count(),
        'processing_count': processing_orders.count(),
        
        # Products data
        'top_products': top_products,
        
        # Current time for dashboard refresh info
        'dashboard_time': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    return render(request, 'admin_dashboard/dashboard.html', context)






logger = logging.getLogger(__name__)

# @login_required
def order_list(request):
    """Improved view that shows orders with complete data first"""
    
    # Get filter parameters
    status = request.GET.get('status', 'all')
    show_with_payment = request.GET.get('with_payment', 'yes') == 'yes'
    
    # Get all orders first to find those with payment data
    base_orders = Order.objects.all().order_by('-date_ordered')
    
    # Filter by status if needed
    if status == 'completed':
        base_orders = base_orders.filter(complete=True)
    elif status == 'processing':
        base_orders = base_orders.filter(complete=False)
    
    # Find orders with payment data
    orders_with_payment_ids = Payment.objects.values_list('payment_order_id', flat=True)
    
    # Apply payment filter if requested
    if show_with_payment:
        base_orders = base_orders.filter(id__in=orders_with_payment_ids)
    
    # Process orders
    order_data = []
    total_revenue = 0
    
    # First process orders with payment data (prioritize these)
    priority_orders = list(base_orders.filter(id__in=orders_with_payment_ids))
    other_orders = list(base_orders.exclude(id__in=orders_with_payment_ids))
    
    # Combine to prioritize orders with payment
    all_orders = priority_orders + other_orders
    
    # Process each order
    for order in all_orders:
        # Skip orders without IDs
        if not order.id:
            continue
            
        # Get order items directly
        order_items = list(order.orderitem_set.all())
        
        # Calculate item count directly
        item_count = sum(item.quantity for item in order_items) if order_items else 0
        
        # Calculate total directly
        order_total = sum(item.get_total for item in order_items) if order_items else 0
        total_revenue += order_total
        
        # Get payment directly
        payment = Payment.objects.filter(payment_order_id=order.id).first()
        payment_data = None
        
        if payment:
            payment_data = {
                'id': payment.id,
                'amount': payment.amount,
                'ref': payment.ref,
                'email': payment.email,
                'verified': payment.verified
            }
        
        # Create order data dictionary
        order_info = {
            'id': order.id,
            'customer_name': str(order.customer) if order.customer and hasattr(order.customer, '__str__') and order.customer.__str__() is not None else "Guest",
            'date_ordered': order.date_ordered,
            'formatted_date': order.date_ordered.strftime('%Y-%m-%d'),
            'formatted_time': order.date_ordered.strftime('%H:%M:%S'),
            'complete': order.complete,
            'transaction_id': order.transaction_id,
            'item_count': item_count,
            'order_total': order_total,
            'payment': payment_data,
            'has_payment': payment is not None,
            'has_items': item_count > 0
        }
        
        # Log important orders for debugging
        if payment_data or item_count > 0:
            logger.debug(f"Order #{order.id}: {item_count} items, ₦{order_total}, payment: {payment_data}")
        
        # Add to list
        order_data.append(order_info)
    
    # Count completed/processing orders
    completed_count = len([o for o in order_data if o['complete']])
    processing_count = len([o for o in order_data if not o['complete']])
    with_payment_count = len([o for o in order_data if o['has_payment']])
    with_items_count = len([o for o in order_data if o['has_items']])
    
    context = {
        'orders': order_data,
        'total_revenue': total_revenue,
        'total_count': len(order_data),
        'completed_count': completed_count,
        'processing_count': processing_count,
        'with_payment_count': with_payment_count,
        'with_items_count': with_items_count,
        'status': status,
        'with_payment': show_with_payment
    }
    
    return render(request, 'order_view/order_list.html', context)


# @login_required
def order_detail(request, order_id):
    """View detailed information about a specific order"""
    
    # Make sure we have a valid order ID
    if not order_id:
        messages.error(request, "Invalid order ID")
        return redirect('order_list')
        
    order = get_object_or_404(Order, id=order_id)
    order_items = order.orderitem_set.all()
    
    # Get payment information directly
    payment = Payment.objects.filter(payment_order_id=order_id).order_by('-date_created').first()
    
    # Calculate additional information for the order
    order_age = timezone.now() - order.date_ordered
    
    # Format the date and time
    formatted_date = order.date_ordered.strftime('%B %d, %Y')
    formatted_time = order.date_ordered.strftime('%I:%M %p')
    
    # Get shipping address if available
    try:
        shipping_address = order.shippingaddress
        has_shipping = True
    except:
        shipping_address = None
        has_shipping = False
    
    # Track product quantities and subtotals
    products_info = []
    for item in order_items:
        product_info = {
            'product': item.product,
            'quantity': item.quantity,
            'price': item.product.price,
            'subtotal': item.get_total,
            'digital': getattr(item.product, 'digital', False)
        }
        products_info.append(product_info)
    
    context = {
        'order': order,
        'order_items': order_items,
        'payment': payment,
        'products_info': products_info,
        'order_date': formatted_date,
        'order_time': formatted_time,
        'order_age_days': order_age.days,
        'shipping_address': shipping_address,
        'has_shipping': has_shipping,
        'cart_total': order.get_cart_total,
        'cart_items': order.get_cart_items,
        'shipping_required': order.shipping,
    }
    
    return render(request, 'order_view/order_detail.html', context)






# @login_required
def mark_order_complete(request, order_id):
    """Mark an order as complete"""
    
    # Make sure we have a valid order ID
    if not order_id:
        messages.error(request, "Invalid order ID")
        return redirect('order_list')
    
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        order.complete = True
        order.save()
        
        messages.success(request, f'Order #{order_id} has been marked as complete.')
        return redirect('order_list')
    
    return redirect('order_list')


# @login_required
def sales_report(request):
    """Generate sales reports and statistics"""
    
    # Get time period from request
    period = request.GET.get('period', 'all')
    
    # Base queryset
    all_orders = Order.objects.all().prefetch_related('orderitem_set')
    
    # Apply time period filter
    today = timezone.now().date()
    
    if period == 'today':
        orders = [order for order in all_orders if order.date_ordered.date() == today]
        title = "Today's Sales"
    elif period == 'week':
        week_start = today - timedelta(days=today.weekday())
        orders = [order for order in all_orders if order.date_ordered.date() >= week_start]
        title = "This Week's Sales"
    elif period == 'month':
        month_start = today.replace(day=1)
        orders = [order for order in all_orders if order.date_ordered.date() >= month_start]
        title = "This Month's Sales"
    else:
        orders = all_orders
        title = "All Sales"
    
    # Calculate totals
    total_revenue = sum(order.get_cart_total for order in orders)
    total_orders = len(orders)
    
    # Calculate average order value
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    # Get top products by order count
    product_counts = {}
    product_revenue = {}
    
    for order in orders:
        for item in order.orderitem_set.all():
            product_id = item.product.id
            if product_id in product_counts:
                product_counts[product_id] += item.quantity
                product_revenue[product_id] += item.get_total
            else:
                product_counts[product_id] = item.quantity
                product_revenue[product_id] = item.get_total
    
    # Prepare top products data
    top_product_data = []
    for pid, count in product_counts.items():
        product = Products.objects.get(id=pid)
        top_product_data.append({
            'product': product,
            'order_count': count,
            'revenue': product_revenue[pid]
        })
    
    # Sort by order count
    top_products = sorted(top_product_data, key=lambda x: x['order_count'], reverse=True)[:10]
    
    # Recent orders
    recent_orders = sorted(orders, key=lambda x: x.date_ordered, reverse=True)[:20]
    
    context = {
        'period': period,
        'title': title,
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'avg_order_value': avg_order_value,
        'top_products': top_products,
        'recent_orders': recent_orders
    }
    
    return render(request, 'order_view/sales_report.html', context)