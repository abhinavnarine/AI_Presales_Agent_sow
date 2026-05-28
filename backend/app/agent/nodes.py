"""The four workflow nodes. Each node is a pure-ish function of state -> partial
state, with external dependencies (retriever, llm) injected by the graph builder.

Separation of responsibilities:
  parse_input     -> clean messy input, infer defaults  (no LLM, no retrieval)
  retrieve        -> RAG: fetch grounding context        (no LLM)
  generate_sow    -> LLM: produce structured SOW         (uses context if present)
  validate_refine -> deterministic QA on the output      (no LLM)
"""
from __future__ import annotations

import json
import re
from typing import List

from app.llm import LLMClient
from app.models import DealInput, NormalizedDeal, RetrievedSource, SOW
from app.rag.retriever import KnowledgeRetriever
from app.agent.state import AgentState

VAGUE_OBJECTIVES = {"improve systems", "improve", "modernize", "better systems"}

DEFAULT_OBJECTIVES = {
    "cloud migration": [
        "Migrate legacy workloads to the target cloud platform",
        "Improve scalability and reliability",
        "Establish a secure, well-governed landing zone",
    ],
    "modernization": [
        "Reduce technical debt in core systems",
        "Improve deployment frequency and reliability",
        "Lower total cost of ownership",
    ],
    "default": [
        "Deliver the stated business outcomes reliably",
        "Improve scalability and maintainability",
    ],
}


# --------------------------------------------------------------------------
# Node 1: parse + normalize
# --------------------------------------------------------------------------
def parse_input(state: AgentState) -> AgentState:
    deal: DealInput = state["raw_deal"]
    inferred: List[str] = []
    warnings: List[str] = []

    client = (deal.client_name or "").strip()
    if not client or client.lower() == "unknown":
        client = "the Client"
        inferred.append("client_name")
        warnings.append("Client name missing/unknown; using neutral placeholder.")

    project_type = (deal.project_type or "").strip() or "Modernization"
    if not (deal.project_type or "").strip():
        inferred.append("project_type")

    industry = (deal.industry or "").strip()
    if not industry:
        joined = " ".join(deal.objectives or []).lower()
        if any(w in joined for w in ("hipaa", "health", "patient", "phi")):
            industry = "Healthcare"
        else:
            industry = "General / Cross-industry"
        inferred.append("industry")

    objectives = [o.strip() for o in (deal.objectives or []) if o and o.strip()]
    if not objectives:
        objectives = DEFAULT_OBJECTIVES.get(
            project_type.lower(), DEFAULT_OBJECTIVES["default"]
        )
        inferred.append("objectives")
        warnings.append("No objectives provided; inferred from project type.")
    elif len(objectives) == 1 and objectives[0].lower() in VAGUE_OBJECTIVES:
        warnings.append(
            f"Objective '{objectives[0]}' is vague; expanded into concrete objectives."
        )
        objectives = DEFAULT_OBJECTIVES.get(
            project_type.lower(), DEFAULT_OBJECTIVES["default"]
        )
        inferred.append("objectives")

    timeline = (deal.timeline or "").strip()
    if not timeline:
        timeline = _infer_timeline(project_type)
        inferred.append("timeline")
        warnings.append(f"Timeline missing; inferred default of '{timeline}'.")

    budget = (deal.budget_range or "").strip()
    if not budget:
        budget = _infer_budget(len(objectives))
        inferred.append("budget_range")
        warnings.append(f"Budget missing; inferred band '{budget}'.")

    normalized = NormalizedDeal(
        client_name=client,
        industry=industry,
        project_type=project_type,
        objectives=objectives,
        timeline=timeline,
        budget_range=budget,
        inferred_fields=inferred,
        warnings=warnings,
    )
    return {"normalized": normalized}


def _infer_timeline(project_type: str) -> str:
    pt = project_type.lower()
    if "assessment" in pt:
        return "6-8 weeks (inferred)"
    if "modernization" in pt:
        return "9-12 months (inferred)"
    return "6 months (inferred)"


def _infer_budget(num_objectives: int) -> str:
    if num_objectives <= 1:
        return "$100k-$250k (inferred)"
    if num_objectives <= 3:
        return "$250k-$500k (inferred)"
    return "$500k-$1M (inferred)"


# --------------------------------------------------------------------------
# Node 2: retrieve (RAG)
# --------------------------------------------------------------------------
def make_retrieve_node(retriever: KnowledgeRetriever):
    def retrieve(state: AgentState) -> AgentState:
        if not state.get("use_rag", True):
            return {"sources": [], "context_text": ""}
        sources = retriever.retrieve(state["normalized"])
        context_text = "\n\n".join(
            f"[{s.source}]\n{s.snippet}" for s in sources
        )
        return {"sources": sources, "context_text": context_text}

    return retrieve


# --------------------------------------------------------------------------
# Node 3: generate SOW (LLM)
# --------------------------------------------------------------------------
SYSTEM_PROMPT = (
    "You are an expert solution architect who writes precise, professional "
    "Statements of Work for enterprise services engagements. You ground every "
    "recommendation in the provided knowledge context when it is available. "
    "Return ONLY a JSON object with keys: project_overview, scope_of_work, "
    "deliverables, timeline, assumptions. No markdown fences, no preamble."
)


def make_generate_node(llm: LLMClient):
    def generate_sow(state: AgentState) -> AgentState:
        normalized: NormalizedDeal = state["normalized"]
        context_text = state.get("context_text", "")
        deal_json = json.dumps(
            {
                "client_name": normalized.client_name,
                "industry": normalized.industry,
                "project_type": normalized.project_type,
                "objectives": normalized.objectives,
                "timeline": normalized.timeline,
                "budget_range": normalized.budget_range,
            }
        )

        context_block = (
            f"<context>\n{context_text}\n</context>\n"
            if context_text
            else "<context></context>\n(No retrieval context supplied — rely on general knowledge.)\n"
        )

        user = (
            "Generate a Statement of Work for the following deal.\n"
            f"<deal>{deal_json}</deal>\n"
            f"{context_block}"
            "Use the knowledge context to ground the scope, deliverables, timeline, "
            "and assumptions. Output the JSON object only."
        )

        raw = llm.complete(SYSTEM_PROMPT, user)
        sow = _parse_sow(raw)
        return {"sow": sow}

    return generate_sow


def _parse_sow(raw: str) -> SOW:
    text = raw.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        data = json.loads(m.group(0)) if m else {}
    return SOW(
        project_overview=str(data.get("project_overview", "")).strip(),
        scope_of_work=str(data.get("scope_of_work", "")).strip(),
        deliverables=str(data.get("deliverables", "")).strip(),
        timeline=str(data.get("timeline", "")).strip(),
        assumptions=str(data.get("assumptions", "")).strip(),
    )


# --------------------------------------------------------------------------
# Node 4: validate / refine
# --------------------------------------------------------------------------
def validate_refine(state: AgentState) -> AgentState:
    sow: SOW = state["sow"]
    notes: List[str] = []
    for field in ("project_overview", "scope_of_work", "deliverables", "timeline", "assumptions"):
        value = getattr(sow, field)
        if not value or len(value) < 20:
            notes.append(f"Section '{field}' was thin; flagged for review.")
    normalized: NormalizedDeal = state["normalized"]
    if normalized.inferred_fields:
        notes.append(
            "SOW relies on inferred fields: " + ", ".join(normalized.inferred_fields)
        )
    if not state.get("use_rag", True):
        notes.append("Generated WITHOUT retrieval — not grounded in the knowledge base.")
    return {"validation_notes": notes}
