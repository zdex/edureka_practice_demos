import streamlit as st
import sqlite3
import pandas as pd
from typing import TypedDict
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END,START

# ---------------- PAGE SETUP ----------------

st.set_page_config(
    page_title="Level 7 IT Helpdesk Agent",
    layout="wide"
)

load_dotenv()

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.2)

st.title("Level 7: IT Helpdesk Agent with Escalation Workflow")
st.write("Ask about ticket status, troubleshooting, policy, or urgent issues that may need escalation.")

# ---------------- SESSION MEMORY ----------------

if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------- STATE ----------------

class HelpdeskState(TypedDict):
    user_input: str
    route: str
    response: str
    escalation_required: str

# ---------------- AGENT NODES ----------------

def classify_query(state: HelpdeskState):
    prompt = f"""
    Classify the query into one route:

    ticket_status
    troubleshooting
    policy
    escalation
    general

    Escalation examples:
    - laptop burning smell
    - data breach
    - account hacked
    - repeated failure
    - urgent business impact
    - hardware damage
    - security risk

    User query:
    {state["user_input"]}

    Return only one route name.
    """

    route = llm.invoke(prompt).content.strip().lower()
    return {"route": route}


def troubleshooting_node(state: HelpdeskState):
    df = pd.DataFrame({
        "issue": [
            "VPN not connecting",
            "Laptop slow",
            "Outlook not opening",
            "Printer not working"
        ],
        "solution": [
            "Restart VPN client, check internet, and verify MFA.",
            "Restart laptop, close unused apps, and check startup programs.",
            "Open Outlook in safe mode and clear cache.",
            "Check printer power, paper tray, and network connection."
        ],
        "escalation_required": ["No", "No", "No", "No"]
    })

    prompt = f"""
    Use this knowledge base:
    {df.to_string(index=False)}

    User issue:
    {state["user_input"]}

    Give:
    1. Best solution
    2. Is escalation required? Answer Yes or No.
    """

    response = llm.invoke(prompt).content
    escalation_required = "Yes" if "yes" in response.lower() else "No"

    return {
        "response": response,
        "escalation_required": escalation_required
    }


def ticket_status_node(state: HelpdeskState):
    conn = sqlite3.connect("tickets.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tickets (
        ticket_id INTEGER PRIMARY KEY,
        user_name TEXT,
        issue TEXT,
        status TEXT,
        assigned_team TEXT
    )
    """)

    cursor.execute("""
    INSERT OR IGNORE INTO tickets 
    (ticket_id, user_name, issue, status, assigned_team)
    VALUES
    (1001, 'Rahul', 'VPN not connecting', 'Open', 'Network Team'),
    (1002, 'Anita', 'Laptop overheating', 'In Progress', 'Hardware Team')
    """)

    conn.commit()

    cursor.execute("SELECT * FROM tickets")
    tickets = cursor.fetchall()

    prompt = f"""
    User query:
    {state["user_input"]}

    Ticket database:
    {tickets}

    Answer the ticket question in simple language.
    If the user has not given a request number, ask for it.
    """

    response = llm.invoke(prompt).content
    conn.close()

    return {
        "response": response,
        "escalation_required": "No"
    }


def policy_node(state: HelpdeskState):
    response = llm.invoke(f"""
    Answer this IT policy question carefully.
    If the question involves security, access rights, or compliance,
    recommend escalation to IT security.

    Question:
    {state["user_input"]}
    """).content

    escalation_required = "Yes" if any(
        word in state["user_input"].lower()
        for word in ["breach", "hacked", "security", "unauthorized", "data loss"]
    ) else "No"

    return {
        "response": response,
        "escalation_required": escalation_required
    }


def general_node(state: HelpdeskState):
    response = llm.invoke(f"""
    You are an IT helpdesk assistant.
    Give a helpful answer in simple language.

    User:
    {state["user_input"]}
    """).content

    return {
        "response": response,
        "escalation_required": "No"
    }


def escalation_node(state: HelpdeskState):
    response = f"""
    This issue should be escalated to a human IT support team.

    Reason:
    The issue may involve urgency, security risk, hardware damage, or repeated failure.

    User issue:
    {state["user_input"]}

    Recommended next step:
    Create a high-priority support ticket and assign it to the appropriate IT team.
    """

    return {
        "response": response,
        "escalation_required": "Yes"
    }

# ---------------- ROUTING ----------------

def route_decision(state: HelpdeskState):
    route = state["route"]

    if "ticket" in route:
        return "ticket_status"
    elif "troubleshooting" in route:
        return "troubleshooting"
    elif "policy" in route:
        return "policy"
    elif "escalation" in route:
        return "escalation"
    else:
        return "general"

# ---------------- GRAPH ----------------

graph = StateGraph(HelpdeskState)

graph.add_node("classify_query", classify_query)
graph.add_node("ticket_status", ticket_status_node)
graph.add_node("troubleshooting", troubleshooting_node)
graph.add_node("policy", policy_node)
graph.add_node("general", general_node)
graph.add_node("escalation", escalation_node)

graph.set_entry_point("classify_query")

graph.add_conditional_edges(
    "classify_query",
    route_decision,
    {
        "ticket_status": "ticket_status",
        "troubleshooting": "troubleshooting",
        "policy": "policy",
        "escalation": "escalation",
        "general": "general"
    }
)

graph.add_edge("ticket_status", END)
graph.add_edge("troubleshooting", END)
graph.add_edge("policy", END)
graph.add_edge("general", END)
graph.add_edge("escalation", END)

app = graph.compile()

# ---------------- SIDEBAR ----------------

with st.sidebar:
    st.header("Try these questions")

    st.markdown("""
    **Ticket Status**
    - What is the status of ticket 1001?

    **Troubleshooting**
    - My VPN is not connecting.
    - My printer is not working.

    **Escalation**
    - My account has been hacked.
    - My laptop has a burning smell.
    """)

    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# ---------------- OLD CHAT ----------------

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

        if message["role"] == "assistant":
            with st.expander("Agent decision details"):
                st.write("Selected Route:", message["route"])
                st.write("Escalation Required:", message["escalation_required"])

# ---------------- CHAT INPUT ----------------

user_input = st.chat_input("Ask your IT helpdesk question...")

if user_input:
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Agent is checking the best support path..."):
            result = app.invoke({
                "user_input": user_input,
                "route": "",
                "response": "",
                "escalation_required": "No"
            })

        bot_reply = result["response"]
        selected_route = result["route"]
        escalation_required = result["escalation_required"]

        st.write(bot_reply)

        if escalation_required == "Yes":
            st.error("Escalation Required: Yes")
        else:
            st.success("Escalation Required: No")

        with st.expander("Agent decision details"):
            st.write("Selected Route:", selected_route)
            st.write("Escalation Required:", escalation_required)

    st.session_state.messages.append({
        "role": "assistant",
        "content": bot_reply,
        "route": selected_route,
        "escalation_required": escalation_required
    })