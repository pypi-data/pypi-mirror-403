class MultipaymentError(Exception):
    """Base exception for multipayment library"""
    pass

class ConfigurationError(MultipaymentError):
    """Raised when configuration is missing or invalid"""
    pass

class GatewayError(MultipaymentError):
    """Raised when the gateway API returns an error"""
    pass

class SignatureError(MultipaymentError):
    """Raised when webhook signature verification leads to failure"""
    pass
