import unittest
from unittest.mock import patch, MagicMock
from paynesia.manager import PaymentManager
from paynesia.dto import PaymentStatusDTO

class TestPaymentManager(unittest.TestCase):
    def setUp(self):
        self.config = {
            'default': 'midtrans',
            'gateways': {
                'midtrans': {'server_key': 'mock_key'},
                'xendit': {'api_key': 'mock_key'}
            }
        }
        self.manager = PaymentManager(self.config)

    def test_manager_driver_midtrans(self):
        driver = self.manager.driver('midtrans')
        self.assertEqual(driver.server_key, 'mock_key')

    def test_manager_driver_xendit(self):
        driver = self.manager.driver('xendit')
        self.assertEqual(driver.api_key, 'mock_key')

if __name__ == '__main__':
    unittest.main()
