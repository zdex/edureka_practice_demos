#Import the required libraries
#streamlit creates the web page.
#dotenv loads the API key from the .env file.
#ChatGroq connects our Python app to the LLM.
import os
import streamlit as st
from dotenv import load_dotenv
from langchain_groq import ChatGroq


load_dotenv()  #Load the API key
GROQ_MODEL = os.getenv("GROQ_MODEL")

#Create the LLM
llm = ChatGroq(model=GROQ_MODEL, temperature=0.3)

#Create the Streamlit screen
st.title("Level 1: Basic IT Helpdesk Chatbot")

user_input = st.text_input("Describe your IT issue:")
#Send the question to AI
if st.button("Ask"):
    if user_input:
        prompt = f"""
        You are a helpful IT helpdesk assistant.
        Give a simple and practical answer.

        User issue: {user_input}
        """

        response = llm.invoke(prompt)
        st.write(response.content)
    #llm.invoke sends the prompt to the model. 
    # response.content contains the AI answer.
    # st.write displays the answer on the page.