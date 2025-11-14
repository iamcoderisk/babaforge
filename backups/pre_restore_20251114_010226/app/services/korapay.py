import requests
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class KorapayService:
    def __init__(self):
        self.base_url = os.environ.get('KORAPAY_BASE_URL', 'https://api.korapay.com/merchant/api/v1')
        self.secret_key = os.environ.get('KORAPAY_SECRET_KEY', '')
        self.public_key = os.environ.get('KORAPAY_PUBLIC_KEY', '')
        
    def _get_headers(self):
        return {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json'
        }
    
    def initialize_transaction(self, amount, email, reference, metadata=None):
        """Initialize a payment transaction"""
        try:
            url = f"{self.base_url}/charges/initialize"
            
            data = {
                'amount': float(amount),
                'currency': 'USD',
                'reference': reference,
                'customer': {
                    'email': email
                },
                'notification_url': f"{os.environ.get('BASE_URL', 'https://sendbaba.com')}/billing/webhook",
                'redirect_url': f"{os.environ.get('BASE_URL', 'https://sendbaba.com')}/billing/verify",
                'metadata': metadata or {}
            }
            
            response = requests.post(url, json=data, headers=self._get_headers())
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Korapay initialize error: {e}")
            return {'status': False, 'message': str(e)}
    
    def verify_transaction(self, reference):
        """Verify a transaction"""
        try:
            url = f"{self.base_url}/charges/{reference}"
            
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Korapay verify error: {e}")
            return {'status': False, 'message': str(e)}
    
    def charge_authorization(self, authorization_code, amount, email, reference):
        """Charge a saved card using authorization code"""
        try:
            url = f"{self.base_url}/charges/card/charge"
            
            data = {
                'amount': float(amount),
                'currency': 'USD',
                'authorization_code': authorization_code,
                'email': email,
                'reference': reference
            }
            
            response = requests.post(url, json=data, headers=self._get_headers())
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Korapay charge authorization error: {e}")
            return {'status': False, 'message': str(e)}
    
    def get_banks(self):
        """Get list of supported banks"""
        try:
            url = f"{self.base_url}/misc/banks"
            
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Korapay get banks error: {e}")
            return {'status': False, 'message': str(e)}

korapay = KorapayService()
