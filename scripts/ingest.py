from app.rag import build_index, load_documents

if __name__ == "__main__":
    docs = load_documents()
    print(f"Loaded {len(docs)} source documents")
    count = build_index()
    print(f"Created {count} chunks")
    print("FAISS index created under data/faiss_index")
