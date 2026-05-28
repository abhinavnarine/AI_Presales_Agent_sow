# AI Presales Agent — Grounded SOW Generator

Takes structured (or messy) deal data → retrieves relevant knowledge via RAG →
runs a multi-step LangGraph workflow → produces a structured **Statement of Work**.

Built with **Python + LangGraph + LangChain + FAISS** on the backend and **Vue 3
(Vite)** on the frontend. It runs end-to-end **with no API key** (deterministic
mock LLM + offline embeddings fallback) and uses **Claude** for real generation
when a key is provided.

---

## Quick start

### 1. Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate      # optional
pip install -r requirements.txt
cp .env.example .env                                   # optional; add ANTHROPIC_API_KEY for real Claude output
python run.py                                          # serves http://localhost:8000
```

Run it offline / without any key (fully functional, mock LLM + hash embeddings):
```bash
LLM_PROVIDER=mock EMBEDDING_BACKEND=hash python run.py
```

### 2. Frontend
```bash
cd frontend
npm install
npm run dev                                            # http://localhost:5173 (proxies /api to :8000)
```

Open http://localhost:5173, load a sample (complete or messy), and click
**Generate SOW** or **Compare WITH vs WITHOUT RAG**.

### 3. CLI demo (no frontend needed)
```bash
cd backend
python ../scripts/demo.py
```

---

## How it runs anywhere (graceful degradation)

| Concern | Primary (recommended) | Automatic fallback |
|---|---|---|
| **LLM** | Claude via `langchain-anthropic` (needs `ANTHROPIC_API_KEY`) | Deterministic `mock` generator — no key required |
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` (real neural vectors) | Deterministic **hash embeddings** — no model download |

The fallbacks mean the system is always runnable for evaluation; the RAG plumbing
(chunk → embed → FAISS → retrieve → ground) is identical in both modes.

---

## Architecture (end-to-end)

```
┌──────────────┐     POST /api/generate            ┌──────────────────────────────┐
│  Vue 3 (UI)  │ ──── POST /api/compare ─────────► │  FastAPI  (app/server.py)    │
│  DealForm    │                                   └──────────────┬───────────────┘
│  SowOutput   │ ◄──── JSON: sow + sources ─────────────────────  │
│  SourcesPanel│                                                   ▼
└──────────────┘                              ┌───────────────────────────────────┐
                                              │  LangGraph workflow (app/agent)     │
                                              │                                     │
   START ─► parse_input ─► retrieve ─► generate_sow ─► validate_refine ─► END       │
                │              │             │               │                      │
        normalize+infer   RAG (FAISS)   LLM (Claude/mock)  QA checks                │
                                              └────────────┬───────────────────────┘
                                                           ▼
   Knowledge base (markdown)  ──►  load+chunk  ──►  embeddings  ──►  FAISS vector store
   app/knowledge_base/*.md         app/rag/loader   app/rag/embeddings   app/rag/vector_store
```

The backend is intentionally **modular, not one script**:

```
backend/app/
├── server.py              FastAPI endpoints (/generate, /compare, /health, /sample-deals)
├── config.py              all tunables (chunk size, top-k, model, backends)
├── models.py              Pydantic schemas (DealInput, NormalizedDeal, SOW, sources)
├── llm.py                 LLM client: Claude provider + offline mock provider
├── knowledge_base/        the RAG corpus (SOW templates, cloud migration, HIPAA, delivery)
├── rag/
│   ├── embeddings.py      pluggable embeddings (HF neural / hash fallback)
│   ├── loader.py          markdown-aware chunking with section metadata
│   ├── vector_store.py    FAISS build / persist / reload / search
│   └── retriever.py       multi-query retrieval + de-dup + ranking
└── agent/
    ├── state.py           LangGraph shared state (TypedDict)
    ├── nodes.py           the 4 workflow nodes (each independently testable)
    └── graph.py           LangGraph wiring + dependency injection + run()
```

---

## RAG Implementation

**Knowledge base.** Four curated markdown documents act as the corpus: SOW templates
and section guidance, cloud-migration best practices (the 7 Rs, waves, landing zone),
HIPAA/compliance guidelines, and delivery frameworks/estimation. This is real domain
knowledge the LLM should *not* be left to invent.

**Chunking strategy.** `RecursiveCharacterTextSplitter` with markdown-aware separators
(`\n## `, `\n### `, paragraph, sentence, word), `chunk_size=900`, `chunk_overlap=150`.
Heading-first splitting keeps each chunk topically coherent; the overlap preserves
context across boundaries. Each chunk stores `source` (filename) and `section`
(nearest heading) metadata so retrieved context is traceable in the UI.

**Embeddings + vector store.** Chunks are embedded (MiniLM by default) and indexed in
**FAISS**. The index is persisted to disk and tagged by embedding backend, so it
rebuilds automatically if the backend changes.

**Retrieval method.** *Multi-query, top-k with de-duplication.* Instead of one generic
query, `retriever.py` derives several focused queries from the **normalized** deal —
one per objective, plus project-type, estimation, and (conditionally) a HIPAA query
when the industry/objectives signal healthcare or compliance. Results across queries
are de-duplicated (keeping the best score per chunk), ranked, and capped. On a small
corpus this materially improves recall versus a single query.

