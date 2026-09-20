# Agno Personal Finance Analyst

A beginner-friendly classroom project using **Agno**, **Gemini 3.5 Flash-Lite**, **local Hugging Face embeddings**, **Streamlit**, **pandas/NumPy**, and **SQLite**.

It analyzes a fictional bank-transaction export, categorizes transactions, calculates cash-flow metrics, detects recurring and statistically unusual expenses, and lets an Agno multi-agent team turn those facts into a practical budgeting report.

> Educational demo only. This is not financial, investment, tax, legal, insurance, debt, or credit advice.

## What you learn
- Agno `Agent`
- Agno `Team` and `TeamMode.coordinate`
- specialist agents and delegation
- custom Python tools
- Gemini tool use
- Pydantic structured output
- local SQLite session history
- local Hugging Face embeddings
- deterministic analytics
- Streamlit UI

## Agents
| Agent | Responsibility |
|---|---|
| Transaction Analyst | Income, expenses, net cash flow, monthly trend |
| Spending Pattern Analyst | Categories and recurring merchants |
| Unusual Transaction Reviewer | Items that deserve manual review |
| Budget Advisor | Evidence-based budget suggestions |
| Finance Coach | Simple next-month action plan |
| Agno Team Leader | Delegates and synthesizes |

## Free services only
### LLM
Default model: `gemini-3.5-flash-lite` through a **Google AI Studio / Gemini Developer API free-tier key**. Free-tier quotas and rate limits apply.

### Embeddings
`sentence-transformers/all-MiniLM-L6-v2` runs locally. It downloads once from Hugging Face and is cached; there is no paid embedding API.

### Storage
Session history is stored in local SQLite: `data/finance_agents.db`.

## Requirements
Recommended Python: **3.11 or 3.12**.

## Setup
### Windows
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:
```env
GOOGLE_API_KEY=your_google_ai_studio_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
HF_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

## Run
```bash
streamlit run app.py
```

The fictional **Classroom sample** is selected by default.

CLI version:
```bash
python run_cli.py
```

## Input format
Upload CSV/XLSX with:
- `date`
- `description`
- `amount`

Optional: `category`.

Use positive values for money in and negative values for money out.

Example:
```csv
date,description,amount
2026-08-01,Salary ACME Pvt Ltd,80000
2026-08-02,Apartment Rent,-22000
2026-08-03,Swiggy,-850
```

## Architecture
```text
CSV/XLSX
   |
   v
normalize + validate
   |
   +--> keyword + local HF embedding categorization
   |
   +--> deterministic Python analytics/tools
                  |
                  v
             Agno Team Leader
                  |
      +-----------+-----------+
      |           |           |
 Transaction   Spending    Unusual
 Analyst       Analyst     Reviewer
      |           |           |
      +------ Budget Advisor -+
                  |
            Finance Coach
                  |
                  v
          Pydantic FinanceReport
```

## Important design idea
The **LLM is not the calculator**.

`src/analytics.py` computes totals, trends, recurring merchants, outliers and budget signals. `src/finance_tools.py` exposes those functions to Agno agents.

So the teaching split is:
```text
Python  -> calculation
Gemini  -> interpretation
Agno    -> orchestration
HF      -> local semantic embeddings
```

## Structured output
`src/schemas.py` defines `FinanceReport`, and the team uses `output_schema=FinanceReport`. This gives the Streamlit app a predictable response object instead of arbitrary text.

## Memory/history
The team uses `SqliteDb`, `add_history_to_context=True`, and the two most recent runs. No paid memory service is required.

## Free API fallback
The Streamlit app can fall back to a deterministic Python report if Gemini hits a temporary quota/rate-limit error. This is useful for a live class.

## First-run note
The Hugging Face model may take time to download on the first run. Run the app once before class so it is cached.

## Privacy
Use the included fictional data in class. Real bank data is sensitive. Do not commit real statements or API keys to Git, and review provider data-handling terms before sending sensitive financial data to a remote model.

## Project structure
```text
agno_personal_finance_analyst/
├── app.py
├── run_cli.py
├── README.md
├── CLASSROOM_DEMO.md
├── requirements.txt
├── .env.example
├── sample_data/sample_transactions.csv
├── src/
│   ├── config.py
│   ├── data_loader.py
│   ├── categorizer.py
│   ├── analytics.py
│   ├── finance_tools.py
│   ├── agent_team.py
│   ├── reporting.py
│   └── schemas.py
└── tests/test_analytics.py
```

## Version note
Pinned for `agno[google]==3.0.2`. Agent frameworks change quickly; if you upgrade Agno, review current Agno team/model migration documentation.
