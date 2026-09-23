"""Embedding generation utilities for RepoMind.

Provides a singleton SentenceTransformer model and helpers
for batch encoding and single query encoding.
"""

from sentence_transformers import SentenceTransformer
from .config import settings

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Encode a batch of texts into embedding vectors."""
    model = _get_model()
    return model.encode(texts, show_progress_bar=False).tolist()


def embed_query(text: str) -> list[float]:
    """Encode a single query string into an embedding vector."""
    model = _get_model()
    return model.encode(text).tolist()
