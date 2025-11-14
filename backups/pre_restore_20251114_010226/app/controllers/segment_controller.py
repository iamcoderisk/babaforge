from flask import Blueprint, render_template
from flask_login import login_required

segment_bp = Blueprint('segments', __name__, url_prefix='/dashboard/segments')

@segment_bp.route('/')
@login_required
def index():
    return render_template('dashboard/segments/index.html')