**Scoring.** FAISS L2 distance is converted to a bounded similarity `1/(1+distance)`
so scores are comparable across embedding backends and display cleanly in the UI.

**How retrieval improves output.** The retrieved chunks are injected into the
generation prompt inside a `<context>` block; the system prompt instructs the model to
ground scope, deliverables, timeline, and assumptions in that context. The UI’s
**Compare** mode runs the pipeline twice (RAG on / off) so the difference is visible:
without RAG the SOW is generic; with RAG it pulls in concrete, source-backed content
(7 Rs dispositions, wave planning, HIPAA BAA/encryption/audit safeguards, budget-band
estimation, "client name Unknown → use a neutral placeholder", etc.). Even in offline
mock mode the grounded output weaves in real phrases from the retrieved sources, so the
RAG effect is demonstrable without a key.

---

## Agent Workflow

A **LangGraph** `StateGraph` with four single-responsibility nodes — explicitly *not*
one big prompt:

1. **parse_input** — cleans messy input and infers defaults. Maps
   `client_name: "Unknown"` → `"the Client"`; infers `industry` from objective keywords;
   defaults `project_type` to `Modernization`; expands vague objectives
   (`"Improve systems"`) into concrete, defensible ones; infers a `timeline` from
   project type and a `budget_range` from objective count. Every inference is recorded
   in `inferred_fields` + `warnings` for transparency. *(No LLM, no retrieval.)*
2. **retrieve** — RAG step; builds queries from the normalized deal and gathers ranked
   grounding context. Skipped when `use_rag=False`. *(No LLM.)*
3. **generate_sow** — builds a grounded prompt (`<deal>` + `<context>`) and calls the
   LLM to emit a strict JSON SOW, which is parsed into the `SOW` schema.
4. **validate_refine** — deterministic QA: flags thin sections, surfaces reliance on
   inferred fields, and warns when output was generated without grounding.

**Why this structure.** Separating parse / retrieve / generate / validate makes each
step independently testable and swappable, keeps prompts small and grounded, and gives
a clean place to extend (e.g. add a `human_review` node, a `pricing` node, or a
conditional refine-loop edge) without touching the others. Dependencies (vector store,
retriever, LLM) are injected into the nodes by the graph builder, so the compiled graph
is reused across requests.

**How it maps to a client’s LangGraph/LangChain platform.** The graph already *is*
LangGraph; nodes are plain callables over a typed state, retrieval uses LangChain’s
FAISS + splitters + `Document` abstractions, and generation uses `langchain-anthropic`.
Dropping this into a larger orchestration layer means registering these nodes in the
existing graph, pointing the retriever at the shared vector store, and swapping the
in-process LLM client for the platform’s model gateway.

---

## Validation: WITH vs WITHOUT RAG

- API: `POST /api/compare` returns both results.
- UI: **Compare WITH vs WITHOUT RAG** renders them side by side with the source panel.
- CLI: `python ../scripts/demo.py` prints the Scope section for both.

The WITHOUT-RAG SOW is plausible but generic and ungrounded; the WITH-RAG SOW cites and
incorporates specific best-practice and compliance content from the knowledge base, and
`validate_refine` explicitly flags ungrounded output.

---

## Tradeoffs

**What I simplified (24h timebox):**
- Knowledge base is four hand-written markdown files, not an ingestion pipeline.
- FAISS runs in-process and persists to local disk (single node).
- No auth, rate limiting, caching layer, or streaming responses.
- The refine step is a deterministic QA pass, not an LLM self-critique loop.
- Mock LLM + hash embeddings exist for offline runnability, not production quality.

**What would break at scale (thousands of deals) — and the fix:**
- **In-process FAISS** won’t scale or share across replicas → move to a managed/dedicated
  vector DB (pgvector, Pinecone, Milvus, OpenSearch) with metadata filtering and ANN
  tuning; separate the index service from the API.
- **Synchronous request/response** blocks under load → make generation a queued async job
  (Celery/SQS) with a status endpoint and streaming.
- **Per-request graph + embedding-model load** → warm singletons (already cached here)
  plus a dedicated embeddings/model-serving service; batch embedding for ingestion.
- **No caching** → cache retrieval and (normalized-deal-keyed) generations; dedupe
  identical deals.
- **Cost/latency of the LLM** → cache, route simple deals to a smaller model, and reserve
  the large model for complex ones; add token budgets.
- **Knowledge freshness & quality** → automated ingestion + re-embedding pipeline,
  versioned indexes, and an eval harness (e.g. RAGAS: faithfulness, context precision/recall)
  in CI to catch retrieval/grounding regressions before deploy.
- **Observability/governance** → tracing (LangSmith/OpenTelemetry), per-stage metrics,
  PII handling for real client data, and human-in-the-loop review for high-value SOWs.

---

## API reference

| Method | Path | Body | Returns |
|---|---|---|---|
| GET  | `/api/health` | – | provider, embedding backend, chunk count |
| POST | `/api/generate` | `{ deal, use_rag }` | normalized deal, SOW, sources |
| POST | `/api/compare` | `deal` | `{ with_rag, without_rag }` |
| GET  | `/api/sample-deals` | – | the complete + messy sample inputs |

`deal` fields are all optional: `client_name, industry, project_type, objectives[], timeline, budget_range`.
