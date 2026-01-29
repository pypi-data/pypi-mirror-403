import hashlib
import requests
import json
import urllib.parse
from typing import Dict, Any, Union
from ..contracts import PaymentGatewayInterface
from ..dto import PaymentStatusDTO
from ..exceptions import ConfigurationError, GatewayError, SignatureError

class DuitkuGateway(PaymentGatewayInterface):
    def __init__(self, config: Dict[str, Any]):
        self.merchant_code = config.get('merchant_code')
        self.merchant_key = config.get('merchant_key')
        self.callback_url = config.get('callback_url')
        self.return_url = config.get('return_url')
        self.is_production = config.get('is_production', False)
        
        if not self.merchant_code or not self.merchant_key:
             raise ConfigurationError('Duitku Configuration Error: Merchant Code or Key is missing.')
             
        self.base_url = 'https://passport.duitku.com/webapi' if self.is_production else 'https://sandbox.duitku.com/webapi'

    def create_payment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        amount = str(int(data['amount'])) # Ensure no decimals for MD5
        order_id = str(data['order_id'])
        
        # MD5(merchantCode + merchantOrderId + paymentAmount + merchantKey)
        signature_str = f"{self.merchant_code}{order_id}{amount}{self.merchant_key}"
        signature = hashlib.md5(signature_str.encode('utf-8')).hexdigest()
        
        customer = data.get('customer', {})
        
        payload = {
            'merchantCode': self.merchant_code,
            'paymentAmount': int(amount),
            'merchantOrderId': order_id,
            'productDetails': data.get('description', 'Payment'),
            'additionalParam': '',
            'merchantUserInfo': '',
            'customerVaName': customer.get('name', 'User'),
            'email': customer.get('email', ''),
            'phoneNumber': customer.get('phone', ''),
            'callbackUrl': self.callback_url,
            'returnUrl': self.return_url,
            'signature': signature,
            'expiryPeriod': data.get('expiry', 60)
        }
        
        try:
            response = requests.post(f"{self.base_url}/api/merchant/v2/inquiry", json=payload)
            response.raise_for_status()
            
            body = response.json()
            
            if body.get('statusCode') != '00':
                raise GatewayError(f"Duitku Error: {body.get('statusMessage', 'Unknown error')}")
                
            return {
                'reference': body.get('reference'),
                'payment_url': body.get('paymentUrl'),
                'raw': body
            }
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if e.response is not None:
                error_msg = e.response.text
            raise GatewayError(f"Duitku Error: {error_msg}")

    def handle_webhook(self, headers: Dict[str, str], payload: Union[Dict[str, Any], bytes, str]) -> PaymentStatusDTO:
        # Determine payload type and parse accordingly
        data = {}
        
        # 1. Try to use Content-Type header if available to guide parsing
        content_type = headers.get('Content-Type', '') or headers.get('content-type', '')
        
        # 2. If payload is already a dict, use it directly
        if isinstance(payload, dict):
            data = payload
        
        # 3. If payload is bytes or str, we need to parse it
        elif isinstance(payload, (bytes, str)):
            decoded_payload = payload
            if isinstance(payload, bytes):
                decoded_payload = payload.decode('utf-8')
            
            # Helper to try JSON parsing
            def try_json(text):
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return None

            # Helper to try Form processing
            def try_form(text):
                # urllib.parse.parse_qs returns {key: [val1, val2]}
                # We need to flatten it to {key: val1} for standard usage
                try:
                    parsed = urllib.parse.parse_qs(text, keep_blank_values=True)
                    if not parsed:
                         return None
                    return {k: v[0] for k, v in parsed.items()}
                except Exception:
                    return None

            # Logic based on Content-Type or fallbacks
            if 'application/json' in content_type:
                data = try_json(decoded_payload)
                if data is None:
                     # Fallback to form just in case content-type is wrong, or raise error?
                     # Plan says: JSON if json type, else form. But if json fails, we should probably error or try form?
                     # User said: "Ensure the fallback parsing order is: 1) JSON if Content-Type is application/json 2) x-www-form-urlencoded otherwise"
                     # But also "Raise a warning or error if the payload cannot be parsed"
                     # Let's try form as a desperate fallback or just fail.
                     # If header says JSON but it's not valid JSON, it's likely an error.
                     raise GatewayError("Invalid JSON payload for Duitku")
            
            elif 'application/x-www-form-urlencoded' in content_type:
                data = try_form(decoded_payload)
                if data is None:
                     raise GatewayError("Invalid form-encoded payload for Duitku")
            
            else:
                # No specific header, try JSON then Form
                data = try_json(decoded_payload)
                if data is None:
                    data = try_form(decoded_payload)
                    
            if data is None:
                 raise GatewayError("Failed to parse Duitku webhook payload (tried JSON and Form-UrlEncoded)")

        # Verify we have data
        if not data:
             raise GatewayError("Empty or invalid Duitku payload")

        merchant_code = data.get('merchantCode')
        amount = data.get('amount')
        order_id = data.get('merchantOrderId')
        signature = data.get('signature')
        
        if str(merchant_code) != str(self.merchant_code):
             raise ConfigurationError("Invalid Duitku Merchant Code")
             
        # MD5(merchantCode + amount + merchantOrderId + merchantKey)
        # Note: amount used in calc might need strict string format matching incoming
        # Duitku documentation says amount is integer for signature usually? 
        # But in webhook it might vary.
        # Check if amount is present
        if amount is None or order_id is None:
             raise GatewayError("Missing required fields in Duitku payload")

        my_signature = hashlib.md5(f"{self.merchant_code}{amount}{order_id}{self.merchant_key}".encode('utf-8')).hexdigest()
        
        if signature != my_signature:
             raise SignatureError(f"Invalid Duitku Signature")
             
        result_code = data.get('resultCode')
        
        status = PaymentStatusDTO.STATUS_PENDING
        if result_code == '00':
             status = PaymentStatusDTO.STATUS_PAID
        elif result_code == '01':
             status = PaymentStatusDTO.STATUS_FAILED
             
        return PaymentStatusDTO(
            order_id=order_id,
            status=status,
            amount=float(amount),
            payment_type='duitku',
            raw_response=data
        )
