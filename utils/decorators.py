"""
Route decorators — @login_required, @admin_required, @token_required.
"""

from functools import wraps

from flask import redirect, request, session, url_for, jsonify

from services.auth_service import validate_token


def login_required(f):
    """Redirect to login page when no session is active."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Redirect to login page when the user is not an admin."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'admin':
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def token_required(f):
    """
    Validate a JWT from the ``Authorization: Bearer <token>`` header.

    On success the decoded payload is passed as the first positional
    argument to the wrapped function.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify(success=False, message='Missing or invalid token'), 401
        token = auth_header.split(' ', 1)[1]
        payload = validate_token(token)
        if payload is None:
            return jsonify(success=False, message='Token expired or invalid'), 401
        return f(payload, *args, **kwargs)
    return decorated
