# ============= app/controllers/domain_controller.py =============
"""
Domain Controller
"""
from flask import Blueprint, request, jsonify, current_app

from app.models.database import Domain
from app.models.schemas import DomainCreate
from app.services.dkim_service import DKIMService
from app.middleware.auth import require_api_key
from app.utils.logger import get_logger

logger = get_logger(__name__)
bp = Blueprint('domains', __name__)

@bp.route('/', methods=['POST'])
@require_api_key
def create_domain(org_id: int):
    """Create new domain"""
    try:
        domain_data = DomainCreate(**request.json)
        
        db = current_app.session()
        
        # Get DKIM records
        dkim_service = DKIMService()
        dkim_record = dkim_service.get_dns_record()
        
        # Create domain
        domain = Domain(
            org_id=org_id,
            domain=domain_data.domain,
            dkim_selector='default',
            dkim_public_key=dkim_record,
            spf_record=f"v=spf1 mx a:{domain_data.domain} ~all",
            dmarc_record=f"v=DMARC1; p=quarantine; rua=mailto:dmarc@{domain_data.domain}",
            status='pending'
        )
        
        db.add(domain)
        db.commit()
        db.refresh(domain)
        
        return jsonify({
            'id': domain.id,
            'domain': domain.domain,
            'dns_records': {
                'dkim': {
                    'name': f'{domain.dkim_selector}._domainkey.{domain.domain}',
                    'type': 'TXT',
                    'value': domain.dkim_public_key
                },
                'spf': {
                    'name': domain.domain,
                    'type': 'TXT',
                    'value': domain.spf_record
                },
                'dmarc': {
                    'name': f'_dmarc.{domain.domain}',
                    'type': 'TXT',
                    'value': domain.dmarc_record
                }
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating domain: {e}")
        return jsonify({'error': str(e)}), 500