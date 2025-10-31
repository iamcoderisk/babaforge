from flask import Blueprint, render_template

web_bp = Blueprint('web', __name__)

@web_bp.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@web_bp.route('/pricing')
def pricing():
    """Pricing page"""
    from app.models.pricing import PricingPlan
    try:
        plans = PricingPlan.query.filter_by(is_active=True).order_by(PricingPlan.display_order).all()
    except Exception as e:
        print(f"Error loading plans: {e}")
        plans = []
    return render_template('pricing.html', plans=plans)

@web_bp.route('/features')
def features():
    """Features page"""
    return render_template('features.html')

@web_bp.route('/docs')
def docs():
    """Documentation page"""
    return render_template('docs.html')

@web_bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')
