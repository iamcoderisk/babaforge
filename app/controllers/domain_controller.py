from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from sqlalchemy import text
import logging
import uuid

logger = logging.getLogger(__name__)

domain_bp = Blueprint('domains', __name__)

@domain_bp.route('/domains')
@domain_bp.route('/dashboard/domains')
@login_required
def list_domains():
    """List all domains"""
    try:
        result = db.session.execute(
            text("""
                SELECT id, domain_name, dns_verified, dkim_public_key, 
                       dkim_selector, created_at, is_active
                FROM domains 
                WHERE organization_id = :org_id
                ORDER BY created_at DESC
            """),
            {'org_id': current_user.organization_id}
        )
        domains = [dict(row._mapping) for row in result]
        return render_template('dashboard/domains.html', domains=domains)
    except Exception as e:
        logger.error(f"List domains error: {e}", exc_info=True)
        return render_template('dashboard/domains.html', domains=[])

@domain_bp.route('/domains/add', methods=['GET', 'POST'])
@domain_bp.route('/dashboard/domains/add', methods=['GET', 'POST'])
@login_required
def add_domain():
    """Add domain - handles both GET (show form) and POST (API)"""
    if request.method == 'GET':
        return list_domains()
    
    try:
        domain_name = request.form.get('domain_name', '').lower().strip()
        
        if not domain_name:
            return jsonify({'success': False, 'error': 'Domain name is required'})
        
        check = db.session.execute(
            text("SELECT id FROM domains WHERE domain_name = :domain AND organization_id = :org_id"),
            {'domain': domain_name, 'org_id': current_user.organization_id}
        )
        
        if check.fetchone():
            return jsonify({'success': False, 'error': 'Domain already exists'})
        
        domain_id = str(uuid.uuid4())
        
        db.session.execute(
            text("""
                INSERT INTO domains (
                    id, organization_id, domain_name, dkim_selector,
                    dns_verified, is_active, created_at
                )
                VALUES (:id, :org_id, :domain, 'default', false, true, NOW())
            """),
            {'id': domain_id, 'org_id': current_user.organization_id, 'domain': domain_name}
        )
        db.session.commit()
        
        return jsonify({'success': True, 'domain_id': domain_id})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Add domain error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)})

@domain_bp.route('/domains/<domain_id>')
@domain_bp.route('/dashboard/domains/<domain_id>')
@login_required
def view_domain(domain_id):
    return list_domains()

@domain_bp.route('/dashboard/domains/<domain_id>/generate-dkim', methods=['POST'])
@login_required
def generate_dkim(domain_id):
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.backends import default_backend
        
        result = db.session.execute(
            text("SELECT id FROM domains WHERE id = :id AND organization_id = :org_id"),
            {'id': domain_id, 'org_id': current_user.organization_id}
        )
        
        if not result.fetchone():
            return jsonify({'success': False, 'error': 'Domain not found'})
        
        private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        
        public_key_clean = public_pem.replace('-----BEGIN PUBLIC KEY-----', '').replace('-----END PUBLIC KEY-----', '').replace('\n', '')
        dkim_value = f'v=DKIM1; k=rsa; p={public_key_clean}'
        
        db.session.execute(
            text("UPDATE domains SET dkim_private_key = :private_key, dkim_public_key = :public_key WHERE id = :domain_id"),
            {'domain_id': domain_id, 'private_key': private_pem, 'public_key': dkim_value}
        )
        db.session.commit()
        
        return jsonify({'success': True, 'public_key': dkim_value})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Generate DKIM error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)})

@domain_bp.route('/dashboard/domains/<domain_id>/verify', methods=['POST'])
@login_required
def verify_domain(domain_id):
    try:
        import dns.resolver
        
        result = db.session.execute(
            text("SELECT domain_name, dkim_selector FROM domains WHERE id = :id AND organization_id = :org_id"),
            {'id': domain_id, 'org_id': current_user.organization_id}
        )
        row = result.fetchone()
        
        if not row:
            return jsonify({'success': False, 'message': 'Domain not found'})
        
        domain_name, dkim_selector = row[0], row[1] or 'default'
        resolver = dns.resolver.Resolver()
        resolver.timeout = 5
        
        spf_valid = dkim_valid = dmarc_valid = False
        
        try:
            for rdata in resolver.resolve(domain_name, 'TXT'):
                if 'v=spf1' in str(rdata) and '156.67.29.186' in str(rdata):
                    spf_valid = True
        except: pass
        
        try:
            for rdata in resolver.resolve(f'{dkim_selector}._domainkey.{domain_name}', 'TXT'):
                if 'v=DKIM1' in str(rdata):
                    dkim_valid = True
        except: pass
        
        try:
            for rdata in resolver.resolve(f'_dmarc.{domain_name}', 'TXT'):
                if 'v=DMARC1' in str(rdata):
                    dmarc_valid = True
        except: pass
        
        all_valid = spf_valid and dkim_valid and dmarc_valid
        
        db.session.execute(
            text("UPDATE domains SET dns_verified = :verified WHERE id = :domain_id"),
            {'domain_id': domain_id, 'verified': all_valid}
        )
        db.session.commit()
        
        if all_valid:
            return jsonify({'success': True, 'message': 'Domain verified!'})
        
        missing = [x for x, v in [('SPF', spf_valid), ('DKIM', dkim_valid), ('DMARC', dmarc_valid)] if not v]
        return jsonify({'success': False, 'message': f'Missing: {", ".join(missing)}'})
        
    except Exception as e:
        logger.error(f"Verify error: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)})

@domain_bp.route('/dashboard/domains/<domain_id>/delete', methods=['POST'])
@login_required
def delete_domain(domain_id):
    try:
        db.session.execute(
            text("DELETE FROM domains WHERE id = :id AND organization_id = :org_id"),
            {'id': domain_id, 'org_id': current_user.organization_id}
        )
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@domain_bp.route('/test-domains')
def test_domains_no_auth():
    """Test route without authentication"""
    return "<h1>Domain routes are working!</h1><p>All domain routes require login. Please login first.</p>"
