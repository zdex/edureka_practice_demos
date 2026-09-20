Prerequisites
Before setting up the project, ensure you have the following installed:

Python 3.8 or higher
pip (Python package manager)

Setup Instructions
1. Download and Extract the Project Files
Obtain the project files (e.g., via a provided zip file or direct download) and extract them to a directory on your local machine. Navigate to the project directory:
cd path/to/insightpulse

2. Create a Virtual Environment
Set up a virtual environment to manage dependencies:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

3. Install Dependencies
Install the required Python packages listed in requirements.txt:
pip install -r requirements.txt

The requirements.txt file includes:

llama-index
pandas
google-generativeai
python-dotenv

4. Set Up Environment Variables
Create a .env file in the project root directory and add your Google API key for Gemini/Groq models API Key


## Project Structure
it_helpdesk_agent/
├── level0.py│
├── level_1_basic_chatbot.py
├── level_2_memory_chatbot.py
├── level_3_pdf_rag.py
├── level_4_csv_retrieval.py
├── level_5_sqlite_ticket_db.py
├── level_6_decision_node.py
├── level_7_escalation_workflow.py
│
├── data/
│   ├── it_policy.pdf
│   ├── helpdesk_kb.csv
│   └── tickets.db
│
├── requirements.txt
└── README.md


## Workshop Flow
### Level 1: Basic Chatbot
Learners see a simple IT assistant.
# Level 1: IT Helpdesk Chatbot with Chat Interface and Memory

This project demonstrates a simple IT Helpdesk chatbot using:

- Streamlit for the user interface
- Groq LLM for generating responses
- Session state for remembering the current conversation
- Chat-style input and output

## What This App Does
Example:

User: My laptop is slow.
Bot: Please restart your laptop and check startup apps.
Purpose: explain LLM input-output.

# Level 2: Add Memory
The bot remembers previous messages.
Level 2: IT Helpdesk Chatbot with Memory

This project demonstrates an IT Helpdesk chatbot using:

Streamlit chat interface
Groq LLM for generating responses
Session state for remembering the current conversation
Chat-style input and output
What This App Does

The user can continue a conversation with the chatbot.

The chatbot remembers earlier messages during the same session.

Example:

User: VPN is not working
Bot: Are you working from home or office?
User: From home
Bot: Since you are working from home, please check your internet connection, VPN client, and MFA approval.

# Level 3: Add PDF RAG
The bot answers from an IT policy PDF.
Level 3: IT Helpdesk Chatbot with PDF RAG

This project demonstrates a PDF-based RAG chatbot using:

Streamlit for the user interface
PDF upload
Document loading
Text chunking
Embeddings
Vector search
Groq LLM for final response generation
What This App Does

The user uploads an IT policy PDF and asks questions from that document.
The chatbot retrieves relevant PDF sections and answers based on the document.

Example:

User: What is the password reset process?
Bot: According to the uploaded IT policy, users must reset their password through the approved password portal or contact IT support if access is blocked.

# Level 4: Add CSV Retrieval
The bot retrieves issue-solution pairs from CSV.
Level 4: IT Helpdesk Chatbot with CSV Retrieval

This project demonstrates retrieval from a structured CSV knowledge base using:

Streamlit for the user interface
CSV upload
Pandas for reading tabular data
Groq LLM for matching the issue with the best solution
What This App Does

The user uploads a CSV file containing common IT issues and solutions.
The chatbot checks the CSV knowledge base and suggests the most relevant solution
Example CSV:
csv
issue,category,solution,escalation_required
VPN not connecting,Network,Restart VPN client and check MFA,No
Laptop overheating,Hardware,Check vents and raise hardware ticket,Yes
Outlook not opening,Email,Open Outlook in safe mode and clear cache,No
Purpose: explain structured knowledge base retrieval.

# Level 5: Add SQLite Ticket Database
The bot checks ticket status.
## Level 5: IT Helpdesk Chatbot with SQLite Ticket Database
This project demonstrates a database-backed IT helpdesk chatbot using:

Streamlit for the user interface
SQLite3 for storing ticket records
Groq LLM for explaining ticket status
Simple ticket creation and ticket lookup
What This App Does

The user can check the status of an existing ticket or create a new ticket.

Example:
User: Check ticket 1001
Bot: Ticket 1001 is currently open and assigned to the Network Team.

# Level 6: Add Decision Node
The agent decides which tool to use.

If policy question → PDF RAG
If issue troubleshooting → CSV KB
If ticket status → SQLite
If unclear → ask follow-up question
## Level 6: IT Helpdesk Agent with Decision Node
This project demonstrates basic Agentic AI using:

    Streamlit for the user interface
    LangGraph for workflow design
    Groq LLM for query classification
    Decision node for routing
    SQLite ticket lookup
    Troubleshooting knowledge base
    General IT response node

What This App Does
    The agent decides which path to use based on the user query.

It can route the query to:
    Ticket status
    Troubleshooting
    Policy
    General IT support

Example:
User: Check ticket 1002
Agent route: Ticket status
Bot: Ticket 1002 is in progress and assigned to the Hardware Team.

Example:
User: VPN is not connecting
Agent route: Troubleshooting
Bot: Restart the VPN client, check internet connection, and verify MFA approval.

# Level 7: Add Escalation Workflow
The agent decides when to hand over to human support.

Escalate when:    
    Issue is critical
    No answer found
    User says issue is unresolved
    Hardware replacement is needed
    Access/security issue is involved

Purpose: explain real-world Agentic AI governance.
Level 7: IT Helpdesk Agent with Escalation Workflow

This project demonstrates a more complete Agentic AI workflow using:

Streamlit for the user interface
LangGraph for agent workflow
Groq LLM for classification and response generation
Multi-tool decision making
SQLite ticket database
Troubleshooting knowledge base
Escalation workflow
What This App Does

The agent decides whether to answer directly or escalate the issue to human support.

It can handle:
    Ticket status queries
    Troubleshooting issues
    Policy questions
    General IT questions
    Critical issues needing escalation

# Multi-tool Decision Making

Final agent behavior:
| User Query                      | Tool Used           |
| ------------------------------- |-------------------- |
| “How do I reset my password?”   | PDF RAG             |
| “VPN is not connecting”         | CSV Retrieval       |
| “Check ticket 1004”             | SQLite              |
| “It is still not working”       | Memory + Escalation |
| “My laptop has a burning smell” | Escalation Workflow |