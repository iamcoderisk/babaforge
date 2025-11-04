from flask import Blueprint, render_template, redirect
from flask_login import current_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect('/dashboard/')
    return render_template('index.html')

@main_bp.route('/features')
def features():
    return render_template('features.html')

@main_bp.route('/pricing')
def pricing():
    return render_template('pricing.html')

@main_bp.route('/docs')
def docs():
    return render_template('docs.html')

@main_bp.route('/api')
def api_docs():
    return render_template('api.html')

@main_bp.route('/health')
def health():
    return {'status': 'ok'}, 200
