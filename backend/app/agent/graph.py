"""Assemble the LangGraph workflow and expose a single run() entry point.

Graph shape (linear, but each node is independently swappable / extensible):

    START -> parse_input -> retrieve -> generate_sow -> validate_refine -> END

Dependencies (vector store, retriever, LLM) are constructed once and injected
into the nodes via closures, so the compiled graph is reusable across requests.
"""
from __future__ import annotations

from functools import lru_cache

from langgraph.graph import StateGraph, START, END

from app.llm import LLMClient
from app.models import DealInput, GenerateResponse
from app.rag.retriever import KnowledgeRetriever
from app.rag.vector_store import VectorStore
from app.agent.nodes import (
    parse_input,
    make_retrieve_node,
    make_generate_node,
    validate_refine,
)
from app.agent.state import AgentState
from app.logging_config import get_logger

logger = get_logger(__name__)


class PresalesAgent:
    def __init__(self) -> None:
        logger.info("Initializing presales agent (vector store, retriever, LLM)")
        self.vector_store = VectorStore().build()
        self.retriever = KnowledgeRetriever(self.vector_store)
        self.llm = LLMClient()
        self.graph = self._build_graph()
        logger.info(
            "Agent ready: llm=%s embedding=%s chunks=%d",
            self.llm.provider,
            self.vector_store.backend,
            self.vector_store.chunk_count,
        )

    def _build_graph(self):
        g = StateGraph(AgentState)
        g.add_node("parse_input", parse_input)
        g.add_node("retrieve", make_retrieve_node(self.retriever))
        g.add_node("generate_sow", make_generate_node(self.llm))
        g.add_node("validate_refine", validate_refine)

        g.add_edge(START, "parse_input")
        g.add_edge("parse_input", "retrieve")
        g.add_edge("retrieve", "generate_sow")
        g.add_edge("generate_sow", "validate_refine")
        g.add_edge("validate_refine", END)
        return g.compile()

    def run(self, deal: DealInput, use_rag: bool = True) -> GenerateResponse:
        logger.info(
            "Running graph for client=%s project=%s use_rag=%s",
            deal.client_name,
            deal.project_type,
            use_rag,
        )
        final: AgentState = self.graph.invoke(
            {"raw_deal": deal, "use_rag": use_rag}
        )
        logger.info(
            "Graph complete: sources=%d validation_notes=%d",
            len(final.get("sources", [])),
            len(final.get("validation_notes", [])),
        )
        return GenerateResponse(
            normalized_deal=final["normalized"],
            sow=final["sow"],
            sources=final.get("sources", []),
            used_rag=use_rag,
            llm_provider=self.llm.provider,
            embedding_backend=self.vector_store.backend,
        )


@lru_cache(maxsize=1)
def get_agent() -> PresalesAgent:
    """Singleton so the vector store and model load only once."""
    return PresalesAgent()
