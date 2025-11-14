from flask import Blueprint, render_template
from flask_login import login_required

workflow_bp = Blueprint('workflows', __name__, url_prefix='/dashboard/workflows')

@workflow_bp.route('/')
@login_required
def index():
    return render_template('dashboard/workflows/index.html')
