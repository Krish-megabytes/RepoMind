"""Qdrant vector store utilities for RepoMind.

Provides functions to get/create/delete a collection per repository.
"""

from qdrant_client import QdrantClient
from qdrant_client.http import models
from .config import settings

_client: QdrantClient | None = None


def _get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
    return _client


def _collection_name(repo_name: str) -> str:
    """Sanitize repo name into a valid Qdrant collection name."""
    return f"repo_{repo_name.replace('-', '_').replace('.', '_')}"


def get_collection(repo_name: str) -> str:
    """Ensure a collection exists for a repository and return its name."""
    client = _get_client()
    cname = _collection_name(repo_name)
    existing = [c.name for c in client.get_collections().collections]
    if cname not in existing:
        client.create_collection(
            collection_name=cname,
            vectors_config=models.VectorParams(
                size=768,  # paraphrase-MPNet-base-v2 dimension
                distance=models.Distance.COSINE,
            ),
        )
    return cname


def upsert_points(repo_name: str, points: list[dict]):
    """Upsert a list of point dicts with id, vector, payload into the collection."""
    client = _get_client()
    cname = get_collection(repo_name)
    batch = [
        models.PointStruct(
            id=p["id"],
            vector=p["vector"],
            payload=p["payload"],
        )
        for p in points
    ]
    client.upsert(collection_name=cname, points=batch)


def search(repo_name: str, query_vector: list[float], limit: int = 10):
    """Perform vector similarity search and return results with payloads."""
    client = _get_client()
    cname = _collection_name(repo_name)
    return client.search(
        collection_name=cname,
        query_vector=query_vector,
        limit=limit,
        with_payload=True,
    )


def list_collections() -> list[str]:
    """Return all repository collection names."""
    client = _get_client()
    return [c.name for c in client.get_collections().collections]


def delete_collection(repo_name: str):
    """Delete a repository's collection."""
    client = _get_client()
    cname = _collection_name(repo_name)
    existing = [c.name for c in client.get_collections().collections]
    if cname not in existing:
        raise ValueError(f"Collection '{cname}' not found")
    client.delete_collection(collection_name=cname)
