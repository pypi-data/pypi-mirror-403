import hashlib
import json
import base64
import requests
from typing import Dict, Any, Union
from ..contracts import PaymentGatewayInterface
from ..dto import PaymentStatusDTO
from ..exceptions import ConfigurationError, GatewayError, SignatureError

class MidtransGateway(PaymentGatewayInterface):
    def __init__(self, config: Dict[str, Any]):
        self.server_key = config.get('server_key')
        self.is_production = config.get('is_production', False)
        
        if not self.server_key:
            raise ConfigurationError("Midtrans Configuration Error: Server Key is missing.")

        self.base_url = 'https://app.midtrans.com/snap/v1' if self.is_production else 'https://app.sandbox.midtrans.com/snap/v1'

    def create_payment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        :param data: {
            'order_id': str,
            'amount': float/int,
            'customer': dict (optional),
            'items': list (optional)
        }
        """
        payload = {
            'transaction_details': {
                'order_id': data['order_id'],
                'gross_amount': data['amount'], # Midtrans expects int/float, will handle JSON conversion
            },
            'customer_details': data.get('customer', {}),
            'item_details': data.get('items', [])
        }

        # Basic Auth: serverKey + ':' encoded base64
        # requests handles BasicAuth easily
        
        try:
            response = requests.post(
                f"{self.base_url}/transactions",
                json=payload,
                auth=(self.server_key, ''),
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            
            body = response.json()
            return {
                'token': body.get('token'),
                'redirect_url': body.get('redirect_url'),
                'raw': body
            }

        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if e.response is not None:
                error_msg = e.response.text
            raise GatewayError(f"Midtrans Error: {error_msg}")

    def handle_webhook(self, headers: Dict[str, str], payload: Union[Dict[str, Any], bytes, str]) -> PaymentStatusDTO:
        # Normalize payload to dict
        if isinstance(payload, (bytes, str)):
             try:
                 data = json.loads(payload)
             except json.JSONDecodeError:
                 raise GatewayError("Invalid JSON payload")
        else:
             data = payload

        # Check required keys
        required_keys = ['order_id', 'status_code', 'gross_amount', 'signature_key', 'transaction_status']
        if not all(k in data for k in required_keys):
             raise GatewayError("Invalid Midtrans Webhook Payload: Missing required keys.")

        order_id = data['order_id']
        status_code = data['status_code']
        gross_amount = data['gross_amount']
        signature_key = data['signature_key']
        transaction_status = data['transaction_status']
        payment_type = data.get('payment_type', 'midtrans')

        # Robust Signature Check logic from PHP
        # SHA512(order_id + status_code + gross_amount + server_key)
        
        is_valid = False
        
        # Try 1: Raw
        raw_signature = hashlib.sha512(f"{order_id}{status_code}{gross_amount}{self.server_key}".encode()).hexdigest()
        if raw_signature == signature_key:
            is_valid = True
        else:
            # Try 2: Int
            try:
                amount_int = int(float(gross_amount))
                sig_int = hashlib.sha512(f"{order_id}{status_code}{amount_int}{self.server_key}".encode()).hexdigest()
                if sig_int == signature_key:
                    is_valid = True
                else:
                    # Try 3: 2 decimals
                    amount_float = "{:.2f}".format(float(gross_amount))
                    sig_float = hashlib.sha512(f"{order_id}{status_code}{amount_float}{self.server_key}".encode()).hexdigest()
                    if sig_float == signature_key:
                         is_valid = True
            except ValueError:
                pass

        if not is_valid:
            raise SignatureError("Invalid Midtrans Signature")

        status = PaymentStatusDTO.STATUS_PENDING
        
        if transaction_status == 'capture':
            if data.get('fraud_status') == 'accept':
                status = PaymentStatusDTO.STATUS_PAID
        elif transaction_status == 'settlement':
            status = PaymentStatusDTO.STATUS_PAID
        elif transaction_status in ['cancel', 'deny', 'expire']:
            status = PaymentStatusDTO.STATUS_FAILED
        elif transaction_status == 'pending':
            status = PaymentStatusDTO.STATUS_PENDING

        return PaymentStatusDTO(
            order_id=order_id,
            status=status,
            amount=float(gross_amount),
            payment_type=payment_type,
            raw_response=data
        )
