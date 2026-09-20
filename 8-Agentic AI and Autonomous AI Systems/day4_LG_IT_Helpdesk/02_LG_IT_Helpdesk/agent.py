import sqlite3
from typing import TypedDict, Annotated
from operator import add
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver

load_dotenv()

class HelpdeskState(TypedDict):
    user_issue: str
    chat_history: Annotated[list, add]
    category: str
    response: str
    ticket_required: bool

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0.2
)

conn = sqlite3.connect("helpdesk_memory.sqlite", check_same_thread=False)
memory = SqliteSaver(conn)


def classify_issue(state: HelpdeskState):
    issue = state["user_issue"].lower()

    if "password" in issue or "login" in issue:
        category = "Password / Login Issue"
    elif "wifi" in issue or "internet" in issue or "network" in issue:
        category = "Internet / Network Issue"
    elif "email" in issue or "outlook" in issue:
        category = "Email Issue"
    elif "software" in issue or "install" in issue:
        category = "Software Request"
    else:
        category = "General IT Issue"

    return {"category": category}


def decide_ticket(state: HelpdeskState):
    issue = state["user_issue"].lower()

    urgent_words = [
        "urgent",
        "not working",
        "cannot work",
        "blocked",
        "critical",
        "still not working"
    ]

    ticket_required = any(word in issue for word in urgent_words)

    return {"ticket_required": ticket_required}


def generate_response(state: HelpdeskState):
    history_text = ""

    for message in state.get("chat_history", []):
        role = message.get("role", "")
        content = message.get("content", "")
        history_text += f"{role}: {content}\n"

    prompt = f"""
You are a basic IT helpdesk support agent.

Previous conversation:
{history_text}

Latest user issue:
{state['user_issue']}

Issue category:
{state['category']}

Ticket required:
{state['ticket_required']}

Use the previous conversation to understand context.
Do not ask again for information the user has already provided.
Give a simple and helpful IT support response.
If its not IT related question please apologies and inform that you are an IT helpdesk agent.
"""

    answer = llm.invoke(prompt).content

    return {
        "response": answer,
        "chat_history": [
            {
                "role": "assistant",
                "content": answer
            }
        ]
    }


builder = StateGraph(HelpdeskState)

builder.add_node("classify_issue", classify_issue)
builder.add_node("decide_ticket", decide_ticket)
builder.add_node("generate_response", generate_response)

builder.add_edge(START, "classify_issue")
builder.add_edge("classify_issue", "decide_ticket")
builder.add_edge("decide_ticket", "generate_response")
builder.add_edge("generate_response", END)

graph = builder.compile(checkpointer=memory)

def run_helpdesk_agent(user_issue, thread_id="employee_001"):
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    input_state = {
        "user_issue": user_issue,
        "chat_history": [
            {
                "role": "user",
                "content": user_issue
            }
        ]
    }

    result = graph.invoke(input_state, config=config)

    return result