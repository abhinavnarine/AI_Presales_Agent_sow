"""FastAPI app exposing the presales agent to the Vue frontend."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app.agent.graph import get_agent
from app.models import DealInput, GenerateRequest, GenerateResponse

app = FastAPI(title="AI Presales Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    agent = get_agent()
    return {
        "status": "ok",
        "llm_provider": agent.llm.provider,
        "embedding_backend": agent.vector_store.backend,
        "kb_chunks": agent.vector_store.chunk_count,
    }


@app.post("/api/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest) -> GenerateResponse:
    """Generate a single SOW (RAG on or off, controlled by req.use_rag)."""
    return get_agent().run(req.deal, use_rag=req.use_rag)


@app.post("/api/compare")
def compare(deal: DealInput) -> dict:
    """Run the pipeline twice and return WITH-RAG and WITHOUT-RAG side by side."""
    agent = get_agent()
    with_rag = agent.run(deal, use_rag=True)
    without_rag = agent.run(deal, use_rag=False)
    return {"with_rag": with_rag, "without_rag": without_rag}


@app.get("/api/sample-deals")
def sample_deals() -> dict:
    return {
        "complete": {
            "client_name": "Acme Health",
            "industry": "Healthcare",
            "project_type": "Cloud Migration",
            "objectives": [
                "Migrate legacy systems to AWS",
                "Improve scalability",
                "Ensure HIPAA compliance",
            ],
            "timeline": "6 months",
            "budget_range": "$250k-$500k",
        },
        "messy": {
            "client_name": "Unknown",
            "project_type": "Modernization",
            "objectives": ["Improve systems"],
            "timeline": None,
        },
    }
