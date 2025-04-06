
# receipts/utils.py
import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from django.conf import settings
from django.core.mail import EmailMessage
from django.core.files.base import ContentFile
from django.utils import timezone
from django.contrib import messages

def generate_receipt_pdf(order):
    """Generate a PDF receipt for an order and return the file object"""
    import io
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    
    buffer = io.BytesIO()
    
    # Create the PDF object using ReportLab
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=1,
        spaceAfter=20
    )
    
    # Content elements
    elements = []
    
    # Add company logo/header
    elements.append(Paragraph("PRINTGATE PRINTING PRESS", title_style))
    elements.append(Paragraph(f"Receipt for Order #{order.id}", styles['Heading2']))
    elements.append(Spacer(1, 20))
    
    # Customer info
    if order.customer:
        elements.append(Paragraph(f"Customer: {order.customer}", styles['Normal']))
        if hasattr(order.customer, 'email'):
            elements.append(Paragraph(f"Email: {order.customer.email}", styles['Normal']))
    else:
        elements.append(Paragraph("Customer: Guest", styles['Normal']))
    
    elements.append(Paragraph(f"Date: {order.date_ordered.strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    elements.append(Paragraph(f"Transaction ID: {order.transaction_id}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Order details header
    elements.append(Paragraph("Order Details:", styles['Heading3']))
    elements.append(Spacer(1, 10))
    
    # Create a table for order items - dynamically based on the products
    # Get order items
    order_items = order.orderitem_set.all()
    
    # Create table headers dynamically based on available product attributes
    header_row = ["Product", "Price", "Quantity", "Total"]
    
    # Create data rows for each order item
    data = [header_row]
    
    for item in order_items:
        product = item.product
        row = [
            product.name,
            f"${product.price:.2f}",
            str(item.quantity),
            f"${item.get_total:.2f}"
        ]
        data.append(row)
    
    # Add a summary row
    data.append(["", "", "Cart Total:", f"${order.get_cart_total:.2f}"])
    data.append(["", "", "Items Count:", f"{order.get_cart_items}"])
    
    # If shipping information is relevant
    if order.shipping:
        data.append(["", "", "Shipping:", "Required"])
    
    # Calculate column widths
    col_widths = [200, 100, 75, 75]
    
    # Create table
    table = Table(data, colWidths=col_widths)
    
    # Style the table
    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        # Style for summary rows
        ('SPAN', (0, -3), (1, -3)),  # Cart Total row
        ('SPAN', (0, -2), (1, -2)),  # Items Count row
        ('ALIGN', (2, -3), (3, -1), 'RIGHT'),
        ('FONTNAME', (2, -3), (2, -1), 'Helvetica-Bold'),
    ]
    
    # Add shipping row styling if present
    if order.shipping:
        table_style.append(('SPAN', (0, -1), (1, -1)))  # Shipping row
    
    table.setStyle(TableStyle(table_style))
    elements.append(table)
    
    # Add any additional information like shipping address if applicable
    if order.shipping:
        elements.append(Spacer(1, 15))
        elements.append(Paragraph("Shipping Information:", styles['Heading4']))
        # Here you would add shipping address details if available in your model
        elements.append(Paragraph("Please ensure your shipping address is up to date in your account.", styles['Normal']))
    
    # Digital products note
    has_digital = any(item.product.digital for item in order_items)
    if has_digital:
        elements.append(Spacer(1, 15))
        elements.append(Paragraph("Digital Products:", styles['Heading4']))
        elements.append(Paragraph("Digital products will be available in your account.", styles['Normal']))
    
    # Footer
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("Thank you for your order!", styles['Normal']))
    elements.append(Paragraph("For any questions, please contact our support team.", styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    
    buffer.seek(0)
    return buffer




def generate_and_save_receipt(order):
    from receipts.models import Receipt

    receipt, created = Receipt.objects.get_or_create(order=order)

    buffer = generate_receipt_pdf(order)

    file_name = f"receipt_order_{order.id}.pdf"
    receipt.pdf_file.save(file_name, ContentFile(buffer.getvalue()), save=True)
    
    return receipt


def send_receipt_email(receipt):
    """Send the receipt via email"""
    order = receipt.order
    
    # Make sure we have a PDF file
    if not receipt.pdf_file:
        receipt = generate_and_save_receipt(order)
    
    # Check if we have a customer email
    if not order.customer or not order.customer.user.email:
        return False
    
    # Get the order items
    order_items = order.orderitem_set.all()
    
    # Create a comma-separated list of product names
    products_str = ", ".join([item.product.name for item in order_items]) if order_items else "Custom Print"
    
    # Prepare email
    subject = f"Your Receipt for Order #{order.id}"
    message = f"""
    Dear {order.customer.name},
    
    Thank you for your order. Please find your receipt attached.
    
    Order ID: #{order.id}
    Products: {products_str}
    Total Amount: ${order.get_cart_total:.2f}
    Items Count: {order.get_cart_items}
    Date: {order.date_ordered.strftime('%Y-%m-%d %H:%M')}
    
    If you have any questions about your order, please contact our support team.
    
    Regards,
    Your Printing Company
    """
    
    email = EmailMessage(
        subject=subject,
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=['padigachris@gmail.com'],
    )
    
    # Attach the PDF
    email.attach_file(receipt.pdf_file.path)
    
    # Send the email
    email.send()
    
    # Update receipt record
    receipt.sent_to_email = True
    receipt.email_sent_at = timezone.now()
    receipt.save()
    
    return True


# def send_receipt_email(receipt):
#     """Send the receipt via email"""
#     order = receipt.order
    
#     # Make sure we have a PDF file
#     if not receipt.pdf_file:
#         receipt = generate_and_save_receipt(order)
    
#     # Check if we have a customer email
#     if not order.customer or not order.customer.user.email:
#         return False
    
#     # Prepare email
#     subject = f"Your Receipt for Order #{order.id}"
#     message = f"""
#     Dear {order.customer.name},
    
#     Thank you for your order. Please find your receipt attached.
    
#     Order ID: #{order.id}
#     Product: {order.product.title if order.product else "Custom Print"}
#     Dimensions: {order.width} x {order.height} {order.dimension_unit}
#     Total Amount: ${order.total_price}
#     Date: {order.date_ordered.strftime('%Y-%m-%d %H:%M')}
    
#     If you have any questions about your order, please contact our support team.
    
#     Regards,
#     Your Printing Company
#     """
    
#     email = EmailMessage(
#         subject=subject,
#         body=message,
#         from_email=settings.DEFAULT_FROM_EMAIL,
#         to=['padigachris@gmail.com'],
#     )
    
#     # Attach the PDF
#     email.attach_file(receipt.pdf_file.path)
    
#     # Send the email
#     email.send()
    
#     # Update receipt record
#     receipt.sent_to_email = True
#     receipt.email_sent_at = timezone.now()
#     receipt.save()
    
#     return True


def generate_receipt_after_verification(order):

    from receipts.utils import generate_and_save_receipt, send_receipt_email

    receipt = generate_and_save_receipt(order)
    
    # Send email with receipt (if customer has email)
    if order.customer and hasattr(order.customer, 'user') and order.customer.user.email:
        send_receipt_email(receipt)
    
    return receipt



def add_to_verify_payment():
    """
    This is just a guide to show where to add the receipt generation
    in the verify_payment function
    """
    # In your verify_payment function, add this after the order is completed:
    # (after "order.save()" and copying specifications)
    
    """
    # Generate and send receipt
    from receipts.utils import generate_receipt_after_verification
    
    print("\nGenerating receipt for the order...")
    receipt = generate_receipt_after_verification(order)
    print(f"Receipt generated with ID: {receipt.id}")
    if receipt.sent_to_email:
        print(f"Receipt sent to customer email: {order.customer.user.email}")
    else:
        print("Receipt created but not sent (no email available)")
    """