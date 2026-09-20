from typing import List, Tuple
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import KB_DIR, VECTOR_DIR, OPENAI_EMBEDDING_MODEL, RAG_TOP_K


FAMILY_FILE_MARKERS = {
    "family",
    "families",
    "with-family",
    "with_family",
}

FAMILY_TOPIC_MARKERS = {
    "family",
    "families",
    "kids",
    "children",
}


def _is_family_document(path_name: str, topic: str = "") -> bool:
    name = path_name.lower().replace(" ", "-")
    topic_lower = topic.lower()
    return (
        any(marker in name for marker in FAMILY_FILE_MARKERS)
        or any(marker in topic_lower for marker in FAMILY_TOPIC_MARKERS)
    )


def load_documents() -> List[Document]:
    docs = []
    for path in sorted(KB_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        metadata = {}
        for line in text.splitlines()[:20]:
            if line.startswith("source_title:"):
                metadata["source_title"] = line.split(":", 1)[1].strip()
            elif line.startswith("source_url:"):
                metadata["source_url"] = line.split(":", 1)[1].strip()
            elif line.startswith("topic:"):
                metadata["topic"] = line.split(":", 1)[1].strip()

        metadata["file_name"] = path.name
        metadata["destination"] = "Singapore"
        # Explicit audience metadata lets retrieval distinguish family-specific
        # content from general Singapore content.
        metadata["audience"] = (
            "family" if _is_family_document(path.name, metadata.get("topic", ""))
            else "general"
        )

        docs.append(Document(page_content=text, metadata=metadata))
    return docs


def build_index() -> int:
    docs = load_documents()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=150,
        separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " "],
    )
    chunks = splitter.split_documents(docs)

    # Propagate document-level metadata to every chunk.
    for chunk in chunks:
        if "audience" not in chunk.metadata:
            chunk.metadata["audience"] = "general"

    embeddings = OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL)
    db = FAISS.from_documents(chunks, embeddings)
    VECTOR_DIR.mkdir(parents=True, exist_ok=True)
    db.save_local(str(VECTOR_DIR))
    return len(chunks)


def load_index():
    if not VECTOR_DIR.exists():
        raise FileNotFoundError("FAISS index not found. Run: python -m scripts.ingest")
    embeddings = OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL)
    return FAISS.load_local(
        str(VECTOR_DIR), embeddings, allow_dangerous_deserialization=True
    )


def retrieve(
    query: str,
    k: int = RAG_TOP_K,
    family_trip: bool = False,
) -> Tuple[List[Document], float]:
    """
    Retrieve relevant chunks while applying a lightweight audience filter.
    """
    db = load_index()

    # Retrieve a larger candidate pool so filtering does not leave too few
    # relevant general chunks.
    candidate_k = max(k * 3, k)
    results = db.similarity_search_with_score(query, k=candidate_k)

    if not family_trip:
        results = [
            (doc, score)
            for doc, score in results
            if doc.metadata.get("audience", "general") != "family"
        ]

    results = results[:k]

    if not results:
        return [], 999.0

    return [doc for doc, _ in results], results[0][1]


def format_context(docs: List[Document]) -> str:
    if not docs:
        return "NO KNOWLEDGE BASE CONTEXT WAS RETRIEVED."

    blocks = []
    for i, doc in enumerate(docs, 1):
        blocks.append(
            f"[KB CHUNK {i}]\n"
            f"Source title: {doc.metadata.get('source_title', 'Unknown source')}\n"
            f"Source URL: {doc.metadata.get('source_url', '')}\n"
            f"Audience: {doc.metadata.get('audience', 'general')}\n"
            f"Content:\n{doc.page_content}"
        )
    return "\n\n".join(blocks)
