"""Unit tests for RepoMind FastAPI endpoints."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from backend.main import app, require_user
from backend.auth import User


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_user():
    return User(id="12345", login="testuser", avatar_url="https://github.com/testuser.png")


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unauthenticated_endpoints(client):
    # Missing auth token
    resp_ingest = client.post("/ingest", json={"repo_url": "https://github.com/owner/repo"})
    assert resp_ingest.status_code == 401

    resp_query = client.post("/query", json={"repository": "owner/repo", "question": "What does this do?"})
    assert resp_query.status_code == 401

    resp_repos = client.get("/repos")
    assert resp_repos.status_code == 401

    resp_delete = client.delete("/repos/test_collection")
    assert resp_delete.status_code == 401


def test_ingest_endpoint(client, mock_user):
    app.dependency_overrides[require_user] = lambda: mock_user
    try:
        with patch("backend.ingestion.process_repository", new_callable=AsyncMock) as mock_ingest:
            mock_ingest.return_value = "owner_repo"
            response = client.post("/ingest", json={"repo_url": "https://github.com/owner/repo"})
            assert response.status_code == 202
            data = response.json()
            assert data["detail"] == "Ingestion started"
            assert data["repo_id"] == "owner_repo"
            mock_ingest.assert_awaited_once_with("https://github.com/owner/repo", user_id="12345")
    finally:
        app.dependency_overrides.clear()


def test_query_endpoint(client, mock_user):
    app.dependency_overrides[require_user] = lambda: mock_user
    try:
        mock_chunk = MagicMock()
        mock_chunk.payload = {
            "file_path": "main.py",
            "start_line": 1,
            "end_line": 10,
            "code_text": "print('hello')",
        }

        with patch("backend.retrieval.hybrid_search", new_callable=AsyncMock) as mock_search, \
             patch("backend.llm.generate_answer", new_callable=AsyncMock) as mock_llm:
            mock_search.return_value = [mock_chunk]
            mock_llm.return_value = "This is the generated answer."

            response = client.post(
                "/query",
                json={"repository": "owner/repo", "question": "How does main work?"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["answer"] == "This is the generated answer."
            assert len(data["citations"]) == 1
            assert data["citations"][0]["file_path"] == "main.py"
    finally:
        app.dependency_overrides.clear()


def test_list_repos_endpoint(client, mock_user):
    app.dependency_overrides[require_user] = lambda: mock_user
    try:
        with patch("backend.vector_store.list_collections") as mock_list:
            mock_list.return_value = ["repo_a", "repo_b"]
            response = client.get("/repos")
            assert response.status_code == 200
            assert response.json() == {"repositories": ["repo_a", "repo_b"]}
    finally:
        app.dependency_overrides.clear()


def test_delete_repo_endpoint(client, mock_user):
    app.dependency_overrides[require_user] = lambda: mock_user
    try:
        with patch("backend.vector_store.delete_collection") as mock_delete:
            mock_delete.return_value = True
            response = client.delete("/repos/repo_a")
            assert response.status_code == 204
            mock_delete.assert_called_once_with("repo_a")
    finally:
        app.dependency_overrides.clear()
