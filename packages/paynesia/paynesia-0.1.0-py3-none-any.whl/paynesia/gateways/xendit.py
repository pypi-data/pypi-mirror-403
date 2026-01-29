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
        if isinstance(payload, (bytes, str)):
             try:
                 data = json.loads(payload)
             except json.JSONDecodeError:
                 raise GatewayError("Invalid JSON payload")
        else:
             data = payload

        # Check Token
        # Headers might be case-insensitive, but usually passed as dict. 
        # We try to get 'x-callback-token' or 'X-Callback-Token'
        token_header = headers.get('x-callback-token') or headers.get('X-Callback-Token')
        
        if self.callback_token and token_header != self.callback_token:
            raise SignatureError("Invalid Xendit Verification Token")

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
