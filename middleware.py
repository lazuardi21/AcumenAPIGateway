"""
API Gateway — Middleware components (auth validation, error handling).
"""
import logging
import uuid
from flask import request, g, jsonify
from shared.auth import decode_token

logger = logging.getLogger(__name__)


def setup_middleware(app):
    """Register all middleware with the Flask app."""

    @app.before_request
    def inject_request_id():
        """Inject a unique request ID for tracing."""
        g.request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))

    @app.after_request
    def add_response_headers(response):
        """Add standard response headers."""
        response.headers['X-Request-ID'] = getattr(g, 'request_id', '')
        response.headers['X-Gateway'] = 'acumen-api-gateway'
        return response

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({'error': 'Bad request', 'message': str(e)}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Not found', 'message': 'The requested endpoint does not exist'}), 404

    @app.errorhandler(429)
    def rate_limited(e):
        return jsonify({'error': 'Rate limit exceeded', 'message': str(e)}), 429

    @app.errorhandler(500)
    def internal_error(e):
        logger.error(f"Internal gateway error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

    @app.errorhandler(502)
    def bad_gateway(e):
        return jsonify({'error': 'Service unavailable', 'message': 'Downstream service is not responding'}), 502


def validate_token_and_get_user():
    """Validate JWT token from the Authorization header.

    Returns:
        tuple: (user_dict, error_response)
        If valid: (user_dict, None)
        If invalid: (None, (error_json, status_code))
    """
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None, (jsonify({'error': 'Authentication required'}), 401)

    token = auth_header.split(' ', 1)[1]
    try:
        payload = decode_token(token)
        return payload, None
    except Exception as e:
        return None, (jsonify({'error': 'Invalid or expired token', 'detail': str(e)}), 401)
