"""START
 → classify_issue
 → check_urgency
 → decide_human_handoff
 → conditional route
     → generate_bot_response
     OR
     → human_handoff_response
 → END
 """

import sqlite3
from typing import TypedDict, Annotated
from operator import add
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver

# ---------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------
# Define Agent State
# ---------------------------------------------------------
class HelpdeskState(TypedDict):
    user_message: str
    chat_history: Annotated[list, add]
    issue_category: str
    urgency_level: str
    handoff_required: bool
    bot_response: str


# ---------------------------------------------------------
# LLM
# ---------------------------------------------------------
llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0.2,
    max_tokens=250
)

# ---------------------------------------------------------
# SQLite Memory
# ---------------------------------------------------------
conn = sqlite3.connect("helpdesk_memory.sqlite", check_same_thread=False)
memory = SqliteSaver(conn)


# ---------------------------------------------------------
# Node 1: Classify Issue
# ---------------------------------------------------------
def classify_issue(state: HelpdeskState):
    message = state["user_message"].lower()

    if "password" in message or "login" in message:
        category = "Password / Login Issue"
    elif "wifi" in message or "internet" in message or "network" in message:
        category = "Network / Internet Issue"
    elif "email" in message or "outlook" in message:
        category = "Email Issue"
    elif "software" in message or "install" in message:
        category = "Software Request"
    elif "laptop" in message or "system" in message or "computer" in message:
        category = "Device Issue"
    else:
        category = "General IT Issue"

    return {
        "issue_category": category
    }


# ---------------------------------------------------------
# Node 2: Check Urgency
# ---------------------------------------------------------
def check_urgency(state: HelpdeskState):
    message = state["user_message"].lower()

    high_urgency_words = [
        "urgent",
        "critical",
        "cannot work",
        "blocked",
        "production down",
        "system down",
        "not working",
        "security breach",
        "data loss"
    ]

    medium_urgency_words = [
        "slow",
        "delay",
        "sometimes",
        "intermittent",
        "issue continues"
    ]

    if any(word in message for word in high_urgency_words):
        urgency = "High"
    elif any(word in message for word in medium_urgency_words):
        urgency = "Medium"
    else:
        urgency = "Low"

    return {
        "urgency_level": urgency
    }


# ---------------------------------------------------------
# Node 3: Decide Human Handoff
# ---------------------------------------------------------
def decide_human_handoff(state: HelpdeskState):
    message = state["user_message"].lower()

    handoff_keywords = [
        "security breach",
        "data loss",
        "payment system",
        "production down",
        "system down",
        "cannot work",
        "urgent",
        "critical",
        "manager",
        "human",
        "escalate"
    ]

    if state["urgency_level"] == "High":
        handoff_required = True
    elif any(word in message for word in handoff_keywords):
        handoff_required = True
    else:
        handoff_required = False

    return {
        "handoff_required": handoff_required
    }


# ---------------------------------------------------------
# Router Function
# ---------------------------------------------------------
def route_after_handoff_decision(state: HelpdeskState):
    if state["handoff_required"]:
        return "human_handoff_response"
    else:
        return "generate_bot_response"


# ---------------------------------------------------------
# Node 4A: Generate Normal Bot Response
# ---------------------------------------------------------
def generate_bot_response(state: HelpdeskState):
    history_text = ""

    for message in state.get("chat_history", []):
        role = message.get("role", "")
        content = message.get("content", "")
        history_text += f"{role}: {content}\n"

    prompt = f"""
You are a simple IT helpdesk chatbot.

Previous conversation:
{history_text}

Latest user message:
{state["user_message"]}

Issue category:
{state["issue_category"]}

Urgency level:
{state["urgency_level"]}

Handoff required:
{state["handoff_required"]}

Instructions:
- Give simple first-level IT support.
- Ask a follow-up question if required.
- Use previous conversation context.
- Do not ask for information already given by user please use your memory.
- Keep the response short and helpful.
"""

    answer = llm.invoke(prompt).content

    return {
        "bot_response": answer,
        "chat_history": [
            {
                "role": "assistant",
                "content": answer
            }
        ]
    }


# ---------------------------------------------------------
# Node 4B: Human Handoff Response
# ---------------------------------------------------------
def human_handoff_response(state: HelpdeskState):
    response = f"""
This issue looks urgent or complex.

Issue category: {state["issue_category"]}
Urgency level: {state["urgency_level"]}

I recommend handing this over to a human IT support engineer.

Please share:
1. Your employee ID
2. Device name or laptop number
3. Screenshot of the error, if available
4. Since when the issue started
"""

    return {
        "bot_response": response,
        "chat_history": [
            {
                "role": "assistant",
                "content": response
            }
        ]
    }


# ---------------------------------------------------------
# Build LangGraph
# ---------------------------------------------------------
builder = StateGraph(HelpdeskState)

builder.add_node("classify_issue", classify_issue)
builder.add_node("check_urgency", check_urgency)
builder.add_node("decide_human_handoff", decide_human_handoff)
builder.add_node("generate_bot_response", generate_bot_response)
builder.add_node("human_handoff_response", human_handoff_response)

builder.add_edge(START, "classify_issue")
builder.add_edge("classify_issue", "check_urgency")
builder.add_edge("check_urgency", "decide_human_handoff")

builder.add_conditional_edges(
    "decide_human_handoff",
    route_after_handoff_decision,
    {
        "generate_bot_response": "generate_bot_response",
        "human_handoff_response": "human_handoff_response"
    }
)

builder.add_edge("generate_bot_response", END)
builder.add_edge("human_handoff_response", END)

graph = builder.compile(checkpointer=memory)


# ---------------------------------------------------------
# Run Graph Once
# ---------------------------------------------------------
def run_helpdesk_bot(user_message, thread_id="terminal_user"):
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    input_state = {
        "user_message": user_message,
        "chat_history": [
            {
                "role": "user",
                "content": user_message
            }
        ]
    }

    result = graph.invoke(input_state, config=config)

    return result


# ---------------------------------------------------------
# Terminal Chat Loop
# ---------------------------------------------------------
def main():
    print("\n====================================")
    print(" IT Helpdesk Chatbot")
    print("====================================")
    print("Type your IT issue below.")
    print("Type 'no more questions' to stop.\n")

    thread_id = "terminal_user"

    while True:
        user_message = input("User: ")

        if user_message.lower().strip() in [
            "no more questions",
            "no more question",
            "stop",
            "exit",
            "quit",
            "bye"
        ]:
            print("\nBot: Thank you. The IT helpdesk chat is now closed.")
            break

        result = run_helpdesk_bot(
            user_message=user_message,
            thread_id=thread_id
        )

        print("\nBot:", result["bot_response"])

        print("\n--- Agent State ---")
        print("Issue Category:", result["issue_category"])
        print("Urgency Level:", result["urgency_level"])
        print("Human Handoff Required:", result["handoff_required"])

        print("-" * 50)


if __name__ == "__main__":
    main()