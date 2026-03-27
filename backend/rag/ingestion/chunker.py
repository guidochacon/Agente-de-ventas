from typing import List


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
    """
    Split text into overlapping chunks.
    Tries to split on paragraph boundaries first, then sentences, then words.
    """
    if not text or not text.strip():
        return []

    text = text.strip()

    # Rough token estimate: 1 token ≈ 4 chars
    char_size = chunk_size * 4
    char_overlap = overlap * 4

    if len(text) <= char_size:
        return [text]

    chunks = []
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    current_chunk = ""
    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 <= char_size:
            current_chunk = (current_chunk + "\n\n" + para).strip()
        else:
            if current_chunk:
                chunks.append(current_chunk)
                # Start new chunk with overlap from end of previous
                overlap_text = current_chunk[-char_overlap:] if len(current_chunk) > char_overlap else current_chunk
                last_newline = overlap_text.rfind("\n")
                if last_newline > 0:
                    overlap_text = overlap_text[last_newline:].strip()
                current_chunk = (overlap_text + "\n\n" + para).strip()
            else:
                # Paragraph itself is too big — split by sentences
                sentences = _split_sentences(para)
                for sent in sentences:
                    if len(current_chunk) + len(sent) + 1 <= char_size:
                        current_chunk = (current_chunk + " " + sent).strip()
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                            overlap_text = current_chunk[-char_overlap:]
                            current_chunk = (overlap_text + " " + sent).strip()
                        else:
                            # Single sentence too long — hard split
                            for i in range(0, len(sent), char_size - char_overlap):
                                chunks.append(sent[i:i + char_size])
                            current_chunk = ""

    if current_chunk:
        chunks.append(current_chunk)

    return [c for c in chunks if c.strip()]


def _split_sentences(text: str) -> List[str]:
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]
