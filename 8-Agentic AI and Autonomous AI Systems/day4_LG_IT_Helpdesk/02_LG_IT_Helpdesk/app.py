import streamlit as st
from agent import run_helpdesk_agent
from langgraph.checkpoint.sqlite import SqliteSaver

#from main import run_helpdesk_bot
# ---------------------------------------------------------
# Page Setup
# ---------------------------------------------------------
st.set_page_config(
    page_title="IT Helpdesk Chatbot",
    layout="wide"
)

# ---------------------------------------------------------
# Session State
# ---------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_result" not in st.session_state:
    st.session_state.last_result = None

# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------
with st.sidebar:
    st.header("IT Helpdesk Bot")

    thread_id = st.text_input(
        "Thread ID",
        value="employee_001"
    )

    st.caption(
        "Use the same Thread ID to keep memory connected."
    )

    st.divider()

    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.session_state.last_result = None
        st.rerun()

    st.divider()

    st.header("Agent State")

    if st.session_state.last_result:
        result = st.session_state.last_result

        st.write(
            "**Issue Category:**",
            result.get("category", "")
        )

        st.write(
            "**Ticket Required:**",
            result.get("ticket_required", False)
        )

        st.divider()

        st.header("Memory")

        history = result.get("chat_history", [])

        if history:
            for msg in history:
                st.write(
                    f"**{msg.get('role', '')}:** {msg.get('content', '')}"
                )
        else:
            st.write("No memory available.")
    else:
        st.write("No agent state yet.")

# ---------------------------------------------------------
# Main Page
# ---------------------------------------------------------
st.title("IT Helpdesk AI Support Agent")

st.caption(
    "A LangGraph + Streamlit chatbot that classifies IT issues, "
    "decides whether a support ticket is required, and remembers conversations."
)

# ---------------------------------------------------------
# Display Chat History
# ---------------------------------------------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ---------------------------------------------------------
# Chat Input
# ---------------------------------------------------------
user_message = st.chat_input(
    "Describe your IT issue..."
)

# ---------------------------------------------------------
# Process User Message
# ---------------------------------------------------------
if user_message:
    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_message
        }
    )

    with st.chat_message("user"):
        st.markdown(user_message)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Analyzing issue..."):

                result = run_helpdesk_agent(
                    user_issue=user_message,
                    thread_id=thread_id
                )

            st.session_state.last_result = result

            bot_response = result.get(
                "response",
                "No response generated."
            )

            st.markdown(bot_response)

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": bot_response
                }
            )

        except Exception as e:
            error_message = f"Error: {str(e)}"

            st.error(error_message)

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": error_message
                }
            )