"""
DNS Validator Service
"""
import dns.resolver
import logging

logger = logging.getLogger(__name__)

class DNSValidator:
    """Validate DNS records"""
    
    def __init__(self, domain):
        self.domain = domain
        self.resolver = dns.resolver.Resolver()
    
    def verify_dkim(self, selector='mail'):
        """Verify DKIM record"""
        try:
            dkim_domain = f'{selector}._domainkey.{self.domain}'
            answers = self.resolver.resolve(dkim_domain, 'TXT')
            
            for rdata in answers:
                txt_value = b''.join(rdata.strings).decode('utf-8')
                if 'v=DKIM1' in txt_value:
                    return {'valid': True, 'record': txt_value}
            
            return {'valid': False, 'message': 'DKIM record not found'}
        except Exception as e:
            return {'valid': False, 'message': str(e)}
    
    def verify_all(self):
        """Verify all records"""
        return {
            'dkim': self.verify_dkim()
        }
