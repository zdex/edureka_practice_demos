from __future__ import annotations

import os
from typing import Literal

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from agents import (
    apply_fix_node,
    approval_rejected_node,
    communication_agent,
    dependency_agent,
    escalation_node,
    evidence_collector_node,
    human_approval_node,
    intake_agent,
    investigation_agent,
    observability_agent,
    postmortem_agent,
    remediation_agent,
    root_cause_agent,
    safety_gate_node,
    severity_agent,
    validation_agent,
)
from state import IncidentState

MAX_INVESTIGATION_ROUNDS = int(os.getenv("MAX_INVESTIGATION_ROUNDS", "3"))
MAX_VALIDATION_ROUNDS = int(os.getenv("MAX_VALIDATION_ROUNDS", "2"))


def route_after_severity(
    state: IncidentState,
) -> Literal["escalation", "observability"]:
    if state.get("severity") == "critical" or state.get("escalation_required"):
        return "escalation"
    return "observability"


def route_after_investigation(
    state: IncidentState,
) -> Literal["collect_evidence", "remediation"]:
    """
    Loop back for more evidence when confidence is insufficient.

    A max-round policy prevents unbounded graph cycles.
    """
    round_number = state.get("investigation_round", 0)

    if (
        not state.get("evidence_sufficient", False)
        and round_number < MAX_INVESTIGATION_ROUNDS
    ):
        return "collect_evidence"

    return "remediation"


def route_after_safety_gate(
    state: IncidentState,
) -> Literal["human_approval", "apply_fix"]:
    if state.get("effective_risk_level") == "high":
        return "human_approval"
    return "apply_fix"


def route_after_approval(
    state: IncidentState,
) -> Literal["apply_fix", "approval_rejected"]:
    if state.get("approval_status") == "approved":
        return "apply_fix"
    return "approval_rejected"


def route_after_validation(
    state: IncidentState,
) -> Literal["communication", "root_cause"]:
    """
    If remediation fails, re-enter root-cause reasoning.

    The validation-round limit prevents infinite retry cycles.
    """
    if state.get("resolved", False):
        return "communication"

    if state.get("validation_round", 0) < MAX_VALIDATION_ROUNDS:
        return "root_cause"

    return "communication"


def build_graph():
    builder = StateGraph(IncidentState)

    # 10 AI agents + deterministic policy/tool nodes
    builder.add_node("intake", intake_agent)
    builder.add_node("severity", severity_agent)
    builder.add_node("escalation", escalation_node)

    builder.add_node("observability", observability_agent)
    builder.add_node("dependency", dependency_agent)
    builder.add_node("root_cause", root_cause_agent)
    builder.add_node("investigation", investigation_agent)
    builder.add_node("collect_evidence", evidence_collector_node)

    builder.add_node("remediation", remediation_agent)
    builder.add_node("safety_gate", safety_gate_node)
    builder.add_node("human_approval", human_approval_node)
    builder.add_node("approval_rejected", approval_rejected_node)
    builder.add_node("apply_fix", apply_fix_node)

    builder.add_node("validation", validation_agent)
    builder.add_node("communication", communication_agent)
    builder.add_node("postmortem", postmortem_agent)

    # Continuous / sequential path
    builder.add_edge(START, "intake")
    builder.add_edge("intake", "severity")

    # Conditional severity branch
    builder.add_conditional_edges(
        "severity",
        route_after_severity,
        {
            "escalation": "escalation",
            "observability": "observability",
        },
    )
    builder.add_edge("escalation", "observability")

    # Investigation chain
    builder.add_edge("observability", "dependency")
    builder.add_edge("dependency", "root_cause")
    builder.add_edge("root_cause", "investigation")

    # Conditional evidence loop
    builder.add_conditional_edges(
        "investigation",
        route_after_investigation,
        {
            "collect_evidence": "collect_evidence",
            "remediation": "remediation",
        },
    )
    builder.add_edge("collect_evidence", "observability")

    # Remediation + deterministic safety gate
    builder.add_edge("remediation", "safety_gate")
    builder.add_conditional_edges(
        "safety_gate",
        route_after_safety_gate,
        {
            "human_approval": "human_approval",
            "apply_fix": "apply_fix",
        },
    )

    # Human-in-the-loop branch
    builder.add_conditional_edges(
        "human_approval",
        route_after_approval,
        {
            "apply_fix": "apply_fix",
            "approval_rejected": "approval_rejected",
        },
    )

    builder.add_edge("approval_rejected", "communication")

    # Apply -> validate
    builder.add_edge("apply_fix", "validation")

    # Conditional validation loop
    builder.add_conditional_edges(
        "validation",
        route_after_validation,
        {
            "communication": "communication",
            "root_cause": "root_cause",
        },
    )

    # Close incident
    builder.add_edge("communication", "postmortem")
    builder.add_edge("postmortem", END)

    # Interrupts require checkpointing to pause/resume safely.
    checkpointer = InMemorySaver()

    return builder.compile(checkpointer=checkpointer)
