"""Token hashing utilities."""

import hashlib
import hmac


def hash_token(token: str | bytes) -> str:
    """Hash a secure random token for storage.

    Args:
        token: The token to hash.

    Returns:
        Hex-encoded hash of the token.
    """
    data = token.encode() if isinstance(token, str) else token
    return hashlib.sha256(data).hexdigest()


def verify_token(token: str | bytes, hashed: str) -> bool:
    """Verify a token against its stored hash.

    Args:
        token: The plaintext token to verify.
        hashed: The stored hash to verify against.

    Returns:
        True if the token matches, False otherwise.
    """
    return hmac.compare_digest(hash_token(token), hashed)
