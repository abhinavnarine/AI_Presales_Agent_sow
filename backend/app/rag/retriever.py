"""Retriever: turns a normalized deal into targeted queries and gathers
de-duplicated, ranked knowledge-base context.

Rather than one generic query, we issue several focused queries (one per
objective plus project-type and compliance-aware queries). This multi-query
retrieval improves recall on a small knowledge base and mirrors how a solution
architect would look up several distinct topics for one deal.
"""
from __future__ import annotations

from typing import List

from app import config
from app.models import NormalizedDeal, RetrievedSource
from app.rag.vector_store import VectorStore
from app.logging_config import get_logger

logger = get_logger(__name__)


def _build_queries(deal: NormalizedDeal) -> List[str]:
    queries = [
        f"Statement of Work structure and sections for a {deal.project_type} project",
        f"{deal.project_type} best practices delivery framework",
        f"timeline phases and estimation for a {deal.budget_range} {deal.project_type}",
    ]
    for obj in deal.objectives:
        queries.append(obj)
    industry = (deal.industry or "").lower()
    if "health" in industry or any(
        "hipaa" in o.lower() or "compliance" in o.lower() for o in deal.objectives
    ):
        queries.append("HIPAA technical safeguards encryption audit controls for PHI")
    return queries


class KnowledgeRetriever:
    def __init__(self, store: VectorStore):
        self.store = store

    def retrieve(self, deal: NormalizedDeal, top_k: int | None = None) -> List[RetrievedSource]:
        top_k = top_k or config.RETRIEVAL_TOP_K
        queries = _build_queries(deal)
        logger.debug("retriever: %d queries for %s", len(queries), deal.project_type)
        seen: dict[str, RetrievedSource] = {}
        for query in queries:
            for doc, score in self.store.search(query, k=top_k):
                key = doc.page_content[:80]
                if key in seen:
                    # keep the best score we have seen for this chunk
                    if score > seen[key].score:
                        seen[key].score = round(float(score), 4)
                    continue
                seen[key] = RetrievedSource(
                    source=f"{doc.metadata.get('source','?')} \u2014 {doc.metadata.get('section','')}",
                    score=round(float(score), 4),
                    snippet=doc.page_content,
                )
        ranked = sorted(seen.values(), key=lambda s: s.score, reverse=True)
        # Cap total context so LLM prompts stay within token limits.
        result = ranked[: top_k * 2]
        logger.info("retriever: returning %d unique chunks", len(result))
        return result
