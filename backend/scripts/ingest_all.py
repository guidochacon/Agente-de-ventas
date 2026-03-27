#!/usr/bin/env python3
"""
Ingest all files in the knowledge_base/ directory into ChromaDB.
Run from the backend/ directory:
  python scripts/ingest_all.py
"""
import os
import sys
import asyncio
import hashlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import init_db, AsyncSessionLocal
from models.document import Document
from sqlalchemy import select
from rag import vector_store
from rag.ingestion import load_text, load_pdf, load_url

KB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "knowledge_base")


async def ingest_file(db, filepath: str):
    filename = os.path.basename(filepath)
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".pdf":
        chunks = load_pdf(filepath, source_name=filename)
        source_type = "pdf"
    elif ext in (".txt", ".md"):
        with open(filepath, encoding="utf-8") as f:
            content = f.read()
        chunks = load_text(content, source_name=filename)
        source_type = "text"
    else:
        print(f"  Skipping {filename} (unsupported format)")
        return

    if not chunks:
        print(f"  No content extracted from {filename}")
        return

    content = "".join(c["text"] for c in chunks)
    content_hash = hashlib.sha256(content.encode()).hexdigest()

    result = await db.execute(select(Document).where(Document.content_hash == content_hash))
    existing = result.scalar_one_or_none()
    if existing:
        print(f"  Already ingested: {filename} ({existing.chunk_count} chunks)")
        return

    doc = Document(
        name=filename,
        source_type=source_type,
        file_path=filepath,
        content_hash=content_hash,
        chunk_count=0,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    count = vector_store.add_chunks(doc.id, chunks)
    doc.chunk_count = count
    await db.commit()

    print(f"  ✓ {filename} → {count} chunks")


async def main():
    await init_db()
    async with AsyncSessionLocal() as db:
        files = [
            os.path.join(KB_DIR, f)
            for f in os.listdir(KB_DIR)
            if not f.startswith(".") and os.path.isfile(os.path.join(KB_DIR, f))
        ]

        if not files:
            print("No files found in knowledge_base/")
            return

        print(f"Ingesting {len(files)} file(s) from knowledge_base/\n")
        for filepath in sorted(files):
            print(f"Processing: {os.path.basename(filepath)}")
            await ingest_file(db, filepath)

    print(f"\nDone! Total vectors in DB: {vector_store.count()}")


if __name__ == "__main__":
    asyncio.run(main())
