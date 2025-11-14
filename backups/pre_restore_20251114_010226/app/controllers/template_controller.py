from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
import os
import logging

logger = logging.getLogger(__name__)

template_bp = Blueprint('templates', __name__, url_prefix='/dashboard/templates')

@template_bp.route('/')
@login_required
def index():
    """Browse all templates"""
    logger.info(f"User {current_user.email} accessing templates")
    return render_template('dashboard/templates/index.html')

@template_bp.route('/editor')
@login_required
def editor():
    """Template editor page"""
    return render_template('dashboard/email_builder.html')

@template_bp.route('/api/list')
@login_required
def list_templates():
    """Get list of all available templates"""
    try:
        templates = [
            {'name': 'welcome', 'category': 'business', 'title': 'Welcome Email'},
            {'name': 'newsletter', 'category': 'newsletter', 'title': 'Newsletter'},
            {'name': 'promotional', 'category': 'promotional', 'title': 'Promotional'},
            {'name': 'event', 'category': 'business', 'title': 'Event Invitation'},
            {'name': 'receipt', 'category': 'transactional', 'title': 'Receipt'},
        ]
        
        return jsonify({'success': True, 'templates': templates})
        
    except Exception as e:
        logger.error(f"List templates error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@template_bp.route('/api/preview/<template_name>')
def preview_template(template_name):
    """Get template HTML with sample data"""
    try:
        # Template path
        template_path = f'email_templates/{template_name}.html'
        full_path = os.path.join('app/templates', template_path)
        
        logger.info(f"Loading template: {full_path}")
        
        if not os.path.exists(full_path):
            logger.error(f"Template not found: {full_path}")
            return jsonify({'error': 'Template not found'}), 404
        
        # Read template
        with open(full_path, 'r', encoding='utf-8') as f:
            html = f.read()
        
        # Sample data for preview
        sample_data = {
            # Common
            '{{first_name}}': 'John',
            '{{last_name}}': 'Doe',
            '{{email}}': 'john@example.com',
            '{{company}}': 'Acme Corp',
            '{{company_name}}': 'Acme Corp',
            
            # Newsletter
            '{{newsletter_title}}': 'Monthly Update - January 2025',
            '{{newsletter_date}}': 'January 15, 2025',
            '{{article_1_title}}': 'Exciting New Features',
            '{{article_1_excerpt}}': 'We\'re thrilled to announce our latest features...',
            '{{article_1_url}}': '#',
            '{{article_2_title}}': 'Customer Success Story',
            '{{article_2_excerpt}}': 'See how Company X achieved amazing results...',
            '{{article_2_url}}': '#',
            '{{hero_image}}': 'https://via.placeholder.com/600x300/8B5CF6/FFFFFF?text=Newsletter',
            
            # Promotional
            '{{discount}}': '50',
            '{{offer_title}}': 'Limited Time Offer - 50% Off!',
            '{{offer_description}}': 'Get 50% off all products this weekend only! Don\'t miss out on this amazing deal.',
            '{{expiry_date}}': 'January 31, 2025',
            '{{promo_code}}': 'SAVE50',
            '{{cta_url}}': '#',
            
            # Event
            '{{event_name}}': 'Annual Tech Conference 2025',
            '{{event_date}}': 'March 15, 2025',
            '{{event_time}}': '9:00 AM - 5:00 PM',
            '{{event_location}}': 'Convention Center, Lagos',
            '{{event_description}}': 'Join us for a day of learning, networking, and innovation!',
            '{{rsvp_url}}': '#',
            '{{rsvp_deadline}}': 'March 1, 2025',
            
            # Receipt
            '{{order_number}}': 'ORD-2025-12345',
            '{{purchase_date}}': 'January 15, 2025',
            '{{payment_method}}': 'Visa ending in 1234',
            '{{transaction_id}}': 'TXN-ABC123XYZ',
            '{{item_name}}': 'Premium Subscription',
            '{{item_price}}': '$99.00',
            '{{subtotal}}': '$99.00',
            '{{tax}}': '$9.90',
            '{{total}}': '$108.90',
            '{{invoice_url}}': '#',
            '{{support_email}}': 'support@sendbaba.com',
            
            # URLs
            '{{unsubscribe_url}}': '#',
            '{{action_url}}': '#',
            '{{link_url}}': '#',
            '{{facebook_url}}': '#',
            '{{twitter_url}}': '#',
            '{{linkedin_url}}': '#',
        }
        
        # Replace all variables
        for variable, value in sample_data.items():
            html = html.replace(variable, value)
        
        logger.info(f"Template {template_name} loaded successfully")
        
        return html, 200, {'Content-Type': 'text/html; charset=utf-8'}
        
    except Exception as e:
        logger.error(f"Preview template error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
