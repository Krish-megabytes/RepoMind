"""Retrieval utilities for RepoMind.

Provides hybrid semantic + keyword search over Qdrant collection.
"""

from typing import List

from qdrant_client import QdrantClient
from qdrant_client.http import models
from .config import settings
from .vector_store import get_collection
from whoosh import index
from whoosh.fields import Schema, TEXT, ID, NUMERIC
from whoosh.qparser import MultifieldParser
import os

# Whoosh index directory (per repo) – will be created on first use
def _get_whoosh_index(repo_name: str):
    idx_dir = os.path.join(".whoosh_index", repo_name)
    os.makedirs(idx_dir, exist_ok=True)
    if not index.exists_in(idx_dir):
        schema = Schema(
            doc_id=NUMERIC(stored=True, unique=True),
            file=TEXT(stored=True),
            content=TEXT(stored=True),
        )
        return index.create_in(idx_dir, schema)
    return index.open_dir(idx_dir)

def _index_documents(repo_name: str, points: List[dict]):
    idx = _get_whoosh_index(repo_name)
    writer = idx.writer()
    for p in points:
        payload = p["payload"]
        writer.add_document(
            doc_id=p["id"],
            file=payload.get("file", ""),
            content=payload.get("content", ""),
        )
    writer.commit()

async def hybrid_search(repo_name: str, query: str, top_k: int = 5, weight_semantic: float = 0.7):
    """Perform a hybrid search.

    Returns a list of Qdrant points (with payload) ordered by combined score.
    """
    collection = get_collection(repo_name)
    # Semantic search
    vector = await _embed_query(query)
    semantic_res = collection.search(
        query_vector=vector,
        limit=top_k * 2,
        with_payload=True,
    )
    # Keyword search via Whoosh
    idx = _get_whoosh_index(repo_name)
    with idx.searcher() as searcher:
        parser = MultifieldParser(["file", "content"], schema=idx.schema)
        kw_res = searcher.search(parser.parse(query), limit=top_k * 2)
        kw_ids = {hit["doc_id"] for hit in kw_res}
    # Combine scores (simple weighted ranking)
    combined = []
    for point in semantic_res:
        doc_id = point.id
        sem_score = point.score
        kw_score = 1.0 if doc_id in kw_ids else 0.0
        combined_score = weight_semantic * sem_score + (1 - weight_semantic) * kw_score
        combined.append((combined_score, point))
    combined.sort(key=lambda x: x[0], reverse=True)
    return [pt for _, pt in combined[:top_k]]

async def _embed_query(text: str):
    # Re‑use the same SentenceTransformer model used for embeddings
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
    return model.encode(text).tolist()
