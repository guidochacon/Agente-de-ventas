from . import vector_store


def retrieve(query: str, n_results: int = 5) -> str:
    """
    Retrieve relevant knowledge base chunks for a query.
    Returns formatted context string to inject into Claude's prompt.
    """
    chunks = vector_store.query(query, n_results=n_results * 2)

    if not chunks:
        return ""

    # Deduplicate by doc_id — keep best chunk per document
    seen_docs: dict[str, dict] = {}
    for chunk in chunks:
        doc_id = chunk["metadata"].get("doc_id", "unknown")
        if doc_id not in seen_docs or chunk["distance"] < seen_docs[doc_id]["distance"]:
            seen_docs[doc_id] = chunk

    # Sort by relevance (lower distance = more similar)
    top_chunks = sorted(seen_docs.values(), key=lambda x: x["distance"])[:n_results]

    if not top_chunks:
        return ""

    parts = []
    for chunk in top_chunks:
        meta = chunk["metadata"]
        source = meta.get("source_name", "knowledge base")
        page = meta.get("page_number", "")
        label = f"[FUENTE: {source}" + (f", página {page}" if page else "") + "]"
        parts.append(f"{label}\n{chunk['text']}")

    return "\n\n---\n\n".join(parts)
