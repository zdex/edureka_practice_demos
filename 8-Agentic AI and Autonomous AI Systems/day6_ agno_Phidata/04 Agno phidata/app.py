#agno working
import os
import re
import json
import traceback
from typing import Any
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Import Agent from Phi. # Agent is used to create an AI agent that can use tools and an LLM.
from phi.agent import Agent

# Import tool decorator from Phi. # This converts a normal Python function into a tool that the agent can call.
from phi.tools import tool

# Import Workflow from Phi. 
# # Workflow is used when we want to connect one or more agents into a process.
from phi.workflow import Workflow

# Import Groq model integration from Phi. We rename it as PhiGroq so it does not conflict with the official Groq client below.
from phi.model.groq import Groq as PhiGroq

# This is used for direct and reliable API calls to Groq models.
from groq import Groq as GroqClient

# Pinecone is a vector database used to store and search embeddings.
from pinecone import Pinecone, ServerlessSpec

# This creates embeddings, which are numeric representations of text.
from sentence_transformers import SentenceTransformer

# =========================================================
# 1. Load environment variables
# =========================================================
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

if not GROQ_API_KEY:
    st.error("GROQ_API_KEY is missing. Add it to your .env file.")
    st.stop()


# =========================================================
# 2. Streamlit setup
# =========================================================
st.set_page_config(
    page_title="CSV Data Analysis Agent",
    layout="wide"
)

st.title("CSV Data Analysis Agent")
st.write(
    "Upload a CSV file and ask questions in chat. "
    "The app uses Groq to generate pandas code, and pandas analyses the full dataset."
)


# =========================================================
# 3. Groq setup
# =========================================================
# Phi model is kept for demonstration / agent setup
phi_model = PhiGroq(id="openai/gpt-oss-20b")

# Official Groq client is used for actual responses to avoid Phi logging error
groq_client = GroqClient(api_key=GROQ_API_KEY)


def ask_groq(prompt: str, temperature: float = 0.0) -> str:
    response = groq_client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=temperature
    )
    return response.choices[0].message.content


# =========================================================
# 4. Pinecone setup
# =========================================================

# Streamlit caches this resource. This means Pinecone connection is created only once,
# # instead of reconnecting every time the app refreshes.
@st.cache_resource
def init_pinecone():

    if not PINECONE_API_KEY:
        return None

    # Create a Pinecone client using the API key. This is like logging in to Pinecone from Python.
    pc = Pinecone(api_key=PINECONE_API_KEY)

    # Name of the Pinecone index where vectors will be stored.
    # An index is like a database table for embeddings.
    index_name = "data-insights"

    # Check whether this index already exists in Pinecone. If it does not exist, we create it.
    if index_name not in pc.list_indexes().names():
        # Create a new Pinecone index.
        pc.create_index(
            name=index_name,

            # Dimension must match the embedding model output size.
            dimension=384, # all-MiniLM-L6-v2 creates 384-dimensional embeddings.
            metric="cosine",# Cosine similarity is used to compare how similar two vectors are.
            
            # ServerlessSpec defines where Pinecone should host the index.
            spec=ServerlessSpec(
                cloud="aws", # means AWS cloud.
                region="us-east-1" # is the selected Pinecone region.
            )
        )
    # This returned index object is used later for upsert and search.
    return pc.Index(index_name)


@st.cache_resource
def load_embedding_model():
    return SentenceTransformer("all-MiniLM-L6-v2")


index = init_pinecone()
embedding_model = load_embedding_model()

# =========================================================
# 5. Session state
# =========================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "df" not in st.session_state:
    st.session_state.df = None

if "file_name" not in st.session_state:
    st.session_state.file_name = None


# =========================================================
# 6. Helper functions
# =========================================================
def short_value(value: Any) -> str:
    value = str(value)
    return value[:80] + "..." if len(value) > 80 else value


