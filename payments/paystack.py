from django.conf import settings
import requests
import json



class Paystack:
    def __init__(self):
        self.base_url = 'https://api.paystack.co'
        print("\n[DEBUG] Initializing Paystack class")
        
        # More detailed key debugging
        try:
            self.secret_key = settings.PAYSTACK_SECRET_KEY
            if not self.secret_key:
                print("[ERROR] PAYSTACK_SECRET_KEY is empty!")
            elif len(self.secret_key) < 20:  # Paystack keys are typically longer
                print(f"[WARNING] Secret key seems too short: length={len(self.secret_key)}")
            else:
                key_prefix = self.secret_key[:8]
                key_suffix = self.secret_key[-4:]
                print(f"[DEBUG] Secret key format check: starts with '{key_prefix}...', ends with '...{key_suffix}'")
                
                # Check if it's a test or live key
                if 'test' in self.secret_key.lower():
                    print("[DEBUG] Using TEST secret key")
                elif 'live' in self.secret_key.lower():
                    print("[DEBUG] Using LIVE secret key")
                else:
                    print("[WARNING] Key doesn't appear to be marked as test or live")
        except AttributeError:
            print("[ERROR] settings.PAYSTACK_SECRET_KEY is not defined!")
            self.secret_key = ""
        except Exception as e:
            print(f"[ERROR] Error accessing secret key: {e}")
            self.secret_key = ""

    def verify_payment(self, reference, amount):
        """
        Verify payment using Paystack API
        """
        print(f"\n[DEBUG] Starting payment verification")
        print(f"[DEBUG] Reference: {reference}")
        print(f"[DEBUG] Amount to verify: {amount}")
        
        # Convert amount to kobo/cents if needed
        amount_in_kobo = int(amount) * 100
        print(f"[DEBUG] Amount in kobo/cents: {amount_in_kobo}")
        
        path = f"/transaction/verify/{reference}"
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }
        url = self.base_url + path
        
        print(f"[DEBUG] Making API request to: {url}")
        print(f"[DEBUG] Headers (Authorization masked): " + 
              f"{{'Authorization': 'Bearer sk_****', 'Content-Type': '{headers['Content-Type']}'}}")
        
        try:
            print("[DEBUG] Sending verification request...")
            response = requests.get(url, headers=headers)
            print(f"[DEBUG] Response status code: {response.status_code}")
            print(f"[DEBUG] Response headers: {dict(response.headers)}")
            
            # Try to parse the response body
            try:
                response_data = response.json()
                print(f"[DEBUG] Response body: {json.dumps(response_data, indent=2)}")
            except ValueError:
                print(f"[DEBUG] Raw response (not JSON): {response.text[:200]}...")
                return False, "Invalid response format"
                
            # Debug authentication issues
            if response.status_code == 401 or response.status_code == 403:
                print("[ERROR] Authentication failed. Check your API key.")
                return False, "Authentication error"
                
            # Check if response contains expected fields
            if 'status' not in response_data:
                print("[ERROR] Response missing 'status' field")
                return False, "Invalid response structure"
                
            if not response_data['status']:
                error_msg = response_data.get('message', 'Unknown error')
                print(f"[ERROR] API returned error: {error_msg}")
                return False, error_msg
                
            # Extract data from response
            if 'data' not in response_data:
                print("[ERROR] Response missing 'data' field")
                return False, "Invalid response structure"
                
            transaction_data = response_data['data']
            print(f"[DEBUG] Transaction data keys: {list(transaction_data.keys())}")
            
            # Check transaction status
            transaction_status = transaction_data.get('status')
            print(f"[DEBUG] Transaction status: {transaction_status}")
            
            if transaction_status != 'success':
                print(f"[ERROR] Transaction not successful: {transaction_status}")
                return False, f"Transaction {transaction_status}"
            
            # Verify the amount
            paystack_amount = int(transaction_data.get('amount', 0))
            print(f"[DEBUG] Paystack amount: {paystack_amount}")
            print(f"[DEBUG] Expected amount: {amount_in_kobo}")
            
            if abs(paystack_amount - amount_in_kobo) > 100:  # Allow for minor differences
                print(f"[ERROR] Amount mismatch: {paystack_amount} vs {amount_in_kobo}")
                return False, "Amount mismatch"
            
            print("[DEBUG] Verification successful!")
            return True, transaction_data
            
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Network error: {str(e)}")
            return False, f"Network error: {str(e)}"
        except Exception as e:
            print(f"[ERROR] Unexpected error: {str(e)}")
            return False, f"Error: {str(e)}"



# class Paystack:
#     def __init__(self):
#         self.base_url = 'https://api.paystack.co'
#         print("\n[DEBUG] Initializing Paystack class")
        
#         # More detailed key debugging
#         try:
#             self.secret_key = settings.PAYSTACK_SECRET_KEY
#             if not self.secret_key:
#                 print("[ERROR] PAYSTACK_SECRET_KEY is empty!")
#             elif len(self.secret_key) < 20:  # Paystack keys are typically longer
#                 print(f"[WARNING] Secret key seems too short: length={len(self.secret_key)}")
#             else:
#                 key_prefix = self.secret_key[:8]
#                 key_suffix = self.secret_key[-4:]
#                 print(f"[DEBUG] Secret key format check: starts with '{key_prefix}...', ends with '...{key_suffix}'")
                
#                 # Check if it's a test or live key
#                 if 'test' in self.secret_key.lower():
#                     print("[DEBUG] Using TEST secret key")
#                 elif 'live' in self.secret_key.lower():
#                     print("[DEBUG] Using LIVE secret key")
#                 else:
#                     print("[WARNING] Key doesn't appear to be marked as test or live")
#         except AttributeError:
#             print("[ERROR] settings.PAYSTACK_SECRET_KEY is not defined!")
#             self.secret_key = ""
#         except Exception as e:
#             print(f"[ERROR] Error accessing secret key: {e}")
#             self.secret_key = ""

