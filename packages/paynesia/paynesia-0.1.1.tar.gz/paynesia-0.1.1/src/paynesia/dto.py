from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class PaymentStatusDTO:
    STATUS_PAID = 'PAID'
    STATUS_PENDING = 'PENDING'
    STATUS_FAILED = 'FAILED'
    STATUS_EXPIRED = 'EXPIRED'

    order_id: str
    status: str
    amount: float
    payment_type: str
    raw_response: Dict[str, Any]
