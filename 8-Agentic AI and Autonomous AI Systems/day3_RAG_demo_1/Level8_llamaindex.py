import streamlit as st
import sqlite3
import pandas as pd
import os
from typing import TypedDict
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.llms.groq import Groq
from llama_index.embeddings.huggingface import HuggingFaceEmbedding


# ---------------- PAGE SETUP ----------------

st.set_page_config(
    page_title="Level 8 IT Helpdesk Agent",
    layout="wide"
)

load_dotenv()

st.title("Level 8: IT Helpdesk Agent with LlamaIndex RAG")
st.write("Upload an IT policy document and ask ticket, troubleshooting, policy, or escalation questions.")


# ---------------- LLM + EMBEDDING SETUP ----------------

Settings.llm = Groq(
    model="llama-3.1-8b-instant",
    temperature=0.2
)

Settings.embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


# ---------------- SESSION MEMORY ----------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "query_engine" not in st.session_state:
    st.session_state.query_engine = None


# ---------------- DOCUMENT UPLOAD ----------------

uploaded_file = st.file_uploader(
    "Upload IT policy document",
    type=["pdf", "txt", "docx"]
)

if uploaded_file and st.session_state.query_engine is None:
    os.makedirs("uploaded_docs", exist_ok=True)

    file_path = os.path.join("uploaded_docs", uploaded_file.name)

    with st.spinner("Reading and indexing document with LlamaIndex..."):
        with open(file_path, "wb") as f:
            f.write(uploaded_file.read())

        documents = SimpleDirectoryReader("uploaded_docs").load_data()

        index = VectorStoreIndex.from_documents(documents)

        st.session_state.query_engine = index.as_query_engine(
            similarity_top_k=3
        )

    st.success("Document indexed successfully. You can now ask policy questions.")


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
    policy_document
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

    route = Settings.llm.complete(prompt).text.strip().lower()

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

    response = Settings.llm.complete(prompt).text
    conn.close()

    return {
        "response": response,
        "escalation_required": "No"
    }


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
    Use this troubleshooting knowledge base:
    {df.to_string(index=False)}

    User issue:
    {state["user_input"]}

    Give:
    1. Best solution
    2. Is escalation required? Answer Yes or No.
    """

    response = Settings.llm.complete(prompt).text
    escalation_required = "Yes" if "yes" in response.lower() else "No"

    return {
        "response": response,
        "escalation_required": escalation_required
    }


def policy_document_node(state: HelpdeskState):
    if st.session_state.query_engine is None:
        return {
            "response": "Please upload an IT policy document first. I need the document before I can answer policy questions.",
            "escalation_required": "No"
        }

    response = st.session_state.query_engine.query(state["user_input"])

    escalation_required = "Yes" if any(
        word in state["user_input"].lower()
        for word in ["breach", "hacked", "security", "unauthorized", "data loss"]
    ) else "No"

    return {
        "response": str(response),
        "escalation_required": escalation_required
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


def general_node(state: HelpdeskState):
    prompt = f"""
    You are an IT helpdesk assistant.
    Give a helpful answer in simple language.

    User:
    {state["user_input"]}
    """

    response = Settings.llm.complete(prompt).text

    return {
        "response": response,
        "escalation_required": "No"
    }


# ---------------- ROUTING ----------------

def route_decision(state: HelpdeskState):
    route = state["route"]

    if "ticket" in route:
        return "ticket_status"
    elif "troubleshooting" in route:
        return "troubleshooting"
    elif "policy" in route or "document" in route:
        return "policy_document"
    elif "escalation" in route:
        return "escalation"
    else:
        return "general"


# ---------------- GRAPH ----------------

graph = StateGraph(HelpdeskState)

graph.add_node("classify_query", classify_query)
graph.add_node("ticket_status", ticket_status_node)
graph.add_node("troubleshooting", troubleshooting_node)
graph.add_node("policy_document", policy_document_node)
graph.add_node("escalation", escalation_node)
graph.add_node("general", general_node)

graph.set_entry_point("classify_query")

graph.add_conditional_edges(
    "classify_query",
    route_decision,
    {
        "ticket_status": "ticket_status",
        "troubleshooting": "troubleshooting",
        "policy_document": "policy_document",
        "escalation": "escalation",
        "general": "general"
    }
)

graph.add_edge("ticket_status", END)
graph.add_edge("troubleshooting", END)
graph.add_edge("policy_document", END)
graph.add_edge("escalation", END)
graph.add_edge("general", END)

app = graph.compile()


# ---------------- SIDEBAR ----------------

with st.sidebar:
    st.header("Try these questions")

    st.markdown("""
    **Ticket Status**
    - What is the status of ticket 1001?

    **Troubleshooting**
    - My VPN is not connecting.

    **Policy Document**
    - What is the leave policy?
    - What are the laptop usage rules?

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