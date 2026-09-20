# LangGraph AI Incident Response & Root-Cause Analysis

A complete educational LangGraph project demonstrating a **multi-agent incident-response workflow** with:

- 10 specialized AI agents
- sequential/continuous graph nodes
- multiple conditional branches
- investigation loops
- validation/retry loops
- shared graph state
- deterministic safety policies
- simulated observability tools
- human-in-the-loop approval using LangGraph `interrupt()`
- Streamlit UI
- Gemini through `langchain-google-genai`

> This project intentionally uses **simulated infrastructure data**. It never restarts services, changes databases, rolls back deployments, or modifies real production systems.

---

## 1. Use Case

A production application experiences an outage or severe degradation.

Example:

> Customers are reporting checkout failures. Payment API latency increased from around 300 ms to more than 5 seconds after a deployment, and roughly 40% of payments are failing.

Instead of giving the problem to one chatbot, LangGraph coordinates several specialized AI agents.

The workflow:

1. understands the incident;
2. determines severity;
3. analyzes telemetry;
4. checks dependencies;
5. proposes competing root-cause hypotheses;
6. tests whether the evidence is sufficient;
7. loops back to gather more evidence when necessary;
8. proposes remediation;
9. pauses for human approval when the action is high risk;
10. simulates applying the remediation;
11. validates the outcome;
12. loops back to root-cause analysis if validation fails;
13. produces stakeholder communication;
14. creates a final postmortem.

This makes the project a strong demonstration of **why LangGraph is useful instead of a simple linear LLM chain**.

---

## 2. The 10 AI Agents

| # | Agent | Responsibility |
|---|---|---|
| 1 | Incident Intake Agent | Converts the raw incident into symptoms, affected services, and suspected trigger |
| 2 | Severity Agent | Assesses business impact and classifies severity |
| 3 | Observability Agent | Interprets metrics, logs, anomalies, and recent changes |
| 4 | Dependency Agent | Determines whether upstream/downstream services are contributing |
| 5 | Root Cause Agent | Generates and ranks competing root-cause hypotheses |
| 6 | Investigation Agent | Challenges hypotheses and decides whether evidence is sufficient |
| 7 | Remediation Agent | Proposes the smallest reversible corrective action |
| 8 | Validation Agent | Determines whether the remediation actually resolved the incident |
| 9 | Communication Agent | Creates stakeholder and technical status updates |
| 10 | Postmortem Agent | Produces a concise blameless incident report |

The project also contains deterministic/tool-style nodes:

- Critical escalation policy
- Evidence collector
- Safety gate
- Human approval checkpoint
- Simulated remediation executor
- Rejection/cancellation node

---

## 3. LangGraph Architecture

```text
START
  |
  v
Incident Intake Agent
  |
  v
Severity Agent
  |
  +---------------------------+
  |                           |
Critical?                   Normal
  |                           |
  v                           |
Escalation Policy             |
  |                           |
  +------------+--------------+
               |
               v
      Observability Agent
               |
               v
       Dependency Agent
               |
               v
        Root Cause Agent
               |
               v
       Investigation Agent
               |
          Evidence enough?
          /             \
        NO               YES
        |                 |
        v                 v
Evidence Collector   Remediation Agent
        |                 |
        +------->          v
        Observability   Safety Gate
                         |
                    High risk?
                    /        \
                  YES         NO
                   |           |
                   v           |
            Human Approval     |
              /       \        |
          Approve    Reject    |
             |          |      |
             v          v      |
          Apply Fix   Cancel   |
             |          |      |
             v          |      |
        Validation Agent       |
             |                 |
        Resolved?              |
        /      \               |
      YES       NO             |
       |         |             |
       |         +----> Root Cause Agent
       |
       v
Communication Agent
       |
       v
Postmortem Agent
       |
       v
      END
```

---

## 4. LangGraph Concepts Demonstrated

### Sequential / continuous nodes

The normal investigation path is:

```text
Intake
  -> Severity
  -> Observability
  -> Dependency
  -> Root Cause
  -> Investigation
```

These are ordinary LangGraph edges.

### Conditional nodes

The application contains several decision points:

```text
Severity Agent
    -> critical? -> escalation
    -> otherwise -> observability
```

```text
Investigation Agent
    -> insufficient evidence -> collect more evidence
    -> sufficient evidence -> remediation
```

```text
Safety Gate
    -> high risk -> human approval
    -> low/medium risk -> simulated execution
```

```text
Human Approval
    -> approved -> apply fix
    -> rejected -> close unresolved
```

```text
Validation Agent
    -> resolved -> communication
    -> not resolved -> root-cause analysis again
```

### Cycles

Two important loops exist.

#### Evidence loop

```text
Root Cause
   -> Investigation
   -> Evidence insufficient
   -> Evidence Collector
   -> Observability
   -> Dependency
   -> Root Cause
```

#### Validation loop

```text
Remediation
   -> Apply Fix
   -> Validation
   -> Not resolved
   -> Root Cause
```

Maximum-round guardrails prevent infinite execution.

