"""
Auth Service — password hashing, JWT token generation & validation.

Phase 1 : password utilities (already used by existing routes)
Phase 2 : JWT token functions will become the primary auth mechanism
"""

import datetime

import jwt
from werkzeug.security import check_password_hash, generate_password_hash

import config


# ─── Password Utilities ──────────────────────────────────

def hash_password(plain_text):
    """Return a werkzeug password hash."""
    return generate_password_hash(plain_text)


def verify_password(stored_hash, plain_text):
    """Compare a plaintext password against a stored hash."""
    return check_password_hash(stored_hash, plain_text)


# ─── JWT Token Utilities (Phase 2 ready) ─────────────────

def generate_token(user_id, role='employee', extra_claims=None):
    """
    Create a signed JWT containing ``user_id`` and ``role``.

    Parameters
    ----------
    user_id : str or int
    role : str
    extra_claims : dict, optional

    Returns
    -------
    str — encoded JWT
    """
    payload = {
        'user_id': str(user_id),
        'role': role,
        'iat': datetime.datetime.utcnow(),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=config.JWT_EXPIRY_HOURS),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, config.JWT_SECRET, algorithm='HS256')


def validate_token(token):
    """
    Decode and validate a JWT.

    Returns
    -------
    dict — decoded payload on success
    None — if token is expired or invalid
    """
    try:
        return jwt.decode(token, config.JWT_SECRET, algorithms=['HS256'])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None
