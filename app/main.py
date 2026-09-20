import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
    
import asyncio
import json
import streamlit as st
from langchain_openai import ChatOpenAI
from app.config import OPENAI_CHAT_MODEL, MAX_HISTORY_TURNS
from app.mcp_client import call_mcp_tool
from app.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from app.rag import retrieve, format_context
from app.router import route_query

st.set_page_config(page_title="Singapore Travel Planning Assistant", page_icon="✈️", layout="wide")
st.title("Singapore Travel Planning Assistant")
st.caption("RAG for destination knowledge + MCP for current weather/currency. No booking/reservation support.")

if "messages" not in st.session_state:
    st.session_state.messages = []

def history_text():
    turns = st.session_state.messages[-(MAX_HISTORY_TURNS * 2):]
    return "\n".join(f"{m['role'].upper()}: {m['content']}" for m in turns)

def run_async(coro):
    return asyncio.run(coro)

def mcp_context_for(intent):
    results = []
    if intent.weather:
        results.append(run_async(call_mcp_tool(
            "get_weather_forecast", {"city": "Singapore", "days": 3, "start_date": intent.forecast_start or "today"}
        )))
    if intent.currency and intent.amount is not None:
        results.append(run_async(call_mcp_tool(
            "convert_currency",
            {"amount": intent.amount, "from_currency": intent.from_currency, "to_currency": intent.to_currency},
        )))
    return "NO MCP TOOL WAS REQUIRED." if not results else json.dumps(results, indent=2)

def answer(query):
    intent = route_query(query)
    kb_docs = retrieve(query)[0] if intent.rag else []
    kb_context = format_context(kb_docs) if intent.rag else "KNOWLEDGE BASE NOT REQUIRED FOR THIS REQUEST."
    mcp_context = mcp_context_for(intent)

    llm = ChatOpenAI(model=OPENAI_CHAT_MODEL, temperature=0)
    prompt = SYSTEM_PROMPT + "\n" + USER_PROMPT_TEMPLATE.format(
        query=query, history=history_text() or "(No previous conversation.)",
        kb_context=kb_context, mcp_context=mcp_context
    )
    response = llm.invoke(prompt)
    sources, seen = [], set()
    for doc in kb_docs:
        key = (doc.metadata.get("source_title"), doc.metadata.get("source_url"))
        if key[0] and key not in seen:
            sources.append({"title": key[0], "url": key[1]})
            seen.add(key)

    tools = []
    if intent.weather:
        tools.append("get_weather_forecast")
    if intent.currency and intent.amount is not None:
        tools.append("convert_currency")
    return response.content, sources, tools

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("Knowledge-base sources"):
                for source in message["sources"]:
                    st.markdown(f"- [{source['title']}]({source['url']})")
        if message.get("tools"):
            st.caption("MCP tools used: " + ", ".join(message["tools"]))

if prompt := st.chat_input("Ask about Singapore travel planning..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Retrieving knowledge and current information..."):
            try:
                text, sources, tools = answer(prompt)
                st.markdown(text)
                if sources:
                    with st.expander("Knowledge-base sources"):
                        for source in sources:
                            st.markdown(f"- [{source['title']}]({source['url']})")
                if tools:
                    st.caption("MCP tools used: " + ", ".join(tools))
                st.session_state.messages.append({
                    "role": "assistant", "content": text, "sources": sources, "tools": tools
                })
            except Exception as exc:
                error = (
                    "I could not complete the request reliably. "
                    f"Technical detail: `{exc}`\n\n"
                    "No unsupported travel information has been fabricated."
                )
                st.error(error)
                st.session_state.messages.append({
                    "role": "assistant", "content": error, "sources": [], "tools": []
                })

with st.sidebar:
    st.header("System status")
    st.write("Destination: Singapore")
    st.write("RAG: FAISS + OpenAI embeddings")
    st.write("MCP: Weather + Currency")
    st.write("LLM: configurable")
    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.rerun()
