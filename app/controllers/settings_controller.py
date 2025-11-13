from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from sqlalchemy import text
import secrets
import logging

logger = logging.getLogger(__name__)

settings_bp = Blueprint('settings', __name__, url_prefix='/dashboard/settings')

@settings_bp.route('/')
@login_required
def index():
    """Settings page with API key"""
    try:
        # Get organization with API key
        result = db.session.execute(
            text("SELECT id, name, api_key FROM organizations WHERE id = :org_id"),
            {'org_id': current_user.organization_id}
        )
        org = result.fetchone()
        
        org_data = {
            'id': org[0],
            'name': org[1],
            'api_key': org[2]
        } if org else None
        
        return render_template('dashboard/settings.html', organization=org_data, user=current_user)
    except Exception as e:
        logger.error(f"Settings error: {e}", exc_info=True)
        return render_template('dashboard/settings.html', organization=None, user=current_user)

@settings_bp.route('/api-key/generate', methods=['POST'])
@login_required
def generate_api_key():
    """Generate new API key"""
    try:
        # Generate secure API key
        new_api_key = 'sb_' + secrets.token_urlsafe(32)
        
        # Update organization
        db.session.execute(
            text("UPDATE organizations SET api_key = :api_key WHERE id = :org_id"),
            {'api_key': new_api_key, 'org_id': current_user.organization_id}
        )
        db.session.commit()
        
        flash('New API key generated successfully!', 'success')
        return redirect(url_for('settings.index'))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Generate API key error: {e}", exc_info=True)
        flash('Failed to generate API key', 'error')
        return redirect(url_for('settings.index'))
