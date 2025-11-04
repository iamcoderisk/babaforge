from flask import Blueprint, render_template
from flask_login import login_required

validatio_bp = Blueprint('validation', __name__, url_prefix='/dashboard/validation')

@validatio_bp.route('/')
@login_required
def index():
    return render_template('dashboard/validation/index.html')
