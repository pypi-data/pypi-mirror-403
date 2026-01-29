#!/usr/bin/env python3
"""
Creed Space SDK - Basic Usage Example

This example demonstrates the core SDK functionality:
1. Creating a client
2. Getting governance decisions
3. Using callbacks for flow control
4. Verifying tokens before execution
5. Querying the audit trail
"""

import asyncio
import os

from creed_sdk import compute_args_hash, create_client, is_token_expired
from creed_sdk.types import AllowDecision, DenyDecision, RequireHumanDecision

# Configuration
API_KEY = os.environ.get("CREED_API_KEY", "crd_test_example")
BASE_URL = os.environ.get("CREED_API_URL", "https://api.creed.space")


async def main():
    print("Creed Space SDK - Basic Usage Example\n")

    # 1. Create the client (using context manager for automatic cleanup)
    async with create_client(
        api_key=API_KEY,
        base_url=BASE_URL,
        timeout_ms=30000,
    ) as client:
        print("1. Client created successfully\n")

        # 2. Get a governance decision with callbacks
        print("2. Requesting governance decision for send_email tool...\n")

        email_args = {
            "to": "user@example.com",
            "subject": "Hello from Creed Space",
            "body": "This is a test email.",
        }

        decision_token = None
        run_id = None

        async def on_allow(decision: AllowDecision):
            nonlocal decision_token
            decision_token = decision.decision_token
            print("   ALLOWED!")
            print(f"   Decision Token: {decision.decision_token[:50]}...")
            print(f"   Expires At: {decision.expires_at}")
            print(f"   Risk Score: {decision.risk.score}")
            print()

        def on_deny(decision: DenyDecision):
            print("   DENIED!")
            print(f"   Reasons: {', '.join(decision.reasons)}")
            print(f"   Guidance: {decision.guidance.get('message', 'N/A')}")
            print()

        def on_require_human(decision: RequireHumanDecision):
            print("   HUMAN REVIEW REQUIRED (planned feature)")
            print(f"   Feature Status: {decision.feature_status}")
            print()

        result = await client.decide(
            tool_name="send_email",
            arguments=email_args,
            constitution_id="default",
            context={
                "user_id": "user_123",
                "session_id": "session_456",
            },
            on_allow=on_allow,
            on_deny=on_deny,
            on_require_human=on_require_human,
        )

        run_id = result.run_id
        print(f"   Decision: {result.decision}")
        print(f"   Run ID: {result.run_id}")
        print()

        # 3. Verify the token before execution (if allowed)
        if result.decision == "ALLOW" and decision_token:
            print("3. Verifying decision token before execution...\n")

            # Check if token is expired locally first (fast check)
            if is_token_expired(decision_token):
                print("   Token is expired! Request a new decision.\n")
            else:
                # Verify with the server
                args_hash = compute_args_hash(email_args)
                auth = await client.authorize(
                    decision_token=decision_token,
                    tool_name="send_email",
                    args_hash=args_hash,
                )

                print(f"   Authorized: {auth.authorized}")
                print(f"   Message: {auth.message}")
                if auth.claims:
                    print(f"   Tool: {auth.claims.tool_name}")
                    print(f"   Valid Until: {auth.claims.expires_at}")
                print()

                # 4. Execute the tool (simulated)
                if auth.authorized:
                    print("4. Executing tool...\n")
                    print(f"   Sending email to {email_args['to']}...")
                    print("   Email sent successfully!\n")

            # 5. Query the audit trail
            print("5. Querying audit trail...\n")

            try:
                audit = await client.audit(
                    run_id=run_id,
                    limit=10,
                )

                print(f"   Run ID: {audit.run_id}")
                print(f"   Event Count: {audit.event_count}")
                print(f"   Chain Verified: {audit.integrity.verified}")

                if audit.events:
                    print("\n   Events:")
                    for event in audit.events:
                        print(f"   - [{event.seq}] {event.type} at {event.timestamp}")
            except Exception:
                print("   Audit trail not available (run not persisted in demo mode)")

        # 6. Get service status
        print("\n6. Checking service status...\n")

        status = await client.status()
        print(f"   Service: {status.service}")
        print(f"   Version: {status.version}")
        print("\n   Features:")
        for name, info in status.features.items():
            print(f"   - {name}: {info.status}")
        print("\n   Decision Types:")
        for dtype, dtype_status in status.decision_types.items():
            print(f"   - {dtype}: {dtype_status}")

    print("\n--- Example Complete ---")


if __name__ == "__main__":
    asyncio.run(main())
