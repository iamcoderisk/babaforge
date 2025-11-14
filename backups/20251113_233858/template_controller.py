from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
import os

template_bp = Blueprint('templates', __name__, url_prefix='/dashboard/templates')

@template_bp.route('/')
@login_required
def index():
    """Browse all templates"""
    return render_template('dashboard/templates/index.html')

@template_bp.route('/editor')
@login_required
def editor():
    """Template editor"""
    return render_template('dashboard/email_builder.html')

@template_bp.route('/api/preview/<template_name>')
def preview_template(template_name):
    """Get template HTML for preview"""
    try:
        template_path = f'email_templates/{template_name}.html'
        
        # Check if template exists
        full_path = os.path.join('app/templates', template_path)
        if not os.path.exists(full_path):
            return jsonify({'error': 'Template not found'}), 404
        
        # Read template file
        with open(full_path, 'r') as f:
            html = f.read()
        
        # Replace variables with sample data
        html = html.replace('{{first_name}}', 'John')
        html = html.replace('{{last_name}}', 'Doe')
        html = html.replace('{{email}}', 'john@example.com')
        html = html.replace('{{company}}', 'Acme Corp')
        html = html.replace('{{company_name}}', 'Acme Corp')
        
        # Newsletter specific
        html = html.replace('{{newsletter_title}}', 'Monthly Update - January 2025')
        html = html.replace('{{newsletter_date}}', 'January 15, 2025')
        html = html.replace('{{article_1_title}}', 'Exciting New Features')
        html = html.replace('{{article_1_excerpt}}', 'We are thrilled to announce...')
        html = html.replace('{{article_1_url}}', '#')
        html = html.replace('{{article_2_title}}', 'Customer Success Story')
        html = html.replace('{{article_2_excerpt}}', 'See how Company X achieved...')
        html = html.replace('{{article_2_url}}', '#')
        
        # Promotional specific
        html = html.replace('{{discount}}', '50')
        html = html.replace('{{offer_title}}', 'Limited Time Offer')
        html = html.replace('{{offer_description}}', 'Get 50% off all products this weekend only!')
        html = html.replace('{{expiry_date}}', 'January 31, 2025')
        html = html.replace('{{promo_code}}', 'SAVE50')
        html = html.replace('{{cta_url}}', '#')
        
        # Event specific
        html = html.replace('{{event_name}}', 'Annual Conference 2025')
        html = html.replace('{{event_date}}', 'March 15, 2025')
        html = html.replace('{{event_time}}', '9:00 AM - 5:00 PM')
        html = html.replace('{{event_location}}', 'Convention Center, Lagos')
        html = html.replace('{{event_description}}', 'Join us for a day of learning and networking!')
        html = html.replace('{{rsvp_url}}', '#')
        html = html.replace('{{rsvp_deadline}}', 'March 1, 2025')
        
        # Receipt specific
        html = html.replace('{{order_number}}', 'ORD-2025-001')
        html = html.replace('{{purchase_date}}', 'January 15, 2025')
        html = html.replace('{{payment_method}}', 'Visa ending in 1234')
        html = html.replace('{{transaction_id}}', 'TXN-ABC123')
        html = html.replace('{{item_name}}', 'Premium Subscription')
        html = html.replace('{{item_price}}', '$99.00')
        html = html.replace('{{subtotal}}', '$99.00')
        html = html.replace('{{tax}}', '$9.90')
        html = html.replace('{{total}}', '$108.90')
        html = html.replace('{{invoice_url}}', '#')
        html = html.replace('{{support_email}}', 'support@sendbaba.com')
        
        # Common replacements
        html = html.replace('{{unsubscribe_url}}', '#')
        html = html.replace('{{action_url}}', '#')
        html = html.replace('{{hero_image}}', 'https://via.placeholder.com/600x300')
        html = html.replace('{{link_url}}', '#')
        
        return html, 200, {'Content-Type': 'text/html'}
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
