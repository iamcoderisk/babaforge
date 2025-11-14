"""
Comprehensive Email Validation Service
Validates emails with multiple checks
"""
import re
import dns.resolver
import socket
import smtplib
from datetime import datetime
from app import db
from app.models.email_validation import EmailValidation

class EmailValidator:
    """Advanced email validation"""
    
    # Disposable email domains
    DISPOSABLE_DOMAINS = [
        'tempmail.com', 'guerrillamail.com', '10minutemail.com',
        'throwaway.email', 'mailinator.com', 'trashmail.com',
        'yopmail.com', 'fakeinbox.com', 'maildrop.cc'
    ]
    
    # Role-based emails
    ROLE_KEYWORDS = [
        'admin', 'info', 'support', 'sales', 'contact',
        'noreply', 'no-reply', 'help', 'team', 'office'
    ]
    
    def validate_email(self, email, organization_id=None, deep_check=True):
        """
        Comprehensive email validation
        Returns: {
            'valid': bool,
            'score': int (0-100),
            'status': str,
            'checks': dict,
            'reason': str
        }
        """
        result = {
            'valid': False,
            'score': 0,
            'status': 'unknown',
            'checks': {},
            'reason': ''
        }
        
        # Check 1: Syntax validation
        syntax_valid, syntax_reason = self.check_syntax(email)
        result['checks']['syntax'] = syntax_valid
        
        if not syntax_valid:
            result['status'] = 'invalid'
            result['reason'] = syntax_reason
            return result
        
        result['score'] += 20
        
        # Check 2: Disposable email check
        is_disposable = self.check_disposable(email)
        result['checks']['disposable'] = not is_disposable
        
        if is_disposable:
            result['status'] = 'risky'
            result['reason'] = 'Disposable email address'
            result['score'] += 10
            return result
        
        result['score'] += 20
        
        # Check 3: Role-based email check
        is_role = self.check_role_based(email)
        result['checks']['role_based'] = not is_role
        
        if is_role:
            result['status'] = 'risky'
            result['reason'] = 'Role-based email address'
            result['score'] += 20
        else:
            result['score'] += 30
        
        # Check 4: Domain validation
        domain_valid, mx_records = self.check_domain(email)
        result['checks']['domain'] = domain_valid
        
        if not domain_valid:
            result['status'] = 'invalid'
            result['reason'] = 'Invalid domain or no MX records'
            return result
        
        result['score'] += 20
        
        # Check 5: SMTP validation (deep check)
        if deep_check:
            smtp_valid = self.check_smtp(email, mx_records)
            result['checks']['smtp'] = smtp_valid
            
            if smtp_valid:
                result['score'] += 10
            else:
                result['score'] -= 10
                result['status'] = 'risky'
                result['reason'] = 'Mailbox verification failed'
        
        # Determine final status
        if result['score'] >= 80:
            result['valid'] = True
            result['status'] = 'deliverable'
            result['reason'] = 'Email is valid and deliverable'
        elif result['score'] >= 60:
            result['status'] = 'risky'
            result['reason'] = 'Email might be valid but has risks'
        else:
            result['status'] = 'undeliverable'
            result['reason'] = 'Email is likely undeliverable'
        
        # Save validation result
        if organization_id:
            self.save_validation(email, organization_id, result)
        
        return result
    
    def check_syntax(self, email):
        """Check email syntax"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not email or not isinstance(email, str):
            return False, "Email is required"
        
        if len(email) > 254:
            return False, "Email too long"
        
        if not re.match(pattern, email):
            return False, "Invalid email format"
        
        # Check for consecutive dots
        if '..' in email:
            return False, "Invalid format (consecutive dots)"
        
        # Check local part
        local, domain = email.rsplit('@', 1)
        
        if len(local) > 64:
            return False, "Local part too long"
        
        if local.startswith('.') or local.endswith('.'):
            return False, "Invalid local part"
        
        return True, "Syntax valid"
    
    def check_disposable(self, email):
        """Check if disposable email"""
        domain = email.split('@')[1].lower()
        return domain in self.DISPOSABLE_DOMAINS
    
    def check_role_based(self, email):
        """Check if role-based email"""
        local = email.split('@')[0].lower()
        return any(keyword in local for keyword in self.ROLE_KEYWORDS)
    
    def check_domain(self, email):
        """Check domain and MX records"""
        try:
            domain = email.split('@')[1]
            
            # Get MX records
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_hosts = [str(r.exchange).rstrip('.') for r in mx_records]
            
            if not mx_hosts:
                return False, []
            
            return True, mx_hosts
            
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout):
            return False, []
        except Exception as e:
            print(f"Domain check error: {e}")
            return False, []
    
    def check_smtp(self, email, mx_hosts):
        """SMTP validation (checks if mailbox exists)"""
        if not mx_hosts:
            return False
        
        # Try first MX host
        try:
            mx_host = mx_hosts[0]
            
            # Connect to SMTP server
            with smtplib.SMTP(timeout=10) as smtp:
                smtp.connect(mx_host)
                smtp.helo('sendbaba.com')
                smtp.mail('verify@sendbaba.com')
                
                # Try to verify recipient
                code, message = smtp.rcpt(email)
                
                # 250 = accepted, 251 = user not local (but we'll accept)
                return code in [250, 251]
                
        except Exception as e:
            # SMTP check failed, but don't fail the email
            # (many servers block SMTP verification)
            print(f"SMTP check error: {e}")
            return None  # Unknown
    
    def bulk_validate(self, emails, organization_id):
        """Validate multiple emails"""
        results = []
        
        for email in emails:
            result = self.validate_email(email, organization_id, deep_check=False)
            results.append({
                'email': email,
                **result
            })
        
        return results
    
    def save_validation(self, email, organization_id, result):
        """Save validation result to database"""
        validation = EmailValidation(
            organization_id=organization_id,
            email=email,
            status=result['status'],
            score=result['score'],
            checks=result['checks']
        )
        
        db.session.add(validation)
        db.session.commit()
        
        return validation
    
    def get_cached_validation(self, email, organization_id, max_age_days=30):
        """Get cached validation result"""
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
        
        validation = EmailValidation.query.filter(
            EmailValidation.email == email,
            EmailValidation.organization_id == organization_id,
            EmailValidation.validated_at >= cutoff_date
        ).first()
        
        if validation:
            return {
                'valid': validation.status == 'deliverable',
                'score': validation.score,
                'status': validation.status,
                'checks': validation.checks,
                'cached': True
            }
        
        return None

# Initialize validator
email_validator = EmailValidator()
