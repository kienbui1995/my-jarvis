# MY JARVIS — Technical Architecture

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENTS                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ Zalo OA  │  │ Telegram │  │ Web App  │  │  Voice   │           │
│  │ (Primary)│  │   Bot    │  │Dashboard │  │(Zalo VN) │           │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘           │
└───────┼──────────────┼──────────────┼──────────────┼────────────────┘
        │              │              │              │
        ▼              ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    EDGE (Cloudflare Tunnel)                          │
│                 SSL Termination · Routing · DDoS Protection         │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────────┐
│                     BACKEND (FastAPI)                                │
│                                                                     │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐            │
│  │  Channel    │  │   Session    │  │   Auth/User    │            │
│  │  Adapters   │  │   Manager    │  │   Service      │            │
│  │             │  │              │  │                │            │
│  │ Zalo/TG/Web │  │ Context mgmt │  │ JWT + profiles │            │
│  └──────┬──────┘  └──────┬───────┘  └────────────────┘            │
│         │                │                                         │
│         ▼                ▼                                         │
│  ┌──────────────────────────────────────────────┐                  │
│  │            AGENT ORCHESTRATOR                 │                  │
│  │              (LangGraph)                      │                  │
│  │                                               │                  │
│  │  ┌─────────┐  ┌──────────┐  ┌─────────────┐ │                  │
│  │  │ Router  │  │ Agentic  │  │  Response    │ │                  │
│  │  │ Node    │→ │ Loop     │→ │  Builder     │ │                  │
│  │  │         │  │          │  │              │ │                  │
│  │  │Classify │  │Plan+Exec │  │Format+Stream│ │                  │
│  │  └─────────┘  └────┬─────┘  └─────────────┘ │                  │
│  │                     │                         │                  │
│  │              ┌──────▼──────┐                  │                  │
│  │              │   TOOLS     │                  │                  │
│  │              │             │                  │                  │
│  │              │ Tasks│Cal   │                  │                  │
│  │              │ Email│Web   │                  │                  │
│  │              │ Docs │Fin   │                  │                  │
│  │              │ Memory│Srch │                  │                  │
│  │              └─────────────┘                  │                  │
│  └──────────────────────────────────────────────┘                  │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │   LLM        │  │   Memory     │  │  Proactive   │             │
│  │   Gateway     │  │   Service    │  │  Scheduler   │             │
│  │              │  │              │  │              │             │
│  │ Model Router │  │ Hot+Cold     │  │ Cron-based   │             │
│  │ LiteLLM Prx │  │ Dual-layer   │  │ triggers     │             │
│  │ Budget Ctrl  │  │ pgvector     │  │ morning brief│             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                                   │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ PostgreSQL   │  │    Redis     │  │   MinIO      │             │
│  │ + pgvector   │  │              │  │              │             │
│  │              │  │ Sessions     │  │ Files/Docs   │             │
│  │ Users,Tasks  │  │ Cache        │  │ Voice notes  │             │
│  │ Calendar     │  │ Rate limits  │  │ Images       │             │
│  │ Conversations│  │ Prompt cache │  │              │             │
│  │ Embeddings   │  │ Pub/Sub      │  │              │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     EXTERNAL SERVICES                               │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐          │
│  │Gemini  │ │Claude  │ │DeepSeek│                               │
│  │Flash   │ │Haiku/  │ │Chat    │    via LiteLLM Proxy          │
│  │        │ │Sonnet  │ │        │    (http://litellm:4000)      │
│  └────────┘ └────────┘ └────────┘                               │
└─────────────────────────────────────────────────────────────────────┘
```

## 2. Key Architecture Decisions (ADR)

### ADR-001: LangGraph for Agent Orchestration

**Decision**: LangGraph StateGraph (not LangChain AgentExecutor)

**Why**:
- AgentExecutor is deprecated (maintenance mode until Dec 2026)
- LangGraph supports: directed graph workflows, checkpointing, streaming, human-in-the-loop
- Built-in persistence for long-running agent sessions
- Industry standard for production agentic systems in 2026

**Trade-off**: Steeper learning curve vs raw LLM calls, but worth it for agentic loop + state management.

### ADR-002: Dual-Layer Memory Architecture

**Decision**: Hot Path (in-context) + Cold Path (vector retrieval)

**Why** (2026 best practice from research):
- Hot Path: Recent messages + summarized context graph → always in prompt
- Cold Path: Long-term episodic/semantic memory → retrieved via pgvector when relevant
- Memory Node after each turn decides what to persist

**Memory Types**:
| Type | Storage | Retrieval |
|------|---------|-----------|
| Working | Redis (session) | Always loaded |
| Episodic | PostgreSQL + pgvector | Semantic search on relevance |
| Semantic | PostgreSQL + pgvector | Fact lookup by entity/topic |
| Procedural | PostgreSQL (structured) | Pattern matching on user behavior |

### ADR-003: PostgreSQL + pgvector (not dedicated vector DB)

**Decision**: Single PostgreSQL instance with pgvector extension

**Why**:
- Already need PostgreSQL for structured data (users, tasks, calendar)
- pgvector handles <10M vectors well with HNSW index
- No separate infra to manage at MVP scale
- Hybrid queries (relational + semantic) in single DB
- Cost: $0 extra vs $50-200/mo for Pinecone/Weaviate

**When to migrate**: If vectors exceed 10M or query latency >100ms at scale.

### ADR-004: Smart LLM Router with Budget Control

**Decision**: Multi-model routing with per-user budget caps

**Architecture**:
```
User Message
    │
    ▼
┌──────────────┐
│  Classifier  │ ← Gemini Flash-Lite ($0.075/M) or local rules
│  (cheap/fast)│
└──────┬───────┘
       │
  ┌────┼────┐
  │    │    │
  ▼    ▼    ▼
Simple Medium Complex
  │    │      │
  ▼    ▼      ▼
Gemini Claude  Claude
Flash  Haiku   Sonnet
$0.10  $1.00   $3.00
```

**Budget enforcement**: Redis tracks daily token spend per user. If budget exceeded → downgrade to cheaper model or queue for next day.

**Fallback chain**: Primary → Secondary → Tertiary (multi-provider resilience).

### ADR-005: Channel Adapter Pattern

**Decision**: Unified internal message format, platform-specific adapters

```python
# Internal message format
class JarvisMessage:
    user_id: str
    channel: str        # "zalo" | "telegram" | "web"
    content: str
    attachments: list   # images, files, voice
    metadata: dict      # platform-specific data
    timestamp: datetime
```

Each adapter handles: message normalization, attachment processing, response formatting, platform-specific features (Zalo stickers, Telegram inline keyboards, etc.)

## 3. Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **API** | FastAPI (Python 3.12) | Async, LangGraph ecosystem, fast |
| **Agent** | LangGraph + LangMem | State machine + memory SDK |
| **LLM** | LiteLLM Proxy → Gemini/Claude/DeepSeek | Unified API, cost tracking, no lock-in |
| **Database** | PostgreSQL 16 + pgvector | Unified structured + vector |
| **Cache** | Redis 7 | Sessions, rate limits, prompt cache |
| **Storage** | MinIO | S3-compatible, self-hosted files |
| **Frontend** | Next.js 15 + TypeScript + Tailwind | Dashboard, settings, analytics |
| **TTS** | Piper TTS (WASM, vi_VN-vais1000) | Offline Vietnamese voice in browser |
| **State** | Zustand | Lightweight client state |
| **Infra** | Docker Compose + Cloudflare Tunnel | Easy dev + production |
| **Migrations** | Alembic | PostgreSQL schema management |
| **Task Queue** | Redis + ARQ | Async jobs (proactive, batch) |
| **Monitoring** | Sentry (backend + frontend) | Error tracking, performance |
| **CI/CD** | Azure Pipelines | Lint, build, deploy |

## 4. Data Model

```sql
-- Core user & identity
users (id, zalo_id, telegram_id, email, name, timezone, created_at)
user_profiles (user_id, preferences JSONB, goals JSONB, routines JSONB)
user_relationships (user_id, name, role, context, metadata JSONB)

-- Conversations & memory
conversations (id, user_id, channel, started_at, ended_at, summary)
messages (id, conversation_id, role, content, attachments JSONB, tokens_used, model_used, cost, created_at)
memories (id, user_id, type ENUM(episodic/semantic/procedural), content, embedding vector(1536), importance FLOAT, created_at, last_accessed)

-- Tasks & calendar
tasks (id, user_id, title, description, status, priority, due_date, parent_task_id, created_by_agent BOOL, created_at)
calendar_events (id, user_id, title, start_time, end_time, location, attendees JSONB, reminders JSONB)

-- Finance
expenses (id, user_id, amount, currency, category, description, receipt_url, created_at)
budgets (id, user_id, category, monthly_limit, current_spend)

-- System
llm_usage (id, user_id, model, input_tokens, output_tokens, cost, task_type, created_at)
proactive_triggers (id, user_id, trigger_type, schedule, config JSONB, last_fired, enabled)
```

## 5. Agent Pipeline (LangGraph)

```
                    ┌─────────────────┐
                    │   START          │
                    │   (new message)  │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  LOAD CONTEXT   │
                    │                 │
                    │ • User profile  │
                    │ • Hot memory    │
                    │ • Active tasks  │
                    │ • Recent msgs   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  ROUTE          │
                    │                 │
                    │ Classify intent │
                    │ Select model    │
                    │ Check budget    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  AGENT LOOP     │◄──────┐
                    │                 │       │
                    │ LLM reasoning   │       │
                    │ Tool calls?     │       │
                    └───┬─────────┬───┘       │
                        │         │           │
                   No tools    Has tools      │
                        │         │           │
                        │    ┌────▼────┐      │
                        │    │ EXECUTE │      │
                        │    │ TOOLS   │      │
                        │    │         │──────┘
                        │    │ task_mgr│  (loop back if
                        │    │ calendar│   more tools needed)
                        │    │ search  │
                        │    │ finance │
                        │    │ memory  │
                        │    └─────────┘
                        │
               ┌────────▼────────┐
               │  RESPOND        │
               │                 │
               │ Format response │
               │ Stream to user  │
               └────────┬────────┘
                        │
               ┌────────▼────────┐
               │  POST-PROCESS   │
               │                 │
               │ • Save memory   │
               │ • Log usage     │
               │ • Update context│
               │ • Trigger follow│
               └─────────────────┘
```

### Tool Registry (MVP)

| Tool | Function | Priority |
|------|----------|----------|
| `task_create` | Create task with optional subtasks + reminders | P0 |
| `task_list` | List/filter user's tasks | P0 |
| `task_update` | Update status, due date, details | P0 |
| `calendar_create` | Create calendar event with reminders | P0 |
| `calendar_list` | List upcoming events | P0 |
| `memory_save` | Explicitly save important info | P0 |
| `memory_search` | Search user's personal knowledge base | P0 |
| `web_search` | Search the web for information | P1 |
| `summarize_url` | Fetch and summarize a URL | P1 |
| `expense_log` | Log an expense (manual or from receipt) | P1 |
| `budget_check` | Check spending vs budget | P1 |
| `draft_email` | Draft an email for user review | P2 |
| `analyze_document` | Read and analyze uploaded document | P2 |

## 6. LLM Gateway — Model Routing

```python
# Model tiers and routing rules
ROUTING_CONFIG = {
    "simple": {
        "models": ["gemini-2.0-flash", "deepseek-v3.2"],
        "max_tokens": 1000,
        "tasks": ["greeting", "simple_qa", "task_status", "reminder"]
    },
    "medium": {
        "models": ["claude-haiku-4.5", "gemini-2.5-flash"],
        "max_tokens": 2000,
        "tasks": ["summarize", "calendar_planning", "expense_analysis"]
    },
    "complex": {
        "models": ["claude-sonnet-4.6", "gpt-5.2"],
        "max_tokens": 4000,
        "tasks": ["research", "document_analysis", "multi_step_planning", "writing"]
    }
}

# Cost optimization stack (applied in order):
# 1. Prompt caching (90% off repeated system prompts)
# 2. Model routing (85% cost reduction vs always-flagship)
# 3. Budget caps (prevent runaway costs)
# 4. Batch processing (50% off for async tasks like proactive briefings)
```

## 7. Memory Service — Dual Layer

```
┌─────────────────────────────────────────────┐
│              MEMORY SERVICE                  │
│                                              │
│  ┌─────────────────────────────────────┐    │
│  │         HOT PATH (always loaded)     │    │
│  │                                      │    │
│  │  • User profile summary (200 tokens) │    │
│  │  • Active tasks (top 5)              │    │
│  │  • Today's calendar                  │    │
│  │  • Last 3 conversation summaries     │    │
│  │  • Key preferences                   │    │
│  │                                      │    │
│  │  Storage: Redis (per session)        │    │
│  │  Token budget: ~500 tokens           │    │
│  └─────────────────────────────────────┘    │
│                                              │
│  ┌─────────────────────────────────────┐    │
│  │         COLD PATH (on demand)        │    │
│  │                                      │    │
│  │  • Episodic: past conversations      │    │
│  │  • Semantic: facts about user        │    │
│  │  • Relationships: people context     │    │
│  │  • Procedural: learned patterns      │    │
│  │                                      │    │
│  │  Storage: PostgreSQL + pgvector      │    │
│  │  Retrieval: top-K semantic search    │    │
│  │  Token budget: ~300 tokens (dynamic) │    │
│  └─────────────────────────────────────┘    │
│                                              │
│  ┌─────────────────────────────────────┐    │
│  │      MEMORY EXTRACTION (post-turn)   │    │
│  │                                      │    │
│  │  After each conversation turn:       │    │
│  │  1. Extract new facts → semantic     │    │
│  │  2. Summarize episode → episodic     │    │
│  │  3. Detect patterns → procedural     │    │
│  │  4. Update user profile if changed   │    │
│  │                                      │    │
│  │  Uses: cheap model (Gemini Flash)    │    │
│  │  Runs: async (not blocking response) │    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

## 8. Proactive Scheduler

```
┌──────────────────────────────────────┐
│        PROACTIVE ENGINE              │
│        (ARQ worker + cron)           │
│                                      │
│  Triggers:                           │
│  ┌────────────────────────────────┐  │
│  │ 08:00  Morning Briefing       │  │
│  │ 21:00  Evening Review         │  │
│  │ -15min Before each meeting    │  │
│  │ -1day  Deadline approaching   │  │
│  │ weekly Sunday Review          │  │
│  │ event  Budget threshold hit   │  │
│  │ event  Pattern anomaly        │  │
│  └────────────────────────────────┘  │
│                                      │
│  Pipeline:                           │
│  1. Trigger fires                    │
│  2. Load user context                │
│  3. Generate message (batch API=50%) │
│  4. Send via user's primary channel  │
│  5. Log interaction                  │
└──────────────────────────────────────┘
```

## 9. Backend Module Structure

```
backend/
├── main.py                    # FastAPI app entry
├── core/
│   ├── config.py              # Settings (env-based)
│   ├── security.py            # JWT, auth helpers
│   └── deps.py                # Dependency injection
├── channels/
│   ├── base.py                # Abstract channel adapter
│   ├── zalo.py                # Zalo OA webhook + API
│   ├── zalo_bot.py            # Zalo Bot Platform
│   └── telegram.py            # Telegram Bot API
├── agent/
│   ├── graph.py               # LangGraph StateGraph definition
│   ├── state.py               # Agent state schema
│   ├── nodes/
│   │   ├── router.py          # Intent classification + model selection
│   │   ├── agent_loop.py      # Core reasoning loop
│   │   ├── response.py        # Response formatting
│   │   └── post_process.py    # Memory extraction, logging
│   └── tools/
│       ├── task_tools.py      # Task CRUD
│       ├── calendar_tools.py  # Calendar CRUD
│       ├── memory_tools.py    # Memory save/search
│       ├── web_tools.py       # Web search, URL summarize
│       ├── finance_tools.py   # Expense, budget
│       └── comms_tools.py     # Email draft
├── llm/
│   ├── gateway.py             # LiteLLM Proxy client (ChatOpenAI)
│   ├── router.py              # Smart model routing
│   ├── cache.py               # Prompt caching layer
│   ├── embeddings.py          # Embedding service
│   └── budget.py              # Per-user budget tracking
├── memory/
│   ├── service.py             # Memory service (hot + cold)
│   ├── extraction.py          # Post-turn memory extraction
│   ├── context_builder.py     # Build context for LLM
│   ├── conversation_memory.py # SummaryBuffer + rolling summary
│   ├── consolidation.py       # LLM-based dedup (INSERT/UPDATE/DELETE)
│   ├── preference_learning.py # Auto-extract user preferences
│   └── knowledge_graph.py     # pgvector knowledge graph
├── services/
│   ├── user.py                # User profile management
│   ├── task.py                # Task business logic
│   ├── calendar.py            # Calendar business logic
│   ├── finance.py             # Finance business logic
│   └── proactive.py           # Proactive scheduler
├── db/
│   ├── session.py             # SQLAlchemy async session
│   ├── models.py              # ORM models
│   └── migrations/            # Alembic
└── api/
    ├── v1/
    │   ├── webhooks.py        # Channel webhooks (Zalo, TG)
    │   ├── auth.py            # Login, register
    │   ├── users.py           # User profile API
    │   ├── tasks.py           # Task API (for web dashboard)
    │   ├── calendar.py        # Calendar API
    │   └── analytics.py       # Usage, spending analytics
    └── deps.py
```

## 10. Infrastructure

```yaml
# docker-compose.yml (simplified)
services:
  backend:        # FastAPI app (port 8000)
  worker:         # ARQ worker (proactive scheduler, async jobs)
  frontend:       # Next.js web dashboard (port 3000)
  postgres:       # PostgreSQL 16 + pgvector
  redis:          # Cache, sessions, queue
  minio:          # File storage

# External services (separate compose stacks):
#   litellm-proxy  — LLM routing proxy (port 4000)
#   cloudflared    — Cloudflare Tunnel (SSL + routing)
```

## 11. Security

| Concern | Solution |
|---------|----------|
| Auth | JWT tokens (access + refresh), Zalo/TG user verification |
| Data at rest | PostgreSQL encryption, MinIO server-side encryption |
| Data in transit | TLS everywhere (Cloudflare Tunnel handles SSL) |
| LLM data | All calls via LiteLLM Proxy, system prompt instructs: never leak user data |
| Rate limiting | Redis-based per-user rate limits (split read/write) |
| Input sanitization | Validate all inputs, prevent prompt injection |
| Secrets | Environment variables, never in code |
| GDPR/VN data law | Data export, deletion API, consent tracking |

## 12. Deployment Strategy

```
Development          Production
───────────          ──────────
docker-compose       docker-compose + docker-compose.prod.yml
local PostgreSQL     PostgreSQL (Docker volume)
local Redis          Redis (Docker volume)
ngrok (webhooks)     Cloudflare Tunnel (SSL + routing)
.env                 .env.prod (strong passwords)
Sentry (dev)         Sentry (production)

Cost: $0             Cost: ~$30-50/mo VPS
                     (scales with users)
```

MVP deployment target: **Single VPS** (4 vCPU, 8GB RAM, ~$30-50/mo) handles up to ~5,000 users.

## 13. Implementation Phases

| Phase | Scope | Duration |
|-------|-------|----------|
| **P0: Core** | Channel adapters (Zalo+TG) + LangGraph agent + basic chat + task tools + simple memory | 3 weeks |
| **P1: Intelligence** | Smart routing + calendar tools + proactive (morning brief) + memory extraction | 2 weeks |
| **P2: Depth** | Finance tools + document analysis + web search + voice input | 2 weeks |
| **P3: Dashboard** | Next.js web app: tasks view, calendar, settings, memory browser | 2 weeks |
| **P4: Polish** | Onboarding flow, trust features (source citations), Vietnamese NLP tuning | 1 week |

**Total MVP: ~10 weeks** with 3-person team.
