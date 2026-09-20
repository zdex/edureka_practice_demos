import os
from io import BytesIO
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
from pypdf import PdfReader
from docx import Document

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


# Load API key from .env file
load_dotenv()

st.write("API key loaded:", os.getenv("GROQ_API_KEY") is not None)


# Page setup
st.set_page_config(
    page_title="Resume Screening Application",
    layout="wide"
)

st.title("Resume Screening Application")
st.write("Upload a resume and compare it with the job requirements.")


# Function to read PDF file
def read_pdf(uploaded_file):
    pdf_reader = PdfReader(BytesIO(uploaded_file.read()))
    text = ""

    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    return text


# Function to read DOCX file
def read_docx(uploaded_file):
    document = Document(uploaded_file)
    text = ""

    for paragraph in document.paragraphs:
        text += paragraph.text + "\n"

    return text


# Function to read TXT file
def read_txt(uploaded_file):
    return uploaded_file.read().decode("utf-8")


# Function to extract text based on file type
def extract_resume_text(uploaded_file):
    file_name = uploaded_file.name.lower()

    if file_name.endswith(".pdf"):
        return read_pdf(uploaded_file)

    elif file_name.endswith(".docx"):
        return read_docx(uploaded_file)

    elif file_name.endswith(".txt"):
        return read_txt(uploaded_file)

    else:
        return ""


# Job description input
job_requirements = st.text_area(
    "Enter Job Requirements",
    height=250,
    placeholder="Example: Senior Python Developer with 5+ years experience, Django/FastAPI, SQL, cloud, REST API..."
)


# Resume upload
uploaded_resume = st.file_uploader(
    "Upload Resume",
    type=["pdf", "docx", "txt"]
)


# Analyze button
if st.button("Analyze Resume"):

    # Check API key
    if not os.getenv("GROQ_API_KEY"):
        st.error("Groq API key not found. Please add GROQ_API_KEY in your .env file.")
        st.stop()

    # Check job requirements
    if not job_requirements:
        st.error("Please enter the job requirements.")
        st.stop()

    # Check resume upload
    if uploaded_resume is None:
        st.error("Please upload a resume.")
        st.stop()

    # Extract resume text
    resume_text = extract_resume_text(uploaded_resume)

    if not resume_text.strip():
        st.error("Could not read the resume text. Please upload a valid file.")
        st.stop()

    # Show extracted text
    with st.expander("View Extracted Resume Text"):
        st.write(resume_text)

    # Create prompt
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
You are an expert HR resume screening assistant.

Your task is to compare a candidate resume with the job requirements.

Rules:
- Use only the information available in the resume.
- Do not assume missing information.
- Keep the evaluation fair and job-related.
- Do not judge based on age, gender, religion, nationality, marital status, or personal background.
"""
        ),
        (
            "human",
            """
Job Requirements:
{job_requirements}

Candidate Resume:
{resume_text}

Create a detailed resume screening report with the following sections only:

1. Candidate Fit Summary
2. Overall Match Score out of 100
3. Matched Skills
4. Missing Skills
5. Experience Relevance
6. Education Evaluation
7. Strengths
8. Weaknesses or Gaps
9. HR Recommendation
Choose one:
- Strongly Shortlist
- Shortlist
- Hold / Needs Review
- Do Not Shortlist

10. Suggested Interview Questions
Give 5 interview questions.
"""
        )
    ])

    # Connect to Groq model
    llm = ChatGroq(
        model="openai/gpt-oss-20b",
        temperature=0.2
    )

    # Create LangChain chain -LCEL
    chain = prompt | llm | StrOutputParser()

    # Generate report
    with st.spinner("Analyzing resume..."):
        report = chain.invoke({
            "job_requirements": job_requirements,
            "resume_text": resume_text
        })

    # Display report
    st.subheader("Resume Screening Report")
    st.write(report)

    # Download report
    file_name = "resume_screening_report_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".txt"

    st.download_button(
        label="Download Report",
        data=report,
        file_name=file_name,
        mime="text/plain"
    )