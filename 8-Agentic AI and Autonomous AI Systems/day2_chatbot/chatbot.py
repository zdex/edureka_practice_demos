import streamlit as st
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativAI

load_dotenv()

#create a LLM

llm=ChatGoogleGenerativAI(
    model="gemini-3.5-flash-lite"
)

st.title("Level1 : Basic Chatbot")
st.write("Describe your IT problem you are facing and AI will assit you to solve it.")

user_input=st.text_input(
    "Describe your IT issue: "
)

if st.button("Ask"):
    if not user_input:
        st.warning("Please write your IT problem first for me to help you")
    else:
        prompt=f"""
        you are a helpful IT helpdesk assistant
        you help the user with simple, practical, and concise answer to the IT Problem the user is facing.
        If the issue is not IT related politely apologies and explain that you only help with IT issues
        if the User issue: {user_input} is IT related you guide with resolution.        
        """

        try:
            response=llm.invoke(prompt)
            st.subheader("Helpdesk Response: ")
            st.write(response.content)
        except Exception as e:
            st.error(f"error : {e}")
