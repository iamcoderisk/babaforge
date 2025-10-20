"""
DKIM Service - Key Generation and Email Signing
"""
import os
import dkim
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import logging

logger = logging.getLogger(__name__)

class DKIMService:
    """DKIM key generation and email signing"""
    
    def __init__(self, domain, selector='mail'):
        self.domain = domain
        self.selector = selector
        self.private_key_path = f'data/dkim/{domain}_private.key'
        self.public_key_path = f'data/dkim/{domain}_public.key'
    
    def generate_keys(self, key_size=2048):
        """Generate DKIM RSA key pair"""
        logger.info(f"Generating DKIM keys for {self.domain}")
        
        os.makedirs('data/dkim', exist_ok=True)
        
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )
        
        pem_private = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        with open(self.private_key_path, 'wb') as f:
            f.write(pem_private)
        
        public_key = private_key.public_key()
        pem_public = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        with open(self.public_key_path, 'wb') as f:
            f.write(pem_public)
        
        return {
            'private_key_path': self.private_key_path,
            'public_key_path': self.public_key_path
        }
    
    def get_dns_record(self):
        """Get DKIM DNS TXT record"""
        if not os.path.exists(self.public_key_path):
            raise FileNotFoundError("Public key not found. Generate keys first.")
        
        with open(self.public_key_path, 'rb') as f:
            public_key = f.read()
        
        key_content = public_key.decode('utf-8')
        key_content = key_content.replace('-----BEGIN PUBLIC KEY-----', '')
        key_content = key_content.replace('-----END PUBLIC KEY-----', '')
        key_content = ''.join(key_content.split())
        
        return {
            'type': 'TXT',
            'name': f'{self.selector}._domainkey.{self.domain}',
            'value': f'v=DKIM1; k=rsa; p={key_content}',
            'ttl': 3600
        }
    
    # def sign_email(self, message, private_key=None):
    #     """Sign email with DKIM and return complete signed message"""
    #     if private_key is None:
    #         if not os.path.exists(self.private_key_path):
    #             logger.warning("Private key not found, skipping DKIM signing")
    #             return message if isinstance(message, bytes) else message.encode('utf-8')
            
    #         with open(self.private_key_path, 'rb') as f:
    #             private_key = f.read()
        
    #     # Convert message to bytes if needed
    #     if isinstance(message, str):
    #         message_bytes = message.encode('utf-8')
    #     else:
    #         message_bytes = message
        
    #     try:
    #         # Generate DKIM signature
    #         signature = dkim.sign(
    #             message=message_bytes,
    #             selector=self.selector.encode('utf-8'),
    #             domain=self.domain.encode('utf-8'),
    #             privkey=private_key,
    #             include_headers=[
    #                 b'from', b'to', b'subject', b'date',
    #                 b'message-id', b'mime-version', b'content-type'
    #             ]
    #         )
            
    #         # The dkim.sign() returns the signature header
    #         # We need to prepend it to the message
    #         if signature:
    #             # Remove trailing \r\n from signature if present
    #             if signature.endswith(b'\r\n'):
    #                 signature = signature[:-2]
    #             # Add proper line ending
    #             return signature + b'\r\n' + message_bytes
    #         else:
    #             return message_bytes
            
    #     except Exception as e:
    #         logger.error(f"DKIM signing failed: {e}")
    #         return message_bytes
    def sign_email(self, message_bytes, private_key=None):
        """Sign email with DKIM and return complete signed message"""
        if private_key is None:
            if not os.path.exists(self.private_key_path):
                logger.warning("Private key not found, skipping DKIM signing")
                return message_bytes if isinstance(message_bytes, bytes) else message_bytes.encode('utf-8')
            
            with open(self.private_key_path, 'rb') as f:
                private_key = f.read()
        
        # Ensure we have bytes
        if isinstance(message_bytes, str):
            message_bytes = message_bytes.encode('utf-8')
        
        try:
            # Generate DKIM signature - this returns signature header + message
            signature = dkim.sign(
                message=message_bytes,
                selector=self.selector.encode('utf-8'),
                domain=self.domain.encode('utf-8'),
                privkey=private_key,
                include_headers=[
                    b'from', b'to', b'subject', b'date',
                    b'message-id', b'mime-version', b'content-type'
                ]
            )
            
            # dkim.sign() returns the DKIM-Signature header
            # We need to prepend it to the original message
            if signature and signature != message_bytes:
                return signature + message_bytes
            else:
                return message_bytes
            
        except Exception as e:
            logger.error(f"DKIM signing failed: {e}")
        return message_bytes