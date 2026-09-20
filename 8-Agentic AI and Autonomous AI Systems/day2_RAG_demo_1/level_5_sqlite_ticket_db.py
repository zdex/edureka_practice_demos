import streamlit as st
import sqlite3
from dotenv import load_dotenv
from langchain_groq import ChatGroq

st.set_page_config(
    page_title="IT Helpdesk Ticket System",
    layout="wide"
)

load_dotenv()

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.2)

st.title("Level 5: IT Helpdesk with SQLite Ticket Database")

conn = sqlite3.connect("tickets.db", check_same_thread=False)
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
(1002, 'Anita', 'Laptop overheating', 'In Progress', 'Hardware Team'),
(1003, 'Meera', 'Outlook not opening', 'Closed', 'Email Support')
""")

conn.commit()

left_col, divider_col, right_col = st.columns([1, 0.05, 1])

with left_col:
    st.subheader("Check Request Status")

    request_number = st.text_input("Enter your request number:")

    if st.button("Check Status"):
        if request_number:
            cursor.execute(
                "SELECT * FROM tickets WHERE ticket_id = ?",
                (request_number,)
            )

            ticket = cursor.fetchone()

            if ticket:
                prompt = f"""
                Explain this IT support request status in simple language.

                Request details:
                Request Number: {ticket[0]}
                User: {ticket[1]}
                Issue: {ticket[2]}
                Status: {ticket[3]}
                Assigned Team: {ticket[4]}
                """

                response = llm.invoke(prompt)
                st.info(response.content)
            else:
                st.warning("No request found with this number.")
        else:
            st.warning("Please enter your request number.")

with divider_col:
    st.markdown(
        """
        <div style="
            border-left: 2px solid #cccccc;
            height: 500px;
            margin: 10px auto;
        "></div>
        """,
        unsafe_allow_html=True
    )

with right_col:
    st.subheader("Create New Support Request")

    name = st.text_input("Your name")
    issue = st.text_area("Describe your issue")

    if st.button("Submit Request"):
        if name and issue:
            cursor.execute("""
            INSERT INTO tickets (user_name, issue, status, assigned_team)
            VALUES (?, ?, ?, ?)
            """, (name, issue, "Open", "Service Desk"))

            conn.commit()

            new_request_number = cursor.lastrowid

            st.success("Your support request has been created successfully.")
            st.info(f"Your request number is: {new_request_number}")
            st.write("Please save this number. You can use it later to check the status of your request.")
        else:
            st.warning("Please enter your name and issue description.")