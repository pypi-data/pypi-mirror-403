"""
Creed Space SDK Client Tests.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from creed_sdk import CreedClient, create_client
from creed_sdk.errors import (
    AuthenticationError,
    CreedError,
    RateLimitError,
    TimeoutError,
)
from creed_sdk.types import AllowDecision, DenyDecision


class TestCreateClient:
    """Tests for create_client factory function."""

    def test_creates_client_with_valid_key(self):
        """Should create client with valid API key."""
        client = create_client(api_key="crd_test_123")
        assert isinstance(client, CreedClient)
        assert client.api_key == "crd_test_123"

    def test_raises_error_for_missing_key(self):
        """Should raise error when API key is missing."""
        with pytest.raises(CreedError) as exc_info:
            create_client(api_key="")
        assert exc_info.value.code == "MISSING_API_KEY"

    def test_uses_default_base_url(self):
        """Should use default base URL when not specified."""
        client = create_client(api_key="crd_test_123")
        assert client.base_url == "https://api.creed.space"

    def test_uses_custom_base_url(self):
        """Should use custom base URL when specified."""
        client = create_client(
            api_key="crd_test_123",
            base_url="https://custom.api.com",
        )
        assert client.base_url == "https://custom.api.com"

    def test_converts_timeout_to_seconds(self):
        """Should convert timeout from ms to seconds."""
        client = create_client(api_key="crd_test_123", timeout_ms=5000)
        assert client.timeout == 5.0


class TestCreedClientContextManager:
    """Tests for async context manager support."""

    @pytest.mark.asyncio
    async def test_context_manager_closes_client(self):
        """Should close client when exiting context."""
        async with create_client(api_key="crd_test_123") as client:
            assert isinstance(client, CreedClient)
        # Client should be closed (no way to verify directly, but should not raise)


class TestDecide:
    """Tests for decide() method."""

    @pytest.mark.asyncio
    async def test_sends_correct_request(self):
        """Should send correct request format."""
        client = create_client(api_key="crd_test_123")

        mock_response = httpx.Response(
            200,
            json={
                "decision": "ALLOW",
                "run_id": "run_123",
                "action_id": "action_456",
                "tool_call_id": "tc_789",
                "args_hash": "sha256:abc",
                "risk": {"score": 0.1, "labels": []},
                "decision_token": "eyJ...",
                "expires_at": "2025-01-01T00:05:00Z",
            },
        )

        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            await client.decide(
                tool_name="send_email",
                arguments={"to": "user@example.com"},
            )

            mock_request.assert_called_once()
            call_kwargs = mock_request.call_args[1]
            assert call_kwargs["method"] == "POST"
            assert call_kwargs["url"] == "/v1/decide"
            assert call_kwargs["json"]["tool_name"] == "send_email"
            assert call_kwargs["json"]["arguments"] == {"to": "user@example.com"}

        await client.close()

    @pytest.mark.asyncio
    async def test_invokes_on_allow_callback(self):
        """Should invoke on_allow callback for ALLOW decision."""
        client = create_client(api_key="crd_test_123")

        mock_response = httpx.Response(
            200,
            json={
                "decision": "ALLOW",
                "run_id": "run_123",
                "action_id": "action_456",
                "tool_call_id": "tc_789",
                "args_hash": "sha256:abc",
                "risk": {"score": 0.1, "labels": []},
                "decision_token": "eyJ...",
                "expires_at": "2025-01-01T00:05:00Z",
            },
        )

        on_allow = MagicMock()
        on_deny = MagicMock()

        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await client.decide(
                tool_name="send_email",
                arguments={"to": "user@example.com"},
                on_allow=on_allow,
                on_deny=on_deny,
            )

            assert result.decision == "ALLOW"
            assert isinstance(result, AllowDecision)
            on_allow.assert_called_once()
            on_deny.assert_not_called()

        await client.close()

    @pytest.mark.asyncio
    async def test_invokes_on_deny_callback(self):
        """Should invoke on_deny callback for DENY decision."""
        client = create_client(api_key="crd_test_123")

        mock_response = httpx.Response(
            200,
            json={
                "decision": "DENY",
                "run_id": "run_123",
                "action_id": "action_456",
                "tool_call_id": "tc_789",
                "args_hash": "sha256:abc",
                "risk": {"score": 0.9, "labels": ["high_risk"]},
                "reasons": ["Tool blocked"],
                "guidance": {"message": "Not allowed"},
            },
        )

        on_allow = MagicMock()
        on_deny = MagicMock()

        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await client.decide(
                tool_name="delete_all",
                arguments={},
                on_allow=on_allow,
                on_deny=on_deny,
            )

            assert result.decision == "DENY"
            assert isinstance(result, DenyDecision)
            on_deny.assert_called_once()
            on_allow.assert_not_called()

        await client.close()

    @pytest.mark.asyncio
    async def test_handles_async_callback(self):
        """Should handle async callbacks correctly."""
        client = create_client(api_key="crd_test_123")

        mock_response = httpx.Response(
            200,
            json={
                "decision": "ALLOW",
                "run_id": "run_123",
                "action_id": "action_456",
                "tool_call_id": "tc_789",
                "args_hash": "sha256:abc",
                "risk": {"score": 0.1, "labels": []},
                "decision_token": "eyJ...",
                "expires_at": "2025-01-01T00:05:00Z",
            },
        )

        callback_called = []

        async def async_callback(decision):
            callback_called.append(decision)

        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            await client.decide(
                tool_name="send_email",
                arguments={"to": "user@example.com"},
                on_allow=async_callback,
            )

            assert len(callback_called) == 1

        await client.close()


class TestAuthorize:
    """Tests for authorize() method."""

    @pytest.mark.asyncio
    async def test_returns_authorized_result(self):
        """Should return authorized result for valid token."""
        client = create_client(api_key="crd_test_123")

        mock_response = httpx.Response(
            200,
            json={
                "authorized": True,
                "message": "Token is valid",
                "claims": {
                    "action_id": "action_456",
                    "tool_name": "send_email",
                    "tool_call_id": "tc_789",
                    "args_hash": "sha256:abc",
                    "run_id": "run_123",
                    "decision": "ALLOW",
                    "issued_at": "2025-01-01T00:00:00Z",
                    "expires_at": "2025-01-01T00:05:00Z",
                },
            },
        )

        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await client.authorize(decision_token="eyJ...")

            assert result.authorized is True
            assert result.claims is not None
            assert result.claims.tool_name == "send_email"

        await client.close()


class TestAudit:
    """Tests for audit() method."""

    @pytest.mark.asyncio
    async def test_returns_audit_events(self):
        """Should return audit events with integrity info."""
        client = create_client(api_key="crd_test_123")

        mock_response = httpx.Response(
            200,
            json={
                "run_id": "run_123",
                "event_count": 2,
                "events": [
                    {
                        "seq": 0,
                        "type": "action_created",
                        "timestamp": "2025-01-01T00:00:00Z",
                        "data": {},
                        "hash": "abc",
                    },
                    {
                        "seq": 1,
                        "type": "decision_made",
                        "timestamp": "2025-01-01T00:00:01Z",
                        "data": {},
                        "hash": "def",
                    },
                ],
                "integrity": {"chain": "sha256_merkle", "verified": True},
            },
        )

        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await client.audit(run_id="run_123")

            assert result.run_id == "run_123"
            assert len(result.events) == 2
            assert result.integrity.verified is True

        await client.close()


class TestStatus:
    """Tests for status() method."""

    @pytest.mark.asyncio
    async def test_returns_status(self):
        """Should return service status."""
        client = create_client(api_key="crd_test_123")

        mock_response = httpx.Response(
            200,
            json={
                "service": "creed-pdp",
                "version": "1.0.0",
                "features": {
                    "creed_decide": {"status": "active", "description": "Get governance decisions"},
                    "require_human": {
                        "status": "planned",
                        "description": "Human review",
                        "eta": "Q1 2025",
                    },
                },
                "decision_types": {"ALLOW": "active", "DENY": "active"},
            },
        )

        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await client.status()

            assert result.service == "creed-pdp"
            assert result.version == "1.0.0"
            assert "creed_decide" in result.features
            assert result.features["creed_decide"].status == "active"

        await client.close()


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_raises_authentication_error(self):
        """Should raise AuthenticationError on 401."""
        client = create_client(api_key="crd_test_invalid")

        mock_response = httpx.Response(401, text="Unauthorized")

        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            with pytest.raises(AuthenticationError):
                await client.status()

        await client.close()

    @pytest.mark.asyncio
    async def test_raises_rate_limit_error(self):
        """Should raise RateLimitError on 429."""
        client = create_client(api_key="crd_test_123")

        mock_response = httpx.Response(429, headers={"retry-after": "60"})

        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            with pytest.raises(RateLimitError) as exc_info:
                await client.status()

            assert exc_info.value.retry_after == 60

        await client.close()

    @pytest.mark.asyncio
    async def test_raises_timeout_error(self):
        """Should raise TimeoutError on timeout."""
        client = create_client(api_key="crd_test_123", timeout_ms=100)

        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = httpx.TimeoutException("Timeout")

            with pytest.raises(TimeoutError):
                await client.status()

        await client.close()

    @pytest.mark.asyncio
    async def test_raises_creed_error_on_network_error(self):
        """Should raise CreedError on network error."""
        client = create_client(api_key="crd_test_123")

        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = httpx.ConnectError("Connection refused")

            with pytest.raises(CreedError) as exc_info:
                await client.status()

            assert exc_info.value.code == "NETWORK_ERROR"

        await client.close()
