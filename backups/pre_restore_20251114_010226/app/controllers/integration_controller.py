from flask import Blueprint, render_template
from flask_login import login_required

integration_bp = Blueprint('integrations', __name__, url_prefix='/dashboard/integrations')

@integration_bp.route('/')
@login_required
def index():
    return render_template('dashboard/integrations/index.html')
