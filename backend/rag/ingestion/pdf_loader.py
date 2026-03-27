import fitz  # PyMuPDF
from .chunker import chunk_text


def load_pdf(file_path: str, source_name: str | None = None) -> list[dict]:
    """Extract text from PDF and return chunk dicts with page metadata."""
    doc = fitz.open(file_path)
    name = source_name or file_path.split("/")[-1]

    all_chunks = []
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text("text").strip()
        if not text:
            continue
        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            all_chunks.append(
                {
                    "text": chunk,
                    "metadata": {
                        "source_type": "pdf",
                        "source_name": name,
                        "page_number": page_num,
                        "chunk_index": i,
                    },
                }
            )

    doc.close()
    return all_chunks
