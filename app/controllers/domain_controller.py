from flask import Blueprint, request, jsonify
from app import db
from app.models.domain import Domain
from app.models.organization import Organization
from app.middleware.auth import require_api_key
from datetime import datetime
import dns.resolver
import logging

logger = logging.getLogger(__name__)

domain_bp = Blueprint('domains', __name__)

@domain_bp.route('/register', methods=['POST'])
def register_organization():
    """Register new organization and get API key"""
    try:
        data = request.get_json()
        
        # Validate input
        if not data.get('organization_name') or not data.get('email'):
            return jsonify({
                'success': False,
                'error': 'organization_name and email are required'
            }), 400
        
        # Check if email already exists
        from app.models.user import User
        existing = User.query.filter_by(email=data['email']).first()
        if existing:
            return jsonify({
                'success': False,
                'error': 'Email already registered'
            }), 400
        
        # Create organization
        org = Organization(name=data['organization_name'])
        db.session.add(org)
        db.session.flush()
        
        # Create user
        user = User(
            email=data['email'],
            password=data.get('password', 'changeme123'),
            first_name=data.get('first_name'),
            last_name=data.get('last_name')
        )
        user.organization_id = org.id
        user.is_verified = True
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'organization_id': org.id,
            'api_key': org.api_key,
            'message': '🎉 Registration successful! Save your API key securely.',
            'next_steps': [
                '1. Add your domain: POST /api/v1/domain/add',
                '2. Configure DNS records',
                '3. Verify domain: POST /api/v1/domain/verify/{domain_id}',
                '4. Start sending emails!'
            ]
        }), 201
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Registration failed. Please try again.'
        }), 500

@domain_bp.route('/domain/add', methods=['POST'])
@require_api_key
def add_domain():
    """Add domain to organization"""
    try:
        data = request.get_json()
        domain_name = data.get('domain', '').lower().strip()
        
        if not domain_name:
            return jsonify({
                'success': False,
                'error': 'domain field is required'
            }), 400
        
        # Validate domain format
        if not '.' in domain_name or ' ' in domain_name:
            return jsonify({
                'success': False,
                'error': 'Invalid domain format'
            }), 400
        
        # Check if domain already exists
        existing = Domain.query.filter_by(domain_name=domain_name).first()
        if existing:
            return jsonify({
                'success': False,
                'error': f'Domain {domain_name} is already registered'
            }), 400
        
        # Create domain
        domain = Domain(
            organization_id=request.organization.id,
            domain_name=domain_name
        )
        
        db.session.add(domain)
        db.session.commit()
        
        dns_records = domain.get_dns_records()
        
        return jsonify({
            'success': True,
            'domain_id': domain.id,
            'domain': domain.domain_name,
            'dns_records': dns_records,
            'instructions': {
                'step_1': 'Add the DNS records above to your domain',
                'step_2': 'Wait 5-10 minutes for DNS propagation',
                'step_3': f'Verify: POST /api/v1/domain/verify/{domain.id}'
            },
            'message': '📝 Domain added! Please configure DNS records to verify ownership.'
        }), 201
        
    except Exception as e:
        logger.error(f"Add domain error: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to add domain'
        }), 500

