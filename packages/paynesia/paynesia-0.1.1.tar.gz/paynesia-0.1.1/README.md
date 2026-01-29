# Paynesia

A framework-agnostic Python library for integrating multiple Indonesian payment gateways.

## Supported Gateways
- Midtrans
- Xendit
- Doku
- Duitku
- AyoConnect
- Fonnte (WhatsApp Notification)

## Security Notes

> [!IMPORTANT]
> **Signature Verification**: Always verify webhook signatures to prevent fraud. This library provides built-in signature verification in `handle_webhook` for all supported gateways.
>
> **Doku Gateway**: You **MUST** pass the `request_path` argument (e.g., `/api/callbacks/doku`) to `handle_webhook` for strict signature verification.
> 
> **Ayoconnect Gateway**: Signature verification requires either `client_secret` (for HMAC) or `public_key` (for RSA). If using RSA, ensure the `cryptography` library is installed.
>
> **Xendit Gateway**: Please configure `webhook_secret` to enable HMAC signature verification. Legacy `callback_token` usage is deprecated.
>
> **Environment Variables**: Never hardcode your keys. Use environment variables and pass them to the configuration.


## Installation

```bash
pip install paynesia
```

## Usage

```python
import os
from paynesia.manager import PaymentManager

# Optional: if using python-dotenv to load .env file
# from dotenv import load_dotenv
# load_dotenv()

config = {
    'default': 'midtrans',
    'gateways': {
        'midtrans': {
            'server_key': os.getenv('MIDTRANS_SERVER_KEY'),
            'is_production': os.getenv('MIDTRANS_IS_PRODUCTION', 'False') == 'True'
        }
    }
}

manager = PaymentManager(config)
payment = manager.driver('midtrans').create_payment({
    'order_id': 'ORDER-123',
    'amount': 10000,
    'customer': {'email': 'user@example.com'}
})

print(payment)
```
