import streamlit as st
import sqlite3
import pandas as pd
from typing import TypedDict
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END

# ---------------- PAGE SETUP ----------------

st.set_page_config(
    page_title="IT Helpdesk Agent",
    layout="wide"
)

load_dotenv()

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.2)

st.title("Level 6: IT Helpdesk Agent with Decision Node")

st.write(
    "Ask about ticket status, troubleshooting, IT policy, or any general IT helpdesk question."
)

# ---------------- SESSION STATE ----------------

if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------- STATE STRUCTURE ----------------

class HelpdeskState(TypedDict):
    user_input: str
    route: str
    response: str

# ---------------- AGENT NODES ----------------

def classify_query(state: HelpdeskState):
    user_input = state["user_input"]

    prompt = f"""
    Classify the user query into one of these routes:

    ticket_status
    troubleshooting
    policy
    general

    User query:
    {user_input}

    Return only one route name.
    """

    route = llm.invoke(prompt).content.strip().lower()

    return {"route": route}


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

    user_input = state["user_input"]

    cursor.execute("SELECT * FROM tickets")
    tickets = cursor.fetchall()

    prompt = f"""
    You are an IT helpdesk assistant.

    The user asked:
    {user_input}

    Ticket database:
    {tickets}

    Answer the ticket-related question in simple language.
    If the ticket number is not available, ask the user to provide the request number.
    """

    response = llm.invoke(prompt).content

    conn.close()

    return {"response": response}


def troubleshooting_node(state: HelpdeskState):
    data = {
        "issue": ["VPN not connecting", "Laptop slow", "Outlook not opening"],
        "solution": [
            "Restart VPN client, check internet, and verify MFA.",
            "Restart laptop, close unused apps, and check startup programs.",
            "Open Outlook in safe mode and clear cache."
        ],
        "escalation_required": ["No", "No", "No"]
    }

    df = pd.DataFrame(data)

    prompt = f"""
    You are an IT helpdesk assistant.

    Use this troubleshooting knowledge base:
    {df.to_string(index=False)}

    User issue:
    {state["user_input"]}

    Give a simple answer with:
    1. Most likely issue
    2. Suggested solution
    3. Whether escalation is required

    If the issue is not found, say that no matching solution was found.
    """

    response = llm.invoke(prompt).content

    return {"response": response}


def policy_node(state: HelpdeskState):
    prompt = f"""
    You are answering a general IT policy question.

    Give a safe and practical answer.
    Do not invent company-specific policy details.

    Question:
    {state["user_input"]}
    """

    response = llm.invoke(prompt).content

    return {"response": response}


def general_node(state: HelpdeskState):
    prompt = f"""
    You are a helpful IT helpdesk assistant.

    Answer the user query in simple language.

    User:
    {state["user_input"]}
    """

    response = llm.invoke(prompt).content

    return {"response": response}


# ---------------- ROUTING LOGIC ----------------

def route_decision(state: HelpdeskState):
    route = state["route"]

    if "ticket" in route:
        return "ticket_status"
    elif "troubleshooting" in route:
        return "troubleshooting"
    elif "policy" in route:
        return "policy"
    else:
        return "general"


# ---------------- LANGGRAPH SETUP ----------------

graph = StateGraph(HelpdeskState)

graph.add_node("classify_query", classify_query)
graph.add_node("ticket_status", ticket_status_node)
graph.add_node("troubleshooting", troubleshooting_node)
graph.add_node("policy", policy_node)
graph.add_node("general", general_node)

graph.set_entry_point("classify_query")

graph.add_conditional_edges(
    "classify_query",
    route_decision,
    {
        "ticket_status": "ticket_status",
        "troubleshooting": "troubleshooting",
        "policy": "policy",
        "general": "general"
    }
)

graph.add_edge("ticket_status", END)
graph.add_edge("troubleshooting", END)
graph.add_edge("policy", END)
graph.add_edge("general", END)

app = graph.compile()

# ---------------- SIDEBAR ----------------

with st.sidebar:
    st.header("Sample Questions")

    st.write("Try these:")

    st.markdown("""
    - What is the status of ticket 1001?
    - My VPN is not connecting.
    - My laptop is very slow.
    - What should I do if I forgot my password?
    - What is the IT policy for using personal devices?
    """)

    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# ---------------- DISPLAY OLD CHAT ----------------

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

        if message["role"] == "assistant" and "route" in message:
            with st.expander("Agent decision details"):
                st.write("Selected route:", message["route"])

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
        with st.spinner("Agent is thinking..."):
            result = app.invoke({
                "user_input": user_input,
                "route": "",
                "response": ""
            })

            bot_reply = result["response"]
            selected_route = result["route"]

        st.write(bot_reply)

        with st.expander("Agent decision details"):
            st.write("Selected route:", selected_route)

    st.session_state.messages.append({
        "role": "assistant",
        "content": bot_reply,
        "route": selected_route
    })