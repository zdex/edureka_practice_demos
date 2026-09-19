import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.2)

st.title("Level 4: IT Helpdesk with CSV Retrieval")

uploaded_csv = st.file_uploader("Upload helpdesk_kb.csv", type=["csv"])

if uploaded_csv:
    df = pd.read_csv(uploaded_csv)
    st.dataframe(df)

    user_issue = st.text_input("Describe your IT issue:")

    if st.button("Find Solution"):
        if user_issue:
            kb_text = df.to_string(index=False)

            prompt = f"""
            You are an IT helpdesk assistant.

            Use the CSV knowledge base below to find the most relevant solution.
            If the issue is not available in the CSV, say that no matching solution was found.

            CSV Knowledge Base:
            {kb_text}

            User issue:
            {user_issue}

            Give:
            1. Most likely issue category
            2. Suggested solution
            3. Whether escalation is required
            """

            response = llm.invoke(prompt)
            st.write(response.content)