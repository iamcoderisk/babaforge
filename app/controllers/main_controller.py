"""
Main Controller
"""
from flask import Blueprint, render_template, jsonify
from app import redis_client
import logging

logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@main_bp.route('/health')
def health():
    """Health check endpoint"""
    try:
        redis_client.ping()
        return jsonify({
            'status': 'healthy',
            'redis': 'connected',
            'service': 'email-system'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503

@main_bp.route('/ready')
def ready():
    """Readiness check"""
    return jsonify({'status': 'ready'})
