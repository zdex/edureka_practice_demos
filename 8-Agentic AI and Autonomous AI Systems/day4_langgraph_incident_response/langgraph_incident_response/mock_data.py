from __future__ import annotations

from copy import deepcopy
from typing import Any


SCENARIOS: dict[str, dict[str, Any]] = {
    "checkout_timeout": {
        "title": "Checkout failures after deployment",
        "description": (
            "Customers are reporting checkout failures. Payment API latency "
            "increased from roughly 300 ms to more than 5 seconds shortly "
            "after deployment v4.12. About 40% of payment attempts are failing."
        ),
        "initial_evidence": {
            "metrics": {
                "checkout_error_rate_pct": 40.8,
                "payment_api_p95_ms": 5230,
                "application_cpu_pct": 42,
                "application_memory_pct": 55,
                "db_connection_pool_pct": 38,
            },
            "logs": [
                "TimeoutError: payment request exceeded configured timeout",
                "HTTP 504 responses increased immediately after deployment v4.12",
            ],
            "dependencies": {
                "external_payment_gateway": "healthy",
                "orders_database": "healthy",
                "identity_service": "healthy",
            },
            "recent_changes": [
                "Deployment v4.12 completed 8 minutes before the incident."
            ],
        },
        "evidence_packets": [
            (
                "Deployment diff: PAYMENT_TIMEOUT_MS changed from 5000 to 500 "
                "in v4.12."
            ),
            (
                "Synthetic payment request to the external gateway completes "
                "successfully in 850-1100 ms, which is above the new 500 ms "
                "application timeout but below the previous 5000 ms timeout."
            ),
            (
                "A replay using the previous timeout configuration completes "
                "successfully with normal checkout error rates."
            ),
        ],
        "resolution_keywords": [
            "timeout",
            "5000",
            "rollback",
            "v4.11",
            "v4.12",
            "configuration",
        ],
        "after_fix_evidence": {
            "metrics": {
                "checkout_error_rate_pct": 0.7,
                "payment_api_p95_ms": 340,
                "application_cpu_pct": 40,
                "db_connection_pool_pct": 37,
            },
            "logs": [
                "Payment timeout exceptions returned to baseline.",
                "Checkout requests completing successfully.",
            ],
        },
        "failed_fix_evidence": {
            "metrics": {
                "checkout_error_rate_pct": 36.2,
                "payment_api_p95_ms": 4860,
            },
            "logs": [
                "TimeoutError continues after remediation attempt."
            ],
        },
    },

    "database_saturation": {
        "title": "Order API slowdown caused by database pressure",
        "description": (
            "The order API is returning intermittent 500 errors and p95 latency "
            "has risen above 4 seconds. Database CPU and active connections are "
            "near capacity. The issue began after enabling a new order-history feature."
        ),
        "initial_evidence": {
            "metrics": {
                "order_api_p95_ms": 4310,
                "order_api_error_rate_pct": 17.5,
                "database_cpu_pct": 93,
                "database_connection_pool_pct": 98,
                "application_cpu_pct": 47,
            },
            "logs": [
                "Database query timeout while loading order history.",
                "Connection pool wait time exceeded 2000 ms.",
            ],
            "dependencies": {
                "payment_service": "healthy",
                "identity_service": "healthy",
                "orders_database": "degraded",
            },
            "recent_changes": [
                "Order-history feature flag enabled 21 minutes before symptoms."
            ],
        },
        "evidence_packets": [
            (
                "Slow-query log: order_history query performs a full table scan "
                "on customer_id and consumes most database time."
            ),
            (
                "Query plan shows no usable index on the new order_history "
                "customer_id filter."
            ),
            (
                "Disabling the order-history feature in staging returns database "
                "CPU and query latency to baseline."
            ),
        ],
        "resolution_keywords": [
            "index",
            "order-history",
            "order history",
            "feature flag",
            "disable",
            "rollback",
        ],
        "after_fix_evidence": {
            "metrics": {
                "order_api_p95_ms": 390,
                "order_api_error_rate_pct": 0.4,
                "database_cpu_pct": 48,
                "database_connection_pool_pct": 51,
            },
            "logs": [
                "Slow order-history query no longer dominates database workload.",
                "Connection pool wait time returned to baseline.",
            ],
        },
        "failed_fix_evidence": {
            "metrics": {
                "order_api_p95_ms": 3890,
                "order_api_error_rate_pct": 14.2,
                "database_cpu_pct": 89,
            },
            "logs": [
                "Slow order-history query remains active."
            ],
        },
    },

    "authentication_outage": {
        "title": "Authentication failures after certificate rotation",
        "description": (
            "Users cannot log in to the customer portal. Authentication failures "
            "rose to 75% shortly after a certificate rotation. Other application "
            "services remain healthy."
        ),
        "initial_evidence": {
            "metrics": {
                "login_failure_rate_pct": 75.1,
                "auth_api_p95_ms": 280,
                "application_cpu_pct": 35,
                "identity_provider_latency_ms": 190,
            },
            "logs": [
                "JWT verification failed: unknown signing key id.",
                "Authentication service health endpoint reports healthy.",
            ],
            "dependencies": {
                "identity_provider": "healthy",
                "customer_database": "healthy",
                "auth_service": "degraded",
            },
            "recent_changes": [
                "Signing certificate rotation completed 12 minutes before incident."
            ],
        },
        "evidence_packets": [
            (
                "Auth service cache still contains the previous JWKS key set and "
                "has not refreshed since the certificate rotation."
            ),
            (
                "A forced JWKS refresh in staging resolves token verification failures."
            ),
            (
                "New tokens contain the rotated key id and verify successfully "
                "when the latest key set is loaded."
            ),
        ],
        "resolution_keywords": [
            "jwks",
            "key",
            "certificate",
            "refresh",
            "cache",
            "rotation",
        ],
        "after_fix_evidence": {
            "metrics": {
                "login_failure_rate_pct": 0.9,
                "auth_api_p95_ms": 245,
            },
            "logs": [
                "JWT verification failures returned to baseline.",
                "New signing key id is recognized by the authentication service.",
            ],
        },
        "failed_fix_evidence": {
            "metrics": {
                "login_failure_rate_pct": 67.4,
                "auth_api_p95_ms": 270,
            },
            "logs": [
                "JWT verification failed: unknown signing key id."
            ],
        },
    },
}


