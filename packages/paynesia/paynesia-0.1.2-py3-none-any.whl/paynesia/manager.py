from typing import Dict, Any, Optional
from .contracts import PaymentGatewayInterface
from .exceptions import ConfigurationError

# Import gateways inside the method or at top? Top is better for static checking
from .gateways.midtrans import MidtransGateway
from .gateways.xendit import XenditGateway
from .gateways.doku import DokuGateway
from .gateways.duitku import DuitkuGateway
from .gateways.ayoconnect import AyoConnectGateway

class PaymentManager:
    def __init__(self, config: Dict[str, Any]):
        """
        :param config: Dictionary containing configuration.
                       Example:
                       {
                           'default': 'midtrans',
                           'gateways': {
                               'midtrans': { ... },
                               'xendit': { ... }
                           }
                       }
        """
        self.config = config

    def driver(self, name: Optional[str] = None) -> PaymentGatewayInterface:
        if name is None:
            name = self.config.get('default')
        
        if not name:
             raise ConfigurationError("No default driver specified in config.")

        gateway_config = self.config.get('gateways', {}).get(name, {})
        
        if name == 'midtrans':
            return MidtransGateway(gateway_config)
        elif name == 'xendit':
             return XenditGateway(gateway_config)
        elif name == 'doku':
             return DokuGateway(gateway_config)
        elif name == 'duitku':
             return DuitkuGateway(gateway_config)
        elif name == 'ayoconnect':
             return AyoConnectGateway(gateway_config)
        
        raise ConfigurationError(f"Payment gateway driver [{name}] is not supported.")