@domain_bp.route('/domain/verify/<domain_id>', methods=['POST'])
@require_api_key
def verify_domain(domain_id):
    """Verify domain DNS configuration"""
    try:
        domain = Domain.query.filter_by(
            id=domain_id,
            organization_id=request.organization.id
        ).first()
        
        if not domain:
            return jsonify({
                'success': False,
                'error': 'Domain not found'
            }), 404
        
        if domain.dns_verified:
            return jsonify({
                'success': True,
                'domain': domain.domain_name,
                'status': 'already_verified',
                'verified_at': domain.verified_at.isoformat(),
                'message': '✅ Domain is already verified!'
            })
        
        # Verify DNS records
        results = {}
        all_passed = True
        
        # 1. Check verification TXT record
        try:
            txt_records = dns.resolver.resolve(f'_sendbaba-verify.{domain.domain_name}', 'TXT')
            verification_txt = ''.join([str(rdata).strip('"') for rdata in txt_records])
            
            if domain.verification_token in verification_txt:
                results['verification'] = {'status': 'passed', 'message': '✅ Verification record found'}
            else:
                results['verification'] = {'status': 'failed', 'message': '❌ Verification token mismatch'}
                all_passed = False
        except dns.resolver.NXDOMAIN:
            results['verification'] = {'status': 'failed', 'message': '❌ Verification record not found'}
            all_passed = False
        except Exception as e:
            results['verification'] = {'status': 'failed', 'message': f'❌ DNS lookup failed: {str(e)}'}
            all_passed = False
        
        # 2. Check SPF record
        try:
            txt_records = dns.resolver.resolve(domain.domain_name, 'TXT')
            spf_found = any('v=spf1' in str(rdata) and 'sendbaba.com' in str(rdata) for rdata in txt_records)
            
            if spf_found:
                results['spf'] = {'status': 'passed', 'message': '✅ SPF record configured correctly'}
            else:
                results['spf'] = {'status': 'failed', 'message': '❌ SPF record missing or incorrect'}
                all_passed = False
        except Exception as e:
            results['spf'] = {'status': 'failed', 'message': f'❌ SPF check failed: {str(e)}'}
            all_passed = False
        
        # 3. Check DKIM record
        try:
            dkim_records = dns.resolver.resolve(f'{domain.dkim_selector}._domainkey.{domain.domain_name}', 'TXT')
            dkim_txt = ''.join([str(rdata).strip('"') for rdata in dkim_records])
            
            if 'v=DKIM1' in dkim_txt and 'p=' in dkim_txt:
                results['dkim'] = {'status': 'passed', 'message': '✅ DKIM record found'}
            else:
                results['dkim'] = {'status': 'failed', 'message': '❌ DKIM record invalid'}
                all_passed = False
        except Exception as e:
            results['dkim'] = {'status': 'failed', 'message': f'❌ DKIM check failed: {str(e)}'}
            all_passed = False
        
        # 4. Check DMARC record (optional)
        try:
            dmarc_records = dns.resolver.resolve(f'_dmarc.{domain.domain_name}', 'TXT')
            dmarc_found = any('v=DMARC1' in str(rdata) for rdata in dmarc_records)
            
            if dmarc_found:
                results['dmarc'] = {'status': 'passed', 'message': '✅ DMARC record found'}
            else:
                results['dmarc'] = {'status': 'warning', 'message': '⚠️ DMARC record recommended'}
        except:
            results['dmarc'] = {'status': 'warning', 'message': '⚠️ DMARC record not found'}
        
        # Update domain status
        if all_passed:
            domain.dns_verified = True
            domain.verified_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'success': True,
                'domain': domain.domain_name,
                'status': 'verified',
                'verified_at': domain.verified_at.isoformat(),
                'dns_checks': results,
                'message': '🎉 Domain verified successfully! You can now send emails.'
            })
        else:
            return jsonify({
                'success': False,
                'domain': domain.domain_name,
                'status': 'pending',
                'dns_checks': results,
                'message': '❌ Domain verification failed. Please check DNS records.',
                'help': 'DNS changes can take 5-60 minutes to propagate.'
            }), 400
            
    except Exception as e:
        logger.error(f"Verify domain error: {e}")
        return jsonify({
            'success': False,
            'error': 'Verification failed. Please try again.'
        }), 500

@domain_bp.route('/domains', methods=['GET'])
@require_api_key
def list_domains():
    """List all domains for organization"""
    try:
        domains = Domain.query.filter_by(
            organization_id=request.organization.id
        ).order_by(Domain.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'organization': request.organization.name,
            'domains': [{
                'id': d.id,
                'domain': d.domain_name,
                'verified': d.dns_verified,
                'active': d.is_active,
                'created_at': d.created_at.isoformat(),
                'verified_at': d.verified_at.isoformat() if d.verified_at else None
            } for d in domains],
            'total': len(domains)
        })
        
    except Exception as e:
        logger.error(f"List domains error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to list domains'
        }), 500

@domain_bp.route('/domain/<domain_id>', methods=['GET'])
@require_api_key
def get_domain_details(domain_id):
    """Get detailed domain information including DNS records"""
    try:
        domain = Domain.query.filter_by(
            id=domain_id,
            organization_id=request.organization.id
        ).first()
        
        if not domain:
            return jsonify({
                'success': False,
                'error': 'Domain not found'
            }), 404
        
        return jsonify({
            'success': True,
            'domain': {
                'id': domain.id,
                'name': domain.domain_name,
                'verified': domain.dns_verified,
                'active': domain.is_active,
                'created_at': domain.created_at.isoformat(),
                'verified_at': domain.verified_at.isoformat() if domain.verified_at else None,
                'dns_records': domain.get_dns_records()
            }
        })
        
    except Exception as e:
        logger.error(f"Get domain error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get domain details'
        }), 500

@domain_bp.route('/domain/<domain_id>', methods=['DELETE'])
@require_api_key
def delete_domain(domain_id):
    """Delete a domain"""
    try:
        domain = Domain.query.filter_by(
            id=domain_id,
            organization_id=request.organization.id
        ).first()
        
        if not domain:
            return jsonify({
                'success': False,
                'error': 'Domain not found'
            }), 404
        
        domain_name = domain.domain_name
        db.session.delete(domain)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Domain {domain_name} deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Delete domain error: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to delete domain'
        }), 500
