from flask import Blueprint, render_template
from flask_login import login_required

warmup_bp = Blueprint('warmup', __name__, url_prefix='/dashboard/warmup')

@warmup_bp.route('/')
@login_required
def index():
    return render_template('dashboard/warmup/index.html')

@warmup_bp.route('/start', methods=['POST'])
@login_required
def start():
    return {'success': True, 'message': 'Warmup started'}
