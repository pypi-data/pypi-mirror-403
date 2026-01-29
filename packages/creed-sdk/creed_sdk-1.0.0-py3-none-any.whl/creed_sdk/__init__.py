"""
Creed Space SDK for Python

Provides governance infrastructure for AI agents with:
- Tool call authorization with cryptographic proof
- Callback-based flow control (on_allow, on_deny, on_require_human)
- Hash-chain audit trails

Design inspired by Superagent's clean SDK patterns.

Example:
    >>> from creed_sdk import create_client
    >>>
    >>> client = create_client(api_key="crd_live_...")
    >>>
    >>> result = await client.decide(
    ...     tool_name="send_email",
    ...     arguments={"to": "user@example.com", "subject": "Hello"},
    ...     on_allow=lambda d: print(f"Authorized: {d.decision_token}"),
    ...     on_deny=lambda d: print(f"Denied: {d.reasons}"),
    ... )
"""

from creed_sdk.client import (
    CreedClient,
    create_client,
)
from creed_sdk.errors import CreedError
from creed_sdk.types import (
    AllowDecision,
    AuditEvent,
    AuditRequest,
    AuditResult,
    AuthorizeRequest,
    AuthorizeResult,
    CreedClientOptions,
    DecideRequest,
    DecideResult,
    DenyDecision,
    RequireHumanDecision,
    Risk,
    StatusResult,
)
from creed_sdk.utils import compute_args_hash, is_token_expired

__version__ = "1.0.0"

__all__ = [
    # Client
    "CreedClient",
    "create_client",
    # Types
    "CreedClientOptions",
    "DecideRequest",
    "DecideResult",
    "AllowDecision",
    "DenyDecision",
    "RequireHumanDecision",
    "AuthorizeRequest",
    "AuthorizeResult",
    "AuditRequest",
    "AuditResult",
    "AuditEvent",
    "Risk",
    "StatusResult",
    # Errors
    "CreedError",
    # Utils
    "compute_args_hash",
    "is_token_expired",
]
