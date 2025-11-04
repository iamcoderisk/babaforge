from flask import Blueprint, render_template
from flask_login import login_required, current_user

analytics_bp = Blueprint('analytics', __name__, url_prefix='/dashboard/analytics')

@analytics_bp.route('/')
@login_required
def index():
    return render_template('dashboard/analytics.html')
