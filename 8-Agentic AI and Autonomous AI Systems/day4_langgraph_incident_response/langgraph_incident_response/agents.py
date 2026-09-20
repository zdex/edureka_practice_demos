from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Literal

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from mock_data import collect_additional_evidence, simulate_fix
from state import IncidentState


# ---------------------------------------------------------------------------
# Structured outputs
# ---------------------------------------------------------------------------

class IntakeOutput(BaseModel):
    summary: str
    symptoms: list[str]
    affected_services: list[str]
    suspected_trigger: str


class SeverityOutput(BaseModel):
    severity: Literal["low", "medium", "high", "critical"]
    impact_summary: str
    escalation_required: bool
    reasoning: str


class ObservabilityOutput(BaseModel):
    metrics_interpretation: list[str]
    log_findings: list[str]
    anomalies: list[str]
    summary: str


class DependencyOutput(BaseModel):
    healthy_dependencies: list[str]
    unhealthy_dependencies: list[str]
    dependency_risks: list[str]
    summary: str


class Hypothesis(BaseModel):
    cause: str
    confidence: int = Field(ge=0, le=100)
    supporting_evidence: list[str]
    contradicting_evidence: list[str]

class RootCauseOutput(BaseModel):
    hypotheses: list[Hypothesis]
    leading_hypothesis: str
    overall_confidence: int = Field(ge=0, le=100)

class InvestigationOutput(BaseModel):
    evidence_sufficient: bool
    confidence: int = Field(ge=0, le=100)
    conclusion: str
    additional_evidence_needed: list[str]

class RemediationOutput(BaseModel):
    proposed_action: str
    steps: list[str]
    risk_level: Literal["low", "medium", "high"]
    rollback_plan: str
    rationale: str


class ValidationOutput(BaseModel):
    resolved: bool
    confidence: int = Field(ge=0, le=100)
    before_after_comparison: list[str]
    remaining_risks: list[str]
    summary: str

class CommunicationOutput(BaseModel):
    audience_status_update: str
    technical_update: str

class PostmortemOutput(BaseModel):
    title: str
    executive_summary: str
    root_cause: str
    impact: str
    resolution: str
    preventive_actions: list[str]
    lessons_learned: list[str]


# ---------------------------------------------------------------------------
# LLM + helpers
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_llm() -> ChatGoogleGenerativeAI:
    model_name = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
    return ChatGoogleGenerativeAI(
        model=model_name,
        max_retries=2,
    )


def _structured_call(
    schema: type[BaseModel],
    role_prompt: str,
    payload: dict[str, Any],
) -> BaseModel:
    """
    Ask Gemini for schema-constrained JSON.

    Current langchain-google-genai supports Gemini native JSON-schema
    structured output via with_structured_output(..., method="json_schema").
    """
    structured = get_llm().with_structured_output(
        schema=schema.model_json_schema(),
        method="json_schema",
    )

    response = structured.invoke(
        [
            (
                "system",
                role_prompt
                + "\nUse only the evidence provided. Do not invent telemetry, "
                  "logs, dependencies, dates, or system changes.",
            ),
            (
                "human",
                json.dumps(payload, indent=2, ensure_ascii=False),
            ),
        ]
    )
    return schema.model_validate(response)


def _trace(agent: str, decision: str, detail: str) -> list[dict[str, Any]]:
    return [
        {
            "time_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "agent": agent,
            "decision": decision,
            "detail": detail,
        }
    ]


# ---------------------------------------------------------------------------
# AI AGENT 1 — Incident Intake Agent
# ---------------------------------------------------------------------------

def intake_agent(state: IncidentState) -> dict[str, Any]:
    output = _structured_call(
        IntakeOutput,
        """
You are the Incident Intake Agent.
Normalize the incident report into a concise technical summary.
Extract observable symptoms, affected services, and any plausible trigger
explicitly suggested by the input. Do not diagnose the root cause yet.
""",
        {
            "incident_description": state["incident_description"],
            "initial_evidence": state.get("raw_evidence", {}),
        },
    )

    return {
        "incident_summary": output.summary,
        "symptoms": output.symptoms,
        "affected_services": output.affected_services,
        "suspected_trigger": output.suspected_trigger,
        "trace": _trace(
            "Incident Intake Agent",
            "Incident normalized",
            output.summary,
        ),
    }


# ---------------------------------------------------------------------------
# AI AGENT 2 — Severity Agent
# ---------------------------------------------------------------------------

