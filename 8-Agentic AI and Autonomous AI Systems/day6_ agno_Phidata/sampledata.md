| Level | Test case | Prompt to enter | What learners should observe 
| **1 — Research Agent** | Current topic search 
 | `What are the latest developments in reusable launch vehicles? Give me 5 concise points.
 | Agent decides to use web search, gathers current information, and synthesizes it. |
| | Comparison | `Compare SpaceX Starship and Blue Origin New Glenn in terms of purpose, reusability, and payload strategy.` | Agent performs multi-source research and organizes findings into a comparison. |
| | Evidence-based answer | `Find three recent announcements related to commercial space stations and summarize why they matter.` | Agent searches externally instead of answering only from model knowledge. |
| **2 — Knowledge Assistant** | Direct document retrieval | `What is the company's international travel reimbursement policy?` | Agent retrieves the relevant passage from the local knowledge base. |
| | Follow-up context | First ask: `What is the hotel reimbursement limit?` Then: `What about meals?` | Second question is understood in the context of the first conversation rather than as an isolated query. |
| | Knowledge boundary | `Does the policy mention reimbursement for upgrading to business class?` | Agent should search the supplied documents and ideally say the information is absent if it is not present, rather than inventing an answer. |
| **3 — Multi-Agent Team** | Full company analysis | `Prepare an executive briefing on NVIDIA covering the company, financial performance, recent news, major risks, and an overall assessment.` | Team leader delegates different subtasks to specialist agents and synthesizes their outputs. |
| | Investment-style comparison | `Compare NVIDIA and AMD as businesses. Cover recent financial performance, strategic positioning, recent developments, and key risks.` | Research, finance, and news agents contribute different parts of a comparative analysis. |
| | Event-driven analysis | `Analyze how the latest major NVIDIA announcement could affect its business outlook. Include supporting company, financial, and news context.` | Different agents investigate the same question from specialized perspectives before the coordinator produces the final response. |
