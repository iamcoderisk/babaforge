"""
DNS Setup Controller
Handles DKIM/SPF/MX/DMARC configuration
"""
from flask import Blueprint, render_template, jsonify, request
from app.services.dkim.dkim_service import DKIMService
from app.services.dns.dns_validator import DNSValidator
from app.models.email import DNSRecord
from app import db
import logging

logger = logging.getLogger(__name__)

dns_bp = Blueprint('dns', __name__)

@dns_bp.route('/setup')
def setup():
    """DNS setup wizard page"""
    return render_template('dns_setup/wizard.html')

@dns_bp.route('/generate-dkim', methods=['POST'])
def generate_dkim():
    """Generate DKIM keys for domain"""
    try:
        data = request.get_json()
        domain = data.get('domain', 'sendbaba.com')
        selector = data.get('selector', 'mail')
        
        dkim_service = DKIMService(domain, selector)
        keys = dkim_service.generate_keys()
        dns_record = dkim_service.get_dns_record()
        
        # Save to database
        record = DNSRecord(
            domain=domain,
            record_type='DKIM',
            record_name=dns_record['name'],
            record_value=dns_record['value']
        )
        db.session.add(record)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'keys_generated': True,
            'private_key_path': keys['private_key_path'],
            'dns_record': dns_record,
            'instructions': {
                'step1': 'Log in to your DNS provider (GoDaddy, Namecheap, Cloudflare, etc.)',
                'step2': f'Add a TXT record with name: {dns_record["name"]}',
                'step3': f'Set the value to: {dns_record["value"]}',
                'step4': 'Wait 5-10 minutes for DNS propagation',
                'step5': 'Click "Verify" button to confirm'
            }
        })
    
    except Exception as e:
        logger.error(f"Error generating DKIM: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@dns_bp.route('/get-spf-record', methods=['POST'])
def get_spf_record():
    """Generate SPF record"""
    try:
        data = request.get_json()
        domain = data.get('domain', 'sendbaba.com')
        ip_addresses = data.get('ip_addresses', [])
        include_domains = data.get('include_domains', [])
        
        # Build SPF record
        spf_parts = ['v=spf1']
        
        # Add IP addresses
        for ip in ip_addresses:
            if ':' in ip:  # IPv6
                spf_parts.append(f'ip6:{ip}')
            else:  # IPv4
                spf_parts.append(f'ip4:{ip}')
        
        # Add include domains
        for inc_domain in include_domains:
            spf_parts.append(f'include:{inc_domain}')
        
        # Add policy
        spf_parts.append('~all')
        
        spf_value = ' '.join(spf_parts)
        
        # Save to database
        record = DNSRecord(
            domain=domain,
            record_type='SPF',
            record_name=domain,
            record_value=spf_value
        )
        db.session.add(record)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'dns_record': {
                'type': 'TXT',
                'name': domain,
                'value': spf_value,
                'ttl': 3600
            },
            'instructions': {
                'step1': 'Log in to your DNS provider',
                'step2': f'Add a TXT record for: {domain}',
                'step3': f'Set the value to: {spf_value}',
                'step4': 'Save and wait for DNS propagation'
            }
        })
    
    except Exception as e:
        logger.error(f"Error generating SPF: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@dns_bp.route('/get-mx-record', methods=['POST'])
def get_mx_record():
    """Generate MX record"""
    try:
        data = request.get_json()
        domain = data.get('domain', 'sendbaba.com')
        mail_server = data.get('mail_server', f'mail.{domain}')
        priority = data.get('priority', 10)
        
        mx_record = {
            'type': 'MX',
            'name': domain,
            'value': mail_server,
            'priority': priority,
            'ttl': 3600
        }
        
        # Also need A record for mail server
        a_record = {
            'type': 'A',
            'name': mail_server.replace(f'.{domain}', ''),
            'value': 'YOUR_SERVER_IP',
            'ttl': 3600
        }
        
        # Save to database
        record = DNSRecord(
            domain=domain,
            record_type='MX',
            record_name=domain,
            record_value=f'{priority} {mail_server}'
        )
        db.session.add(record)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'mx_record': mx_record,
            'a_record': a_record,
            'instructions': {
                'step1': f'Add MX record: {domain} → {mail_server} (priority {priority})',
                'step2': f'Add A record: {mail_server} → YOUR_SERVER_IP',
                'step3': 'Replace YOUR_SERVER_IP with your actual server IP',
                'note': 'MX records are only needed if you want to RECEIVE emails'
            }
        })
    
    except Exception as e:
        logger.error(f"Error generating MX: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@dns_bp.route('/get-dmarc-record', methods=['POST'])
def get_dmarc_record():
    """Generate DMARC record"""
    try:
        data = request.get_json()
        domain = data.get('domain', 'sendbaba.com')
        policy = data.get('policy', 'quarantine')  # none, quarantine, reject
        rua_email = data.get('rua_email', f'dmarc@{domain}')
        
        dmarc_value = f'v=DMARC1; p={policy}; rua=mailto:{rua_email}; ruf=mailto:{rua_email}; fo=1'
        
        # Save to database
        record = DNSRecord(
            domain=domain,
            record_type='DMARC',
            record_name=f'_dmarc.{domain}',
            record_value=dmarc_value
        )
        db.session.add(record)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'dns_record': {
                'type': 'TXT',
                'name': f'_dmarc.{domain}',
                'value': dmarc_value,
                'ttl': 3600
            },
            'instructions': {
                'step1': f'Add TXT record: _dmarc.{domain}',
                'step2': f'Set value: {dmarc_value}',
                'step3': 'DMARC provides reporting on email authentication',
                'policies': {
                    'none': 'Monitor only (recommended for testing)',
                    'quarantine': 'Send suspicious emails to spam',
                    'reject': 'Reject unauthenticated emails (strictest)'
                }
            }
        })
    
    except Exception as e:
        logger.error(f"Error generating DMARC: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@dns_bp.route('/verify', methods=['POST'])
def verify_dns():
    """Verify DNS records are properly configured"""
    try:
        data = request.get_json()
        domain = data.get('domain', 'sendbaba.com')
        
        validator = DNSValidator(domain)
        results = validator.verify_all()
        
        return jsonify({
            'success': True,
            'domain': domain,
            'results': results,
            'all_valid': all(r['valid'] for r in results.values())
        })
    
    except Exception as e:
        logger.error(f"Error verifying DNS: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@dns_bp.route('/get-ptr-instructions', methods=['POST'])
def get_ptr_instructions():
    """Get instructions for reverse DNS (PTR) setup"""
    try:
        data = request.get_json()
        domain = data.get('domain', 'sendbaba.com')
        
        return jsonify({
            'success': True,
            'instructions': {
                'title': 'Reverse DNS (PTR) Record Setup',
                'important': 'PTR records CANNOT be set by you directly',
                'step1': 'Contact your hosting/IP provider (AWS, Google Cloud, DigitalOcean, etc.)',
                'step2': f'Request PTR record: YOUR_IP → mail.{domain}',
                'step3': 'Provide them your server IP and desired hostname',
                'step4': 'Wait for them to configure it (usually 24-48 hours)',
                'providers': {
                    'AWS': 'Submit request via AWS Support',
                    'Google Cloud': 'Use Cloud Console > VPC > External IP addresses',
                    'DigitalOcean': 'Settings > Networking > Edit reverse DNS',
                    'Azure': 'Azure Portal > Public IP > Configuration'
                },
                'verification': 'Use "host YOUR_IP" command to verify PTR record'
            }
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@dns_bp.route('/records')
def list_records():
    """List all configured DNS records"""
    try:
        records = DNSRecord.query.order_by(DNSRecord.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'records': [{
                'id': r.id,
                'domain': r.domain,
                'type': r.record_type,
                'name': r.record_name,
                'value': r.record_value,
                'validated': r.validated,
                'last_checked': r.last_checked.isoformat() if r.last_checked else None
            } for r in records]
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
