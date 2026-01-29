"""
Creed Space SDK Utils Tests.
"""

import base64
import json
import time

from creed_sdk.utils import compute_args_hash, is_token_expired


class TestComputeArgsHash:
    """Tests for compute_args_hash function."""

    def test_produces_consistent_hash(self):
        """Should produce consistent hash for same arguments."""
        args = {"to": "user@example.com", "subject": "Hello"}
        hash1 = compute_args_hash(args)
        hash2 = compute_args_hash(args)
        assert hash1 == hash2

    def test_produces_different_hash_for_different_args(self):
        """Should produce different hash for different arguments."""
        hash1 = compute_args_hash({"a": 1})
        hash2 = compute_args_hash({"a": 2})
        assert hash1 != hash2

    def test_hash_starts_with_sha256_prefix(self):
        """Should start hash with sha256: prefix."""
        hash_value = compute_args_hash({"test": True})
        assert hash_value.startswith("sha256:")

    def test_canonical_hash_regardless_of_key_order(self):
        """Should produce same hash regardless of key order."""
        hash1 = compute_args_hash({"a": 1, "b": 2})
        hash2 = compute_args_hash({"b": 2, "a": 1})
        assert hash1 == hash2

    def test_handles_nested_objects(self):
        """Should handle nested objects consistently."""
        args = {"user": {"name": "Test", "id": 123}, "action": "send"}
        hash1 = compute_args_hash(args)
        hash2 = compute_args_hash(args)
        assert hash1 == hash2

    def test_handles_empty_dict(self):
        """Should handle empty dict."""
        hash_value = compute_args_hash({})
        assert hash_value.startswith("sha256:")
        assert len(hash_value) > 10


class TestIsTokenExpired:
    """Tests for is_token_expired function."""

    def test_returns_true_for_empty_token(self):
        """Should return True for empty token."""
        assert is_token_expired("") is True

    def test_returns_true_for_malformed_token(self):
        """Should return True for malformed token."""
        assert is_token_expired("invalid") is True
        assert is_token_expired("a.b") is True
        assert is_token_expired("not.a.jwt.token") is True

    def test_returns_true_for_expired_token(self):
        """Should return True for expired token."""
        # Create expired JWT payload
        payload = {"exp": int(time.time()) - 3600}  # 1 hour ago
        payload_b64 = base64.b64encode(json.dumps(payload).encode()).decode()
        token = f"header.{payload_b64}.signature"
        assert is_token_expired(token) is True

    def test_returns_false_for_valid_token(self):
        """Should return False for non-expired token."""
        # Create future JWT payload
        payload = {"exp": int(time.time()) + 3600}  # 1 hour from now
        payload_b64 = base64.b64encode(json.dumps(payload).encode()).decode()
        token = f"header.{payload_b64}.signature"
        assert is_token_expired(token) is False

    def test_returns_true_for_invalid_base64(self):
        """Should return True for invalid base64 in payload."""
        assert is_token_expired("header.not_valid_base64!!!.signature") is True

    def test_returns_true_for_invalid_json(self):
        """Should return True for invalid JSON in payload."""
        invalid_json_b64 = base64.b64encode(b"not json").decode()
        token = f"header.{invalid_json_b64}.signature"
        assert is_token_expired(token) is True
