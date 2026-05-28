"""Shared state passed between LangGraph nodes."""
from __future__ import annotations

from typing import List, TypedDict

from app.models import DealInput, NormalizedDeal, RetrievedSource, SOW


class AgentState(TypedDict, total=False):
    raw_deal: DealInput
    use_rag: bool

    normalized: NormalizedDeal
    sources: List[RetrievedSource]
    context_text: str
    sow: SOW
    validation_notes: List[str]
