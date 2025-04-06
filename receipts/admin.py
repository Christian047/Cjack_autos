
from django.contrib import admin
from .models import Receipt

class ReceiptAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'created_at', 'sent_to_email', 'email_sent_at')
    list_filter = ('sent_to_email',)
    search_fields = ('order__id', 'order__transaction_id', 'order__customer__name')
    
    actions = ['regenerate_receipts', 'send_receipts_by_email']
    
    def regenerate_receipts(self, request, queryset):
        from receipts.utils import generate_and_save_receipt
        count = 0
        for receipt in queryset:
            generate_and_save_receipt(receipt.order)
            count += 1
        self.message_user(request, f"{count} receipts have been regenerated.")
    
    def send_receipts_by_email(self, request, queryset):
        from receipts.utils import send_receipt_email
        sent = 0
        failed = 0
        for receipt in queryset:
            if send_receipt_email(receipt):
                sent += 1
            else:
                failed += 1
        
        if failed:
            self.message_user(request, f"{sent} receipts sent, {failed} failed.")
        else:
            self.message_user(request, f"{sent} receipts have been sent.")

admin.site.register(Receipt, ReceiptAdmin)