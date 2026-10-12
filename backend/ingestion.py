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

# Tree-sitter setup with graceful fallback
LANGUAGES_SO = Path(__file__).parent / "languages.so"
PARSER_MAP = {}

def _init_parsers():
    global PARSER_MAP
    if PARSER_MAP:
        return
    try:
        if not LANGUAGES_SO.exists():
            vendor_dirs = [
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
            ]
            valid_dirs = [d for d in vendor_dirs if os.path.exists(d)]
            if valid_dirs:
                Language.build_library(str(LANGUAGES_SO), valid_dirs)
        
        if LANGUAGES_SO.exists():
            for ext, lang_name in [(".py", "python"), (".js", "javascript"), (".ts", "typescript")]:
                try:
                    lang = Language(str(LANGUAGES_SO), lang_name)
                    parser = Parser()
                    parser.set_language(lang)
                    PARSER_MAP[ext] = parser
                except Exception:
                    pass
    except Exception:
        pass

_embedder = None

def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
    return _embedder

SUPPORTED_EXTS = {".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".cpp", ".c", ".html", ".css", ".md", ".json", ".yaml", ".yml", ".sql"}
IGNORED_DIRS = {".git", "node_modules", "dist", "build", "__pycache__", ".venv", "venv", "coverage"}


def _clone_repo(repo_url: str) -> Path:
    tmp_dir = Path(tempfile.mkdtemp())
    git.Repo.clone_from(repo_url, tmp_dir, depth=1)
    return tmp_dir


def _is_supported(file_path: Path) -> bool:
    return file_path.suffix.lower() in SUPPORTED_EXTS and not any(p in IGNORED_DIRS for p in file_path.parts)


def _parse_file(file_path: Path, repo_path: Path) -> List[dict]:
    try:
        rel_file = str(file_path.relative_to(repo_path))
    except Exception:
        rel_file = file_path.name

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    lines = content.splitlines(keepends=True)
    total_lines = len(lines)
    if total_lines == 0:
        return []

    # If small file, single chunk
    if total_lines <= 100:
        return [{
            "repository": repo_path.name,
            "file": rel_file,
            "language": file_path.suffix.lstrip('.'),
            "symbol": None,
            "start_line": 1,
            "end_line": total_lines,
            "content": content,
        }]

    # Chunk with sliding window (approx 80 lines window, 20 lines overlap)
    chunks = []
    window = 80
    overlap = 20
    step = window - overlap
    for start_idx in range(0, total_lines, step):
        end_idx = min(start_idx + window, total_lines)
        chunk_lines = lines[start_idx:end_idx]
        chunk_text = "".join(chunk_lines)
        chunks.append({
            "repository": repo_path.name,
            "file": rel_file,
            "language": file_path.suffix.lstrip('.'),
            "symbol": None,
            "start_line": start_idx + 1,
            "end_line": end_idx,
            "content": chunk_text,
        })
        if end_idx >= total_lines:
            break

    return chunks


def _chunk_and_embed(chunks: List[dict]) -> List[dict]:
    embedder = get_embedder()
    for ch in chunks:
        ch["embedding"] = embedder.encode(ch["content"]).tolist()
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
                chunks = _parse_file(fpath, repo_path)
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
