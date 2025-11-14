from flask import Blueprint, render_template
from flask_login import login_required

form_bp = Blueprint('forms', __name__, url_prefix='/dashboard/forms')

@form_bp.route('/')
@login_required
def index():
    return render_template('dashboard/forms/index.html')
