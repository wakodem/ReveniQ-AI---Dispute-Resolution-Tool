"""
RAG (Retrieval-Augmented Generation) for ReveniQ dispute resolution.
Loads policy/playbook docs, embeds via Ollama, retrieves relevant chunks for each dispute.
Digital COE Gen AI Team
"""

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import List, Optional, Tuple

try:
    from dotenv import load_dotenv
    _root = Path(__file__).resolve().parent.parent
    load_dotenv(_root / ".env")
except Exception:
    pass

# Default paths
_DEFAULT_DOCS_DIR = Path(__file__).resolve().parent.parent / "docs" / "rag"
def _get_docs_dir() -> Path:
    d = os.environ.get("REVENIQ_RAG_DOCS_DIR", "")
    if d and Path(d).is_dir():
        return Path(d)
    if _DEFAULT_DOCS_DIR.is_dir():
        return _DEFAULT_DOCS_DIR
    return _DEFAULT_DOCS_DIR


def _get_embed_model() -> str:
    return os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text").strip() or "nomic-embed-text"


def _get_base_url() -> str:
    return (os.environ.get("OLLAMA_BASE_URL") or "http://localhost:11434").strip().rstrip("/")


def _get_ollama_embed_timeout() -> int:
    """
    Seconds for Ollama /api/embed. Set OLLAMA_EMBED_TIMEOUT_SECONDS, or falls back to
    OLLAMA_TIMEOUT_SECONDS if set, else 120.
    """
    try:
        raw = os.environ.get("OLLAMA_EMBED_TIMEOUT_SECONDS", "").strip()
        if raw:
            return max(30, int(raw))
        raw2 = os.environ.get("OLLAMA_TIMEOUT_SECONDS", "").strip()
        if raw2:
            return max(30, int(raw2))
        return 120
    except ValueError:
        return 120


def is_rag_disabled() -> bool:
    """Set REVENIQ_RAG_DISABLED=1 to skip RAG (local testing only)."""
    return os.environ.get("REVENIQ_RAG_DISABLED", "").strip().lower() in ("1", "true", "yes")


def is_rag_enabled() -> bool:
    """
    RAG is on by default when the knowledge base directory exists.
    Legacy REVENIQ_RAG_ENABLED=0 no longer disables RAG; use REVENIQ_RAG_DISABLED=1 instead.
    """
    if is_rag_disabled():
        return False
    return _get_docs_dir().is_dir()


def get_rag_docs_dir() -> Path:
    """Resolved path to the RAG knowledge base (docs/rag or REVENIQ_RAG_DOCS_DIR)."""
    return _get_docs_dir()


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks."""
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= chunk_size:
        return [text] if text else []
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end].strip())
        start = end - overlap
    return chunks


def _load_documents(docs_dir: Path) -> List[str]:
    """Load .txt and .md files from docs_dir into a list of chunks."""
    chunks = []
    for ext in ("*.txt", "*.md"):
        for path in docs_dir.glob(ext):
            try:
                raw = path.read_text(encoding="utf-8", errors="ignore")
                for c in _chunk_text(raw):
                    if len(c) > 30:
                        chunks.append(c)
            except Exception:
                continue
    return chunks


def _call_ollama_embed_one(
    text: str, model: str, base_url: str, timeout: Optional[int] = None
) -> Optional[List[float]]:
    """Ollama /api/embed returns one vector per request."""
    if timeout is None:
        timeout = _get_ollama_embed_timeout()
    url = f"{base_url}/api/embed"
    body = json.dumps({"model": model, "input": text}).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    emb = data.get("embeddings", data.get("embedding"))
    if isinstance(emb, list) and len(emb) == 1 and isinstance(emb[0], list):
        return emb[0]
    if isinstance(emb, list) and emb and isinstance(emb[0], (int, float)):
        return emb
    return None


def _call_ollama_embed(texts: List[str], model: str, base_url: str, timeout: Optional[int] = None) -> List[List[float]]:
    """Embed multiple texts via Ollama (one request per text for compatibility)."""
    if timeout is None:
        timeout = _get_ollama_embed_timeout()
    out = []
    for t in texts:
        v = _call_ollama_embed_one(t, model, base_url, timeout=timeout)
        if v:
            out.append(v)
        else:
            out.append([0.0] * 768)
    return out


# Module-level cache: (chunks, embeddings) built once
_rag_cache: Optional[Tuple[List[str], List[List[float]]]] = None


def _build_index(docs_dir: Path, embed_model: str, base_url: str) -> Tuple[List[str], List[List[float]]]:
    """Load docs, chunk, embed; return (chunks, embeddings)."""
    global _rag_cache
    if _rag_cache is not None:
        return _rag_cache
    chunks = _load_documents(docs_dir)
    if not chunks:
        _rag_cache = ([], [])
        return _rag_cache
    embeddings = []
    batch_size = 10
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        try:
            emb_batch = _call_ollama_embed(batch, embed_model, base_url)
            if emb_batch:
                embeddings.extend(emb_batch)
            else:
                for t in batch:
                    e = _call_ollama_embed_one(t, embed_model, base_url)
                    if e:
                        embeddings.append(e)
                    else:
                        embeddings.append([0.0] * 768)
        except Exception:
            try:
                for t in batch:
                    e = _call_ollama_embed_one(t, embed_model, base_url)
                    if e:
                        embeddings.append(e)
                    else:
                        embeddings.append([0.0] * 768)
            except Exception:
                embeddings.extend([[0.0] * 768] * len(batch))
    if len(embeddings) != len(chunks):
        chunks = chunks[: len(embeddings)]
    _rag_cache = (chunks, embeddings)
    return _rag_cache


def retrieve(query: str, category: str = "", top_k: int = 3) -> str:
    """
    Retrieve top_k most relevant chunks from RAG index for this query (and optional category).
    Returns a single string to inject into the LLM prompt, or empty if RAG disabled/fails.
    """
    if is_rag_disabled() or not is_rag_enabled():
        return ""
    docs_dir = _get_docs_dir()
    if not docs_dir.is_dir():
        return ""
    embed_model = _get_embed_model()
    base_url = _get_base_url()
    try:
        chunks, embeddings = _build_index(docs_dir, embed_model, base_url)
    except Exception:
        return ""
    if not chunks or not embeddings:
        return ""
    query_combined = f"{category} {query}"[:2000].strip()
    try:
        q_vec_single = _call_ollama_embed_one(query_combined, embed_model, base_url)
        q_emb = [q_vec_single] if q_vec_single else []
    except Exception:
        return ""
    if not q_emb:
        return ""
    q_vec = q_emb[0]
    dim = len(q_vec)
    scores = []
    for i, e in enumerate(embeddings):
        if len(e) != dim:
            continue
        dot = sum(a * b for a, b in zip(q_vec, e))
        scores.append((i, dot))
    scores.sort(key=lambda x: -x[1])
    top = scores[:top_k]
    if not top:
        return ""
    lines = [chunks[i] for i, _ in top]
    return "Relevant policy/guidance from knowledge base:\n" + "\n---\n".join(lines)


def clear_rag_cache() -> None:
    """Clear the in-memory RAG index (e.g. after adding new docs)."""
    global _rag_cache
    _rag_cache = None
    try:
        from . import ai_sql_runner

        ai_sql_runner.clear_literal_sql_cache()
    except Exception:
        pass
