"""
Automated DNS Verification Service
Checks SPF, DKIM, and DMARC records automatically
"""
import dns.resolver
import re
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class DNSVerifier:
    """Automated DNS verification for email authentication"""
    
    def __init__(self):
        self.resolver = dns.resolver.Resolver()
        self.resolver.timeout = 5
        self.resolver.lifetime = 5
    
    def verify_domain(self, domain: str, expected_ip: str = None) -> Dict:
        """
        Complete domain verification
        Returns: {
            'domain': str,
            'verified': bool,
            'spf': dict,
            'dkim': dict,
            'dmarc': dict,
            'score': int (0-100)
        }
        """
        result = {
            'domain': domain,
            'verified': False,
            'spf': self.check_spf(domain, expected_ip),
            'dkim': self.check_dkim(domain),
            'dmarc': self.check_dmarc(domain),
            'mx': self.check_mx(domain),
            'score': 0
        }
        
        # Calculate verification score
        if result['spf']['valid']:
            result['score'] += 30
        if result['dkim']['valid']:
            result['score'] += 40
        if result['dmarc']['valid']:
            result['score'] += 20
        if result['mx']['valid']:
            result['score'] += 10
        
        result['verified'] = result['score'] >= 70
        
        return result
    
    def check_spf(self, domain: str, expected_ip: str = None) -> Dict:
        """Check SPF record"""
        try:
            answers = self.resolver.resolve(domain, 'TXT')
            
            for rdata in answers:
                txt = str(rdata).strip('"')
                if txt.startswith('v=spf1'):
                    result = {
                        'valid': True,
                        'record': txt,
                        'includes_ip': False,
                        'policy': self._extract_spf_policy(txt)
                    }
                    
                    if expected_ip and expected_ip in txt:
                        result['includes_ip'] = True
                    
                    return result
            
            return {
                'valid': False,
                'error': 'No SPF record found',
                'recommendation': f'Add: v=spf1 ip4:{expected_ip} ~all'
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'recommendation': f'Add SPF record to DNS'
            }
    
    def check_dkim(self, domain: str, selector: str = 'default') -> Dict:
        """Check DKIM record"""
        dkim_domain = f'{selector}._domainkey.{domain}'
        
        try:
            answers = self.resolver.resolve(dkim_domain, 'TXT')
            
            for rdata in answers:
                txt = str(rdata).strip('"')
                if 'v=DKIM1' in txt:
                    return {
                        'valid': True,
                        'selector': selector,
                        'record': txt,
                        'key_found': 'p=' in txt
                    }
            
            return {
                'valid': False,
                'error': 'No DKIM record found',
                'recommendation': f'Add DKIM record at {dkim_domain}'
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'recommendation': 'Generate and add DKIM public key'
            }
    
    def check_dmarc(self, domain: str) -> Dict:
        """Check DMARC record"""
        dmarc_domain = f'_dmarc.{domain}'
        
        try:
            answers = self.resolver.resolve(dmarc_domain, 'TXT')
            
            for rdata in answers:
                txt = str(rdata).strip('"')
                if txt.startswith('v=DMARC1'):
                    return {
                        'valid': True,
                        'record': txt,
                        'policy': self._extract_dmarc_policy(txt),
                        'reporting': 'rua=' in txt
                    }
            
            return {
                'valid': False,
                'error': 'No DMARC record found',
                'recommendation': f'Add: v=DMARC1; p=none; rua=mailto:dmarc@{domain}'
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'recommendation': 'Add DMARC record'
            }
    
    def check_mx(self, domain: str) -> Dict:
        """Check MX records"""
        try:
            answers = self.resolver.resolve(domain, 'MX')
            mx_records = [(mx.preference, str(mx.exchange).rstrip('.')) 
                         for mx in answers]
            
            return {
                'valid': len(mx_records) > 0,
                'records': mx_records,
                'count': len(mx_records)
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }
    
    def _extract_spf_policy(self, record: str) -> str:
        """Extract SPF policy (~all, -all, etc)"""
        if '~all' in record:
            return 'softfail'
        elif '-all' in record:
            return 'fail'
        elif '+all' in record:
            return 'pass'
        return 'neutral'
    
    def _extract_dmarc_policy(self, record: str) -> str:
        """Extract DMARC policy"""
        match = re.search(r'p=(\w+)', record)
        return match.group(1) if match else 'none'
