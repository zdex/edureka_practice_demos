# Level 3 — Multi-Agent Executive Research Team

## Teaching objective
Demonstrate specialization, delegation, tool separation, and synthesis.

```text
                         Team Leader
                  /          |           \
                 /           |            \
        Company Research   Finance      News/Risk
          DuckDuckGo       yfinance     DuckDuckGo News
                 \           |            /
                  \          |           /
                   Executive synthesis
```

## Run

```bash
python level3_multi_agent_team/app.py
```

## Good classroom prompts
- Prepare an executive briefing on NVIDIA (NVDA).
- Compare the business and financial position of Microsoft (MSFT) and Alphabet (GOOGL).
- Research Tesla (TSLA): strategy, financial snapshot, recent developments, major risks, and opportunities.

## What to watch during the demo
`show_members_responses=True` lets learners see specialist contributions before the leader synthesizes the final answer.

## Teaching distinction
A **Team** lets the model dynamically decide which members to delegate to. A deterministic sequence such as `research → financial analysis → compliance review → retry if rejected` is better taught later as an Agno **Workflow**.
