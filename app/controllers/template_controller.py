from flask import Blueprint, render_template
from flask_login import login_required

template_bp = Blueprint('templates', __name__, url_prefix='/dashboard/templates')

@template_bp.route('/')
@login_required
def index():
    return render_template('dashboard/templates/index.html')
