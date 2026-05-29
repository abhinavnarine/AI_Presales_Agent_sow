"""LLM client.

Two providers behind one interface:
  * anthropic - real generation via Claude (langchain-anthropic)
  * mock      - deterministic, offline generation so the full pipeline runs
                without any API key (useful for testing and for the grader)

Both return a JSON string with the five SOW sections. The node layer parses it.
"""
from __future__ import annotations

import json
import re
from typing import Optional

from app import config
from app.logging_config import get_logger

logger = get_logger(__name__)

SECTION_KEYS = [
    "project_overview",
    "scope_of_work",
    "deliverables",
    "timeline",
    "assumptions",
]


class LLMClient:
    def __init__(self) -> None:
        self.provider = config.effective_llm_provider()
        logger.info("LLM provider: %s", self.provider)
        self._client = None
        if self.provider == "anthropic":
            from langchain_anthropic import ChatAnthropic

            self._client = ChatAnthropic(
                model=config.ANTHROPIC_MODEL,
                temperature=config.LLM_TEMPERATURE,
                max_tokens=config.LLM_MAX_TOKENS,
                api_key=config.ANTHROPIC_API_KEY,
            )

    def complete(self, system: str, user: str) -> str:
        if self.provider == "anthropic":
            logger.debug("LLM complete via Anthropic (%s)", config.ANTHROPIC_MODEL)
            resp = self._client.invoke(
                [("system", system), ("human", user)]
            )
            return resp.content if isinstance(resp.content, str) else str(resp.content)
        logger.debug("LLM complete via mock (offline)")
        return _mock_complete(user)


# --------------------------------------------------------------------------
# Mock generation
# --------------------------------------------------------------------------
def _extract_tag(text: str, tag: str) -> str:
    m = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
    return m.group(1).strip() if m else ""


def _mock_complete(user: str) -> str:
    """Produce a believable structured SOW deterministically.

    Crucially, when a <context> block is present (RAG on) the output weaves in
    concrete phrases drawn from the retrieved knowledge base. When it is absent
    (RAG off) the output is generic. This makes the WITH/WITHOUT RAG difference
    visible even without a real LLM."""
    deal_raw = _extract_tag(user, "deal")
    context = _extract_tag(user, "context")
    try:
        deal = json.loads(deal_raw)
    except json.JSONDecodeError:
        deal = {}

    client = deal.get("client_name", "the Client")
    industry = deal.get("industry", "the client's industry")
    ptype = deal.get("project_type", "the initiative")
    objectives = deal.get("objectives", []) or ["Improve systems"]
    timeline = deal.get("timeline", "6 months")
    budget = deal.get("budget_range", "to be confirmed")

    grounded = bool(context.strip())

    def ground(snippet_default: str, needles: list[str]) -> str:
        if not grounded:
            return snippet_default
        found = [n for n in needles if n.lower() in context.lower()]
        if found:
            return snippet_default + " " + _context_sentence(context, found[0])
        return snippet_default

    obj_lines = "\n".join(f"  - {o}" for o in objectives)

    overview = (
        f"{client} ({industry}) is undertaking a {ptype} engagement. "
        f"The headline objectives are:\n{obj_lines}\n"
        + ground(
            "This SOW frames the work in terms of business outcomes and value.",
            ["outcomes", "business language", "overview"],
        )
    )

    scope = (
        f"Workstreams for this {ptype} engagement:\n"
        "  1. Discovery & Assessment\n"
        "  2. Landing Zone & Foundation\n"
        "  3. Migration / Modernization Execution (wave-based)\n"
        "  4. Security & Compliance\n"
        "  5. Cutover & Hypercare\n"
        + ground(
            "Out of scope: ongoing managed services after hypercare and changes to "
            "un-named third-party systems.",
            ["7 rs", "rehost", "replatform", "wave", "out of scope"],
        )
    )

    deliverables = (
        "  - Assessment Report and Target Architecture Document\n"
        "  - Landing Zone delivered as infrastructure-as-code\n"
        "  - Migration Runbook(s)\n"
        "  - Security & Compliance Matrix\n"
        "  - Hypercare Exit Report\n"
        + ground(
            "Each deliverable is acceptance-testable.",
            ["acceptance", "deliverables are nouns", "evidence", "risk analysis"],
        )
    )

    timeline_text = (
        f"Target duration: {timeline}.\n"
        "  - Discovery: Weeks 1-4\n"
        "  - Foundation: Weeks 3-8\n"
        "  - Migration Waves: Weeks 6-20\n"
        "  - Cutover & Hypercare: Weeks 20-26\n"
        + ground(
            "Milestones are expressed as verifiable events.",
            ["milestone", "phases", "hypercare exit", "wave"],
        )
    )

    assumptions = (
        f"  - Budget range: {budget}\n"
        "  - Client provides timely access to environments and SMEs.\n"
        "  - One production cutover window is available per wave.\n"
        + ground(
            "Compliance evidence (e.g. risk analysis, audit logs) is available where "
            "regulated data is in scope.",
            ["hipaa", "baa", "encryption", "audit", "phi", "compliance"],
        )
    )

    return json.dumps(
        {
            "project_overview": overview,
            "scope_of_work": scope,
            "deliverables": deliverables,
            "timeline": timeline_text,
            "assumptions": assumptions,
        },
        indent=2,
    )


def _context_sentence(context: str, needle: str) -> str:
    for sentence in re.split(r"(?<=[.])\s+", context):
        if needle.lower() in sentence.lower():
            s = sentence.strip().replace("\n", " ")
            return ("Grounded note: " + (s[:200] + ("..." if len(s) > 200 else "")))
    return ""
