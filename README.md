# AI Travel Planning Assistant — Singapore

A context-aware Singapore travel assistant combining document-based RAG with MCP tools for current weather and currency information.

## Assignment alignment

This implementation covers the supplied brief's required deliverables and acceptance criteria:

- 5 public-source knowledge-base documents.
- Meaningful chunking + embeddings + FAISS.
- Grounded destination answers with source titles/URLs.
- MCP weather tool.
- MCP currency-conversion tool.
- Combined RAG + MCP itinerary planning.
- Multi-turn conversation context.
- Intent-based tool selection.
- Explicit missing-knowledge and tool-failure handling.
- Simple Streamlit interface.
- Source code, KB, README, sample questions/responses and demo guide.

## Scope

### In scope
- Singapore attractions and neighbourhoods.
- Local transportation guidance.
- Cultural/practical travel tips.
- Food/local experiences.
- Indoor/outdoor activities.
- Itinerary generation.
- Current weather/forecast.
- Currency conversion.
- Multi-turn planning.

### Out of scope
- Flight booking.
- Hotel booking.
- Payment processing.
- Route navigation.
- Travel reservations.
- Live attraction ticket inventory/opening status unless added through a current-information tool.

## Architecture

```text
                    ┌─────────────────────────┐
                    │      Streamlit UI       │
                    │ chat + sources + tools  │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │   LangChain assistant   │
                    │  prompt + orchestration │
                    └──────┬──────────┬───────┘
                           │          │
                    stable │          │ current
                           │          │
                           ▼          ▼
                    ┌────────────┐  ┌──────────────┐
                    │ RAG / FAISS│  │ Intent Router│
                    │ embeddings │  │ weather/FX   │
                    └──────┬─────┘  └──────┬───────┘
                           │               │ MCP
                           ▼               ▼
                    ┌────────────┐  ┌──────────────────┐
                    │ KB chunks +│  │ MCP Server       │
                    │ metadata   │  │ weather + FX      │
                    └──────┬─────┘  └────────┬─────────┘
                           │                 │
                           └────────┬────────┘
                                    ▼
                           ┌─────────────────┐
                           │ LLM synthesis   │
                           │ facts + current │
                           │ info + advice   │
                           └─────────────────┘
```

The router is deliberately deterministic: destination questions use RAG, current weather uses the weather MCP tool, currency conversion uses the currency MCP tool, and combined questions use both. This prevents unnecessary MCP calls and makes tool selection auditable.

## Knowledge-base sources

The repository contains concise paraphrased notes, not wholesale copies, and preserves source title/URL metadata:

1. Wikivoyage — Singapore Travel Guide  
   https://en.wikivoyage.org/wiki/Singapore

2. Visit Singapore — Essential Singapore Travel Information  
   https://www.visitsingapore.com/travel-tips/essential-travel-information/

3. Visit Singapore — Singapore Itineraries  
   https://www.visitsingapore.com/travel-tips/travelling-to-singapore/itineraries/

4. Visit Singapore — Family Getaway / Places to Visit With Family  
   https://www.visitsingapore.com/content/visitsingapore/en/travel-tips/travelling-to-singapore/itineraries/places-to-visit-with-family/

5. Visit Singapore — Things to Do / Family and Cultural Activities  
   https://www.visitsingapore.com/content/visitsingapore/en/things-to-do/top-things-to-do/family-fun/

Review the source websites' reuse terms before redistributing the source material itself.

## RAG workflow

`scripts/ingest.py`:

1. Loads Markdown KB files.
2. Creates LangChain `Document` objects.
3. Preserves source title, URL, filename and destination as metadata.
4. Splits content using `RecursiveCharacterTextSplitter`.
5. Creates embeddings with `OpenAIEmbeddings`.
6. Stores vectors in FAISS under `data/faiss_index/`.

At query time:

1. Embed the question.
2. Retrieve top-k chunks.
3. Pass retrieved chunks to a strict grounding prompt.
4. Generate the answer.
5. Display source title and URL.

The prompt explicitly prohibits using general model knowledge to fill missing destination facts.

## MCP workflow

`app/mcp_server.py` exposes two MCP tools.

### `get_weather_forecast`
Uses Open-Meteo to retrieve current conditions and daily forecast data for Singapore. The tool accepts `start_date=today`, an explicit ISO date, or `start_date=next_week`; the latter resolves to the next Monday at runtime, which supports the assignment's three-day 'next week' scenario.

