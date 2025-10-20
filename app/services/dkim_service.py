import dkim
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class DKIMService:
    """DKIM signing and verification service"""
    
    def __init__(self):
        self.private_key = self._load_private_key()
        self.public_key = self._load_public_key()
    
    def _load_private_key(self):
        """Load DKIM private key"""
        key_path = Path(settings.DKIM_PRIVATE_KEY_PATH)
        
        if not key_path.exists():
            logger.warning("DKIM private key not found, generating new key")
            self.generate_keys()
        
        with open(key_path, 'rb') as f:
            return f.read()
    
    def _load_public_key(self):
        """Load DKIM public key"""
        key_path = Path(settings.DKIM_PUBLIC_KEY_PATH)
        
        if not key_path.exists():
            return None
        
        with open(key_path, 'rb') as f:
            return f.read()
    
    def generate_keys(self):
        """Generate new DKIM key pair"""
        logger.info("Generating DKIM keys...")
        
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=settings.DKIM_KEY_SIZE,
            backend=default_backend()
        )
        
        # Save private key
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        Path(settings.DKIM_PRIVATE_KEY_PATH).parent.mkdir(parents=True, exist_ok=True)
        with open(settings.DKIM_PRIVATE_KEY_PATH, 'wb') as f:
            f.write(private_pem)
        
        # Save public key
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        with open(settings.DKIM_PUBLIC_KEY_PATH, 'wb') as f:
            f.write(public_pem)
        
        logger.info("DKIM keys generated successfully")
    
    def sign_message(self, message: bytes, domain: str, selector: str = None) -> bytes:
        """Sign email message with DKIM"""
        if selector is None:
            selector = settings.DKIM_SELECTOR
        
        try:
            signature = dkim.sign(
                message,
                selector.encode(),
                domain.encode(),
                self.private_key,
                include_headers=[b'from', b'to', b'subject', b'date']
            )
            
            return signature + message
        except Exception as e:
            logger.error(f"DKIM signing failed: {e}")
            return message
    
    def verify_message(self, message: bytes) -> bool:
        """Verify DKIM signature"""
        try:
            return dkim.verify(message)
        except Exception as e:
            logger.error(f"DKIM verification failed: {e}")
            return False
    
    def get_dns_record(self) -> str:
        """Get DKIM DNS TXT record value"""
        public_key_str = self.public_key.decode('utf-8')
        public_key_str = public_key_str.replace('-----BEGIN PUBLIC KEY-----', '')
        public_key_str = public_key_str.replace('-----END PUBLIC KEY-----', '')
        public_key_str = public_key_str.replace('\n', '')
        
        return f"v=DKIM1; k=rsa; p={public_key_str}"

