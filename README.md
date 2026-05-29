# AI Presales Agent 

You give it deal data (structured or messy), it pulls relevant context from a knowledge base via RAG, runs it through a LangGraph workflow, and spits out a Statement of Work.

Backend is Python + LangGraph + LangChain + FAISS. Frontend is Vue 3 (Vite). It runs fully offline with no API key — uses a deterministic mock LLM and hash embeddings as fallback — and switches to Claude when you provide one.

---

## Quick start

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # add ANTHROPIC_API_KEY if you want real output
python run.py               # http://localhost:8000
```

If you just want to poke around without any API key:
```bash
LLM_PROVIDER=mock EMBEDDING_BACKEND=hash python run.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev                 # http://localhost:5173, proxies /api → :8000
```

Load a sample deal, click **Generate SOW** or **Compare WITH vs WITHOUT RAG**.

### CLI (no frontend)
```bash
cd backend
python ../scripts/demo.py
```

---

## Running without a key

The system always runs — no key, no model download required. Here's how it degrades:

| | Primary | Fallback |
|---|---|---|
| LLM | Claude (`ANTHROPIC_API_KEY`) | Deterministic mock — no key |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` | Hash embeddings — no download |

The RAG pipeline (chunk → embed → FAISS → retrieve → inject) is identical in both modes. The fallback makes it easy to evaluate the plumbing without standing up any external services.

---

## Architecture

```
┌──────────────┐     POST /api/generate            ┌──────────────────────────────┐
│  Vue 3 (UI)  │ ──── POST /api/compare ─────────► │  FastAPI  (app/server.py)    │
│  DealForm    │                                   └──────────────┬───────────────┘
│  SowOutput   │ ◄──── JSON: sow + sources ─────────────────────  │
│  SourcesPanel│                                                   ▼
└──────────────┘                              ┌───────────────────────────────────┐
                                              │  LangGraph workflow (app/agent)   │
                                              │                                   │
   START ─► parse_input ─► retrieve ─► generate_sow ─► validate_refine ─► END    │
                │              │             │               │                    │
        normalize+infer   RAG (FAISS)   LLM (Claude/mock)  QA checks             │
                                              └────────────┬──────────────────────┘
                                                           ▼
   Knowledge base (markdown)  ──►  load+chunk  ──►  embeddings  ──►  FAISS
   app/knowledge_base/*.md         app/rag/loader   app/rag/embeddings
```

Backend layout:
```
backend/app/
├── server.py              FastAPI endpoints (/generate, /compare, /health, /sample-deals)
├── config.py              tunables (chunk size, top-k, model, backends)
├── models.py              Pydantic schemas (DealInput, NormalizedDeal, SOW, sources)
├── llm.py                 Claude + offline mock provider
├── logging_config.py      structured logging setup
├── knowledge_base/        RAG corpus (SOW templates, cloud migration, HIPAA, delivery)
├── rag/
│   ├── embeddings.py      pluggable embeddings (HF neural / hash fallback)
│   ├── loader.py          markdown-aware chunking with section metadata
│   ├── vector_store.py    FAISS build / persist / reload / search
│   └── retriever.py       multi-query retrieval + de-dup + ranking
└── agent/
    ├── state.py           LangGraph shared state (TypedDict)
    ├── nodes.py           the 4 workflow nodes
    └── graph.py           graph wiring + dependency injection + run()
```

---

## RAG

The knowledge base is four markdown files: SOW templates and section guidance, cloud-migration best practices (7 Rs, waves, landing zone), HIPAA/compliance guidelines, and delivery/estimation frameworks. Real domain content the LLM shouldn't be left to hallucinate.

Chunking uses `RecursiveCharacterTextSplitter` with markdown-aware separators (`\n## `, `\n### `, paragraph, sentence, word) at `chunk_size=900`, `chunk_overlap=150`. Each chunk carries `source` and `section` metadata so the UI can show where retrieved content came from.

Retrieval is multi-query: instead of one generic search, the retriever builds several focused queries from the normalized deal — one per objective, plus project type, estimation, and a HIPAA query when the deal signals healthcare or compliance. Results are de-duped across queries (keeping the best score per chunk) and capped. On a small corpus this meaningfully improves recall over a single query.

FAISS L2 distance gets converted to `1/(1+distance)` so scores are comparable across embedding backends and display cleanly.

Retrieved chunks are injected into the generation prompt in a `<context>` block. The system prompt tells the model to ground scope, deliverables, timeline, and assumptions in that content. The **Compare** mode in the UI runs the pipeline twice so you can see the difference: without RAG the SOW is generic; with RAG it pulls in concrete content from the knowledge base — 7 Rs dispositions, HIPAA BAA/encryption/audit safeguards, budget estimation, etc.

---

## Agent workflow

Four nodes in a LangGraph `StateGraph`, each with one job:

1. **parse_input** — cleans input, infers defaults. `client_name: "Unknown"` → `"the Client"`, infers industry from objective keywords, expands vague objectives into concrete ones, infers timeline and budget from project type and objective count. Every inference is logged in `inferred_fields` + `warnings`. No LLM, no retrieval.
2. **retrieve** — builds queries from the normalized deal, runs RAG, returns ranked grounding context. Skipped when `use_rag=False`.
3. **generate_sow** — builds a grounded prompt (`<deal>` + `<context>`) and calls the LLM for a JSON SOW, parsed into the `SOW` schema.
4. **validate_refine** — deterministic QA: flags thin sections, surfaces reliance on inferred fields, warns if the output was generated without grounding.

Keeping parse / retrieve / generate / validate separate makes each step independently testable, keeps prompts small, and gives a clean extension point — adding a `human_review` node, a `pricing` node, or a refine-loop edge means touching one node, not rewriting a monolith.

Dependencies (vector store, retriever, LLM client) are injected by the graph builder, so the compiled graph is reused across requests without reloading anything.

---

## Tradeoffs and known limitations

**What I simplified** (built in ~24h):
- Knowledge base is hand-written markdown, not an ingestion pipeline
- FAISS runs in-process, persisted to local disk
- No auth, rate limiting, or streaming
- The refine step is deterministic QA, not an LLM self-critique loop
- Mock LLM + hash embeddings are for offline runnability, not production quality

**What would need to change at real scale:**

In-process FAISS won't scale across replicas — that needs a managed vector DB (pgvector, Pinecone, Milvus) with a separate index service. Synchronous request/response blocks under load — generation should be a queued async job with a status endpoint. Per-request graph compilation and embedding model load need to be warm singletons. There's no caching anywhere — retrieval results and normalized-deal-keyed generations both want caching. LLM cost needs routing (small model for simple deals, large for complex) with token budgets. And knowledge freshness needs an automated ingestion + re-embedding pipeline, versioned indexes, and an eval harness (RAGAS or similar) in CI to catch retrieval regressions before deploy.

---

## API

| Method | Path | Body | Returns |
|---|---|---|---|
| GET  | `/api/health` | — | provider, embedding backend, chunk count |
| POST | `/api/generate` | `{ deal, use_rag }` | normalized deal, SOW, sources |
| POST | `/api/compare` | `deal` | `{ with_rag, without_rag }` |
| GET  | `/api/sample-deals` | — | complete + messy sample inputs |

All `deal` fields are optional: `client_name`, `industry`, `project_type`, `objectives[]`, `timeline`, `budget_range`.
