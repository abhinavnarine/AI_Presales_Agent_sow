"""Embeddings layer.

Primary backend is HuggingFace sentence-transformers (real neural embeddings).
If that model cannot be loaded (e.g. offline, no download), we transparently fall
back to a deterministic hashing embedder so the RAG pipeline always works. The
hash embedder is lower quality but produces a genuine vector space that FAISS can
index and search, which keeps the whole system runnable anywhere.
"""
from __future__ import annotations

import hashlib
import math
import re
from typing import List

from langchain_core.embeddings import Embeddings

from app import config
from app.logging_config import get_logger

logger = get_logger(__name__)


class HashingEmbeddings(Embeddings):
    """Deterministic, dependency-free embeddings via hashed bag-of-words.

    Each token is hashed into the vector dimension and weighted; the vector is
    L2-normalized so cosine similarity is meaningful. Not as good as neural
    embeddings, but fully offline and reproducible.
    """

    def __init__(self, dim: int = config.HASH_EMBED_DIM):
        self.dim = dim

    def _embed(self, text: str) -> List[float]:
        vec = [0.0] * self.dim
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        for tok in tokens:
            h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
            idx = h % self.dim
            sign = 1.0 if (h >> 8) % 2 == 0 else -1.0
            vec[idx] += sign
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)


def get_embeddings() -> tuple[Embeddings, str]:
    """Return (embeddings, backend_name_actually_used)."""
    if config.EMBEDDING_BACKEND == "huggingface":
        try:
            from langchain_huggingface import HuggingFaceEmbeddings

            emb = HuggingFaceEmbeddings(model_name=config.HUGGINGFACE_EMBED_MODEL)
            # Probe once so a failed download surfaces here, not mid-pipeline.
            emb.embed_query("probe")
            logger.info("Using HuggingFace embeddings: %s", config.HUGGINGFACE_EMBED_MODEL)
            return emb, "huggingface"
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "HuggingFace embeddings unavailable (%s); falling back to hash",
                str(exc)[:120],
            )
    logger.info("Using hash embeddings (dim=%d)", config.HASH_EMBED_DIM)
    return HashingEmbeddings(), "hash"
