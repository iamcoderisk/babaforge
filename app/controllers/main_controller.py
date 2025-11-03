from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
import redis
from app import redis_client

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Homepage"""
    return render_template('index.html')


@main_bp.route('/pricing')
def pricing():
    """Pricing page"""
    return render_template('pricing.html')


@main_bp.route('/features')
def features():
    """Features page"""
    return render_template('features.html')


@main_bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')


@main_bp.route('/docs')
def docs():
    """Documentation page"""
    return render_template('docs.html')


@main_bp.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'sendbaba'}), 200
