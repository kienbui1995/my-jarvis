# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is this?

MY JARVIS is a Vietnamese-first agentic personal AI assistant. Multi-channel (Zalo, Zalo Bot, Telegram, Web), smart LLM routing, persistent memory, proactive actions. Currently at v3.0.0.

## Commands

```bash
# Development (hot reload, exposed ports)
make dev                          # Start all services (backend :8002, frontend :3002)
make dev-down                     # Stop dev services
make dev-logs s=backend           # Tail logs for a service

# Production
make prod                         # Start prod (uses .env.prod + docker-compose.prod.yml)
make prod-down

# Database (Alembic)
make db-migrate m="description"   # Create migration
make db-upgrade                   # Apply migrations
make db-downgrade                 # Rollback one migration

# Linting & Testing
make lint                         # ruff check . (backend only)
make test                         # pytest -x -q (backend only)

# Frontend lint/test (run inside container or locally)
cd frontend && npm run lint       # next lint
cd frontend && npx vitest run     # vitest (jsdom env)

# Utilities
make shell                        # Shell into backend container
make clean                        # Remove containers + volumes
```

## Architecture

```
Zalo / Telegram / Web (WebSocket)
        |
   Cloudflare Tunnel
        |
   Next.js 15 (frontend :3000)  +  FastAPI (backend :8000)
        |
   LangGraph Agent Pipeline:
     route -> [planner -> executor -> replan -> synthesize] | delegate | agent_loop <-> tools -> respond -> evaluate -> post_process
        |
   LLM Gateway (all via LiteLLM Proxy http://litellm:4000)
        |
   PostgreSQL+pgvector | Redis | MinIO
```

### Backend (`backend/`)

- **Entry:** `main.py` — FastAPI app with lifespan (Redis init, PG+pgvector check), middleware stack (CORS, rate limit, security headers)
- **API routes:** `api/v1/` — all prefixed `/api/v1`. Key routers: `auth`, `ws` (WebSocket chat), `webhooks` (Zalo/Telegram), `conversations`, `tasks`, `calendar`, `analytics`, `settings`, `preferences`, `audit`, `feedback`, `mcp`, `notifications`
- **Agent pipeline:** `agent/graph.py` — LangGraph StateGraph with nodes: `route`, `agent_loop`, `tools`, `delegate`, `respond`, `evaluate`, `post_process`, plus plan-and-execute nodes (`planner`, `executor`, `replan`, `synthesize`). State defined in `agent/state.py` (extends `MessagesState`)
- **Agent tools:** `agent/tools/` — task, calendar, memory (pgvector), web search, finance, knowledge graph. All tools receive `user_id` injected from state
- **LLM layer:** `llm/gateway.py` routes all models through LiteLLM Proxy using `ChatOpenAI`. `llm/router.py` selects model by complexity tier (simple/medium/complex) and budget. `llm/budget.py` tracks per-user daily spend. `llm/cache.py` and `llm/embeddings.py` for caching and vector embeddings
- **Channels:** `channels/` — adapters for Zalo OA, Zalo Bot, Telegram. Base class in `channels/base.py`
- **Background worker:** `services/proactive.py` — ARQ worker for morning briefings and deadline reminders (cron-based)
- **Config:** `core/config.py` — Pydantic Settings, validates secrets in production. Feature flags control v3 capabilities (planning, memory consolidation, HITL, supervision, etc.)
- **DB:** SQLAlchemy async (`db/session.py`), models in `db/models/`, Alembic migrations in `db/migrations/`

### Frontend (`frontend/`)

- Next.js 15 with App Router, Tailwind CSS v4, TypeScript
- Route groups: `(auth)/` (login, register) and `(app)/` (chat, tasks, calendar, analytics, settings, onboarding)
- State: Zustand stores in `lib/stores/` — `auth.ts`, `chat.ts`
- API client: `lib/api.ts` — typed fetch wrapper with auto-refresh on 401
- WebSocket: `lib/ws.ts` for real-time chat streaming
- UI components: `components/ui/` (button, modal, input, etc.), `components/chat/` (message bubble, input, plan progress, approval dialog)
- Path alias: `@/*` maps to project root
- Tests: Vitest + React Testing Library in `tests/`

### Docker

- 3-file compose: `docker-compose.yml` (base) + `docker-compose.dev.yml` (dev overrides) + `docker-compose.prod.yml` (prod)
- Services: `postgres` (pgvector/pgvector:pg16), `redis` (7-alpine), `minio`, `backend`, `worker` (ARQ), `frontend`
- Dev ports: backend=8002, frontend=3002, postgres=5435, redis=6381, minio=9000/9001
- Backend connects to `litellm-proxy_default` network for LLM access
- Multi-stage Dockerfiles: `dev` and `prod` targets. Backend uses `uv` for dependency install

## Key Conventions

- Python: ruff (line-length=100, py312, select E/F/I). No type annotations enforcement beyond what exists
- Frontend: Next.js lint rules, TypeScript strict mode
- All LLM calls go through LiteLLM Proxy — never call provider APIs directly (see `llm/gateway.py`)
- DB: async SQLAlchemy throughout, `async_session` context manager pattern
- Tests require running services (postgres, redis) — run via `make test` inside Docker
- Vietnamese is the primary user-facing language; code and comments may mix Vietnamese and English

## Pending Migration: API & Error Handling Standard

Chi tiet: xem `MIGRATE_API_ERROR_STANDARD.md` tai root du an.

**Viec can lam**:
1. Tao `backend/core/errors.py` — AppError class + `_error_body()` (giu `detail` field cho backward compat) + `setup_error_handlers(app)`
2. Tao `backend/core/request_id.py` — RequestIDMiddleware (ASGI, inject `scope.state`)
3. Sua `backend/main.py`:
   - Them `app.add_middleware(RequestIDMiddleware)` DAU TIEN (truoc SecurityHeaders)
   - Them `setup_error_handlers(app)` sau middleware
4. Sua `backend/core/rate_limit.py` — doi 3 cho `JSONResponse({"detail": "..."})` sang `_rate_limit_response()` voi format `{detail: "...", error: {code: "RATE_LIMITED", ...}}`
5. Sua `frontend/lib/api.ts` (luu y: `lib/` khong phai `src/lib/`):
   - Them ApiError class (extends Error)
   - Thay `throw new Error(await res.text())` bang JSON parsing voi `body.error` + fallback `body.detail`

**Luu y quan trong**:
- Middleware order: RequestID → SecurityHeaders → CORS → RateLimit
- WebSocket rate limiting (`check_ws_rate()`) khong bi anh huong
- Public API (`/api/public/v1/`) — kiem tra external consumers truoc khi deploy
- Deploy backend + frontend cung luc