def severity_agent(state: IncidentState) -> dict[str, Any]:
    output = _structured_call(
        SeverityOutput,
        """
You are the Severity and Impact Agent.
Assess operational severity from low, medium, high, or critical.
Use customer impact, error rates, revenue-path impact, and service scope.
Critical means immediate business/customer impact requiring escalation.
""",
        {
            "incident_summary": state.get("incident_summary"),
            "symptoms": state.get("symptoms", []),
            "affected_services": state.get("affected_services", []),
            "metrics": state.get("raw_evidence", {}).get("metrics", {}),
        },
    )

    return {
        "severity": output.severity,
        "business_impact": output.impact_summary,
        "escalation_required": output.escalation_required,
        "trace": _trace(
            "Severity Agent",
            f"Severity = {output.severity}",
            output.reasoning,
        ),
    }


def escalation_node(state: IncidentState) -> dict[str, Any]:
    return {
        "trace": _trace(
            "Escalation Policy Node",
            "Critical incident escalated",
            "Critical incidents follow the priority investigation path.",
        )
    }


# ---------------------------------------------------------------------------
# AI AGENT 3 — Observability Agent
# ---------------------------------------------------------------------------

def observability_agent(state: IncidentState) -> dict[str, Any]:
    output = _structured_call(
        ObservabilityOutput,
        """
You are the Observability Agent.
Analyze metrics, logs, recent changes, and any newly collected evidence.
Identify anomalies and correlations. Do not jump directly to remediation.
""",
        {
            "incident": state.get("incident_summary"),
            "raw_evidence": state.get("raw_evidence", {}),
            "additional_evidence": state.get("collected_evidence", []),
            "post_fix_evidence": state.get("post_fix_evidence", {}),
        },
    )

    findings = (
        output.metrics_interpretation
        + output.log_findings
        + output.anomalies
    )

    return {
        "observability_findings": findings,
        "observability_summary": output.summary,
        "trace": _trace(
            "Observability Agent",
            "Telemetry analyzed",
            output.summary,
        ),
    }


# ---------------------------------------------------------------------------
# AI AGENT 4 — Dependency Agent
# ---------------------------------------------------------------------------

def dependency_agent(state: IncidentState) -> dict[str, Any]:
    output = _structured_call(
        DependencyOutput,
        """
You are the Dependency Analysis Agent.
Determine whether upstream/downstream services or infrastructure dependencies
are likely contributors. Separate healthy from unhealthy dependencies and
identify dependency-related risks.
""",
        {
            "incident": state.get("incident_summary"),
            "dependencies": state.get("raw_evidence", {}).get("dependencies", {}),
            "observability_findings": state.get("observability_findings", []),
            "additional_evidence": state.get("collected_evidence", []),
        },
    )

    return {
        "healthy_dependencies": output.healthy_dependencies,
        "unhealthy_dependencies": output.unhealthy_dependencies,
        "dependency_risks": output.dependency_risks,
        "dependency_summary": output.summary,
        "trace": _trace(
            "Dependency Agent",
            "Dependencies evaluated",
            output.summary,
        ),
    }


# ---------------------------------------------------------------------------
# AI AGENT 5 — Root Cause Agent
# ---------------------------------------------------------------------------

def root_cause_agent(state: IncidentState) -> dict[str, Any]:
    output = _structured_call(
        RootCauseOutput,
        """
You are the Root Cause Hypothesis Agent.
Generate 2-4 competing root-cause hypotheses.
Rank them using the available evidence.
For each hypothesis, explicitly list supporting and contradicting evidence.
Avoid certainty unless evidence is strong.
""",
        {
            "incident": state.get("incident_summary"),
            "suspected_trigger": state.get("suspected_trigger"),
            "observability_summary": state.get("observability_summary"),
            "dependency_summary": state.get("dependency_summary"),
            "observability_findings": state.get("observability_findings", []),
            "additional_evidence": state.get("collected_evidence", []),
            "post_fix_evidence": state.get("post_fix_evidence", {}),
        },
    )

    return {
        "hypotheses": [item.model_dump() for item in output.hypotheses],
        "leading_hypothesis": output.leading_hypothesis,
        "root_cause_confidence": output.overall_confidence,
        "trace": _trace(
            "Root Cause Agent",
            f"Leading hypothesis confidence = {output.overall_confidence}%",
            output.leading_hypothesis,
        ),
    }


# ---------------------------------------------------------------------------
# AI AGENT 6 — Investigation Agent
# ---------------------------------------------------------------------------