def get_dataset_profile(df: pd.DataFrame) -> str:
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    column_profile = []
    for col in df.columns:
        column_profile.append({
            "column": col,
            "dtype": str(df[col].dtype),
            "missing_values": int(df[col].isna().sum()),
            "sample_values": [short_value(v) for v in df[col].dropna().head(5).tolist()]
        })

    numeric_summary = (
        df[numeric_cols].describe().to_string()
        if numeric_cols
        else "No numeric columns."
    )

    categorical_summary = {}
    for col in categorical_cols[:15]:
        categorical_summary[col] = df[col].value_counts(dropna=False).head(10).to_dict()

    profile = {
        "rows": df.shape[0],
        "columns_count": df.shape[1],
        "columns": column_profile,
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols
    }

    return f"""
DATASET PROFILE:
{json.dumps(profile, indent=2, default=str)}
# Convert the profile dictionary into nicely formatted JSON text.
# This includes rows, columns, data types, missing values, and sample values.

NUMERIC SUMMARY:
{numeric_summary}
# Add statistical summary for numeric columns.
# Example: count, mean, std, min, max, etc.
TOP CATEGORICAL VALUES:
{json.dumps(categorical_summary, indent=2, default=str)}
# Convert categorical summary dictionary into formatted JSON text.
# This shows the most frequent values in text/category columns.
"""


def extract_python_code(text: str) -> str:
    code_block = re.search(r"```(?:python)?(.*?)```", text, re.DOTALL)
    if code_block:
        return code_block.group(1).strip()
    return text.strip()


def generate_pandas_code(question: str, df: pd.DataFrame) -> str:
    dataset_profile = get_dataset_profile(df)

    prompt = f"""
You are an expert Python pandas data analyst.

A pandas dataframe named df is already loaded.
The user is asking a question about this dataframe.

{dataset_profile}

USER QUESTION:
{question}

Write ONLY executable Python code.

Rules:
1. Use the full dataframe df.
2. Do not import any library.
3. Do not read or write files.
4. Do not use charts.
5. Store the final answer in a variable named result.
6. result can be a string, number, list, dictionary, Series, or DataFrame.
7. If the user asks "details by gender", group by the gender column if it exists.
8. If the exact column name is unclear, choose the most likely column from the dataset profile.
9. Do not explain the code.
"""

    raw_code = ask_groq(prompt, temperature=0)
    return extract_python_code(raw_code)


def run_pandas_code(code: str, df: pd.DataFrame) -> Any:
    local_vars = {"df": df.copy(), "pd": pd}
    exec(code, {}, local_vars)
    return local_vars.get("result", "No result variable was created.")


def explain_result(question: str, result: Any, code: str) -> str:
    if isinstance(result, pd.DataFrame):
        result_text = result.head(100).to_string()
    elif isinstance(result, pd.Series):
        result_text = result.head(100).to_string()
    else:
        result_text = str(result)

    prompt = f"""
You are explaining a data analysis result to a business user.

USER QUESTION:
{question}

RESULT:
{result_text}

PANDAS CODE USED:
{code}

Explain the result clearly and briefly.
Do not overclaim beyond the result.
"""

    return ask_groq(prompt, temperature=0.2)


def store_dataset_summary_in_pinecone(df: pd.DataFrame, file_name: str) -> str:
    if index is None:
        return "Pinecone is not configured. Add PINECONE_API_KEY in your .env file."

    text_summary = get_dataset_profile(df)
    max_chunk_size = 800
    chunks = [text_summary[i:i + max_chunk_size] for i in range(0, len(text_summary), max_chunk_size)]

    vectors = []

    for i, chunk in enumerate(chunks):
        embedding = embedding_model.encode(chunk).tolist()
        vector_id = f"{file_name}_chunk_{i}"

        vectors.append({
            "id": vector_id,
            "values": embedding,
            "metadata": {
                "file_name": file_name,
                "chunk_text": chunk
            }
        })

    index.upsert(vectors=vectors)
    return f"Stored {len(vectors)} chunks in Pinecone."


def search_pinecone(query: str) -> str:
    if index is None:
        return "Pinecone is not configured."

    query_embedding = embedding_model.encode(query).tolist()

    results = index.query(
        vector=query_embedding,
        top_k=5,
        include_metadata=True
    )

    matches = []

    for match in results.get("matches", []):
        chunk_text = match.get("metadata", {}).get("chunk_text", "")
        score = match.get("score", "")
        matches.append(f"Score: {score}\n{chunk_text}")

    return "\n\n".join(matches) if matches else "No similar summary found."


# =========================================================
# 7. Phi tools and workflow
# These are included to demonstrate Phi features.
# The actual data chat uses direct Groq calls because that is more stable.
# =========================================================
@tool
def describe_data() -> str:
    """Describe the uploaded CSV dataset."""
    df = st.session_state.df
    if df is None:
        return "No CSV file uploaded."
    return df.describe(include="all").to_string()


