"""
Token model — CRUD operations for the tokens table.
Stores JWT tokens with revocation support.
"""

from datetime import datetime
from models.db import get_db_connection


def _generate_token_id():
    """Generate a unique token ID like TOK001, TOK002, etc."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM tokens")
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return f"TOK{count + 1:03d}"


def store_token(user_id, token_str, expires_at):
    """Store a JWT token in the database."""
    token_id = _generate_token_id()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO tokens (tokenId, userId, token, expiresAt, revoked)
           VALUES (%s, %s, %s, %s, FALSE)""",
        (token_id, str(user_id), token_str, expires_at),
    )
    conn.commit()
    cursor.close()
    conn.close()
    return token_id


def get_token(token_str):
    """Look up a token record by the token string."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tokens WHERE token = %s", (token_str,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row


def get_active_tokens_for_user(user_id):
    """Return all non-revoked, non-expired tokens for a user."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """SELECT * FROM tokens
           WHERE userId = %s AND revoked = FALSE AND expiresAt > %s
           ORDER BY expiresAt DESC""",
        (str(user_id), datetime.now()),
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def revoke_token(token_str):
    """Mark a token as revoked."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tokens SET revoked = TRUE WHERE token = %s", (token_str,))
    conn.commit()
    cursor.close()
    conn.close()


def revoke_all_user_tokens(user_id):
    """Revoke all tokens for a user (e.g. on password change or logout)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tokens SET revoked = TRUE WHERE userId = %s", (str(user_id),))
    conn.commit()
    cursor.close()
    conn.close()


def is_token_valid(token_str):
    """Check if a token exists, is not revoked, and has not expired."""
    row = get_token(token_str)
    if not row:
        return False
    if row['revoked']:
        return False
    if row['expiresAt'] < datetime.now():
        return False
    return True


def cleanup_expired_tokens():
    """Delete tokens that have expired (housekeeping)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tokens WHERE expiresAt < %s", (datetime.now(),))
    conn.commit()
    cursor.close()
    conn.close()
