python manage.py startapp receipts

pip install reportlab


# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.your-email-provider.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@example.com'
EMAIL_HOST_PASSWORD = 'your-email-password'
DEFAULT_FROM_EMAIL = 'Your Company <your-email@example.com>'



python manage.py makemigrations receipts
python manage.py migrate



# Add this code:
# Generate and send receipt
print("\nGenerating receipt for the order...")
receipt = generate_receipt_after_verification(order)
print(f"Receipt generated with ID: {receipt.id}")
if receipt.sent_to_email:
    print(f"Receipt sent to customer email: {order.customer.user.email}")
else:
    print("Receipt created but not sent (no email available)")