@tool
def embed_and_store() -> str:
    """Store uploaded dataset summary in Pinecone."""
    df = st.session_state.df
    file_name = st.session_state.file_name or "uploaded_data.csv"

    if df is None:
        return "No CSV file uploaded."

    return store_dataset_summary_in_pinecone(df, file_name)


@tool
def search_similar(query: str) -> str:
    """Search similar dataset summaries in Pinecone."""
    return search_pinecone(query)


agent = Agent(
    name="Data Analyst Agent",
    model=phi_model,
    tools=[describe_data, embed_and_store, search_similar],
    description="Analyzes CSV data, stores metadata in Pinecone, and searches similar summaries."
)

workflow = Workflow(
    name="csv_insight_workflow",
    agents=[agent]
)


# =========================================================
# 8. Sidebar
# =========================================================
with st.sidebar:
    st.header("Options")

    show_generated_code = st.checkbox("Show generated pandas code", value=True)
    show_dataset_profile = st.checkbox("Show dataset profile", value=False)

    if st.button("Clear chat"):
        st.session_state.messages = []
        st.rerun()

    if st.session_state.df is not None:
        st.write("Rows:", st.session_state.df.shape[0])
        st.write("Columns:", st.session_state.df.shape[1])

        if st.button("Store dataset summary in Pinecone"):
            with st.spinner("Storing summary in Pinecone..."):
                message = store_dataset_summary_in_pinecone(
                    st.session_state.df,
                    st.session_state.file_name or "uploaded_data.csv"
                )
                st.success(message)


# =========================================================
# 9. Upload CSV
# =========================================================
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file is None:
    st.info("Upload a CSV file to start.")

    st.markdown("""
Try questions like:

- Give me the details by gender.
- What are the different jobs?
- What is the average salary by job?
- Which job has the highest average salary?
- Show the top 5 employees by salary.
- Which columns have missing values?
""")

else:
    try:
        df = pd.read_csv(uploaded_file)

        st.session_state.df = df
        st.session_state.file_name = uploaded_file.name

        st.success(f"Uploaded: {uploaded_file.name}")

        tab1, tab2, tab3 = st.tabs(["Data Preview", "Summary", "Chat Analysis"])

        with tab1:
            st.subheader("Data Preview")
            st.dataframe(df.head(30), width=True)

        with tab2:
            st.subheader("Dataset Summary")
            st.dataframe(df.describe(include="all"), use_container_width=True)

            summary_csv = df.describe(include="all").to_csv()

            st.download_button(
                label="Download Summary CSV",
                data=summary_csv,
                file_name="data_summary.csv",
                mime="text/csv"
            )

            if show_dataset_profile:
                st.text_area("Dataset Profile", get_dataset_profile(df), height=400)

        with tab3:
            st.subheader("Chat with your full dataset")

            st.info(
                "The LLM writes pandas code, and pandas runs the code on the full CSV. "
                "This avoids guessing from only a preview."
            )

            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.write(message["content"])

            user_question =st.chat_input("Ask a question about your CSV...")

            if user_question:
                st.session_state.messages.append({
                    "role": "user",
                    "content": user_question
                })

                with st.chat_message("user"):
                    st.write(user_question)
        
                try:
                    with st.spinner("Analysing the full dataset..."):
                        code = generate_pandas_code(user_question, df)
                        result = run_pandas_code(code, df)
                        answer = explain_result(user_question, result, code)

                    final_answer = answer

                    if show_generated_code:
                        final_answer += f"\n\nGenerated pandas code:\n```python\n{code}\n```"

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": final_answer
                    })

                    with st.chat_message("assistant"):
                        st.write(final_answer)

                        if isinstance(result, pd.DataFrame):
                            st.dataframe(result, use_container_width=True)
                        elif isinstance(result, pd.Series):
                            st.dataframe(result.reset_index(), use_container_width=True)

                except Exception as e:
                    error_message = f"""
Sorry, I could not analyse that question.

Error:
{e}

Try asking more specifically, for example:
- Give me the average salary by gender.
- Show count of employees by gender.
- What is the average salary by job?
"""
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_message
                    })

                    with st.chat_message("assistant"):
                        st.error(error_message)

                        with st.expander("Technical error details"):
                            st.code(traceback.format_exc())
            
    except Exception as e:
        st.error(f"Error during file upload: {e}")
