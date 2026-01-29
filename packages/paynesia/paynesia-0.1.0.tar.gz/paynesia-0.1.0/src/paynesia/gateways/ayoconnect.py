import requests
import json
from typing import Dict, Any, Union
from ..contracts import PaymentGatewayInterface
from ..dto import PaymentStatusDTO
from ..exceptions import ConfigurationError, GatewayError

class AyoConnectGateway(PaymentGatewayInterface):
    def __init__(self, config: Dict[str, Any]):
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
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
