"""FAISS vector store: build from the knowledge base, persist, and reload.

The store is built once and cached on disk. Because the embedding backend can
change (huggingface vs hash), we tag the persisted index with the backend name
and rebuild automatically if the configured backend differs from what was saved.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from app import config
from app.rag.embeddings import get_embeddings
from app.rag.loader import load_and_chunk
from app.logging_config import get_logger

logger = get_logger(__name__)


class VectorStore:
    def __init__(self) -> None:
        self.embeddings: Embeddings
        self.backend: str
        self.embeddings, self.backend = get_embeddings()
        self._store: FAISS | None = None

    @property
    def _persist_path(self) -> Path:
        return Path(config.VECTOR_STORE_DIR) / self.backend

    def build(self, force: bool = False) -> "VectorStore":
        persist = self._persist_path
        index_file = persist / "index.faiss"
        if index_file.exists() and not force:
            logger.info("Loading cached FAISS index from %s", persist)
            self._store = FAISS.load_local(
                str(persist),
                self.embeddings,
                allow_dangerous_deserialization=True,
            )
            logger.info("Loaded %d indexed chunks (backend=%s)", self.chunk_count, self.backend)
            return self

        logger.info("Building new FAISS index (backend=%s)", self.backend)
        docs = load_and_chunk()
        self._store = FAISS.from_documents(docs, self.embeddings)
        persist.mkdir(parents=True, exist_ok=True)
        self._store.save_local(str(persist))
        logger.info("Built FAISS index: %d chunks, saved to %s", len(docs), persist)
        return self

    def search(self, query: str, k: int | None = None) -> List[Tuple[Document, float]]:
        if self._store is None:
            self.build()
        k = k or config.RETRIEVAL_TOP_K
        # Use raw FAISS distance (lower = closer) and convert to a bounded
        # similarity in (0, 1] so scores are comparable across embedding
        # backends and never trigger out-of-range warnings.
        results = self._store.similarity_search_with_score(query, k=k)
        return [(doc, 1.0 / (1.0 + float(dist))) for doc, dist in results]

    @property
    def chunk_count(self) -> int:
        if self._store is None:
            return 0
        return self._store.index.ntotal