def investigation_agent(state: IncidentState) -> dict[str, Any]:
    round_number = state.get("investigation_round", 0) + 1

    output = _structured_call(
        InvestigationOutput,
        """
You are the Investigation Agent.
Challenge the leading hypothesis against all evidence.
Decide whether the evidence is sufficient to proceed to remediation.
Use a high bar: evidence should be coherent, causally plausible, and have
limited contradiction. If evidence is insufficient, request specific evidence
such as deployment diffs, query plans, dependency tests, logs, or configuration.
""",
        {
            "investigation_round": round_number,
            "incident": state.get("incident_summary"),
            "hypotheses": state.get("hypotheses", []),
            "leading_hypothesis": state.get("leading_hypothesis"),
            "observability_findings": state.get("observability_findings", []),
            "dependency_findings": {
                "healthy": state.get("healthy_dependencies", []),
                "unhealthy": state.get("unhealthy_dependencies", []),
                "risks": state.get("dependency_risks", []),
            },
            "additional_evidence": state.get("collected_evidence", []),
        },
    )

    return {
        "investigation_round": round_number,
        "investigation_summary": output.conclusion,
        "evidence_sufficient": output.evidence_sufficient,
        "investigation_confidence": output.confidence,
        "additional_evidence_needed": output.additional_evidence_needed,
        "trace": _trace(
            "Investigation Agent",
            (
                "Evidence sufficient"
                if output.evidence_sufficient
                else "More evidence required"
            ),
            output.conclusion,
        ),
    }


def evidence_collector_node(state: IncidentState) -> dict[str, Any]:
    evidence = collect_additional_evidence(
        scenario_id=state["scenario_id"],
        investigation_round=state.get("investigation_round", 1),
        requested_items=state.get("additional_evidence_needed", []),
    )

    return {
        "collected_evidence": evidence,
        "trace": _trace(
            "Evidence Collector Tool Node",
            "Additional evidence collected",
            " | ".join(evidence),
        ),
    }


# ---------------------------------------------------------------------------
# AI AGENT 7 — Remediation Agent
# ---------------------------------------------------------------------------

def remediation_agent(state: IncidentState) -> dict[str, Any]:
    output = _structured_call(
        RemediationOutput,
        """
You are the Remediation Planning Agent.
Propose the smallest reversible action that addresses the leading hypothesis.
Include ordered implementation steps and a rollback plan.
Classify operational risk as low, medium, or high.
Do not claim the action has been executed.
""",
        {
            "incident": state.get("incident_summary"),
            "leading_hypothesis": state.get("leading_hypothesis"),
            "root_cause_confidence": state.get("root_cause_confidence"),
            "investigation_summary": state.get("investigation_summary"),
            "evidence": state.get("collected_evidence", []),
        },
    )

    plan = output.model_dump()

    return {
        "remediation_plan": plan,
        "trace": _trace(
            "Remediation Agent",
            f"Proposed {output.risk_level}-risk remediation",
            output.proposed_action,
        ),
    }


def safety_gate_node(state: IncidentState) -> dict[str, Any]:
    """
    Deterministic policy gate.

    LLMs may recommend actions, but whether an action requires approval should
    not rely on the LLM alone.
    """
    plan = state.get("remediation_plan", {})
    agent_risk = str(plan.get("risk_level", "medium")).lower()

    action_text = " ".join(
        [
            str(plan.get("proposed_action", "")),
            " ".join(plan.get("steps", []) or []),
        ]
    ).lower()

    high_risk_terms = [
        "rollback",
        "restart",
        "failover",
        "database",
        "index",
        "disable",
        "traffic shift",
        "certificate",
        "production configuration",
    ]

    requires_high_risk = any(term in action_text for term in high_risk_terms)

    if agent_risk == "high" or requires_high_risk:
        effective = "high"
    elif agent_risk == "low":
        effective = "low"
    else:
        effective = "medium"

    return {
        "effective_risk_level": effective,
        "trace": _trace(
            "Safety Gate",
            f"Effective risk = {effective}",
            (
                "High-risk changes require explicit human approval."
                if effective == "high"
                else "Action may proceed in the simulation without interruption."
            ),
        ),
    }


# ---------------------------------------------------------------------------
# Human approval node (LangGraph interrupt)
# ---------------------------------------------------------------------------

def human_approval_node(state: IncidentState) -> dict[str, Any]:
    from langgraph.types import interrupt

    plan = state.get("remediation_plan", {})

    decision = interrupt(
        {
            "question": "Approve the proposed high-risk remediation?",
            "proposed_action": plan.get("proposed_action"),
            "steps": plan.get("steps", []),
            "rollback_plan": plan.get("rollback_plan"),
            "effective_risk_level": state.get("effective_risk_level"),
        }
    )

    if isinstance(decision, dict):
        approved = bool(decision.get("approved", False))
    else:
        approved = bool(decision)

    status = "approved" if approved else "rejected"

    return {
        "approval_status": status,
        "trace": _trace(
            "Human Approval Node",
            f"Remediation {status}",
            "Human-in-the-loop decision recorded.",
        ),
    }


