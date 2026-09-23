"""RepoMind FastAPI backend entry point.

Exposes endpoints for repository ingestion, querying, listing, and deletion.
Includes GitHub OAuth routes.
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .models import IngestRequest, IngestResponse, QueryRequest, QueryResponse
from .config import settings
from . import ingestion, retrieval, llm, auth

app = FastAPI(title="RepoMind", version="0.1.0", description="AI‑powered GitHub Repository Intelligence Assistant")

# CORS – allow frontend on localhost:5173 (Vite default)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register OAuth routes
app.include_router(auth.router)


# ---------- Dependency ----------
async def require_user(token: str = Depends(auth.get_current_user)):
    if token is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return token


# ---------- Health ----------
@app.get("/health")
async def health_check():
    return {"status": "ok"}


# ---------- Ingest ----------
@app.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_repo(request: IngestRequest, user: auth.User = Depends(require_user)):
    try:
        repo_id = await ingestion.process_repository(str(request.repo_url), user_id=user.id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return IngestResponse(detail="Ingestion started", repo_id=repo_id)


# ---------- Query ----------
@app.post("/query", response_model=QueryResponse)
async def query_repo(request: QueryRequest, user: auth.User = Depends(require_user)):
    try:
        chunks = await retrieval.hybrid_search(request.repository, request.question)
        answer = await llm.generate_answer(request.question, chunks)
        citations = [pt.payload for pt in chunks]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return QueryResponse(answer=answer, citations=citations)


# ---------- List repos ----------
@app.get("/repos")
async def list_repos(user: auth.User = Depends(require_user)):
    from .vector_store import list_collections
    collections = list_collections()
    return {"repositories": collections}


# ---------- Delete repo ----------
@app.delete("/repos/{repo_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repo(repo_name: str, user: auth.User = Depends(require_user)):
    from .vector_store import delete_collection
    try:
        delete_collection(repo_name)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))
