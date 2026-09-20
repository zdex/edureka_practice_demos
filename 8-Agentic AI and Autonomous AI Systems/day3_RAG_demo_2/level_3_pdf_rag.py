import streamlit as st
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.2)

st.title("Level 3: IT Helpdesk with PDF RAG")

# Store chat messages
if "messages" not in st.session_state:
    st.session_state.messages = []

# Store retriever so PDF is not processed again and again
if "retriever" not in st.session_state:
    st.session_state.retriever = None

uploaded_pdf = st.file_uploader("Upload IT policy PDF", type=["pdf"])

if uploaded_pdf and st.session_state.retriever is None:
    pdf_path = "temp_it_policy.pdf"

    with st.spinner("Uploading and processing the document..."):
        with open(pdf_path, "wb") as f:
            f.write(uploaded_pdf.read())

        loader = PyPDFLoader(pdf_path)
        documents = loader.load()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100
        )

        chunks = splitter.split_documents(documents)

        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        vectorstore = FAISS.from_documents(chunks, embeddings)

        st.session_state.retriever = vectorstore.as_retriever(
            search_kwargs={"k": 3}
        )

    st.success("PDF uploaded and processed successfully.")

# Display old chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input box
question = st.chat_input("Ask a question from the PDF...")

if question:
    if st.session_state.retriever is None:
        st.warning("Please upload a PDF first.")
    else:
        st.session_state.messages.append({
            "role": "user",
            "content": question
        })

        with st.chat_message("user"):
            st.write(question)

        with st.chat_message("assistant"):
            with st.spinner("Searching the PDF and preparing the answer..."):
                docs = st.session_state.retriever.invoke(question)

                context = "\n\n".join([doc.page_content for doc in docs])

                prompt = f"""
                You are an IT helpdesk assistant.
                Answer only using the PDF context below.
                If the answer is not found, say that the policy document does not mention it.

                Context:
                {context}

                Question:
                {question}
                """

                response = llm.invoke(prompt)
                bot_reply = response.content

            st.write(bot_reply)

            with st.expander("Retrieved PDF context"):
                st.write(context)

        st.session_state.messages.append({
            "role": "assistant",
            "content": bot_reply
        })

if st.button("Clear Chat"):
    st.session_state.messages = []
    st.rerun()