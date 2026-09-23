"""Configuration settings for RepoMind backend.

Uses environment variables with sensible defaults. Adjust as needed.
"""
import os
from pydantic import BaseSettings, AnyUrl

class Settings(BaseSettings):
    # GitHub OAuth settings
    GITHUB_CLIENT_ID: str = os.getenv("GITHUB_CLIENT_ID", "your_client_id")
    GITHUB_CLIENT_SECRET: str = os.getenv("GITHUB_CLIENT_SECRET", "your_client_secret")
    GITHUB_REDIRECT_URI: AnyUrl = os.getenv(
        "GITHUB_REDIRECT_URI", "http://localhost:3000/auth/callback"
    )

    # Qdrant settings
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    QDRANT_URL: str = f"http://{QDRANT_HOST}:{QDRANT_PORT}"

    # Embedding model
    EMBEDDING_MODEL_NAME: str = os.getenv(
        "EMBEDDING_MODEL_NAME", "sentence-transformers/paraphrase-MPNet-base-v2"
    )

    # LLM model (Flan-T5)
    LLM_MODEL_NAME: str = os.getenv("LLM_MODEL_NAME", "google/flan-t5-base")

    # Chunking parameters
    MAX_CHUNK_TOKENS: int = int(os.getenv("MAX_CHUNK_TOKENS", "512"))
    OVERLAP_TOKENS: int = int(os.getenv("OVERLAP_TOKENS", "50"))

    # Misc
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

settings = Settings()
