"""HMAC signature generation for webhook security."""

import hmac
import hashlib
import time
from typing import Tuple


def generate_signature(secret: str, timestamp: int, body: bytes) -> str:
    """Generate HMAC SHA-256 signature.

    Args:
        secret: HMAC secret (should start with 'whsec_' prefix)
        timestamp: Unix timestamp (seconds since epoch)
        body: Raw request body bytes

    Returns:
        Hexadecimal signature string

    Raises:
        ValueError: If secret is empty or invalid
    """
    if not secret or not secret.strip():
        raise ValueError("Secret must be non-empty")

    # Remove 'whsec_' prefix if present (for compatibility)
    secret_key = secret.removeprefix("whsec_") if secret.startswith("whsec_") else secret

    # Create signature payload: timestamp + '.' + raw_body
    signature_payload = f"{timestamp}.{body.decode('utf-8', errors='replace')}".encode('utf-8')

    # Generate HMAC SHA-256 signature
    signature = hmac.new(
        secret_key.encode('utf-8'),
        signature_payload,
        hashlib.sha256
    ).hexdigest()

    return signature


def generate_signature_header(secret: str, body: bytes) -> Tuple[int, str]:
    """Generate signature header value with timestamp.

    Args:
        secret: HMAC secret
        body: Raw request body bytes

    Returns:
        Tuple of (timestamp, signature_header_value)
        signature_header_value format: "t=<timestamp>,v1=<signature>"
    """
    timestamp = int(time.time())
    signature = generate_signature(secret, timestamp, body)

    # Format: "t=<timestamp>,v1=<signature>"
    header_value = f"t={timestamp},v1={signature}"

    return timestamp, header_value


def verify_signature(secret: str, timestamp: int, body: bytes, signature: str) -> bool:
    """Verify HMAC signature.

    Args:
        secret: HMAC secret
        timestamp: Unix timestamp from signature header
        body: Raw request body bytes
        signature: Signature to verify (hexadecimal)

    Returns:
        True if signature is valid, False otherwise
    """
    try:
        expected_signature = generate_signature(secret, timestamp, body)
        return hmac.compare_digest(expected_signature, signature)
    except Exception:
        return False

