# Assignment Traceability

| Assignment requirement | Implementation |
|---|---|
| One destination | Singapore |
| 3+ public resources | 5 KB documents |
| Document loading | `app/rag.py` |
| Meaningful chunking | `RecursiveCharacterTextSplitter` |
| Embeddings | OpenAI `text-embedding-3-small` |
| Vector store | FAISS |
| Grounded answers | `app/prompts.py` |
| Source title/link | document metadata + UI |
| Missing KB behavior | strict prompt + explicit boundary |
| Weather MCP | `get_weather_forecast` |
| Currency MCP | `convert_currency` |
| MCP client | `app/mcp_client.py` |
| Tool selection | `app/router.py` |
| Combined RAG + MCP | `app/main.py` |
| Prompt strategy | README + `app/prompts.py` |
| Multi-turn context | Streamlit session history |
| Simple UI | Streamlit |
| Sample responses | `SAMPLE_RESPONSES.md` |
| Demonstration | `DEMO_GUIDE.md` |
| Setup/architecture | `README.md` |
