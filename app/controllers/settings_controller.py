from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db

settings_bp = Blueprint('settings', __name__, url_prefix='/dashboard/settings')

@settings_bp.route('/')
@login_required
def index():
    org = current_user.organization
    user = current_user
    return render_template('dashboard/settings.html', organization=org, user=user)