def list_scenarios() -> list[tuple[str, str]]:
    """Return (scenario_id, title) pairs for the UI."""
    return [(key, value["title"]) for key, value in SCENARIOS.items()]


def get_scenario(scenario_id: str) -> dict[str, Any]:
    if scenario_id not in SCENARIOS:
        raise KeyError(f"Unknown scenario: {scenario_id}")
    return deepcopy(SCENARIOS[scenario_id])


def public_scenario(scenario_id: str) -> dict[str, Any]:
    """Return only information the AI agents are allowed to see initially."""
    scenario = get_scenario(scenario_id)
    return {
        "title": scenario["title"],
        "description": scenario["description"],
        "initial_evidence": scenario["initial_evidence"],
    }


def collect_additional_evidence(
    scenario_id: str,
    investigation_round: int,
    requested_items: list[str] | None = None,
) -> list[str]:
    """
    Simulate calls to monitoring, logging, deployment, and dependency tools.

    In production these would be connectors to systems such as Datadog,
    CloudWatch, Grafana, Splunk, Kubernetes, GitHub, or a CMDB.
    """
    scenario = get_scenario(scenario_id)
    packets = scenario["evidence_packets"]

    index = max(0, min(investigation_round - 1, len(packets) - 1))
    packet = packets[index]

    request_text = ", ".join(requested_items or []) or "general diagnostic evidence"
    return [f"Requested: {request_text}", packet]


def simulate_fix(
    scenario_id: str,
    remediation_plan: dict[str, Any],
) -> dict[str, Any]:
    """
    Simulate the effect of a remediation action.

    This demo never changes real infrastructure.
    """
    scenario = get_scenario(scenario_id)

    action_text = " ".join(
        [
            str(remediation_plan.get("proposed_action", "")),
            " ".join(remediation_plan.get("steps", []) or []),
            str(remediation_plan.get("rollback_plan", "")),
        ]
    ).lower()

    matched = any(
        keyword.lower() in action_text
        for keyword in scenario["resolution_keywords"]
    )

    result = (
        scenario["after_fix_evidence"]
        if matched
        else scenario["failed_fix_evidence"]
    )

    return deepcopy(result)
