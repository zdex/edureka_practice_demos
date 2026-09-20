from __future__ import annotations

import os
import uuid

import streamlit as st
from dotenv import load_dotenv
from langgraph.types import Command

from graph import build_graph
from mock_data import list_scenarios, public_scenario


load_dotenv()

st.set_page_config(
    page_title="LangGraph Incident Response",
    page_icon="🧭",
    layout="wide",
)


@st.cache_resource
def get_graph():
    # The same compiled graph/checkpointer must survive Streamlit reruns so
    # an interrupted thread can be resumed with the same thread_id.
    return build_graph()


graph = get_graph()


def make_initial_state(scenario_id: str) -> dict:
    scenario = public_scenario(scenario_id)

    return {
        "scenario_id": scenario_id,
        "incident_id": str(uuid.uuid4()),
        "incident_description": scenario["description"],
        "raw_evidence": scenario["initial_evidence"],
        "collected_evidence": [],
        "trace": [],
        "investigation_round": 0,
        "validation_round": 0,
        "approval_status": "not_required",
        "resolved": False,
        "fix_applied": False,
    }


def current_interrupt(result: dict | None):
    if not result:
        return None

    interrupts = result.get("__interrupt__", [])
    if not interrupts:
        return None

    first = interrupts[0]
    return getattr(first, "value", first)


def render_trace(result: dict):
    trace = result.get("trace", [])
    if not trace:
        return

    st.subheader("Execution trace")
    st.dataframe(
        trace,
        width=True,
        hide_index=True,
    )


def render_state(result: dict):
    if not result:
        return

    st.subheader("Current incident state")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Severity", str(result.get("severity", "Pending")).upper())
    c2.metric(
        "Investigation confidence",
        f"{result.get('investigation_confidence', 0)}%",
    )
    c3.metric(
        "Root-cause confidence",
        f"{result.get('root_cause_confidence', 0)}%",
    )

    status = (
        "Resolved"
        if result.get("resolved")
        else "In progress / unresolved"
    )
    c4.metric("Status", status)

    if result.get("incident_summary"):
        st.markdown("### Incident summary")
        st.write(result["incident_summary"])

    if result.get("business_impact"):
        st.markdown("### Business impact")
        st.write(result["business_impact"])

    if result.get("leading_hypothesis"):
        st.markdown("### Leading root-cause hypothesis")
        st.write(result["leading_hypothesis"])

    hypotheses = result.get("hypotheses", [])
    if hypotheses:
        with st.expander("Competing root-cause hypotheses"):
            for index, item in enumerate(hypotheses, start=1):
                st.markdown(
                    f"**{index}. {item.get('cause', 'Hypothesis')} "
                    f"({item.get('confidence', 0)}%)**"
                )
                supporting = item.get("supporting_evidence", [])
                contradicting = item.get("contradicting_evidence", [])
                if supporting:
                    st.write("Supporting evidence:")
                    for x in supporting:
                        st.write(f"- {x}")
                if contradicting:
                    st.write("Contradicting evidence:")
                    for x in contradicting:
                        st.write(f"- {x}")

    if result.get("remediation_plan"):
        plan = result["remediation_plan"]
        st.markdown("### Proposed remediation")
        st.write(plan.get("proposed_action", ""))
        st.write(
            f"**Agent risk:** {plan.get('risk_level', 'unknown')}  |  "
            f"**Effective policy risk:** "
            f"{result.get('effective_risk_level', 'pending')}"
        )

        with st.expander("Remediation steps and rollback plan"):
            for step in plan.get("steps", []):
                st.write(f"- {step}")
            st.write("**Rollback plan**")
            st.write(plan.get("rollback_plan", ""))

    if result.get("validation_summary"):
        st.markdown("### Validation")
        st.write(result["validation_summary"])

    if result.get("communication_update"):
        st.markdown("### Stakeholder update")
        st.info(result["communication_update"])

    if result.get("technical_update"):
        with st.expander("Technical status update"):
            st.write(result["technical_update"])

    if result.get("postmortem"):
        st.markdown("### Final postmortem")
        st.markdown(result["postmortem"])

    render_trace(result)


