
# receipts/views.py
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import View
from django.utils.decorators import method_decorator

from .models import Receipt
from .utils import generate_receipt_pdf, generate_and_save_receipt, send_receipt_email

@login_required
def download_receipt(request, order_id):
   
    # Get the order, ensuring it belongs to the logged-in user
    from store.models import Order
    
    try:
        order = Order.objects.get(id=order_id, customer__user=request.user, complete=True)
    except Order.DoesNotExist:
        return HttpResponseNotFound("Receipt not found")
    
    # Get or create receipt
    receipt, created = Receipt.objects.get_or_create(order=order)
    
    # If receipt PDF doesn't exist, generate it
    if not receipt.pdf_file:
        receipt = generate_and_save_receipt(order)
    
    # Create HTTP response with PDF
    with open(receipt.pdf_file.path, 'rb') as pdf:
        response = HttpResponse(pdf.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="receipt_order_{order.id}.pdf"'
        return response

@login_required
def email_receipt(request, order_id):
    """View to email a receipt to the user"""
    # Get the order, ensuring it belongs to the logged-in user
    from store.models import Order
    
    try:
        order = Order.objects.get(id=order_id, customer__user=request.user, complete=True)
    except Order.DoesNotExist:
        return HttpResponseNotFound("Receipt not found")
    
    # Get or create receipt
    receipt, created = Receipt.objects.get_or_create(order=order)
    
    # If receipt PDF doesn't exist, generate it
    if not receipt.pdf_file:
        receipt = generate_and_save_receipt(order)
    
    # Send email
    if send_receipt_email(receipt):
        return HttpResponse("Receipt has been sent to your email.")
    else:
        return HttpResponse("Could not send receipt to email. Please contact support.")
