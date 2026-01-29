import unittest
import json
import hashlib
import hmac
import base64
import warnings
import sys
import os

# Ensure src is in path
sys.path.append(os.path.join(os.getcwd(), 'src'))

# Mock requests module since it might not be installed in the agent env
from unittest.mock import MagicMock
mock_requests = MagicMock()
mock_requests.exceptions.RequestException = Exception
sys.modules['requests'] = mock_requests

from paynesia.gateways.duitku import DuitkuGateway
from paynesia.gateways.doku import DokuGateway
from paynesia.gateways.ayoconnect import AyoConnectGateway
from paynesia.gateways.xendit import XenditGateway
from paynesia.exceptions import GatewayError, SignatureError, ConfigurationError
from paynesia.dto import PaymentStatusDTO

# Mock Cryptography if not installed for testing logic flow
try:
    from cryptography.hazmat.primitives import serialization, hashes
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

class TestDuitkuGateway(unittest.TestCase):
    def setUp(self):
        self.config = {
            'merchant_code': 'test_merchant',
            'merchant_key': 'test_key',
            'is_production': False
        }
        self.gateway = DuitkuGateway(self.config)

    def test_json_payload(self):
        payload = {
            'merchantCode': 'test_merchant',
            'amount': '10000',
            'merchantOrderId': 'ORDER123',
            'resultCode': '00',
            'signature': hashlib.md5(b'test_merchant10000ORDER123test_key').hexdigest()
        }
        headers = {'Content-Type': 'application/json'}
        result = self.gateway.handle_webhook(headers, json.dumps(payload))
        self.assertEqual(result.status, PaymentStatusDTO.STATUS_PAID)

    def test_form_payload(self):
        # raw string: merchantCode=test_merchant&amount=10000...
        sig = hashlib.md5(b'test_merchant10000ORDER123test_key').hexdigest()
        payload_str = f"merchantCode=test_merchant&amount=10000&merchantOrderId=ORDER123&resultCode=00&signature={sig}"
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        result = self.gateway.handle_webhook(headers, payload_str)
        self.assertEqual(result.status, PaymentStatusDTO.STATUS_PAID)

    def test_fallback_parsing(self):
        # No content type, try form logic (failed json)
        sig = hashlib.md5(b'test_merchant10000ORDER123test_key').hexdigest()
        payload_str = f"merchantCode=test_merchant&amount=10000&merchantOrderId=ORDER123&resultCode=01&signature={sig}"
        headers = {}
        result = self.gateway.handle_webhook(headers, payload_str)
        self.assertEqual(result.status, PaymentStatusDTO.STATUS_FAILED)

    def test_invalid_signature(self):
        payload = {
            'merchantCode': 'test_merchant',
            'amount': '10000',
            'merchantOrderId': 'ORDER123',
            'resultCode': '00',
            'signature': 'invalid'
        }
        with self.assertRaises(SignatureError):
            self.gateway.handle_webhook({}, json.dumps(payload))

class TestDokuGateway(unittest.TestCase):
    def setUp(self):
        self.config = {
            'client_id': 'CLIENT123',
            'shared_key': 'SHARED_KEY',
            'is_production': False
        }
        self.gateway = DokuGateway(self.config)

    def test_valid_signature_with_path(self):
        payload = {'order': {'invoice_number': 'INV123', 'amount': 10000}, 'transaction': {'status': 'SUCCESS'}}
        raw_body = json.dumps(payload, separators=(',', ':'))
        digest = base64.b64encode(hashlib.sha256(raw_body.encode()).digest()).decode()
        
        target_path = '/api/callback'
        req_id = 'REQ1'
        ts = '2023-01-01T00:00:00Z'
        
        comp = f"Client-Id:{self.config['client_id']}\nRequest-Id:{req_id}\nRequest-Timestamp:{ts}\nRequest-Target:{target_path}\nDigest:{digest}"
        sig = "HMACSHA256=" + base64.b64encode(hmac.new(self.config['shared_key'].encode(), comp.encode(), hashlib.sha256).digest()).decode()
        
        headers = {
            'Client-Id': self.config['client_id'],
            'Request-Id': req_id,
            'Request-Timestamp': ts,
            'Signature': sig
        }
        
        result = self.gateway.handle_webhook(headers, payload, request_path=target_path)
        self.assertEqual(result.status, PaymentStatusDTO.STATUS_PAID)

    def test_missing_request_path(self):
        headers = {'Client-Id': 'CLIENT123'}
        with self.assertRaises(SignatureError):
             self.gateway.handle_webhook(headers, {'order': {}})

class TestAyoConnectGateway(unittest.TestCase):
    def setUp(self):
        self.config = {
            'client_id': 'CID',
            'client_secret': 'SECRET',
            'is_production': False
        }
        self.gateway = AyoConnectGateway(self.config)

    def test_hmac_verification(self):
        payload = '{"amount":100,"status":"SUCCESS","orderId":"OID"}'
        sig = base64.b64encode(hmac.new(b'SECRET', payload.encode(), hashlib.sha256).digest()).decode()
        headers = {'X-Signature': sig}
        
        result = self.gateway.handle_webhook(headers, payload)
        self.assertEqual(result.status, PaymentStatusDTO.STATUS_PAID)

    def test_invalid_hmac(self):
        with self.assertRaises(SignatureError):
            self.gateway.handle_webhook({'X-Signature': 'invalid'}, '{}')

class TestXenditGateway(unittest.TestCase):
    def setUp(self):
        self.config = {
            'api_key': 'KEY',
            'webhook_secret': 'SECRET',
            'callback_token': 'TOKEN'
        }
        self.gateway = XenditGateway(self.config)

    def test_hmac_verification(self):
        payload = '{"status":"PAID","external_id":"OID","amount":100}'
        sig = hmac.new(b'SECRET', payload.encode(), hashlib.sha256).hexdigest()
        headers = {'x-callback-signature': sig}
        
        result = self.gateway.handle_webhook(headers, payload)
        self.assertEqual(result.status, PaymentStatusDTO.STATUS_PAID)

    def test_legacy_token_warning(self):
        # valid legacy, invalid hmac (or hmac header missing)
        headers = {'x-callback-token': 'TOKEN'}
        payload = '{"status":"PAID"}'
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            self.gateway.handle_webhook(headers, payload)
            self.assertTrue(len(w) > 0)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))

if __name__ == '__main__':
    unittest.main()
