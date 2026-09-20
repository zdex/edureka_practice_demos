Components

1. server.py: A FastAPI server that hosts a joke generator using LangChain's components
2. client.py: A command-line client that connects to the server and generates jokes


Requirements
pip install langchain langchain-google-genai fastapi uvicorn langserve sse_starlette

Running the Demo

Start the server:
python server.py

Deploy in Playground:
http://localhost:8000/joke-generator/playground/

In a separate cmd, run the client:
python client.py --topic programming

Try different topics:
python client.py --topic food
python client.py --topic sports
python client.py --topic space

You can also explore the API directly in your browser:
http://localhost:8000/docs

How It Works
This demo showcases the core principles of LangChain and LangServe:

Chains: Connecting prompts, models, and parsers
Deployment: Using FastAPI and LangServe to expose chains as API endpoints
Client: Using RemoteRunnable to interact with the deployed chains