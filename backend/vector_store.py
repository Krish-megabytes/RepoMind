"""Qdrant vector store utilities for RepoMind.

Provides functions to get/create a collection per repository and perform basic operations.
"""

from qdrant_client import QdrantClient
from qdrant_client.http import models
from .config import settings

_client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)


def get_collection(repo_name: str):
    """Get or create a Qdrant collection for a repository.

    The collection name is sanitized to be URL‑safe.
    """
    collection_name = f"repo_{repo_name.replace('-', '_').replace('.', '_')}"
    # Ensure collection exists with appropriate schema
    if collection_name not in client.get_collections().collections:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
        )
    return client.get_collection(collection_name)
