"""
Type definitions for Creed Space SDK.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class Risk:
    """Risk assessment for a decision."""

    score: float
    labels: list[str]


@dataclass
class CreedClientOptions:
    """Client configuration options."""

    api_key: str
    base_url: str = "https://api.creed.space"
    timeout_ms: int = 30000


@dataclass
class DecideRequest:
    """Request for a governance decision."""

    tool_name: str
    arguments: dict[str, Any]
    constitution_id: str = "default"
    context: dict[str, Any] | None = None
    on_allow: Callable[["AllowDecision"], None | Awaitable[None]] | None = None
    on_deny: Callable[["DenyDecision"], None | Awaitable[None]] | None = None
    on_require_human: Callable[["RequireHumanDecision"], None | Awaitable[None]] | None = None


@dataclass
class AllowDecision:
    """Decision result when tool is allowed."""

    decision: Literal["ALLOW"]
    run_id: str
    action_id: str
    tool_call_id: str
    args_hash: str
    risk: Risk
    decision_token: str
    expires_at: str


@dataclass
class DenyDecision:
    """Decision result when tool is denied."""

    decision: Literal["DENY"]
    run_id: str
    action_id: str
    tool_call_id: str
    args_hash: str
    risk: Risk
    reasons: list[str]
    guidance: dict[str, str]


@dataclass
class RequireHumanDecision:
    """Decision result when human review is required (planned feature)."""

    decision: Literal["REQUIRE_HUMAN"]
    run_id: str
    action_id: str
    tool_call_id: str
    args_hash: str
    risk: Risk
    review_id: str | None = None
    feature_status: str = "planned"  # Always "planned" until feature is released


DecideResult = AllowDecision | DenyDecision | RequireHumanDecision


@dataclass
class AuthorizeRequest:
    """Request to verify a decision token."""

    decision_token: str
    tool_name: str | None = None
    args_hash: str | None = None


@dataclass
class AuthorizeClaims:
    """Claims extracted from a verified token."""

    action_id: str
    tool_name: str
    tool_call_id: str
    args_hash: str
    run_id: str
    decision: str
    issued_at: str
    expires_at: str


@dataclass
class AuthorizeResult:
    """Result of token verification."""

    authorized: bool
    message: str
    claims: AuthorizeClaims | None = None
    error: str | None = None


@dataclass
class AuditRequest:
    """Request to query audit trail."""

    run_id: str
    action_id: str | None = None
    limit: int = 50


@dataclass
class AuditEvent:
    """Single audit event."""

    seq: int
    type: str
    timestamp: str
    data: dict[str, Any]
    hash: str


@dataclass
class ChainIntegrity:
    """Audit chain integrity status."""

    chain: str
    verified: bool


@dataclass
class AuditResult:
    """Result of audit query."""

    run_id: str
    event_count: int
    events: list[AuditEvent]
    integrity: ChainIntegrity
    action_id: str | None = None


@dataclass
class FeatureStatus:
    """Status of a feature."""

    status: str
    description: str
    eta: str | None = None


@dataclass
class StatusResult:
    """Service status result."""

    service: str
    version: str
    features: dict[str, FeatureStatus]
    decision_types: dict[str, str]