---

## 5. Human-in-the-Loop

High-risk remediation should not execute automatically.

The project uses LangGraph's current human-in-the-loop pattern:

```python
from langgraph.types import interrupt

decision = interrupt(
    {
        "question": "Approve the proposed high-risk remediation?",
        "proposed_action": "...",
    }
)
```

Execution pauses and state is retained by a LangGraph checkpointer.

The Streamlit application resumes the same graph thread using:

```python
from langgraph.types import Command

graph.invoke(
    Command(resume=True),
    config=config,
)
```

or:

```python
graph.invoke(
    Command(resume=False),
    config=config,
)
```

The same `thread_id` must be used when resuming.

---

## 6. Shared State

The agents communicate through one shared `IncidentState`.

Important state fields include:

```python
incident_description
severity
business_impact
observability_findings
healthy_dependencies
unhealthy_dependencies
hypotheses
leading_hypothesis
investigation_confidence
additional_evidence_needed
remediation_plan
effective_risk_level
approval_status
post_fix_evidence
resolved
validation_summary
communication_update
postmortem
trace
```

The shared state is what allows LangGraph to coordinate agents without each agent independently starting from zero.

---

## 7. Why Some Decisions Are Deterministic

A useful production architecture should **not make every control decision an LLM decision**.

For example, the Remediation Agent may estimate risk, but the project also has a deterministic `safety_gate_node`.

If the proposed action contains high-risk concepts such as:

- production rollback
- service restart
- database changes
- index changes
- failover
- certificate changes
- disabling a production capability

the graph requires human approval.

This demonstrates an important design principle:

> Use AI for interpretation and reasoning. Use deterministic policy for safety-critical control boundaries.

---

## 8. Simulated Tools and Infrastructure

The project contains three sample incidents:

1. Checkout failures after deployment
2. Database saturation after a new feature
3. Authentication outage after certificate rotation

`mock_data.py` acts like a fake operations environment.

It provides:

- metrics
- logs
- dependency health
- deployment/change evidence
- additional diagnostic evidence
- post-remediation telemetry

In a real enterprise implementation, these functions could be replaced with tools/connectors for:

- Datadog
- Grafana
- Prometheus
- CloudWatch
- Splunk
- Elasticsearch
- Kubernetes
- GitHub/GitLab
- ServiceNow
- PagerDuty
- a CMDB
- cloud provider APIs

The LangGraph structure can stay largely the same while the mock functions are replaced.

---

## 9. Project Structure

```text
langgraph_incident_response/
|
|-- app.py
|-- graph.py
|-- agents.py
|-- state.py
|-- mock_data.py
|-- requirements.txt
|-- .env.example
|-- .gitignore
`-- README.md
```

### `app.py`

Streamlit user interface.

Responsibilities:

- choose an incident scenario;
- start a LangGraph thread;
- display agent results;
- detect an interrupt;
- display approve/reject buttons;
- resume the interrupted graph;
- display the final postmortem and execution trace.

### `graph.py`

Defines the LangGraph topology.

Contains:

- `StateGraph`
- graph nodes
- normal edges
- conditional edges
- loop conditions
- `InMemorySaver` checkpointer

### `agents.py`

Contains the AI agents and supporting control nodes.

The Gemini agents use structured output so downstream graph decisions do not depend on parsing free-form prose.

### `state.py`

Defines `IncidentState`.

### `mock_data.py`

Contains the simulated incidents, telemetry, evidence collection, and simulated remediation outcomes.

---

## 10. Requirements

Recommended Python:

```text
Python 3.11+
```

Install:

```bash
pip install -U -r requirements.txt
```

`requirements.txt` contains:

```text
streamlit
langgraph
langchain-google-genai>=4.0.0
pydantic>=2.0
python-dotenv
typing-extensions
```

---

## 11. Gemini API Key

Copy the example environment file:

### Windows

```bash
copy .env.example .env
```

### macOS/Linux

```bash
cp .env.example .env
```

Open `.env` and set:

```text
GOOGLE_API_KEY=your_google_ai_studio_api_key
```

The project defaults to:

```text
GEMINI_MODEL=gemini-3.5-flash
```

If your Google AI account uses another available Gemini model, change the environment variable rather than editing the Python code.

---

## 12. Run the Application

From the project folder:

```bash
streamlit run app.py
```

Streamlit normally opens:

```text
http://localhost:8501
```

---

## 13. How to Demonstrate the Project

### Demo 1: Checkout incident

Select:

```text
Checkout failures after deployment
```

Click:

```text
Start LangGraph investigation
```

Watch the agents:

```text
Intake
-> Severity
-> Observability
-> Dependency
-> Root Cause
-> Investigation
```

If the Investigation Agent says evidence is insufficient, the graph automatically loops through:

```text
Evidence Collector
-> Observability
-> Dependency
-> Root Cause
-> Investigation
```

The Remediation Agent then proposes a fix.

The deterministic Safety Gate may classify the action as high risk.

The graph pauses.

The Streamlit page displays:

```text
Approve remediation
Reject remediation
```

Choose **Approve** to resume the graph.

The simulated fix is applied and the Validation Agent checks the before/after telemetry.

The final agents create:

- stakeholder status;
- technical status;
- postmortem.

### Demo 2: Reject the remediation

Run the workflow again and choose:

```text
Reject remediation
```

The graph follows a different path:

```text
Human Approval
-> Rejection Node
-> Communication
-> Postmortem
-> END
```

The postmortem correctly reports that the incident remains unresolved.

This is a useful way to demonstrate conditional workflow execution.

---

## 14. Structured AI Outputs

The project uses Gemini native structured output.

Example:

```python
class SeverityOutput(BaseModel):
    severity: Literal["low", "medium", "high", "critical"]
    impact_summary: str
    escalation_required: bool
    reasoning: str
