from __future__ import annotations

import operator
from typing import Annotated, Any
from typing_extensions import TypedDict


class IncidentState(TypedDict, total=False):
    """
    Shared LangGraph state.
    `trace` and `collected_evidence` use reducers so nodes can append to them
    instead of replacing the previous values.
    """

    scenario_id: str
    incident_id: str
    incident_description: str

    # Simulated telemetry / evidence
    raw_evidence: dict[str, Any]
    collected_evidence: Annotated[list[str], operator.add]
    post_fix_evidence: dict[str, Any]

    # Intake Agent
    incident_summary: str
    symptoms: list[str]
    affected_services: list[str]
    suspected_trigger: str

    # Severity Agent
    severity: str
    business_impact: str
    escalation_required: bool

    # Observability Agent
    observability_findings: list[str]
    observability_summary: str

    # Dependency Agent
    healthy_dependencies: list[str]
    unhealthy_dependencies: list[str]
    dependency_risks: list[str]
    dependency_summary: str

    # Root Cause Agent
    hypotheses: list[dict[str, Any]]
    leading_hypothesis: str
    root_cause_confidence: int

    # Investigation Agent
    investigation_summary: str
    evidence_sufficient: bool
    investigation_confidence: int
    additional_evidence_needed: list[str]
    investigation_round: int

    # Remediation Agent + deterministic safety gate
    remediation_plan: dict[str, Any]
    effective_risk_level: str

    # Human-in-the-loop
    approval_status: str

    # Simulated execution
    fix_applied: bool

    # Validation Agent
    resolved: bool
    validation_confidence: int
    validation_summary: str
    remaining_risks: list[str]
    validation_round: int

    # Closing Agents
    communication_update: str
    technical_update: str
    postmortem: str

    # Append-only execution trace
    trace: Annotated[list[dict[str, Any]], operator.add]
