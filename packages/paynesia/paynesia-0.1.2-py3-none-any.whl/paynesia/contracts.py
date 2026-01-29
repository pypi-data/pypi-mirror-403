from abc import ABC, abstractmethod
from typing import Dict, Any, Union
from .dto import PaymentStatusDTO

class PaymentGatewayInterface(ABC):
    @abstractmethod
    def create_payment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a payment request.

        :param data: Dictionary containing order_id, amount, customer info, etc.
        :return: standardized response dictionary (e.g. including 'payment_url')
        """
        pass

    @abstractmethod
    def handle_webhook(self, headers: Dict[str, str], payload: Union[Dict[str, Any], bytes, str]) -> PaymentStatusDTO:
        """
        Handle webhook incoming request.

        :param headers: Request headers (dict)
        :param payload: Request body (parsed dict or raw bytes/str depending on gateway needs)
        :return: PaymentStatusDTO
        """
        pass
