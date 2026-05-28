"""Pydantic schemas shared across the API and the agent workflow."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class DealInput(BaseModel):
    """Raw deal data as it arrives from the client/UI. Every field is optional
    on purpose: the system must handle messy / incomplete input gracefully."""

    client_name: Optional[str] = None
    industry: Optional[str] = None
    project_type: Optional[str] = None
    objectives: Optional[List[str]] = None
    timeline: Optional[str] = None
    budget_range: Optional[str] = None


class NormalizedDeal(BaseModel):
    """Deal after the parse/normalize node has cleaned it and inferred defaults."""

    client_name: str
    industry: str
    project_type: str
    objectives: List[str]
    timeline: str
    budget_range: str
    inferred_fields: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class RetrievedSource(BaseModel):
    """A single retrieved knowledge-base chunk surfaced to the UI for transparency."""

    source: str
    score: float
    snippet: str


class SOW(BaseModel):
    """Structured Statement of Work."""

    project_overview: str
    scope_of_work: str
    deliverables: str
    timeline: str
    assumptions: str


class GenerateRequest(BaseModel):
    deal: DealInput
    use_rag: bool = True


class GenerateResponse(BaseModel):
    normalized_deal: NormalizedDeal
    sow: SOW
    sources: List[RetrievedSource]
    used_rag: bool
    llm_provider: str
    embedding_backend: str
