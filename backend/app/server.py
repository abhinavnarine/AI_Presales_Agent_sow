"""FastAPI app exposing the presales agent to the Vue frontend."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app.agent.graph import get_agent
from app.logging_config import get_logger, setup_logging
from app.models import DealInput, GenerateRequest, GenerateResponse

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage FastAPI startup and shutdown lifecycle hooks.

    Args:
        app: The FastAPI application instance.

    Yields:
        Control back to the server after warming the agent singleton.
    """
    setup_logging()
    logger.info(
        "API ready (llm=%s, embedding=%s)",
        config.effective_llm_provider(),
        config.EMBEDDING_BACKEND,
    )
    get_agent()  # load vector store / models once at startup
    yield
    logger.info("API shutdown")


app = FastAPI(title="AI Presales Agent", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    """Report API health and loaded backend configuration.

    Returns:
        Dict with ``status``, ``llm_provider``, ``embedding_backend``,
        and ``kb_chunks`` counts.
    """
    agent = get_agent()
    return {
        "status": "ok",
        "llm_provider": agent.llm.provider,
        "embedding_backend": agent.vector_store.backend,
        "kb_chunks": agent.vector_store.chunk_count,
    }


@app.post("/api/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest) -> GenerateResponse:
    """Generate a single Statement of Work for the given deal.

    Args:
        req: Request body with ``deal`` and ``use_rag`` flag.

    Returns:
        Full pipeline response including normalized deal, SOW, and sources.
    """
    logger.info(
        "POST /api/generate client=%s use_rag=%s",
        req.deal.client_name,
        req.use_rag,
    )
    return get_agent().run(req.deal, use_rag=req.use_rag)


@app.post("/api/compare")
def compare(deal: DealInput) -> dict:
    """Run the pipeline twice: with RAG and without RAG.

    Args:
        deal: Raw deal input shared by both runs.

    Returns:
        Dict with ``with_rag`` and ``without_rag`` ``GenerateResponse`` objects.
    """
    logger.info("POST /api/compare client=%s", deal.client_name)
    agent = get_agent()
    with_rag = agent.run(deal, use_rag=True)
    without_rag = agent.run(deal, use_rag=False)
    return {"with_rag": with_rag, "without_rag": without_rag}


@app.get("/api/sample-deals")
def sample_deals() -> dict:
    """Return example deal payloads for UI demos and testing.

    Returns:
        Dict with ``complete`` (fully specified) and ``messy`` (sparse) samples.
    """
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
