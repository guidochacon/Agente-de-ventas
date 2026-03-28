import os
import hashlib
import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions

_default_data = os.path.join(os.path.dirname(__file__), "..", "data")
CHROMA_DIR = os.path.join(os.environ.get("DATA_DIR", _default_data), "chroma")
COLLECTION_NAME = "sales_knowledge"

_client = None
_collection = None
_ef = None


def _get_ef() -> embedding_functions.DefaultEmbeddingFunction:
    global _ef
    if _ef is None:
        _ef = embedding_functions.DefaultEmbeddingFunction()
    return _ef


def _get_collection() -> chromadb.Collection:
    global _client, _collection
    if _collection is None:
        os.makedirs(CHROMA_DIR, exist_ok=True)
        _client = chromadb.PersistentClient(
            path=CHROMA_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=_get_ef(),
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def embed(texts: list[str]) -> list[list[float]]:
    return list(_get_ef()(texts))


def add_chunks(doc_id: str, chunks: list[dict]) -> int:
    """Add document chunks to the vector store. Returns number of chunks added."""
    if not chunks:
        return 0

    collection = _get_collection()
    texts = [c["text"] for c in chunks]
    embeddings = embed(texts)

    ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
    metadatas = []
    for c in chunks:
        meta = {k: str(v) for k, v in c.get("metadata", {}).items()}
        meta["doc_id"] = doc_id
        metadatas.append(meta)

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )
    return len(chunks)


def query(query_text: str, n_results: int = 5) -> list[dict]:
    """Query the vector store and return top-N relevant chunks."""
    collection = _get_collection()
    if collection.count() == 0:
        return []

    query_embedding = embed([query_text])[0]
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(n_results, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for i, doc in enumerate(results["documents"][0]):
        chunks.append(
            {
                "text": doc,
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            }
        )
    return chunks


def delete_doc(doc_id: str):
    """Remove all chunks for a document from the vector store."""
    collection = _get_collection()
    collection.delete(where={"doc_id": doc_id})


def count() -> int:
    return _get_collection().count()


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()
