"""Password hashing and session tokens. Never log the values handled here."""

import hashlib
import secrets

from pwdlib import PasswordHash

MAX_PASSWORD_LENGTH = 1024  # bounds Argon2 work per request

_hasher = PasswordHash.recommended()  # Argon2id
# Verified against when the user does not exist, so both failure paths cost about the same.
_DUMMY_HASH = _hasher.hash(secrets.token_urlsafe(16))


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    if password_hash is None:
        _hasher.verify(password, _DUMMY_HASH)
        return False
    return _hasher.verify(password, password_hash)


def password_problem(password: str, min_length: int) -> str | None:
    """Return a user-facing reason the password is unacceptable, or None."""
    if len(password) < min_length:
        return f"Password must be at least {min_length} characters"
    if len(password) > MAX_PASSWORD_LENGTH:
        return f"Password must be at most {MAX_PASSWORD_LENGTH} characters"
    return None


def new_session_token() -> str:
    """32 random bytes, base64url-encoded for the cookie."""
    return secrets.token_urlsafe(32)


def token_hash(token: str) -> bytes:
    """SHA-256 digest of the cookie value. Only this is stored."""
    return hashlib.sha256(token.encode()).digest()
