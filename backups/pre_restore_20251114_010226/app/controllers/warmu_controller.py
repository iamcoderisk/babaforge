from flask import Blueprint, render_template
from flask_login import login_required

warmu_bp = Blueprint('warmup', __name__, url_prefix='/dashboard/warmup')

@warmu_bp.route('/')
@login_required
def index():
    return render_template('dashboard/warmup/index.html')
