# 🍷 Wine Sommelier AI — Production-Grade Agentic RAG

A professional, full-stack AI wine sommelier powered by an Agentic RAG pipeline (LangGraph + FastAPI), a polished React frontend, JWT authentication, conversation memory, LLM-as-judge evaluation, CI/CD, and Docker.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        React Frontend                        │
│         (Vite + React 18, TailwindCSS, Framer Motion)       │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP / REST
┌────────────────────────▼────────────────────────────────────┐
│                    FastAPI Backend                            │
│   /auth   /chat   /ingest   /eval   /health   /metrics      │
└──────┬──────────────┬──────────────────────┬────────────────┘
       │              │                      │
  ┌────▼────┐   ┌─────▼──────┐        ┌─────▼──────┐
  │  JWT    │   │ LangGraph  │        │  Pinecone  │
  │  Auth   │   │ RAG Agent  │        │  Vector DB │
  └─────────┘   └─────┬──────┘        └────────────┘
                      │
          ┌───────────┼───────────┐
          │           │           │
    ┌─────▼──┐  ┌─────▼──┐ ┌─────▼──┐
    │ Vector │  │ Vision │ │  OCR   │
    │ Search │  │GPT-4o  │ │Tesser. │
    └────────┘  └────────┘ └────────┘
```

## ✨ Features

- **Agentic RAG Pipeline** — LangGraph state machine with vector search → vision → OCR → synthesis fallback
- **Conversation Memory** — Multi-turn context preserved per session
- **JWT Authentication** — Secure login, personal wine libraries per user
- **LLM-as-Judge Eval Suite** — Auto-evaluate answer quality (relevance, faithfulness, completeness)
- **React Frontend** — Beautiful, animated UI with luxury wine aesthetic
- **Docker** — One command to run everything
- **CI/CD** — GitHub Actions: lint → test → build → deploy

---

## 📁 Project Structure

```
wine-sommelier/
├── app/                          # FastAPI backend
│   ├── agent/
│   │   ├── agent_graph.py          # LangGraph StateGraph
│   │   ├── nodes.py                # Individual pipeline nodes
│   │   └── document_processing.py  # PDF/PPTX loaders
│   ├── models/
│   │   ├── config.py               # WineRAGConfig (Pydantic settings)
│   │   ├── enums.py                # Query/document type enums
│   │   └── schemas.py              # Request/Response schemas
│   ├── routers/
│   │   ├── agent_router.py         # /chat, /ingest endpoints
│   │   ├── auth_router.py          # /auth/register, /auth/login
│   │   └── eval_router.py          # /eval/run, /eval/results
│   ├── services/
│   │   ├── agentic_rag_service.py  # Core RAG orchestrator
│   │   ├── auth_service.py         # JWT + user management
│   │   ├── conversation_service.py # Memory / chat history
│   │   └── eval_service.py         # LLM-as-judge evaluation
│   ├── utils/
│   │   ├── chunking_utils.py       # Text splitting
│   │   ├── ocr_utils.py            # Tesseract OCR
│   │   ├── vector_utils.py         # Pinecone upsert/query
│   │   └── vision_utils.py         # GPT-4o vision analysis
│   ├── middleware/
│   │   └── logging_middleware.py   # Structured JSON logging
│   └── main.py                     # FastAPI entry point
├── frontend/                       # React frontend
│   ├── src/
│   │   ├── api/client.ts           # Axios API client
│   │   ├── context/AuthContext.tsx # JWT auth state
│   │   ├── hooks/useChat.ts        # Chat + memory hook
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx
│   │   │   ├── ChatPage.tsx
│   │   │   └── EvalPage.tsx
│   │   └── components/
│   │       ├── ChatBubble.tsx
│   │       ├── MessageInput.tsx
│   │       ├── Sidebar.tsx
│   │       └── EvalPanel.tsx
│   ├── package.json
│   └── vite.config.ts
├── tests/
│   ├── unit/                       # Pytest unit tests
│   └── integration/                # API integration tests
├── .github/workflows/
│   └── ci.yml                      # Lint → Test → Build → Deploy
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
└── .env.example
```

---

## 🚀 Quick Start (Docker)

```bash
# 1. Clone and configure
cp .env.example .env
# Fill in OPENAI_API_KEY, PINECONE_API_KEY, JWT_SECRET_KEY

# 2. Run everything
docker compose up --build

# Frontend → http://localhost:5173
# Backend API → http://localhost:8000
# API Docs → http://localhost:8000/docs
```

## 🛠️ Local Development

```bash
# Backend
cd app
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

---

## 🧪 Running Tests

```bash
# All tests
pytest tests/ -v --cov=app --cov-report=html

# Unit only
pytest tests/unit/ -v

# Integration only (requires running backend)
pytest tests/integration/ -v
```

---

## 📊 LLM-as-Judge Evaluation

```bash
# Run eval suite against live backend
curl -X POST http://localhost:8000/eval/run \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"num_samples": 20}'

# Get results
curl http://localhost:8000/eval/results \
  -H "Authorization: Bearer <token>"
```

Metrics: **Relevance**, **Faithfulness**, **Completeness**, **Sommelier Tone**

---

## ⚙️ Environment Variables

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | **Primary** LLM provider. Used for chat, vision, eval, and embeddings (required — Groq has no embeddings API). |
| `GROQ_API_KEY` | **Fallback** LLM provider for chat/vision/eval only. Used automatically if OpenAI is missing, rate-limited, or errors. Get a free key at [console.groq.com](https://console.groq.com/keys). |
| `PINECONE_API_KEY` | Pinecone vector DB key |
| `PINECONE_ENVIRONMENT` | e.g. `us-east-1-aws` |
| `JWT_SECRET_KEY` | Strong random secret for JWT signing |
| `JWT_ALGORITHM` | Default: `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Default: `1440` (24h) |
| `DATABASE_URL` | SQLite path or Postgres URL for user/session store |
| `REDIS_URL` | Optional: for semantic caching |

### 🔁 LLM Fallback Policy

OpenAI is **always** the primary provider for every chat, vision, and evaluation call.
If an OpenAI call fails for any reason (missing key, auth error, rate limit, timeout, 5xx),
the system automatically retries with Groq — provided `GROQ_API_KEY` is set. This logic lives
entirely in `app/utils/llm_client.py`.

**Embeddings are OpenAI-only.** Groq does not offer an embeddings API, so if `OPENAI_API_KEY`
is missing or invalid, document ingestion and vector search will fail with a clear error
rather than silently falling back to a different embedding space.

---

## 👥 Credits
Powered by OpenAI, Pinecone, LangGraph, FastAPI, React
