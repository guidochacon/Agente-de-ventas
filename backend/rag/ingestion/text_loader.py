from .chunker import chunk_text


def load_text(text: str, source_name: str = "text") -> list[dict]:
    """Load plain text and return list of chunk dicts with metadata."""
    chunks = chunk_text(text)
    return [
        {
            "text": chunk,
            "metadata": {
                "source_type": "text",
                "source_name": source_name,
                "chunk_index": i,
            },
        }
        for i, chunk in enumerate(chunks)
    ]
