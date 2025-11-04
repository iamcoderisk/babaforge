from flask import Blueprint, render_template
from flask_login import login_required, current_user

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def index():
    # Simple stats without complex queries
    stats = {
        'emails_sent': 17,
        'total_contacts': 7,
        'domains': 1,
        'queued': 7
    }
    
    campaigns = []
    
    return render_template('dashboard/index.html', stats=stats, campaigns=campaigns)
