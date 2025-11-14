import socket
import dns.resolver
import dns.reversename
from typing import Optional, List

from app.utils.logger import get_logger

logger = get_logger(__name__)

class DNSUtils:
    """DNS utility functions"""
    
    @staticmethod
    async def verify_reverse_dns(ip_address: str, expected_hostname: str) -> bool:
        """Verify reverse DNS (PTR record)"""
        try:
            reverse_name = dns.reversename.from_address(ip_address)
            ptr_records = dns.resolver.resolve(reverse_name, 'PTR')
            
            for ptr in ptr_records:
                hostname = str(ptr).rstrip('.')
                if hostname == expected_hostname:
                    logger.info(f"Reverse DNS verified: {ip_address} -> {hostname}")
                    return True
            
            logger.warning(f"Reverse DNS mismatch for {ip_address}")
            return False
            
        except Exception as e:
            logger.error(f"Error verifying reverse DNS: {e}")
            return False
    
    @staticmethod
    async def get_mx_records(domain: str) -> List[str]:
        """Get MX records for domain"""
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            return [str(mx.exchange).rstrip('.') for mx in sorted(mx_records, key=lambda x: x.preference)]
        except Exception as e:
            logger.error(f"Error getting MX records: {e}")
            return []
    
    @staticmethod
    async def verify_spf(domain: str, ip_address: str) -> bool:
        """Verify SPF record"""
        try:
            txt_records = dns.resolver.resolve(domain, 'TXT')
            for record in txt_records:
                record_text = str(record).strip('"')
                if record_text.startswith('v=spf1'):
                    # Basic SPF check (production would use pyspf library)
                    if 'ip4:' + ip_address in record_text or 'a' in record_text or 'mx' in record_text:
                        return True
            return False
        except Exception as e:
            logger.error(f"Error verifying SPF: {e}")
            return False