"""Configuration settings for RepoMind backend.

Uses environment variables with sensible defaults. Adjust as needed.
"""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # GitHub OAuth settings
    GITHUB_CLIENT_ID: str = "your_client_id"
    GITHUB_CLIENT_SECRET: str = "your_client_secret"
    GITHUB_REDIRECT_URI: str = "http://localhost:3000/auth/callback"

    # Qdrant settings
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_URL: str = "http://localhost:6333"

    # Embedding model
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/paraphrase-MPNet-base-v2"
    EMBEDDING_DIM: int = 768

    # LLM model (Flan-T5)
    LLM_MODEL_NAME: str = "google/flan-t5-base"

    # Chunking parameters
    MAX_CHUNK_TOKENS: int = 512
    OVERLAP_TOKENS: int = 50

    # Misc
    DEBUG: bool = False


settings = Settings()
