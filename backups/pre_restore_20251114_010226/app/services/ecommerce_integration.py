"""
E-commerce Platform Integrations
Support for Shopify, WooCommerce, and more
"""
import requests
from datetime import datetime

class ShopifyIntegration:
    """Shopify integration"""
    
    def __init__(self, shop_url, access_token):
        self.shop_url = shop_url
        self.access_token = access_token
        self.base_url = f"https://{shop_url}/admin/api/2024-01"
    
    def get_headers(self):
        return {
            'X-Shopify-Access-Token': self.access_token,
            'Content-Type': 'application/json'
        }
    
    def get_customers(self, limit=250):
        """Get customers from Shopify"""
        url = f"{self.base_url}/customers.json"
        params = {'limit': limit}
        
        response = requests.get(url, headers=self.get_headers(), params=params)
        response.raise_for_status()
        
        return response.json().get('customers', [])
    
    def get_orders(self, limit=250, status='any'):
        """Get orders from Shopify"""
        url = f"{self.base_url}/orders.json"
        params = {'limit': limit, 'status': status}
        
        response = requests.get(url, headers=self.get_headers(), params=params)
        response.raise_for_status()
        
        return response.json().get('orders', [])
    
    def get_abandoned_checkouts(self, limit=250):
        """Get abandoned carts"""
        url = f"{self.base_url}/checkouts.json"
        params = {'limit': limit, 'status': 'abandoned'}
        
        response = requests.get(url, headers=self.get_headers(), params=params)
        response.raise_for_status()
        
        return response.json().get('checkouts', [])
    
    def sync_customers(self, organization_id):
        """Sync Shopify customers to contacts"""
        from app.models.contact import Contact
        from app import db
        
        customers = self.get_customers()
        synced = 0
        
        for customer in customers:
            email = customer.get('email')
            if not email:
                continue
            
            # Find or create contact
            contact = Contact.query.filter_by(
                organization_id=organization_id,
                email=email
            ).first()
            
            if not contact:
                contact = Contact(
                    organization_id=organization_id,
                    email=email,
                    first_name=customer.get('first_name'),
                    last_name=customer.get('last_name'),
                    status='active'
                )
                db.session.add(contact)
                synced += 1
        
        db.session.commit()
        return synced

class WooCommerceIntegration:
    """WooCommerce integration"""
    
    def __init__(self, site_url, consumer_key, consumer_secret):
        self.site_url = site_url
        self.auth = (consumer_key, consumer_secret)
        self.base_url = f"{site_url}/wp-json/wc/v3"
    
    def get_customers(self, per_page=100):
        """Get customers from WooCommerce"""
        url = f"{self.base_url}/customers"
        params = {'per_page': per_page}
        
        response = requests.get(url, auth=self.auth, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def get_orders(self, per_page=100, status='any'):
        """Get orders from WooCommerce"""
        url = f"{self.base_url}/orders"
        params = {'per_page': per_page, 'status': status}
        
        response = requests.get(url, auth=self.auth, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def sync_customers(self, organization_id):
        """Sync WooCommerce customers to contacts"""
        from app.models.contact import Contact
        from app import db
        
        customers = self.get_customers()
        synced = 0
        
        for customer in customers:
            email = customer.get('email')
            if not email:
                continue
            
            # Find or create contact
            contact = Contact.query.filter_by(
                organization_id=organization_id,
                email=email
            ).first()
            
            if not contact:
                contact = Contact(
                    organization_id=organization_id,
                    email=email,
                    first_name=customer.get('first_name'),
                    last_name=customer.get('last_name'),
                    status='active'
                )
                db.session.add(contact)
                synced += 1
        
        db.session.commit()
        return synced
