import streamlit as st
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.3)

st.title("Level 2: IT Helpdesk Chatbot with Memory")

# Create memory
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input box at bottom
user_input = st.chat_input("Describe your IT issue...")

if user_input:
    # Add user message to memory
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    # Display user message
    with st.chat_message("user"):
        st.write(user_input)

    # Convert chat history into text for the LLM
    history_text = ""

    for msg in st.session_state.messages:
        history_text += f"{msg['role']}: {msg['content']}\n"

    prompt = f"""
    You are an IT Helpdesk Assistant.

    Use the full conversation history to answer the user.
    If the user gives a follow-up answer, connect it to the previous issue.
    Ask a follow-up question if important details are missing.

    Conversation history:
    {history_text}

    Latest user message:
    {user_input}
    """

    # Show waiting message while bot is thinking
    with st.chat_message("assistant"):
        with st.spinner("Checking the previous conversation and preparing the response..."):
            response = llm.invoke(prompt)
            bot_reply = response.content

        st.write(bot_reply)

    # Add assistant reply to memory
    st.session_state.messages.append({
        "role": "assistant",
        "content": bot_reply
    })

# Clear chat button
if st.button("Clear Chat"):
    st.session_state.messages = []
    st.rerun()