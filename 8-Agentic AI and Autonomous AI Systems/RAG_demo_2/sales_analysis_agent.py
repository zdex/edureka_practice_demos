import os
import asyncio
import pandas as pd
from dotenv import load_dotenv

from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.core.tools import QueryEngineTool
from llama_index.core.agent.workflow import FunctionAgent

from llama_index.llms.google_genai import GoogleGenAI
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding


load_dotenv()

# 1. Load sales data
df = pd.read_csv("sales_data.csv")

# 2. Set LLM and embedding model
Settings.llm = GoogleGenAI(model="gemini-2.0-flash")
Settings.embed_model = GoogleGenAIEmbedding(
    model_name="gemini-embedding-001"
)

# 3. Convert CSV rows into documents for RAG
documents = []

for _, row in df.iterrows():
    text = f"""
    Order ID: {row['OrderID']}
    Date: {row['Date']}
    Region: {row['Region']}
    Product: {row['Product']}
    Category: {row['Category']}
    Quantity: {row['Quantity']}
    Unit Price: {row['UnitPrice']}
    Total Sale: {row['TotalSale']}
    """
    documents.append(Document(text=text))

# 4. Create vector index
index = VectorStoreIndex.from_documents(documents)

query_engine = index.as_query_engine()

# 5. RAG search tool
sales_search_tool = QueryEngineTool.from_defaults(
    query_engine=query_engine,
    name="sales_data_search",
    description="Search sales records from the CSV and answer questions about orders, products, regions, and dates."
)

# 6. Exact analytics tool
def calculate_total_sales(product: str = "", region: str = "") -> str:
    """
    Calculate exact total sales.
    Use this when the user asks for total sales overall,
    by product, or by region.
    """

    filtered_df = df.copy()

    if product:
        filtered_df = filtered_df[
            filtered_df["Product"].str.lower() == product.lower()
        ]

    if region:
        filtered_df = filtered_df[
            filtered_df["Region"].str.lower() == region.lower()
        ]

    total_sales = filtered_df["TotalSale"].sum()
    return f"Total sales is {total_sales}"


# 7. Create FunctionAgent
agent = FunctionAgent(
    tools=[sales_search_tool, calculate_total_sales],
    llm=Settings.llm,
    system_prompt="""
    You are InsightPulse, an AI sales analysis assistant.
    Use the sales_data_search tool for searching sales records.
    Use calculate_total_sales for exact numerical sales calculations.
    Answer clearly and simply.
    """
)


async def main():
    print("InsightPulse Agent is ready.")
    print("Ask a sales question. Type 'exit' to stop.\n")

    while True:
        question = input("Ask your question: ")

        if question.lower() == "exit":
            print("Goodbye!")
            break

        response = await agent.run(question)
        print("\nAnswer:")
        print(response)
        print("-" * 50)


if __name__ == "__main__":
    asyncio.run(main())