```

The model is invoked using:

```python
structured = llm.with_structured_output(
    schema=SeverityOutput.model_json_schema(),
    method="json_schema",
)
```

This is preferable to asking the model to return arbitrary prose and manually parsing it.

---

## 15. Execution Trace

Every node appends an event to the shared `trace`.

Example:

```text
Incident Intake Agent    Incident normalized
Severity Agent           Severity = critical
Escalation Policy Node   Critical incident escalated
Observability Agent      Telemetry analyzed
Dependency Agent         Dependencies evaluated
Root Cause Agent         Leading hypothesis confidence = 72%
Investigation Agent      More evidence required
Evidence Collector       Additional evidence collected
...
```

The Streamlit UI displays the complete trace as a table.

This is particularly helpful when teaching LangGraph because learners can see **which node executed and why the graph took a particular branch**.

---

## 16. Production Architecture

This demo uses:

```text
InMemorySaver
```

for checkpointing.

That is appropriate for a local demonstration.

A production system should use persistent checkpointing and durable storage.

Potential production architecture:

```text
Incident Source
   |
   v
LangGraph Service
   |
   +--> Observability tools
   +--> Deployment tools
   +--> CMDB
   +--> Ticketing
   +--> PagerDuty
   |
   v
Persistent LangGraph Checkpointer
   |
   v
Human Incident Commander
```

Production requirements would also include:

- authentication;
- role-based authorization;
- secrets management;
- audit logs;
- durable checkpoints;
- incident isolation;
- approval policies;
- read-only diagnostics by default;
- idempotent tool execution;
- rate limits;
- monitoring of the AI workflow itself.

---

## 17. Important Safety Boundary

The supplied project is a **simulation**.

`apply_fix_node()` calls:

```python
simulate_fix(...)
```

It does not call Kubernetes, cloud APIs, databases, or shell commands.

This is intentional.

When moving toward a real implementation, keep diagnostic tools separate from state-changing tools and require explicit human approval before any consequential action.

---

## 18. Current LangGraph Patterns Used

The project uses the modern LangGraph Graph API concepts:

```python
StateGraph
START
END
add_edge()
add_conditional_edges()
```

For human-in-the-loop it uses:

```python
interrupt()
Command(resume=...)
InMemorySaver()
```

This follows the current LangGraph approach where an interrupt pauses graph execution, checkpointed state is retained, and the same thread is resumed with a `Command`.

Official references:

- https://docs.langchain.com/oss/python/langgraph/quickstart
- https://docs.langchain.com/oss/python/langgraph/graph-api
- https://docs.langchain.com/oss/python/langgraph/interrupts
- https://docs.langchain.com/oss/python/integrations/chat/google_generative_ai

---

## 19. Suggested Enhancements

Once the base project works, useful extensions include:

### Tool-calling agents

Give the Observability Agent tools such as:

```text
get_logs()
get_metrics()
get_recent_deployments()
get_dependency_health()
```

### Parallel branches

Run observability and dependency analysis concurrently.

### Incident memory

Store past incidents and retrieve similar postmortems.

### LangSmith

Add tracing and evaluation of agent decisions.

### Slack / Teams

Push approval requests and status updates to incident channels.

### ServiceNow / Jira

Automatically create and update incident tickets.

### Real observability platform

Replace `mock_data.py` with read-only production telemetry integrations.

---

## 20. Learning Outcomes

After completing this project, learners should understand:

- why LangGraph is useful for non-linear AI workflows;
- how multiple specialized agents share state;
- how to implement sequential nodes;
- how to implement conditional edges;
- how loops work in a graph;
- why loop termination conditions are important;
- how to pause and resume a graph;
- how human approval fits into agentic systems;
- why deterministic safety gates should complement LLM decisions;
- how to separate AI reasoning from actual infrastructure actions.

---

## 21. Core Takeaway

A linear LLM chain might do this:

```text
Incident -> Analyze -> Answer
```

This project does this:

```text
Incident
  -> specialized analysis
  -> branching
  -> evidence gathering
  -> hypothesis testing
  -> re-investigation
  -> remediation
  -> human approval
  -> validation
  -> retry when needed
  -> communication
  -> postmortem
```

That is the type of stateful, conditional, cyclic workflow LangGraph is designed to model.
