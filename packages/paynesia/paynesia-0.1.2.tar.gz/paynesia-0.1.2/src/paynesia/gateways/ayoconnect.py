import hmac
import hashlib
import base64
import requests
import json
from typing import Dict, Any, Union
from ..contracts import PaymentGatewayInterface
from ..dto import PaymentStatusDTO
from ..exceptions import ConfigurationError, GatewayError, SignatureError

# Try importing cryptography for RSA
try:
    from cryptography.hazmat.primitives import serialization, hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

class AyoConnectGateway(PaymentGatewayInterface):
    def __init__(self, config: Dict[str, Any]):
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        self.public_key_string = config.get('public_key')
        self.use_hmac_if_no_key = config.get('use_hmac', True) # Default fallback
        self.is_production = config.get('is_production', False)
        self.endpoint = config.get('endpoint', '/v1/transactions')
        
        self.base_url = 'https://api.ayoconnect.id' if self.is_production else 'https://api-stg.ayoconnect.id'
        
        if not self.client_id or not self.client_secret:
             raise ConfigurationError('AyoConnect Configuration Error: Client ID or Secret is missing.')

    def _get_access_token(self) -> str:
        try:
            response = requests.post(f"{self.base_url}/v1/oauth/token", data={
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret
            })
            response.raise_for_status()
            return response.json()['access_token']
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if e.response is not None:
                error_msg = e.response.text
            raise GatewayError(f"AyoConnect OAuth Error: {error_msg}")

    def create_payment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        token = self._get_access_token()
        
        payload = {
            'orderId': data['order_id'],
            'amount': data['amount'],
            'currency': 'IDR',
            'description': data.get('description', 'Payment'),
            'customer': data.get('customer', {})
        }
        
        try:
            response = requests.post(
                f"{self.base_url}{self.endpoint}",
                json=payload,
                headers={'Authorization': f"Bearer {token}"}
            )
            response.raise_for_status()
            
            body = response.json()
            data_body = body.get('data', {})
            
            return {
                'transaction_id': data_body.get('transactionId'),
                'payment_url': data_body.get('url'),
                'raw': body
            }
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if e.response is not None:
                error_msg = e.response.text
            raise GatewayError(f"AyoConnect Error: {error_msg}")

    def handle_webhook(self, headers: Dict[str, str], payload: Union[Dict[str, Any], bytes, str]) -> PaymentStatusDTO:
        # Get signature from header
        signature = headers.get('X-Signature') or headers.get('x-signature')
        
        if not signature:
             raise SignatureError("Missing Ayoconnect X-Signature header")

        # Prepare raw body for verification
        if isinstance(payload, bytes):
             raw_body = payload
        elif isinstance(payload, str):
             raw_body = payload.encode('utf-8')
        else:
             # Dict - dump to json string as best effort, but strongly discouraged for strict signature
             raw_body = json.dumps(payload, separators=(',', ':')).encode('utf-8')

        # Logic: Prefer RSA if public_key is set, else HMAC with client_secret
        verified = False
        
        if self.public_key_string:
            if not HAS_CRYPTO:
                 raise ConfigurationError("Ayoconnect 'public_key' is set but 'cryptography' library is not installed. "
                                          "Please install it via `pip install cryptography` to use RSA verification.")
            
            try:
                public_key = serialization.load_pem_public_key(
                    self.public_key_string.encode('utf-8') if isinstance(self.public_key_string, str) else self.public_key_string
                )
                
                # Decode signature from Base64
                signature_bytes = base64.b64decode(signature)
                
                public_key.verify(
                    signature_bytes,
                    raw_body,
                    padding.PKCS1v15(),
                    hashes.SHA256()
                )
                verified = True
            except Exception as e:
                 # Verification failed
                 raise SignatureError(f"Ayoconnect RSA Signature Verification Failed: {str(e)}")
        
        elif self.client_secret:
             # Fallback to HMAC-SHA256 using client_secret
             # Ayoconnect format for HMAC? 
             # Usually standard HMAC-SHA256(secret, body) base64
             
             calculated_signature = base64.b64encode(
                 hmac.new(
                     self.client_secret.encode('utf-8'),
                     raw_body,
                     hashlib.sha256
                 ).digest()
             ).decode('utf-8')
             
             # Compare (timing safe)
             # signature header might be 'HMACSHA256=' prefix? Ayoconnect usually just the base64 string
             # Adjust if needed based on typical formats, but normally it's raw base64.
             # Note: Doku used a prefix, Ayo usually doesn't, or it's just the hash.
             # We compare directly.
             
             if not hmac.compare_digest(signature, calculated_signature):
                  raise SignatureError(f"Ayoconnect HMAC Signature Verification Failed")
             
             verified = True
             
        if not verified:
             raise ConfigurationError("Ayoconnect Signature Verification failed to execute: No valid key (RSA public key or client secret) available.")

        # Parsing Payload
        if isinstance(payload, (bytes, str)):
             try:
                 data = json.loads(payload)
             except json.JSONDecodeError:
                 data = {}
        else:
             data = payload
             
        status_str = data.get('status', '')
        
        status = PaymentStatusDTO.STATUS_PENDING
        if status_str == 'SUCCESS':
             status = PaymentStatusDTO.STATUS_PAID
        elif status_str == 'FAILED':
             status = PaymentStatusDTO.STATUS_FAILED
             
        return PaymentStatusDTO(
            order_id=data.get('orderId'),
            status=status,
            amount=float(data.get('amount', 0)),
            payment_type='ayoconnect',
            raw_response=data
        )
