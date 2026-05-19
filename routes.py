"""
API Gateway — Route definitions.

Proxies requests to downstream services (Portfolio, Notification) with
JWT validation and user context injection.
"""
import logging
import requests
from flask import Blueprint, request, jsonify, g, Response
from middleware import validate_token_and_get_user

logger = logging.getLogger(__name__)

gateway_bp = Blueprint('gateway', __name__)

# Service URLs are injected via app config
_portfolio_url = None
_notification_url = None


def init_routes(app):
    """Initialize routes with service URLs from app config."""
    global _portfolio_url, _notification_url
    _portfolio_url = app.config['PORTFOLIO_SERVICE_URL']
    _notification_url = app.config['NOTIFICATION_SERVICE_URL']


def _proxy_request(service_url, path, user=None, timeout=30):
    """Forward the current request to a downstream service.

    Injects user context headers (X-User-ID, X-Username, X-Email) for internal auth.
    """
    url = f"{service_url}{path}"

    # Build headers — pass through original headers plus internal auth
    headers = {
        key: value for key, value in request.headers
        if key.lower() not in ('host', 'content-length')
    }
    headers['X-Request-ID'] = getattr(g, 'request_id', '')
    headers['X-Forwarded-By'] = 'api-gateway'

    if user:
        headers['X-User-ID'] = str(user['user_id'])
        headers['X-Username'] = user.get('username', '')
        headers['X-Email'] = user.get('email', '')

    try:
        resp = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            data=request.get_data(),
            params=request.args,
            timeout=timeout,
            allow_redirects=False,
        )

        # Build response
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        response_headers = {
            k: v for k, v in resp.headers.items() if k.lower() not in excluded_headers
        }

        return Response(resp.content, resp.status_code, response_headers)

    except requests.exceptions.ConnectionError:
        logger.error(f"Service unavailable: {url}")
        return jsonify({'error': 'Service unavailable'}), 502

    except requests.exceptions.Timeout:
        logger.error(f"Service timeout: {url}")
        return jsonify({'error': 'Service timeout'}), 504

    except Exception as e:
        logger.error(f"Proxy error: {e}", exc_info=True)
        return jsonify({'error': 'Gateway error', 'detail': str(e)}), 500


# =============================================================================
# Public Routes (no auth required)
# =============================================================================

@gateway_bp.route('/api/auth/register', methods=['POST'])
def register():
    """Proxy registration to Portfolio Service."""
    return _proxy_request(_portfolio_url, '/api/auth/register')


@gateway_bp.route('/api/auth/login', methods=['POST'])
def login():
    """Proxy login to Portfolio Service."""
    return _proxy_request(_portfolio_url, '/api/auth/login')


# =============================================================================
# Portfolio Routes (auth required)
# =============================================================================

@gateway_bp.route('/api/portfolios', methods=['GET', 'POST'])
def portfolios():
    """Proxy portfolio list/create."""
    user, error = validate_token_and_get_user()
    if error:
        return error
    return _proxy_request(_portfolio_url, '/api/portfolios', user=user)


@gateway_bp.route('/api/portfolios/<int:portfolio_id>', methods=['GET', 'PUT', 'DELETE'])
def portfolio_detail(portfolio_id):
    """Proxy portfolio detail/update/delete."""
    user, error = validate_token_and_get_user()
    if error:
        return error
    return _proxy_request(_portfolio_url, f'/api/portfolios/{portfolio_id}', user=user)


@gateway_bp.route('/api/portfolios/<int:portfolio_id>/holdings', methods=['GET'])
def portfolio_holdings(portfolio_id):
    """Proxy portfolio holdings."""
    user, error = validate_token_and_get_user()
    if error:
        return error
    return _proxy_request(_portfolio_url, f'/api/portfolios/{portfolio_id}/holdings', user=user)


@gateway_bp.route('/api/portfolios/<int:portfolio_id>/transactions', methods=['GET', 'POST'])
def portfolio_transactions(portfolio_id):
    """Proxy portfolio transactions."""
    user, error = validate_token_and_get_user()
    if error:
        return error
    return _proxy_request(_portfolio_url, f'/api/portfolios/{portfolio_id}/transactions', user=user)


# =============================================================================
# Notification Routes (auth required)
# =============================================================================

@gateway_bp.route('/api/notifications', methods=['GET'])
def notifications():
    """Proxy notification list."""
    user, error = validate_token_and_get_user()
    if error:
        return error
    return _proxy_request(_notification_url, '/api/notifications', user=user)


@gateway_bp.route('/api/notifications/<int:notification_id>/read', methods=['PATCH'])
def notification_read(notification_id):
    """Proxy mark notification as read."""
    user, error = validate_token_and_get_user()
    if error:
        return error
    return _proxy_request(_notification_url, f'/api/notifications/{notification_id}/read', user=user)


@gateway_bp.route('/api/notifications/read-all', methods=['PATCH'])
def notifications_read_all():
    """Proxy mark all read."""
    user, error = validate_token_and_get_user()
    if error:
        return error
    return _proxy_request(_notification_url, '/api/notifications/read-all', user=user)


@gateway_bp.route('/api/preferences', methods=['GET', 'PUT'])
def preferences():
    """Proxy user preferences."""
    user, error = validate_token_and_get_user()
    if error:
        return error
    return _proxy_request(_notification_url, '/api/preferences', user=user)


@gateway_bp.route('/api/rules', methods=['GET', 'POST'])
def rules():
    """Proxy notification rules."""
    user, error = validate_token_and_get_user()
    if error:
        return error
    return _proxy_request(_notification_url, '/api/rules', user=user)


@gateway_bp.route('/api/rules/<int:rule_id>', methods=['PUT', 'DELETE'])
def rule_detail(rule_id):
    """Proxy notification rule detail."""
    user, error = validate_token_and_get_user()
    if error:
        return error
    return _proxy_request(_notification_url, f'/api/rules/{rule_id}', user=user)


@gateway_bp.route('/api/auth/me', methods=['GET'])
def get_me():
    """Proxy get current user."""
    user, error = validate_token_and_get_user()
    if error:
        return error
    return _proxy_request(_portfolio_url, '/api/auth/me', user=user)