st.title("AI Incident Response & Root-Cause Analysis")
st.caption(
    "LangGraph demo with 10 AI agents, conditional routing, cycles, "
    "tool-style evidence collection, validation loops, and human approval."
)

if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
    st.error(
        "No Gemini API key found. Copy `.env.example` to `.env` and add "
        "`GOOGLE_API_KEY=...` before running the application."
    )
    st.stop()


scenario_options = list_scenarios()
scenario_ids = [item[0] for item in scenario_options]
scenario_titles = {item[0]: item[1] for item in scenario_options}

selected_id = st.selectbox(
    "Choose a simulated production incident",
    options=scenario_ids,
    format_func=lambda value: scenario_titles[value],
)

scenario = public_scenario(selected_id)

st.markdown("### Incident report")
st.write(scenario["description"])

with st.expander("Initial telemetry available to the agents"):
    st.json(scenario["initial_evidence"])

col_start, col_reset = st.columns([3, 1])

with col_start:
    if st.button(
        "Start LangGraph investigation",
        type="primary",
        use_container_width=True,
    ):
        thread_id = f"incident-{uuid.uuid4()}"
        config = {
            "configurable": {"thread_id": thread_id},
            "recursion_limit": 50,
        }

        with st.spinner("Agents are investigating the incident..."):
            result = graph.invoke(
                make_initial_state(selected_id),
                config=config,
            )

        st.session_state["incident_thread_id"] = thread_id
        st.session_state["incident_config"] = config
        st.session_state["incident_result"] = result

with col_reset:
    if st.button("Reset", use_container_width=True):
        for key in [
            "incident_thread_id",
            "incident_config",
            "incident_result",
        ]:
            st.session_state.pop(key, None)
        st.rerun()


result = st.session_state.get("incident_result")
interrupt_payload = current_interrupt(result)

if interrupt_payload:
    st.warning("Human approval is required before the workflow can continue.")
    st.json(interrupt_payload)

    approve_col, reject_col = st.columns(2)

    with approve_col:
        if st.button(
            "Approve remediation",
            type="primary",
            width=True,
        ):
            config = st.session_state["incident_config"]

            with st.spinner("Resuming the LangGraph workflow..."):
                resumed = graph.invoke(
                    Command(resume=True),
                    config=config,
                )

            st.session_state["incident_result"] = resumed
            st.rerun()

    with reject_col:
        if st.button(
            "Reject remediation",
            width=True,
        ):
            config = st.session_state["incident_config"]

            with st.spinner("Closing the workflow without applying the fix..."):
                resumed = graph.invoke(
                    Command(resume=False),
                    config=config,
                )

            st.session_state["incident_result"] = resumed
            st.rerun()


if result:
    render_state(result)


with st.sidebar:
    st.header("LangGraph concepts")

    st.markdown(
        """
**10 AI agents**
1. Incident Intake
2. Severity
3. Observability
4. Dependency
5. Root Cause
6. Investigation
7. Remediation
8. Validation
9. Communication
10. Postmortem

**Conditional decisions**
- Critical incident escalation
- Evidence sufficient?
- High-risk remediation?
- Human approval?
- Validation successful?

**Cycles**
- Weak evidence → collect evidence → re-analyze
- Failed validation → root-cause investigation again

**Human-in-the-loop**
- High-risk remediation pauses with `interrupt()`
- Resume with `Command(resume=True/False)`
"""
    )

    with st.expander("Generated Mermaid graph"):
        try:
            st.code(graph.get_graph().draw_mermaid(), language="text")
        except Exception as exc:
            st.write(f"Graph visualization unavailable: {exc}")