def approval_rejected_node(state: IncidentState) -> dict[str, Any]:
    return {
        "fix_applied": False,
        "resolved": False,
        "validation_summary": (
            "The proposed high-risk remediation was rejected by the human reviewer. "
            "No simulated infrastructure change was applied."
        ),
        "remaining_risks": [
            "Incident remains unresolved because the proposed remediation was not approved."
        ],
        "trace": _trace(
            "Control Node",
            "Remediation cancelled",
            "Workflow will close with an unresolved incident status.",
        ),
    }


# ---------------------------------------------------------------------------
# Simulated remediation execution
# ---------------------------------------------------------------------------

def apply_fix_node(state: IncidentState) -> dict[str, Any]:
    evidence = simulate_fix(
        scenario_id=state["scenario_id"],
        remediation_plan=state.get("remediation_plan", {}),
    )

    return {
        "fix_applied": True,
        "post_fix_evidence": evidence,
        "trace": _trace(
            "Simulated Execution Node",
            "Remediation applied in simulation",
            "No real infrastructure was modified.",
        ),
    }


# ---------------------------------------------------------------------------
# AI AGENT 8 — Validation Agent
# ---------------------------------------------------------------------------

def validation_agent(state: IncidentState) -> dict[str, Any]:
    round_number = state.get("validation_round", 0) + 1

    output = _structured_call(
        ValidationOutput,
        """
You are the Validation Agent.
Compare pre-remediation and post-remediation evidence.
Decide whether the incident is resolved.
Resolution requires material improvement in the incident's primary symptoms,
not merely one improved metric.
""",
        {
            "validation_round": round_number,
            "incident": state.get("incident_summary"),
            "pre_fix_evidence": state.get("raw_evidence", {}),
            "post_fix_evidence": state.get("post_fix_evidence", {}),
            "remediation_plan": state.get("remediation_plan", {}),
        },
    )

    return {
        "validation_round": round_number,
        "resolved": output.resolved,
        "validation_confidence": output.confidence,
        "validation_summary": output.summary,
        "remaining_risks": output.remaining_risks,
        "trace": _trace(
            "Validation Agent",
            "Resolved" if output.resolved else "Validation failed",
            output.summary,
        ),
    }


# ---------------------------------------------------------------------------
# AI AGENT 9 — Communication Agent
# ---------------------------------------------------------------------------

def communication_agent(state: IncidentState) -> dict[str, Any]:
    output = _structured_call(
        CommunicationOutput,
        """
You are the Incident Communication Agent.
Prepare two concise updates:
1. A stakeholder/customer-facing status update without excessive technical detail.
2. A technical internal update for engineering/operations.
Clearly state whether the incident is resolved, unresolved, or remediation was rejected.
""",
        {
            "incident": state.get("incident_summary"),
            "severity": state.get("severity"),
            "business_impact": state.get("business_impact"),
            "resolved": state.get("resolved", False),
            "approval_status": state.get("approval_status"),
            "leading_hypothesis": state.get("leading_hypothesis"),
            "remediation_plan": state.get("remediation_plan", {}),
            "validation_summary": state.get("validation_summary"),
        },
    )

    return {
        "communication_update": output.audience_status_update,
        "technical_update": output.technical_update,
        "trace": _trace(
            "Communication Agent",
            "Status updates prepared",
            output.audience_status_update,
        ),
    }


# ---------------------------------------------------------------------------
# AI AGENT 10 — Postmortem Agent
# ---------------------------------------------------------------------------

def postmortem_agent(state: IncidentState) -> dict[str, Any]:
    output = _structured_call(
        PostmortemOutput,
        """
You are the Postmortem Agent.
Create a concise blameless incident postmortem based only on the completed
workflow evidence. If the incident is unresolved or remediation was rejected,
say so explicitly rather than inventing a successful resolution.
""",
        {
            "incident": state.get("incident_summary"),
            "severity": state.get("severity"),
            "business_impact": state.get("business_impact"),
            "leading_hypothesis": state.get("leading_hypothesis"),
            "root_cause_confidence": state.get("root_cause_confidence"),
            "investigation_summary": state.get("investigation_summary"),
            "remediation_plan": state.get("remediation_plan", {}),
            "approval_status": state.get("approval_status"),
            "resolved": state.get("resolved", False),
            "validation_summary": state.get("validation_summary"),
            "remaining_risks": state.get("remaining_risks", []),
        },
    )

    preventive = "\n".join(f"- {item}" for item in output.preventive_actions)
    lessons = "\n".join(f"- {item}" for item in output.lessons_learned)

    report = f"""# {output.title}

## Executive Summary
{output.executive_summary}

## Impact
{output.impact}

## Root Cause
{output.root_cause}

## Resolution
{output.resolution}

## Preventive Actions
{preventive}

## Lessons Learned
{lessons}
"""

    return {
        "postmortem": report,
        "trace": _trace(
            "Postmortem Agent",
            "Postmortem completed",
            output.executive_summary,
        ),
    }
