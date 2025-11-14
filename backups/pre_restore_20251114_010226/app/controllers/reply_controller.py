from flask import Blueprint, render_template
from flask_login import login_required

reply_bp = Blueprint('replies', __name__, url_prefix='/dashboard/replies')

@reply_bp.route('/')
@login_required
def index():
    # Don't query database - just show the page
    return render_template('dashboard/replies/index.html')
