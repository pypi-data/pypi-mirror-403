import hmac
import hashlib
import warnings
import requests
import json
from typing import Dict, Any, Union
from ..contracts import PaymentGatewayInterface
from ..dto import PaymentStatusDTO
from ..exceptions import ConfigurationError, GatewayError, SignatureError

class XenditGateway(PaymentGatewayInterface):
    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get('api_key')
        self.callback_token = config.get('callback_token')
        self.webhook_secret = config.get('webhook_secret')
        self.base_url = 'https://api.xendit.co'

        if not self.api_key:
            raise ConfigurationError("Xendit Configuration Error: API Key is missing.")

    def create_payment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            'external_id': data['order_id'],
            'amount': data['amount'],
            'payer_email': data.get('customer', {}).get('email'),
            'description': data.get('description', f"Payment for {data['order_id']}")
        }

        try:
            response = requests.post(
                f"{self.base_url}/v2/invoices",
                json=payload,
                auth=(self.api_key, '')
            )
            response.raise_for_status()
            
            body = response.json()
            return {
                'invoice_id': body['id'],
                'invoice_url': body['invoice_url'],
                'raw': body
            }
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if e.response is not None:
                error_msg = e.response.text
            raise GatewayError(f"Xendit Error: {error_msg}")

    def handle_webhook(self, headers: Dict[str, str], payload: Union[Dict[str, Any], bytes, str]) -> PaymentStatusDTO:
        # Determine raw payload for HMAC
        if isinstance(payload, bytes):
             raw_payload = payload
        elif isinstance(payload, str):
             raw_payload = payload.encode('utf-8')
        else:
             # Dict - strictly this is risky for HMAC. 
             # We warn user or try best effort. 
             raw_payload = json.dumps(payload, separators=(',', ':')).encode('utf-8')
        
        # Parse data for logic
        if isinstance(payload, (bytes, str)):
             try:
                 data = json.loads(payload)
             except json.JSONDecodeError:
                 raise GatewayError("Invalid JSON payload")
        else:
             data = payload

        # Validation Logic
        verified = False
        
        # 1. HMAC Verification (Modern)
        signature = headers.get('x-callback-signature') or headers.get('X-Callback-Signature')
        
        if self.webhook_secret and signature:
             # Verify HMAC
             calculated_signature = hmac.new(
                 self.webhook_secret.encode('utf-8'),
                 raw_payload,
                 hashlib.sha256
             ).hexdigest()
             
             if not hmac.compare_digest(signature, calculated_signature):
                  raise SignatureError(f"Invalid Xendit HMAC Signature")
             verified = True
             
        # 2. Legacy Token Verification (Deprecated)
        if not verified and self.callback_token:
             token_header = headers.get('x-callback-token') or headers.get('X-Callback-Token')
             if token_header == self.callback_token:
                  verified = True
                  warnings.warn(
                      "Xendit `callback_token` verification is deprecated. "
                      "Please configure `webhook_secret` and use HMAC verification.",
                      DeprecationWarning
                  )
             else:
                  # Only raise if this was the ONLY method available or if token explicitly mismatched
                  if not self.webhook_secret:
                       raise SignatureError("Invalid Xendit Verification Token")

        # 3. Final Check
        if not verified:
             if self.webhook_secret:
                  raise SignatureError("Xendit Signature Verification Failed (HMAC missing or invalid)")
             elif self.callback_token:
                  # Already handled above
                  pass 
             else:
                  raise ConfigurationError("Xendit Configuration Error: No verification method configured (webhook_secret or callback_token missing)")

        status_str = data.get('status', '')
        
        status = PaymentStatusDTO.STATUS_PENDING
        if status_str == 'PAID':
            status = PaymentStatusDTO.STATUS_PAID
        elif status_str == 'EXPIRED':
            status = PaymentStatusDTO.STATUS_EXPIRED
            
        return PaymentStatusDTO(
            order_id=data.get('external_id'),
            status=status,
            amount=float(data.get('amount', 0)),
            payment_type='xendit',
            raw_response=data
        )
