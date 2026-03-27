import os
import hashlib
import tempfile
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.database import get_db
from models.document import Document
from rag import vector_store
from rag.ingestion import load_text, load_pdf, load_url

router = APIRouter(prefix="/api/knowledge")


class IngestTextRequest(BaseModel):
    name: str
    content: str


class IngestURLRequest(BaseModel):
    url: str
    name: str | None = None


@router.post("/ingest/text")
async def ingest_text(body: IngestTextRequest, db: AsyncSession = Depends(get_db)):
    content_hash = hashlib.sha256(body.content.encode()).hexdigest()
    existing = await _check_existing(db, content_hash)
    if existing:
        return {"message": "Document already exists", "doc_id": existing.id}

    chunks = load_text(body.content, source_name=body.name)
    doc = await _save_document(db, body.name, "text", content_hash, chunks)
    return {"message": "Ingested", "doc_id": doc.id, "chunks": doc.chunk_count}


@router.post("/ingest/url")
async def ingest_url(body: IngestURLRequest, db: AsyncSession = Depends(get_db)):
    try:
        chunks = load_url(body.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    content = "".join(c["text"] for c in chunks)
    content_hash = hashlib.sha256(content.encode()).hexdigest()
    existing = await _check_existing(db, content_hash)
    if existing:
        return {"message": "Document already exists", "doc_id": existing.id}

    name = body.name or body.url
    doc = await _save_document(db, name, "url", content_hash, chunks, source_url=body.url)
    return {"message": "Ingested", "doc_id": doc.id, "chunks": doc.chunk_count}


@router.post("/ingest/pdf")
async def ingest_pdf(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    if not file.filename or not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    content = await file.read()
    content_hash = hashlib.sha256(content).hexdigest()
    existing = await _check_existing(db, content_hash)
    if existing:
        return {"message": "Document already exists", "doc_id": existing.id}

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        chunks = load_pdf(tmp_path, source_name=file.filename)
    finally:
        os.unlink(tmp_path)

    doc = await _save_document(db, file.filename, "pdf", content_hash, chunks)
    return {"message": "Ingested", "doc_id": doc.id, "chunks": doc.chunk_count}


@router.get("")
async def list_documents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).order_by(Document.ingested_at.desc()))
    docs = result.scalars().all()
    return {"documents": [d.to_dict() for d in docs], "total_vectors": vector_store.count()}


@router.delete("/{doc_id}")
async def delete_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    vector_store.delete_doc(doc_id)
    await db.delete(doc)
    await db.commit()
    return {"message": "Deleted"}


async def _check_existing(db: AsyncSession, content_hash: str) -> Document | None:
    result = await db.execute(select(Document).where(Document.content_hash == content_hash))
    return result.scalar_one_or_none()


async def _save_document(
    db: AsyncSession,
    name: str,
    source_type: str,
    content_hash: str,
    chunks: list[dict],
    source_url: str | None = None,
) -> Document:
    doc = Document(
        name=name,
        source_type=source_type,
        source_url=source_url,
        content_hash=content_hash,
        chunk_count=0,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    count = vector_store.add_chunks(doc.id, chunks)
    doc.chunk_count = count
    await db.commit()
    return doc
