"""Repository ingestion utilities.

- Clone the repository via GitPython.
- Filter supported file extensions.
- Parse source code using Tree‑sitter to identify symbols.
- Chunk code with overlap and generate embeddings.
- Upsert chunks to Qdrant.
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import List

import git
from tree_sitter import Language, Parser
from sentence_transformers import SentenceTransformer

from .config import settings
from .vector_store import get_collection

# Load Tree‑sitter languages (compiled shared library should be built separately)
LANGUAGES_SO = Path(__file__).parent / "languages.so"
Language.build_library(
    str(LANGUAGES_SO),
    [
        "vendor/tree-sitter-python",
        "vendor/tree-sitter-javascript",
        "vendor/tree-sitter-typescript/typescript",
        "vendor/tree-sitter-java",
        "vendor/tree-sitter-cpp",
        "vendor/tree-sitter-c",
        "vendor/tree-sitter-html",
        "vendor/tree-sitter-css",
        "vendor/tree-sitter-json",
        "vendor/tree-sitter-yaml",
        "vendor/tree-sitter-sql",
    ],
)

PY_LANG = Language(str(LANGUAGES_SO), "python")
JS_LANG = Language(str(LANGUAGES_SO), "javascript")
TS_LANG = Language(str(LANGUAGES_SO), "typescript")
# Additional languages can be added similarly.

PARSER_MAP = {
    ".py": PY_LANG,
    ".js": JS_LANG,
    ".ts": TS_LANG,
    # add other extensions as needed
}

EMBEDDER = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)

SUPPORTED_EXTS = {".py", ".js", ".ts", ".java", ".cpp", ".c", ".html", ".css", ".md", ".json", ".yaml", ".yml", ".sql"}
IGNORED_DIRS = {".git", "node_modules", "dist", "build", "__pycache__", ".venv", "venv", "coverage"}


def _clone_repo(repo_url: str) -> Path:
    tmp_dir = Path(tempfile.mkdtemp())
    git.Repo.clone_from(repo_url, tmp_dir, depth=1)
    return tmp_dir


def _is_supported(file_path: Path) -> bool:
    return file_path.suffix.lower() in SUPPORTED_EXTS and not any(p in IGNORED_DIRS for p in file_path.parts)


def _parse_file(file_path: Path) -> List[dict]:
    # Very basic parser: return a single chunk representing the whole file.
    # In a full implementation we would walk the syntax tree and create chunks per symbol.
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    return [{
        "repository": file_path.parent.name,
        "file": str(file_path.relative_to(file_path.parents[2])),
        "language": file_path.suffix.lstrip('.'),
        "symbol": None,
        "start_line": 1,
        "end_line": content.count("\n") + 1,
        "content": content,
    }]


def _chunk_and_embed(chunks: List[dict]) -> List[dict]:
    for ch in chunks:
        ch["embedding"] = EMBEDDER.encode(ch["content"]).tolist()
    return chunks


async def process_repository(repo_url: str, user_id: str) -> str:
    """Main entry point for ingestion.

    Returns a repository identifier used for later queries.
    """
    repo_path = _clone_repo(repo_url)
    repo_name = repo_url.rstrip('/')
    repo_name = repo_name.split('/')[-1]
    collection = get_collection(repo_name)
    all_chunks = []
    for root, _, files in os.walk(repo_path):
        for fname in files:
            fpath = Path(root) / fname
            if _is_supported(fpath):
                chunks = _parse_file(fpath)
                all_chunks.extend(chunks)
    enriched = _chunk_and_embed(all_chunks)
    # Upsert to Qdrant
    points = [
        {
            "id": idx,
            "vector": ch["embedding"],
            "payload": {
                "repository": repo_name,
                "file": ch["file"],
                "language": ch["language"],
                "symbol": ch["symbol"],
                "start_line": ch["start_line"],
                "end_line": ch["end_line"],
                "content": ch["content"],
            },
        }
        for idx, ch in enumerate(enriched)
    ]
    collection.upload_points(points)
    # Cleanup temporary clone
    shutil.rmtree(repo_path)
    return repo_name
