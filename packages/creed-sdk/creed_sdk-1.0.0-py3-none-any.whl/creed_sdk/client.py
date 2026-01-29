"""
Creed Space SDK Client.

Provides async client for interacting with Creed Space governance API.
"""

import inspect
from typing import Any

import httpx

from creed_sdk.errors import AuthenticationError, CreedError, RateLimitError, TimeoutError
from creed_sdk.types import (
    AllowDecision,
    AuditEvent,
    AuditResult,
    AuthorizeClaims,
    AuthorizeResult,
    ChainIntegrity,
    DecideResult,
    DenyDecision,
    FeatureStatus,
    RequireHumanDecision,
    Risk,
    StatusResult,
)


class CreedClient:
    """
    Async client for Creed Space governance API.

    Example:
        >>> client = CreedClient(api_key="crd_live_...")
        >>> result = await client.decide(
        ...     tool_name="send_email",
        ...     arguments={"to": "user@example.com"},
        ... )
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.creed.space",
        timeout_ms: int = 30000,
    ):
        """
        Initialize the client.

        Args:
            api_key: Creed API key (crd_live_... or crd_test_...)
            base_url: API base URL
            timeout_ms: Request timeout in milliseconds
        """
        if not api_key:
            raise CreedError("API key is required", "MISSING_API_KEY")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout_ms / 1000.0  # Convert to seconds

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "X-Creed-SDK": "python/1.0.0",
            },
        )

    async def __aenter__(self) -> "CreedClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an API request."""
        try:
            response = await self._client.request(
                method=method,
                url=endpoint,
                json=json_data,
            )

            if response.status_code == 401:
                raise AuthenticationError()
            elif response.status_code == 429:
                retry_after = response.headers.get("retry-after")
                raise RateLimitError(retry_after=int(retry_after) if retry_after else None)
            elif not response.is_success:
                raise CreedError(
                    response.text or f"Request failed with status {response.status_code}",
                    "REQUEST_FAILED",
                    response.status_code,
                )

            return response.json()

        except httpx.TimeoutException as e:
            raise TimeoutError() from e
        except httpx.RequestError as e:
            raise CreedError(str(e), "NETWORK_ERROR") from e

    async def decide(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        constitution_id: str = "default",
        context: dict[str, Any] | None = None,
        on_allow: Any | None = None,
        on_deny: Any | None = None,
        on_require_human: Any | None = None,
    ) -> DecideResult:
        """
        Get a governance decision for a tool call.

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            constitution_id: Constitution to evaluate against
            context: Optional context (tenant_id, user_id, etc.)
            on_allow: Callback when allowed (sync or async)
            on_deny: Callback when denied (sync or async)
            on_require_human: Callback when human review required (sync or async)

        Returns:
            Decision result (AllowDecision, DenyDecision, or RequireHumanDecision)
        """
        data = await self._request(
            "POST",
            "/v1/decide",
            {
                "tool_name": tool_name,
                "arguments": arguments,
                "constitution_id": constitution_id,
                "context": context or {},
            },
        )

        # Parse response into typed decision
        decision_type = data.get("decision", "DENY")
        risk = Risk(
            score=data.get("risk", {}).get("score", 0.0),
            labels=data.get("risk", {}).get("labels", []),
        )

        result: DecideResult

        if decision_type == "ALLOW":
            result = AllowDecision(
                decision="ALLOW",
                run_id=data.get("run_id", ""),
                action_id=data.get("action_id", ""),
                tool_call_id=data.get("tool_call_id", ""),
                args_hash=data.get("args_hash", ""),
                risk=risk,
                decision_token=data.get("decision_token", ""),
                expires_at=data.get("expires_at", ""),
            )
            if on_allow:
                await self._invoke_callback(on_allow, result)

        elif decision_type == "REQUIRE_HUMAN":
            result = RequireHumanDecision(
                decision="REQUIRE_HUMAN",
                run_id=data.get("run_id", ""),
                action_id=data.get("action_id", ""),
                tool_call_id=data.get("tool_call_id", ""),
                args_hash=data.get("args_hash", ""),
                risk=risk,
                review_id=data.get("review_id"),
                feature_status="planned",  # Always planned until released
            )
            if on_require_human:
                await self._invoke_callback(on_require_human, result)

        else:  # DENY
            result = DenyDecision(
                decision="DENY",
                run_id=data.get("run_id", ""),
                action_id=data.get("action_id", ""),
                tool_call_id=data.get("tool_call_id", ""),
                args_hash=data.get("args_hash", ""),
                risk=risk,
                reasons=data.get("reasons", []),
                guidance=data.get("guidance", {}),
            )
            if on_deny:
                await self._invoke_callback(on_deny, result)

        return result

    async def authorize(
        self,
        decision_token: str,
        tool_name: str | None = None,
        args_hash: str | None = None,
    ) -> AuthorizeResult:
        """
        Verify a decision token before execution.

        Args:
            decision_token: JWT decision token from decide()
            tool_name: Expected tool name (optional validation)
            args_hash: Expected args hash (optional validation)

        Returns:
            Authorization result with verified claims
        """
        data = await self._request(
            "POST",
            "/v1/authorize",
            {
                "decision_token": decision_token,
                "tool_name": tool_name,
                "args_hash": args_hash,
            },
        )

        claims = None
        if data.get("claims"):
            c = data["claims"]
            claims = AuthorizeClaims(
                action_id=c.get("action_id", ""),
                tool_name=c.get("tool_name", ""),
                tool_call_id=c.get("tool_call_id", ""),
                args_hash=c.get("args_hash", ""),
                run_id=c.get("run_id", ""),
                decision=c.get("decision", ""),
                issued_at=c.get("issued_at", ""),
                expires_at=c.get("expires_at", ""),
            )

        return AuthorizeResult(
            authorized=data.get("authorized", False),
            message=data.get("message", ""),
            claims=claims,
            error=data.get("error"),
        )

    async def audit(
        self,
        run_id: str,
        action_id: str | None = None,
        limit: int = 50,
    ) -> AuditResult:
        """
        Query the audit trail for a run.

        Args:
            run_id: Run ID to query
            action_id: Specific action ID (optional)
            limit: Maximum events to return

        Returns:
            Audit result with events and integrity info
        """
        data = await self._request(
            "POST",
            "/v1/audit",
            {
                "run_id": run_id,
                "action_id": action_id,
                "limit": limit,
            },
        )

        events = [
            AuditEvent(
                seq=e.get("seq", 0),
                type=e.get("type", ""),
                timestamp=e.get("timestamp", ""),
                data=e.get("data", {}),
                hash=e.get("hash", ""),
            )
            for e in data.get("events", [])
        ]

        integrity_data = data.get("integrity", {})
        integrity = ChainIntegrity(
            chain=integrity_data.get("chain", "sha256_merkle"),
            verified=integrity_data.get("verified", False),
        )

        return AuditResult(
            run_id=data.get("run_id", ""),
            action_id=data.get("action_id"),
            event_count=data.get("event_count", len(events)),
            events=events,
            integrity=integrity,
        )

    async def status(self) -> StatusResult:
        """
        Get service status.

        Returns:
            Status with features and decision types
        """
        data = await self._request("GET", "/v1/status")

        features = {}
        for name, info in data.get("features", {}).items():
            features[name] = FeatureStatus(
                status=info.get("status", "unknown"),
                description=info.get("description", ""),
                eta=info.get("eta"),
            )

        return StatusResult(
            service=data.get("service", "creed-pdp"),
            version=data.get("version", ""),
            features=features,
            decision_types=data.get("decision_types", {}),
        )

    async def _invoke_callback(self, callback: Any, arg: Any) -> None:
        """Invoke a callback (sync or async)."""
        if inspect.iscoroutinefunction(callback):
            await callback(arg)
        else:
            callback(arg)


def create_client(
    api_key: str,
    base_url: str = "https://api.creed.space",
    timeout_ms: int = 30000,
) -> CreedClient:
    """
    Create a Creed Space client.

    Args:
        api_key: Creed API key (crd_live_... or crd_test_...)
        base_url: API base URL
        timeout_ms: Request timeout in milliseconds

    Returns:
        CreedClient instance

    Example:
        >>> client = create_client(api_key="crd_live_...")
        >>> result = await client.decide(
        ...     tool_name="send_email",
        ...     arguments={"to": "user@example.com"},
        ...     on_allow=lambda d: print(f"Token: {d.decision_token}"),
        ... )
    """
    return CreedClient(
        api_key=api_key,
        base_url=base_url,
        timeout_ms=timeout_ms,
    )
