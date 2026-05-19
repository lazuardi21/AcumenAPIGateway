"""
API Gateway — Flask application factory.
"""
import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import config_map
from shared.auth import init_auth
from shared.tracing import init_tracing
from shared.logging_config import setup_logging

logger = logging.getLogger(__name__)


def create_app(config_name=None):
    """Application factory for API Gateway."""

    # Setup structured logging
    setup_logging()

    config_name = config_name or os.environ.get('FLASK_ENV', 'production')
    cfg = config_map.get(config_name, config_map['production'])

    app = Flask(__name__)
    app.url_map.strict_slashes = False
    app.config.from_object(cfg)

    # CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Rate limiting via Redis
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=[app.config.get('RATE_LIMIT_DEFAULT', '100/hour')],
        storage_uri=app.config.get('REDIS_URL', 'memory://'),
    )

    # Initialize auth
    init_auth(
        secret=app.config['SECRET_KEY'],
        algorithm=app.config.get('JWT_ALGORITHM', 'HS256'),
        expiry_hours=app.config.get('JWT_EXPIRY_HOURS', 24),
    )

    # Initialize distributed tracing
    init_tracing(app, service_name='api-gateway')

    # Setup middleware (error handlers, request ID)
    from middleware import setup_middleware
    setup_middleware(app)

    # Register routes
    from routes import gateway_bp, init_routes
    init_routes(app)
    app.register_blueprint(gateway_bp)

    # Health check
    @app.route('/health', methods=['GET'])
    @limiter.exempt
    def health():
        return jsonify({
            'status': 'healthy',
            'service': 'api-gateway',
            'version': '1.0.0',
        })

    # Service discovery endpoint
    @app.route('/api/services', methods=['GET'])
    @limiter.exempt
    def service_info():
        return jsonify({
            'gateway': 'api-gateway',
            'services': {
                'portfolio': app.config['PORTFOLIO_SERVICE_URL'],
                'notification': app.config['NOTIFICATION_SERVICE_URL'],
            },
        })

    logger.info(f"API Gateway started (config={config_name})")
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
