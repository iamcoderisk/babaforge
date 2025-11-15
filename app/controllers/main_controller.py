from flask import Blueprint, render_template, request, flash, redirect, url_for

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@main_bp.route('/pricing')
def pricing():
    """Pricing page"""
    return render_template('pricing.html')

@main_bp.route('/features')
def features():
    """Features page"""
    return render_template('features.html')

@main_bp.route('/docs')
def docs():
    """API Documentation page"""
    return render_template('docs.html')

@main_bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@main_bp.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')

@main_bp.route('/contact/submit', methods=['POST'])
def contact_submit():
    """Handle contact form submission"""
    name = request.form.get('name')
    email = request.form.get('email')
    subject = request.form.get('subject')
    message = request.form.get('message')
    
    # TODO: Send email notification or save to database
    flash('Thank you for your message! We\'ll get back to you soon.', 'success')
    return redirect(url_for('main.contact'))

@main_bp.route('/terms')
def terms():
    """Terms of Service"""
    # Create a simple terms page if it doesn't exist
    return render_template('terms.html')

@main_bp.route('/privacy')
def privacy():
    """Privacy Policy"""
    return render_template('privacy.html')

@main_bp.route('/security')
def security():
    """Security page"""
    return render_template('security.html')

@main_bp.route('/cookies')
def cookies():
    """Cookie Policy"""
    return render_template('cookies.html')

@main_bp.route('/careers')
def careers():
    """Careers page"""
    return render_template('careers.html')
