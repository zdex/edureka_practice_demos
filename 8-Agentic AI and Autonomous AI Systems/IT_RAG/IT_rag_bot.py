import os

import streamlit as st
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.document_loaders import PyPDFLoader
#from langchain_pymupdf import PyMuPDFLoader

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings


# ------------------------------------------------------------
# App setup
# ------------------------------------------------------------

load_dotenv()

st.set_page_config(
    page_title="IT Policy RAG Chatbot",
    page_icon="📄",
    layout="centered",
)

st.title("📄 IT Policy RAG Chatbot")
st.write("Ask questions about the IT Policy document.")


# ------------------------------------------------------------
# Check API key
# ------------------------------------------------------------

if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
    st.error(
        "Google Gemini API key not found. "
        "Add GOOGLE_API_KEY=your_key_here to your .env file."
    )
    st.stop()


# ------------------------------------------------------------
# Gemini LLM
# ------------------------------------------------------------

llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite"
)


# ------------------------------------------------------------
# Embedding model
# ------------------------------------------------------------

@st.cache_resource
def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


# ------------------------------------------------------------
# Load PDF and build FAISS vector store
# ------------------------------------------------------------

@st.cache_resource
def load_vector_store(pdf_path: str):
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(
            f"{pdf_path} was not found. "
            "Place the PDF in the same folder as this Python file."
        )

    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )

    chunks = splitter.split_documents(documents)

    if not chunks:
        raise ValueError("No readable text was found in the PDF.")

    return FAISS.from_documents(
        documents=chunks,
        embedding=get_embeddings(),
    )


PDF_PATH = "IT_policy.pdf"

try:
    vector_store = load_vector_store(PDF_PATH)
except Exception as exc:
    st.error(f"Could not load the knowledge base: {exc}")
    st.stop()


# ------------------------------------------------------------
# Session chat memory
# ------------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []


# ------------------------------------------------------------
# Display previous messages
# ------------------------------------------------------------

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ------------------------------------------------------------
# User question
# ------------------------------------------------------------

user_question = st.chat_input("Ask a question about the IT Policy...")


# ------------------------------------------------------------
# RAG workflow
# ------------------------------------------------------------

if user_question:
    st.session_state.messages.append(
        {"role": "user", "content": user_question}
    )

    with st.chat_message("user"):
        st.markdown(user_question)

    # Retrieve the most relevant chunks from the PDF.
    docs = vector_store.similarity_search(
        user_question,
        k=4,
    )

    context = "\\n\\n".join(
        doc.page_content
        for doc in docs
    )

    prompt = f"""
You are an IT Policy Assistant.

Answer the user's question ONLY using the information provided
in the Policy Context below.

Rules:
1. Do not use outside knowledge.
2. Do not make assumptions.
3. If the answer is not available in the Policy Context, respond exactly:
   "I apologize, but that information is not available in the IT Policy document."
4. Keep the answer clear and concise.

Policy Context:
-------------------------
{context}
-------------------------

Question:
{user_question}

Answer:
"""

    with st.chat_message("assistant"):
        with st.spinner("Searching the policy..."):
            try:
                response = llm.invoke(prompt)
                ai_answer = response.text
            except Exception as exc:
                st.error(f"Gemini request failed: {exc}")
                st.stop()

        st.markdown(ai_answer)

    st.session_state.messages.append(
        {"role": "assistant", "content": ai_answer}
    )


# ------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------

st.sidebar.title("Settings")
st.sidebar.caption(f"Knowledge base: {PDF_PATH}")

if st.sidebar.button("Clear Chat"):
    st.session_state.messages = []
    st.rerun()