### `convert_currency`
Uses Frankfurter to retrieve an exchange rate and convert an amount.

The application invokes these tools through an MCP-compatible stdio client in `app/mcp_client.py`.

If a service fails, the returned error is surfaced and the assistant is instructed not to estimate/fabricate the missing value.

## Prompt and context strategy

The synthesis prompt receives four layers:

1. Retrieved KB context.
2. MCP results.
3. Recent conversation history.
4. Current user request.

It instructs the model to distinguish:

- `[KB]` destination facts.
- `[MCP]` current weather/currency.
- `[AI recommendation]` itinerary sequencing and weather-aware planning choices.

It also says to state clearly when evidence is insufficient.

## Multi-turn context

Streamlit keeps recent messages in `st.session_state`. A bounded recent history is passed to the LLM so user preferences persist across turns.

Example:

1. "I am travelling with children."
2. "Make it three days and adapt it to rain."

The second turn retains the family preference.

## Missing information policy

If the KB does not support a destination fact, the assistant should say so rather than invent it.

Example:

> I don't have enough information in the Singapore knowledge base to answer that reliably. I won't invent destination details.

If the current MCP service fails:

> The current weather tool could not return a verified forecast, so I cannot provide a reliable current forecast.

The app never silently substitutes model knowledge for failed current data.

## Setup

Prerequisites:
- Python 3.11+
- OpenAI API key
- Internet access for OpenAI, Open-Meteo and Frankfurter

Install:

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Create `.env` from `.env.example` and set:

```text
OPENAI_API_KEY=your_key_here
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

Build the vector index:

```bash
python scripts/ingest.py
```

Run:

```bash
streamlit run app/main.py
```

## Run the MCP server manually

For troubleshooting:

```bash
python app/mcp_server.py
```

It uses stdio and is normally started automatically by the application.

## Sample questions

See `SAMPLE_RESPONSES.md`.

Key acceptance tests:

1. What are the must-visit attractions in Singapore?
2. Which neighbourhoods are suitable for cultural experiences?
3. How can a tourist travel around Singapore?
4. Suggest activities for a family with children.
5. What indoor attractions can I visit?
6. What is the weather in Singapore?
7. What is the forecast for the next three days?
8. Convert INR 50,000 to SGD.
9. Plan a three-day Singapore itinerary for next week and adjust activities according to the weather forecast.
10. I have INR 60,000. Convert it to SGD and suggest a three-day itinerary.
11. What is the exact ticket price for every attraction in Singapore? (should trigger missing-KB handling)
12. Is Gardens by the Bay sold out tomorrow? (should explain that reservation/inventory is out of scope)

## Demonstration

See `DEMO_GUIDE.md` for a 5-minute demonstration covering RAG, weather MCP, combined planning, currency MCP, multi-turn context and missing knowledge.

## Project structure

```text
ai-travel-planning-assistant/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── rag.py
│   ├── router.py
│   ├── mcp_client.py
│   ├── mcp_server.py
│   └── prompts.py
├── scripts/
│   ├── ingest.py
│   └── smoke_test.py
├── travel_kb/
│   ├── 01_wikivoyage_singapore.md
│   ├── 02_visitsingapore_essential.md
│   ├── 03_visitsingapore_itineraries.md
│   ├── 04_visitsingapore_family.md
│   ├── 05_visitsingapore_activities.md
│   └── SOURCE_MANIFEST.json
├── tests/
│   └── test_router.py
├── requirements.txt
├── .env.example
├── SAMPLE_RESPONSES.md
├── DEMO_GUIDE.md
├── ASSIGNMENT_TRACEABILITY.md
└── README.md
```

## Design decisions

- **FAISS:** local, lightweight and easy to demonstrate.
- **OpenAI embeddings:** configurable semantic embeddings with a simple setup.
- **Local MCP server:** makes the MCP boundary reproducible while the tools call live external services.
- **Deterministic routing:** auditable and prevents destination questions from unnecessarily invoking current-data tools.
- **Streamlit:** deliberately simple because the brief prioritizes core AI workflow over visual design.

## Limitations

- One destination: Singapore.
- Weather depends on Open-Meteo availability.
- Currency depends on Frankfurter availability.
- Destination knowledge is limited to the supplied KB.
- No booking/reservation/payment/route-navigation capabilities.
