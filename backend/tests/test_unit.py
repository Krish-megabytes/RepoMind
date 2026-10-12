"""Unit tests for ingestion helpers and LLM context formatting."""

from pathlib import Path
from unittest.mock import MagicMock
from backend.ingestion import _is_supported, _parse_file
from backend.llm import _format_context
from backend.config import Settings


def test_supported_file_extensions():
    assert _is_supported(Path("main.py")) is True
    assert _is_supported(Path("src/App.tsx")) is True
    assert _is_supported(Path("src/index.ts")) is True
    assert _is_supported(Path("query.sql")) is True
    assert _is_supported(Path("doc.xyz")) is False
    assert _is_supported(Path(".git/config")) is False
    assert _is_supported(Path("node_modules/pkg/index.js")) is False


def test_parse_file_sliding_window(tmp_path):
    repo_dir = tmp_path / "myrepo"
    repo_dir.mkdir()
    test_file = repo_dir / "large.py"

    # Create 250 lines
    content = "\n".join([f"x = {i}" for i in range(250)])
    test_file.write_text(content, encoding="utf-8")

    chunks = _parse_file(test_file, repo_dir)
    assert len(chunks) > 1
    assert chunks[0]["start_line"] == 1
    assert chunks[0]["end_line"] == 80
    assert chunks[0]["file"] == "large.py"
    assert chunks[0]["repository"] == "myrepo"


def test_format_context():
    mock_point1 = MagicMock()
    mock_point1.payload = {
        "file": "utils.py",
        "start_line": 10,
        "end_line": 20,
        "content": "def calculate():\n    return 42",
    }
    mock_point2 = MagicMock()
    mock_point2.payload = {
        "file": "main.py",
        "start_line": 1,
        "end_line": 5,
        "content": "import utils\nutils.calculate()",
    }

    context = _format_context([mock_point1, mock_point2])
    assert "[Citation 1] File: utils.py Lines: 10-20" in context
    assert "[Citation 2] File: main.py Lines: 1-5" in context
    assert "calculate" in context


def test_settings_default_values():
    s = Settings(
        GITHUB_CLIENT_ID="mock_id",
        GITHUB_CLIENT_SECRET="mock_secret",
        GITHUB_REDIRECT_URI="http://localhost:8000/auth/callback"
    )
    assert s.QDRANT_HOST == "localhost"
    assert s.QDRANT_PORT == 6333
    assert s.EMBEDDING_DIM == 768
    assert s.LLM_MODEL_NAME == "google/flan-t5-base"
