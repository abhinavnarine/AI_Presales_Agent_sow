"""CLI demo: runs the agent on the standard deal and the messy deal, and prints
the WITH-RAG vs WITHOUT-RAG comparison required by the assessment.

Run from the backend/ directory:  python ../scripts/demo.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.agent.graph import get_agent  # noqa: E402
from app.models import DealInput  # noqa: E402

STANDARD = DealInput(
    client_name="Acme Health",
    industry="Healthcare",
    project_type="Cloud Migration",
    objectives=[
        "Migrate legacy systems to AWS",
        "Improve scalability",
        "Ensure HIPAA compliance",
    ],
    timeline="6 months",
    budget_range="$250k-$500k",
)

MESSY = DealInput(
    client_name="Unknown",
    project_type="Modernization",
    objectives=["Improve systems"],
    timeline=None,
)


def show(title: str, deal: DealInput) -> None:
    agent = get_agent()
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)

    with_rag = agent.run(deal, use_rag=True)
    without_rag = agent.run(deal, use_rag=False)

    print(f"\nLLM provider: {with_rag.llm_provider} | "
          f"Embedding backend: {with_rag.embedding_backend}")

    n = with_rag.normalized_deal
    print(f"\nNormalized deal -> client='{n.client_name}', industry='{n.industry}', "
          f"type='{n.project_type}', timeline='{n.timeline}', budget='{n.budget_range}'")
    if n.inferred_fields:
        print(f"Inferred fields: {', '.join(n.inferred_fields)}")

    print(f"\nRetrieved {len(with_rag.sources)} grounding sources:")
    for s in with_rag.sources[:5]:
        print(f"   - {s.source}  (score={s.score})")

    print("\n--- SCOPE OF WORK: WITHOUT RAG ---")
    print(without_rag.sow.scope_of_work)
    print("\n--- SCOPE OF WORK: WITH RAG ---")
    print(with_rag.sow.scope_of_work)


if __name__ == "__main__":
    show("STANDARD (complete) INPUT", STANDARD)
    show("MESSY (incomplete) INPUT", MESSY)
    print("\nDone.")
