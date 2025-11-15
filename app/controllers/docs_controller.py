from flask import Blueprint, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
import os

docs_bp = Blueprint('api_docs', __name__)

# Swagger UI configuration for /api/docs
SWAGGER_URL = '/api/docs'
API_URL = '/api/openapi.yaml'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "SendBaba API Documentation",
        'defaultModelsExpandDepth': -1,
        'displayRequestDuration': True,
        'filter': True,
        'showExtensions': True,
        'tryItOutEnabled': True,
        'syntaxHighlight.theme': 'monokai'
    }
)

@docs_bp.route('/api/openapi.yaml')
def serve_openapi_spec():
    """Serve OpenAPI specification"""
    docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'docs', 'api')
    return send_from_directory(docs_dir, 'openapi.yaml')
