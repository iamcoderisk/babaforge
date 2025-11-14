"""
Advanced Email Validation Service
Validates emails before sending to prevent bounces
"""
import re
import dns.resolver
import socket
import smtplib
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class EmailValidator:
    """Comprehensive email validation"""
    
    # Common disposable email domains
    DISPOSABLE_DOMAINS = {
        'tempmail.com', 'guerrillamail.com', '10minutemail.com',
        'throwaway.email', 'mailinator.com', 'trashmail.com'
    }
    
    # Common role-based emails
    ROLE_BASED = {
        'admin', 'info', 'support', 'sales', 'contact',
        'noreply', 'postmaster', 'webmaster', 'abuse'
    }
    
    def __init__(self):
        self.dns_cache = {}
    
    def validate(self, email: str) -> Dict:
        """
        Comprehensive email validation
        Returns: {
            'valid': bool,
            'email': str,
            'score': int (0-100),
            'issues': list,
            'details': dict
        }
        """
        result = {
            'valid': False,
            'email': email.lower().strip(),
            'score': 0,
            'issues': [],
            'details': {}
        }
        
        try:
            # 1. Format validation
            if not self._validate_format(email):
                result['issues'].append('Invalid email format')
                return result
            
            result['score'] += 20
            
            # 2. Extract domain
            local, domain = email.split('@')
            result['details']['local'] = local
            result['details']['domain'] = domain
            
            # 3. Check disposable
            if domain in self.DISPOSABLE_DOMAINS:
                result['issues'].append('Disposable email address')
                result['score'] -= 30
            else:
                result['score'] += 10
            
            # 4. Check role-based
            if local in self.ROLE_BASED:
                result['issues'].append('Role-based email address')
                result['details']['role_based'] = True
            else:
                result['score'] += 10
            
            # 5. DNS validation
            dns_valid, mx_records = self._validate_dns(domain)
            if dns_valid:
                result['score'] += 30
                result['details']['mx_records'] = mx_records
            else:
                result['issues'].append('No valid MX records')
                return result
            
            # 6. SMTP validation (optional - can be slow)
            # smtp_valid = self._validate_smtp(email, mx_records[0])
            # if smtp_valid:
            #     result['score'] += 30
            
            result['score'] = min(100, result['score'])
            result['valid'] = result['score'] >= 60
            
        except Exception as e:
            logger.error(f"Validation error for {email}: {e}")
            result['issues'].append(f'Validation error: {str(e)}')
        
        return result
    
    def _validate_format(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _validate_dns(self, domain: str) -> Tuple[bool, list]:
        """Validate domain has MX records"""
        if domain in self.dns_cache:
            return self.dns_cache[domain]
        
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            records = [str(mx.exchange).rstrip('.') for mx in mx_records]
            self.dns_cache[domain] = (True, records)
            return True, records
        except:
            self.dns_cache[domain] = (False, [])
            return False, []
    
    def _validate_smtp(self, email: str, mx_host: str) -> bool:
        """Validate email exists via SMTP (optional)"""
        try:
            server = smtplib.SMTP(timeout=10)
            server.connect(mx_host)
            server.helo()
            server.mail('verify@sendbaba.com')
            code, message = server.rcpt(email)
            server.quit()
            return code == 250
        except:
            return False
    
    def bulk_validate(self, emails: list) -> Dict:
        """Validate multiple emails"""
        results = {
            'total': len(emails),
            'valid': 0,
            'invalid': 0,
            'risky': 0,
            'results': []
        }
        
        for email in emails:
            result = self.validate(email)
            results['results'].append(result)
            
            if result['valid']:
                if result['score'] >= 80:
                    results['valid'] += 1
                else:
                    results['risky'] += 1
            else:
                results['invalid'] += 1
        
        return results
