"""Pydantic models for RepoMind API requests and responses."""

from pydantic import BaseModel, HttpUrl

class IngestRequest(BaseModel):
    repo_url: HttpUrl

class IngestResponse(BaseModel):
    detail: str
    repo_id: str

class QueryRequest(BaseModel):
    repository: str  # owner/name
    question: str

class QueryResponse(BaseModel):
    answer: str
    citations: list[dict]
