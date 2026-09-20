import streamlit as st
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.3)

st.title("Level 1: Basic IT Helpdesk Chatbot")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

user_input = st.chat_input("Describe your IT issue...")
if user_input:
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.write(user_input)

    history_text = ""

    for msg in st.session_state.messages:
        history_text += f"{msg['role']}: {msg['content']}\n"

    prompt = f"""
    You are an IT Helpdesk Assistant.

    Use the full conversation history to answer the user.
    If the user gives a follow-up answer, connect it to the previous issue.

    Conversation history:
    {history_text}

    Latest user message:
    {user_input}
    """

    with st.spinner("Thninking about the conversation and preparing the response..."):
        response = llm.invoke(prompt)
        bot_reply = response.content

    st.session_state.messages.append({
        "role": "assistant",
        "content": bot_reply
    })

    with st.spinner("Checking the conversation and preparing the response..."):
        with st.chat_message("assistant"):
            st.write(bot_reply)

if st.button("Clear Chat"):
    st.session_state.messages = []
    st.rerun()