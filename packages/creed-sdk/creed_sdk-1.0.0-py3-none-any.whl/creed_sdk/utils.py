"""
Utility functions for Creed Space SDK.
"""

import base64
import hashlib
import json
import time
from typing import Any


def compute_args_hash(args: dict[str, Any]) -> str:
    """
    Compute SHA-256 hash of arguments (for verification).
    Uses the same canonical JSON format as the server.

    Args:
        args: Arguments dictionary

    Returns:
        Hash string in format "sha256:..."
    """
    # Canonical JSON: sorted keys, no whitespace
    canonical = json.dumps(args, sort_keys=True, separators=(",", ":"))
    hash_bytes = hashlib.sha256(canonical.encode("utf-8")).digest()
    return f"sha256:{hash_bytes.hex()}"


def is_token_expired(token: str) -> bool:
    """
    Check if a decision token is expired (without verification).

    Args:
        token: JWT token string

    Returns:
        True if expired or invalid, False otherwise
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return True

        # Decode payload (with padding fix)
        payload_b64 = parts[1]
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding

        payload_json = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(payload_json)

        exp = payload.get("exp", 0)
        return exp < time.time()
    except Exception:
        return True


def canonical_json(obj: dict[str, Any]) -> str:
    """
    Convert dict to canonical JSON for hashing.

    Args:
        obj: Dictionary to serialize

    Returns:
        Canonical JSON string
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))
