from django.db import models
from django.conf import settings

class Receipt(models.Model):
    order = models.OneToOneField('store.Order', on_delete=models.CASCADE, related_name='receipt')
    pdf_file = models.FileField(upload_to='receipts/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_to_email = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Receipt for Order #{self.order.id}"