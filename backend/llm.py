"""LLM generation utilities for RepoMind.

Uses the FLAN‑T5 model (via HuggingFace Transformers) to generate answers
based on retrieved chunks. The function formats citations so the caller can
include them in the response.
"""

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from .config import settings

# Load model lazily – this will be executed on first request
_tokenizer = None
_model = None

def _load_model():
    global _tokenizer, _model
    if _tokenizer is None or _model is None:
        _tokenizer = AutoTokenizer.from_pretrained(settings.LLM_MODEL_NAME)
        _model = AutoModelForSeq2SeqLM.from_pretrained(settings.LLM_MODEL_NAME)
        _model.to(torch.device("cpu"))  # change to gpu if available

def _format_context(chunks):
    """Create a prompt string containing the retrieved chunks.
    Each chunk includes file, line numbers and a snippet.
    """
    parts = []
    for i, pt in enumerate(chunks, start=1):
        payload = pt.payload
        snippet = payload.get("content", "").strip().split("\n")[:10]
        snippet_text = " ".join(snippet)
        parts.append(
            f"[Citation {i}] File: {payload.get('file')} Lines: {payload.get('start_line')}-{payload.get('end_line')}\nSnippet: {snippet_text}\n"
        )
    return "\n".join(parts)

async def generate_answer(question: str, chunks):
    """Generate an answer to *question* using the provided *chunks*.
    Returns a string that includes the answer text.
    """
    _load_model()
    context = _format_context(chunks)
    prompt = (
        f"You are an AI assistant answering questions about a code repository.\n"
        f"Question: {question}\n"
        f"Relevant context:\n{context}\n"
        f"Provide a concise answer and reference the citations using the numbers above."
    )
    inputs = _tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024)
    with torch.no_grad():
        output_ids = _model.generate(
            **inputs,
            max_new_tokens=256,
            num_beams=4,
            early_stopping=True,
        )
    answer = _tokenizer.decode(output_ids[0], skip_special_tokens=True)
    return answer
