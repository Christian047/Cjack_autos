from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import secrets
from .paystack import Paystack
from store.models import Order
import requests


# Create your models here.


class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    amount = models.PositiveIntegerField()
    ref = models.CharField(max_length=200)
    email = models.EmailField()
    verified = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    session_id = models.CharField(max_length=255)  # Ensure this field exists
    payment_order = models.ForeignKey(Order, on_delete=models.CASCADE, default= None, related_name= 'myorder')

    class Meta:
        ordering = ('-date_created',)

    def __str__(self):
        return f"Payment: {self.amount}"

    def save(self, *args, **kwargs):
        while not self.ref:
            ref = secrets.token_urlsafe(50)
            object_with_similar_ref = Payment.objects.filter(ref=ref)
            if not object_with_similar_ref:
                self.ref = ref

        super().save(*args, **kwargs)

    def amount_value(self):
        return int(self.amount) * 100






    def verify_payment(self):
        paystack = Paystack()
        
        # Debug paystack instance
        print(f"DEBUG - Paystack instance: {paystack}")
        print(f"DEBUG - Using reference: {self.ref}")
        print(f"DEBUG - Amount to verify: {self.amount}")
        
        # Debug API key (NEVER print the full secret key, just a masked version)
        if hasattr(paystack, 'secret_key'):
            masked_key = paystack.secret_key[:4] + '****' + paystack.secret_key[-4:] if len(paystack.secret_key) > 8 else '****'
            print(f"DEBUG - Using key starting with: {masked_key}")
        
        # Call verify_payment and capture result
        try:
            status, result = paystack.verify_payment(self.ref, self.amount)
            print(f"DEBUG - API Response Raw: {result}")
            print(f"DEBUG - Verification status: {status}")
        except Exception as e:
            print(f"DEBUG - Exception during verification: {str(e)}")
            return False
        
        # Detailed inspection of the result
        if isinstance(result, dict):
            print(f"DEBUG - Result keys: {list(result.keys())}")
            
            # Check for error messages in the result
            if 'status' in result:
                print(f"DEBUG - Paystack status: {result['status']}")
            if 'message' in result:
                print(f"DEBUG - Paystack message: {result['message']}")
            if 'data' in result and isinstance(result['data'], dict):
                print(f"DEBUG - Data keys: {list(result['data'].keys())}")
                
                # If there's data with status info
                if 'status' in result['data']:
                    print(f"DEBUG - Transaction status: {result['data']['status']}")
                if 'gateway_response' in result['data']:
                    print(f"DEBUG - Gateway response: {result['data']['gateway_response']}")
        
        if status:
            # For dictionaries, get the amount safely
            if isinstance(result, dict):
                # Try different paths to find amount
                if 'amount' in result:
                    paystack_amount = int(result['amount'])
                    print(f"DEBUG - Found amount directly in result: {paystack_amount}")
                elif 'data' in result and isinstance(result['data'], dict) and 'amount' in result['data']:
                    paystack_amount = int(result['data']['amount'])
                    print(f"DEBUG - Found amount in result['data']: {paystack_amount}")
                else:
                    print(f"DEBUG - Could not find amount in result structure: {result}")
                    return False
                
                expected_amount = int(self.amount) * 100  # Convert to kobo/cents
                print(f"DEBUG - Expected amount (converted): {expected_amount}")
                
                # Check if amounts match
                if abs(paystack_amount - expected_amount) < 100:  # Allow for minor differences
                    print(f"DEBUG - Amount verification passed")
                    self.verified = True
                    self.save()
                    print(f"DEBUG - Payment verified successfully: {self.ref}")
                else:
                    print(f"DEBUG - Amount mismatch: Paystack={paystack_amount}, Expected={expected_amount}")
            else:
                print(f"DEBUG - Unexpected result type: {type(result)}")
        else:
            print(f"DEBUG - Verification failed with result: {result}")
        
        return self.verified
    
  
    # def verify_payment(self):
        paystack = Paystack()
        status, result = paystack.verify_payment(self.ref, self.amount)
        
        print(f"Verification result: status={status}, result={result}")
        
        if status:
            # For dictionaries, get the amount safely
            if isinstance(result, dict) and 'amount' in result:
                paystack_amount = int(result['amount'])
                expected_amount = int(self.amount) * 100
                
                # Check if amounts match
                if abs(paystack_amount - expected_amount) < 1:  # Allow for minor differences
                    self.verified = True
                    self.save()
                    print(f"Payment verified successfully: {self.ref}")
                else:
                    print(f"Amount mismatch: Paystack={paystack_amount}, Expected={expected_amount}")
            else:
                print(f"Unexpected result structure: {result}")
        else:
            print(f"Verification failed: {result}")
            
        return self.verified






