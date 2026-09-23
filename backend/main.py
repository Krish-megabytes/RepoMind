"""RepoMind FastAPI backend entry point."""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer
from pydantic import BaseModel, HttpUrl

from . import config, ingestion, retrieval, llm, auth

app = FastAPI(title="RepoMind Backend", version="0.1.0")

# OAuth2 scheme – placeholder; actual implementation in auth.py
oauth2_scheme = OAuth2AuthorizationCodeBearer(authorizationUrl="/auth/login", tokenUrl="/auth/token")

class IngestRequest(BaseModel):
    repo_url: HttpUrl

class QueryRequest(BaseModel):
    repository: str  # format: owner/name
    question: str

@app.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_repo(request: IngestRequest, token: str = Depends(oauth2_scheme)):
    # Validate auth token (placeholder)
    user = await auth.get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    # Trigger ingestion (synchronous for now)
    result = await ingestion.process_repository(request.repo_url, user_id=user.id)
    return {"detail": "Ingestion started", "repo_id": result}

@app.post("/query")
async def query_repo(request: QueryRequest, token: str = Depends(oauth2_scheme)):
    user = await auth.get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    # Retrieve relevant chunks
    chunks = await retrieval.hybrid_search(request.repository, request.question)
    # Generate answer
    answer = await llm.generate_answer(request.question, chunks)
    return {"answer": answer, "citations": [c.metadata for c in chunks]}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
