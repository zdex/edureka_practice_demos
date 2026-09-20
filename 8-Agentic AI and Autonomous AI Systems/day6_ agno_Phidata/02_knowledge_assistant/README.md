# Level 2 — Knowledge Assistant

## Teaching objective
Extend the agent with private knowledge and persistent conversation context.

```text
Policy document → Google embedding → ChromaDB
                                  ↘
User → Agent → Groq LLM → knowledge search → answer
       ↑
       └── SQLite conversation history
```

## Run

```bash
python level2_knowledge_assistant/app.py
```

The first run creates the local vector database and may take slightly longer because the sample document is embedded.

## Recommended live sequence
1. `What is the hotel limit in continental Europe?`
2. `What about meals?`
3. `Do I need a receipt for a EUR 20 taxi?`
4. `Can I fly business class on a 9-hour flight?`
5. Ask something absent from the document: `What is the annual leave policy?`

## Concepts to explain
- **Knowledge** = external information the agent can retrieve.
- **Embedding** = numeric semantic representation used for retrieval.
- **Vector database** = stores and searches embeddings.
- **Chat history** = previous turns supplied to the model for continuity.
- Retrieval and chat history solve different problems.
