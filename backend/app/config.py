"""Central configuration. All tunables live here so the rest of the code stays clean."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- Logging ---------------------------------------------------------------
# LOG_LEVEL: DEBUG | INFO | WARNING | ERROR (see app.logging_config)

# --- Paths -----------------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parent.parent
APP_DIR = Path(__file__).resolve().parent
KNOWLEDGE_BASE_DIR = APP_DIR / "knowledge_base"
VECTOR_STORE_DIR = BACKEND_DIR / ".vector_store"

# --- RAG knobs -------------------------------------------------------------
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "900"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "4"))

# Embedding backend: "huggingface" (real neural embeddings, recommended) or
# "hash" (deterministic offline fallback, no model download required).
# If "huggingface" is selected but the model cannot be loaded, the code
# automatically falls back to "hash" so the pipeline never hard-fails.
EMBEDDING_BACKEND = os.getenv("EMBEDDING_BACKEND", "huggingface")
HUGGINGFACE_EMBED_MODEL = os.getenv(
    "HUGGINGFACE_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)
HASH_EMBED_DIM = 512

# --- LLM knobs -------------------------------------------------------------
# Provider: "anthropic" (uses ANTHROPIC_API_KEY) or "mock" (no key needed,
# deterministic templated generation so the system runs end-to-end offline).
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2000"))


def effective_llm_provider() -> str:
    """Fall back to mock if anthropic is requested but no key is present."""
    if LLM_PROVIDER == "anthropic" and not ANTHROPIC_API_KEY:
        return "mock"
    return LLM_PROVIDER
