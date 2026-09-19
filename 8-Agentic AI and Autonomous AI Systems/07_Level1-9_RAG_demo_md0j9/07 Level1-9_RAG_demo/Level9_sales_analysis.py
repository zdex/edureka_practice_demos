import streamlit as st
import pandas as pd
import json
from dotenv import load_dotenv
from llama_index.llms.groq import Groq

# ---------------- PAGE SETUP ----------------

st.set_page_config(
    page_title="Sales Analysis Agent",
    layout="wide"
)

load_dotenv()

st.title("Level 9: Sales Analysis Agent with LlamaIndex")
st.write("Upload sales_data.csv and ask sales questions in natural language.")

# ---------------- LLM SETUP ----------------

llm = Groq(
    model="llama-3.1-8b-instant",
    temperature=0.1
)

# ---------------- SESSION MEMORY ----------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "df" not in st.session_state:
    st.session_state.df = None

# ---------------- FILE UPLOAD ----------------

uploaded_file = st.file_uploader("Upload sales_data.csv", type=["csv"])

if uploaded_file:
    st.session_state.df = pd.read_csv(uploaded_file)
    st.success("Sales data uploaded successfully.")

    with st.expander("Preview Sales Data"):
        st.dataframe(st.session_state.df)

# ---------------- UNDERSTAND QUESTION USING LLAMAINDEX LLM ----------------
def understand_question(user_question, df):
    regions = list(df["Region"].dropna().unique())
    products = list(df["Product"].dropna().unique())
    categories = list(df["Category"].dropna().unique())

    prompt = f"""
    You are an intent extraction engine for a sales analysis app.

    Your job is NOT to answer the question.
    Your job is ONLY to convert the user's question into JSON.

    Available regions from CSV:
    {regions}

    Available products from CSV:
    {products}

    Available categories from CSV:
    {categories}

    Choose analysis_type from ONLY this list:
    - total_sales
    - sales_by_region
    - sales_by_product
    - sales_by_category
    - quantity_sold
    - general_summary

    Rules:
    1. If the user asks "by region", "region wise", "all regions", or "for all regions",
       use "sales_by_region".
    2. If the user asks "by product" or "product wise",
       use "sales_by_product".
    3. If the user asks "by category" or "category wise",
       use "sales_by_category".
    4. If the user asks "quantity", "units", or "how many",
       use "quantity_sold".
    5. If the user asks total sales, revenue, or sales for a specific region/product/category,
       use "total_sales".
    6. Match product, region, and category only from the available CSV values.
    7. If user says "laptop for all regions", this means:
       analysis_type = sales_by_region
       product = Laptop
    8. If user says "webcam by region", this means:
       analysis_type = sales_by_region
       product = Webcam
    9. If user says "electronics sales", this means:
       analysis_type = total_sales
       category = Electronics
    10. If user says "qty sold for each product", "quantity by product", 
        or "quantity sold for all products",
        use:
        analysis_type = quantity_by_product

    11. If user says "qty sold for all the products in North", this means:
        analysis_type = quantity_by_product
        region = North

    12. If user says "quantity by category" or "qty by category",
        use:
        analysis_type = quantity_by_category
        Return ONLY valid JSON.
        Do not add explanation.
        Do not use markdown.

    JSON format:
    {{
        "analysis_type": "",
        "region": "",
        "product": "",
        "category": ""
    }}

    User question:
    {user_question}
    """

    response = llm.complete(prompt).text.strip()

    try:
        return json.loads(response)
    except:
        return {
            "analysis_type": "general_summary",
            "region": "",
            "product": "",
            "category": ""
        }

# ---------------- RUN ANALYSIS USING PANDAS ----------------

def run_sales_analysis(df, intent):
    analysis_type = intent.get("analysis_type", "")
    region = intent.get("region", "")
    product = intent.get("product", "")
    category = intent.get("category", "")

    filtered_df = df.copy()

    if region:
        filtered_df = filtered_df[
            filtered_df["Region"].astype(str).str.lower() == str(region).lower()
        ]

    if product:
        filtered_df = filtered_df[
            filtered_df["Product"].astype(str).str.lower() == str(product).lower()
        ]

    if category:
        filtered_df = filtered_df[
            filtered_df["Category"].astype(str).str.lower() == str(category).lower()
        ]

    if filtered_df.empty:
        return "No matching sales data found for your question."

    if analysis_type == "total_sales":
        total_sales = filtered_df["TotalSale"].sum()
        return f"Total sales = ₹{total_sales:,.2f}"

    elif analysis_type == "sales_by_region":
        return (
            filtered_df
            .groupby("Region")["TotalSale"]
            .sum()
            .reset_index()
            .sort_values("TotalSale", ascending=False)
        )

    elif analysis_type == "sales_by_product":
        return (
            filtered_df
            .groupby("Product")["TotalSale"]
            .sum()
            .reset_index()
            .sort_values("TotalSale", ascending=False)
        )

    elif analysis_type == "sales_by_category":
        return (
            filtered_df
            .groupby("Category")["TotalSale"]
            .sum()
            .reset_index()
            .sort_values("TotalSale", ascending=False)
        )

    elif analysis_type == "quantity_sold":
        total_quantity = filtered_df["Quantity"].sum()
        return f"Total quantity sold = {total_quantity}"

    else:
        total_sales = filtered_df["TotalSale"].sum()
        total_quantity = filtered_df["Quantity"].sum()
        total_orders = filtered_df["OrderID"].nunique()

        return f"""
Sales Summary:

Total Orders: {total_orders}

Total Quantity Sold: {total_quantity}

Total Sales: ₹{total_sales:,.2f}
"""

# ---------------- SIDEBAR ----------------

with st.sidebar:
    st.header("Try these questions")

    st.markdown("""
- What is total sales from North?
- Sales for Webcam by region
- Total sales of Electronics
- Total quantity sold for Laptop
- Sales by product
- Sales by category
- Which region has the highest sales?
- Which product generated the highest revenue?
""")

    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# ---------------- OLD CHAT ----------------

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# ---------------- CHAT INPUT ----------------

user_question = st.chat_input("Ask a sales question...")

if user_question:
    st.session_state.messages.append({
        "role": "user",
        "content": user_question
    })

    with st.chat_message("user"):
        st.write(user_question)

    with st.chat_message("assistant"):
        if st.session_state.df is None:
            st.warning("Please upload sales_data.csv first.")
        else:
            df = st.session_state.df

            with st.spinner("Analyzing sales data..."):
                intent = understand_question(user_question, df)
                result = run_sales_analysis(df, intent)

            st.write("### Answer")

            if isinstance(result, pd.DataFrame):
                st.dataframe(result)
                bot_reply = result.to_string(index=False)
            else:
                st.write(result)
                bot_reply = result

            with st.expander("Agent Understanding"):
                st.json(intent)

            st.session_state.messages.append({
                "role": "assistant",
                "content": bot_reply
            })