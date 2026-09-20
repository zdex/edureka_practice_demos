# Three Progressive Agno (formerly Phidata) Classroom Projects

This pack is designed to teach Agno in three levels without paid APIs.

## Progression

| Level | Project | New concepts |
|---|---|---|
| 1 | Research Assistant | Agent, Groq model, instructions, web-search tool |
| 2 | Knowledge Assistant | RAG, Google embeddings, ChromaDB, SQLite chat history |
| 3 | Executive Research Team | Specialist agents, different tools, dynamic delegation, team synthesis |

## APIs / services used

### Groq
Used for LLM inference in all three examples.

Environment variable:
```text
GROQ_API_KEY=...
```

Default model configured in this pack:
```text
openai/gpt-oss-20b
```

You can change it in `.env` using `GROQ_MODEL=...` if Groq changes the models available to your account.

### Google AI Studio
Used only in Level 2 for Gemini embeddings.

Environment variable:
```text
GOOGLE_API_KEY=...
```

Embedding model:
```text
gemini-embedding-001
```

### No-key resources
- DuckDuckGo search through `ddgs`
- Yahoo Finance data through `yfinance`
- ChromaDB local vector store
- SQLite local conversation storage

These do not require an API key, but public services can impose their own rate limits or change availability.

## 1. Setup

Recommended Python: **3.11 or 3.12**.

### Windows PowerShell
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and insert your keys.

## 2. Run the demos

```bash
python level1_research_agent/app.py
python level2_knowledge_assistant/app.py
python level3_multi_agent_team/app.py
```

## Suggested 60–90 minute teaching flow

### Level 1 — Why an agent?
Start with a normal LLM limitation: it cannot reliably know today's external information. Add a search tool and show the agent selecting the tool.

### Level 2 — What if the information is private?
Show the fictional policy document. Explain chunking/embedding/retrieval at a conceptual level, then ask multi-turn questions so learners see both RAG and chat history.

### Level 3 — Why multiple agents?
Explain that a single agent *could* have every tool, but specialization gives clearer responsibilities and makes delegation observable. Run a company briefing and show the leader calling specialists.

## Free-tier note
The code itself does not call a paid-only API. Groq and Google API availability, model catalogs, quotas, and free-tier limits are controlled by those providers and can change. If a model ID is no longer enabled for an account, change `GROQ_MODEL` in `.env` to another tool-capable Groq model available on that account.

## Troubleshooting

### `Missing GROQ_API_KEY`
Make sure `.env` is in the root `agno_three_levels` folder and contains a valid key.

### `Missing GOOGLE_API_KEY`
Only Level 2 needs it. Create a Gemini API key in Google AI Studio and put it in `.env`.

### Model not available / deprecated
Edit:
```text
GROQ_MODEL=openai/gpt-oss-20b
```
to a current Groq model available to your account.

### DuckDuckGo temporary error
Public search endpoints can throttle requests. Retry later or reduce the number of searches.

### Level 2 vector database issue after changing embedding dimensions/model
Delete `level2_knowledge_assistant/tmp/chromadb` and rerun Level 2 so the collection is rebuilt.

## Files learners should focus on
Each use case deliberately keeps its core logic in one `app.py`. This makes it easy to compare the architectural progression without hiding concepts behind application scaffolding.

