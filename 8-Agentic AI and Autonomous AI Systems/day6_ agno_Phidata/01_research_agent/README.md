# Level 1 — Research Assistant

## Teaching objective
Show the smallest useful agent architecture:

**User → Agent → Groq LLM → DuckDuckGo tool → Answer**

## Run
From the root folder:

```bash
python level1_research_agent/app.py
```

## Good classroom prompts
- What are the latest developments in reusable launch vehicles?
- Compare solar and wind energy for a data center.
- Find three recent developments in AI agents and summarize them.

## Point out to learners
- `model=` supplies intelligence.
- `instructions=` constrain behavior.
- `tools=` give the agent capabilities outside the model.
- The agent decides when it needs the search tool.
