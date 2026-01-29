import hashlib
import hmac
import base64
import json
import uuid
import datetime
import requests
from typing import Dict, Any, Union
from ..contracts import PaymentGatewayInterface
from ..dto import PaymentStatusDTO
from ..exceptions import ConfigurationError, GatewayError, SignatureError

class DokuGateway(PaymentGatewayInterface):
    def __init__(self, config: Dict[str, Any]):
        self.client_id = config.get('client_id')
        self.shared_key = config.get('shared_key')
        self.is_production = config.get('is_production', False)
        
        if not self.client_id or not self.shared_key:
             raise ConfigurationError('Doku Configuration Error: Client ID or Shared Key is missing.')

        self.base_url = 'https://api.doku.com' if self.is_production else 'https://api-sandbox.doku.com'

    def _generate_signature(self, client_id: str, request_id: str, timestamp: str, target_path: str, digest: str) -> str:
        # Signature = HMAC-SHA256(Client-Id + Request-Id + Request-Timestamp + Request-Target + Digest, Secret-Key)
        component = f"Client-Id:{client_id}\nRequest-Id:{request_id}\nRequest-Timestamp:{timestamp}\nRequest-Target:{target_path}\nDigest:{digest}"
        
        signature = hmac.new(
            self.shared_key.encode('utf-8'),
            component.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        return "HMACSHA256=" + base64.b64encode(signature).decode('utf-8')

    def create_payment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        request_id = str(uuid.uuid4())
        target_path = "/checkout/v1/payment"
        # ISO 8601 UTC
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        
        payload = {
            'order': {
                'invoice_number': data['order_id'],
                'amount': data['amount']
            },
            'payment': {
                'payment_due_date': 60 # minutes
            },
            'customer': data.get('customer', {})
        }
        
        json_body = json.dumps(payload)
        digest_bytes = hashlib.sha256(json_body.encode('utf-8')).digest()
        digest = base64.b64encode(digest_bytes).decode('utf-8')
        
        signature = self._generate_signature(self.client_id, request_id, timestamp, target_path, digest)
        
        try:
            response = requests.post(
                f"{self.base_url}{target_path}",
                data=json_body, # Already dumped
                headers={
                    'Client-Id': self.client_id,
                    'Request-Id': request_id,
                    'Request-Timestamp': timestamp,
                    'Signature': signature,
                    'Content-Type': 'application/json'
                }
            )
            response.raise_for_status()
            
            body = response.json()
            response_data = body.get('response', {})
            return {
                'invoice_number': response_data.get('order', {}).get('invoice_number'),
                'payment_url': response_data.get('payment', {}).get('url'),
                'raw': body
            }

        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if e.response is not None:
                error_msg = e.response.text
            raise GatewayError(f"Doku Error: {error_msg}")

    def handle_webhook(self, headers: Dict[str, str], payload: Union[Dict[str, Any], bytes, str], request_path: str = None) -> PaymentStatusDTO:
        """
        Handle Doku webhook.
        
        IMPORTANT: strict signature verification REQUIRES the `request_path` (the part of the URL after the domain).
        You MUST pass `request_path` to ensure security. 
        Example: if webhook URL is https://yoursite.com/api/callbacks/doku, pass '/api/callbacks/doku'.
        """
        # For Doku signature verification, we need the raw body to calculate digest
        if isinstance(payload, dict):
             # If passed as dict, we dump it back to verify signature which might fail if key order differs
             # Ideally framework passes raw bytes. If not, best effort.
             raw_body = json.dumps(payload, separators=(',', ':')) # Default json format usually
             data = payload
        elif isinstance(payload, bytes):
             raw_body = payload.decode('utf-8')
             data = json.loads(raw_body)
        else: # str
             raw_body = payload
             data = json.loads(raw_body)

        client_id = headers.get('Client-Id') or headers.get('client-id')
        request_id = headers.get('Request-Id') or headers.get('request-id')
        timestamp = headers.get('Request-Timestamp') or headers.get('request-timestamp')
        signature = headers.get('Signature') or headers.get('signature')
        
        # We try to find path in headers if user didn't pass it, but it's non-standard
        if not request_path:
             request_path = headers.get('Request-Path') or headers.get('request-path')

        if not request_path:
             # STRICT ENFORCEMENT as per review
             raise SignatureError("Doku Signature Verification Failed: `request_path` is missing. "
                                  "You MUST provide the request path (e.g. '/api/callback') to handle_webhook "
                                  "to verify the signature.")

        digest_bytes = hashlib.sha256(raw_body.encode('utf-8')).digest()
        digest = base64.b64encode(digest_bytes).decode('utf-8')
        
        calc_signature = self._generate_signature(self.client_id, request_id, timestamp, request_path, digest)
        if signature != calc_signature:
                raise SignatureError(f"Invalid Doku Signature (Got: {signature}, Calc: {calc_signature})")

        transaction_status = data.get('transaction', {}).get('status')
        invoice_number = data.get('order', {}).get('invoice_number')
        
        status = PaymentStatusDTO.STATUS_PENDING
        if transaction_status == 'SUCCESS':
             status = PaymentStatusDTO.STATUS_PAID
        elif transaction_status == 'FAILED':
             status = PaymentStatusDTO.STATUS_FAILED
             
        return PaymentStatusDTO(
            order_id=invoice_number,
            status=status,
            amount=float(data.get('order', {}).get('amount', 0)),
            payment_type='doku',
            raw_response=data
        )
