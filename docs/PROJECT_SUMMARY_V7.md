# MY JARVIS — Project Summary V7.0.0

> Scope closed: 2026-03-17

Vietnamese-first agentic personal AI assistant. Multi-channel, smart LLM routing, persistent memory, proactive automation, developer ecosystem.

**Timeline**: V1 (2026-01) → V7 (2026-03-16) — 3 months, 44 modules, 7 major releases.

---

## Final Numbers

| Metric | Count |
|--------|-------|
| Channels | 8 (Zalo OA, Zalo Bot, Telegram, Web, Mini App, WhatsApp, Slack, Discord) |
| Agent tools | 24 built-in + custom tools SDK |
| API endpoints | 54 (v1) + public API (v1) |
| DB models | 22 |
| Alembic migrations | 11 |
| Tests | 51 passing (Docker) |
| Feature flags | 15 (all enabled) |
| Trigger types | 7 |
| Backend files | 155+ Python |
| Frontend files | 50+ TypeScript/TSX |

---

## Architecture

```
Zalo OA / Zalo Bot / Telegram / WhatsApp / Slack / Discord / Web / Mini App
        |
   Cloudflare Tunnel (HTTPS at edge)
        |
   Next.js 15 (frontend)  +  FastAPI (backend)
        |
   LangGraph Agent Pipeline:
     route → [planner → executor → replan → synthesize] | delegate | agent_loop ↔ tools → respond → evaluate → post_process
        |
   LiteLLM Proxy (http://litellm:4000)
     → Gemini 2.0 Flash / 1.5 Pro, Claude 3.5 Sonnet, DeepSeek, GPT-4
        |
   PostgreSQL+pgvector | Redis | MinIO
```

### Services (Docker Compose)

| Service | Image | Dev Port | Prod Memory |
|---------|-------|----------|-------------|
| backend | FastAPI (Python 3.12, uv) | 8002 | 1G |
| frontend | Next.js 15 | 3002 | 256M |
| worker | ARQ (proactive engine) | — | 512M |
| postgres | pgvector/pgvector:pg16 | 5435 | — |
| redis | redis:7-alpine | 6381 | 256M |
| minio | minio (S3) | 9000/9001 | 512M |

Networks: `litellm-proxy_default` (LLM), `tunnel-net` (Cloudflare, prod only).

---

## Version History

### V1.0.0 (2026-01) — Initial Release
FastAPI backend + Next.js frontend + basic chat.

### V2.0.0 (2026-02) — Core Foundation
- LangGraph agent pipeline with multi-agent delegation
- Multi-model LLM gateway via LiteLLM Proxy
- Knowledge graph (pgvector 3072-dim embeddings)
- Security: injection detection, rate limiting, budget control
- MCP client integration
- 4 channels: Zalo OA, Zalo Bot, Telegram, Web
- 13 tools: tasks, calendar, memory, web search, finance, knowledge graph

### V3.0.0 (2026-03-12) — Intelligence Layer
11 modules (M1-M11):

| Module | Feature |
|--------|---------|
| M1 | Smart Router — intent classification, complexity detection, model selection |
| M2 | Conversation Memory — SummaryBuffer (10 turns + rolling summary) |
| M3 | Plan-and-Execute — planner → executor → replan → synthesize (max 7 steps) |
| M4 | Memory Consolidation — LLM-based INSERT/UPDATE/DELETE/SKIP |
| M5 | Preference Learning — auto-extract from conversations |
| M6 | Context Guard — token estimation, truncation, 20% output reserve |
| M7 | Checkpointing — AsyncPostgresSaver for state persistence |
| M8 | HITL — WebSocket approval for destructive tool calls |
| M9 | Evidence Logging — audit trail on every tool call |
| M10 | Supervision — heartbeat (10s), timeout (5min), stale cleanup |
| M11 | Tool Permissions — per-user enable/disable, Redis-cached |

Post-release: security hardening (refresh token rotation, WebSocket auth, password strength, git history clean), Piper TTS, Sentry, Azure Pipelines CI/CD, Cloudflare Tunnel.

### V4.0.0 (2026-03-16) — Voice & Intelligence Pipeline
7 modules (M12-M18):

| Module | Feature |
|--------|---------|
| M12 | Voice Pipeline — Gemini STT + Vertex TTS, streaming WAV |
| M13 | Zalo Mini App — HTTP chat, ZMP auth, 4 pages (voice-first) |
| M14 | Proactive Engine — Redis Streams event bus, 5 trigger types, ARQ worker |
| M15 | Vietnamese Services — weather_vn, news_vn, Google Calendar/Gmail (OAuth2) |
| M16 | Auto-TTS — hands-free voice loop (speak → listen → send → repeat) |
| M17 | File & Image — MinIO upload, Gemini vision, OCR (20MB limit) |
| M18 | Browser Automation — Playwright headless, 4 tools (navigate/click/fill/screenshot) |

Tools: 13 → 24.

### V5.0.0 (2026-03-16) — Production & Growth
14 modules (M19-M32):

**Phase A — Production Hardening (M19-M23)**: deep healthcheck, per-endpoint rate limits, SSRF protection, weather cache.

**Phase B — AI Quality (M24-M27)**: smart tool selection, RAG v2 (hybrid search + RRF), agentic workflow templates, Vietnamese prompt tuning.

**Phase C — Growth & Monetization (M28-M32)**: onboarding wizard, Stripe billing (free/$5/$15), landing page v2, analytics digest, Zalo store submission.

### V6.0.0 (2026-03-16) — Autonomy & Ecosystem
12 modules (M33-M44):

**Phase A — Deep Autonomy (M33-M36)**: long-running tasks (30min), scheduled agents (user cron), multi-agent collaboration (parallel), agent memory v2 (user profile).

**Phase B — Developer Ecosystem (M37-M40)**: public API (`/api/public/v1/`), custom tools SDK (AST validation), plugin marketplace, webhook actions.

**Phase C — Retention & Engagement (M41-M44)**: daily habits + streaks, achievements (6 badges), data export (full JSON).

### V7.0.0 (2026-03-16) — Channel Expansion
5 → 8 channels:

| Channel | Protocol | Verification |
|---------|----------|-------------|
| WhatsApp | Business Cloud API | X-Hub-Signature-256 |
| Slack | Events API | HMAC signing secret v0 |
| Discord | Interactions API | Ed25519 (PyNaCl) |

All 8 channels receive proactive notifications. DB: `whatsapp_id`, `slack_id`, `discord_id` columns.

---

## Agent Pipeline

```
route (Smart Router)
 ├─ simple → agent_loop → tools ↔ agent_loop → respond → evaluate → post_process
 ├─ complex → planner → executor → tools → replan? → synthesize
 └─ delegate → sub-agents (parallel) → aggregate → respond
```

### 10 Pipeline Nodes

1. **route** — classify intent + complexity, select model, detect injection
2. **agent_loop** — core reasoning, generate tool calls
3. **tools** — execute with permission check + HITL + evidence logging
4. **delegate** — spawn parallel sub-agents
5. **respond** — format response, memory consolidation
6. **evaluate** — quality check, supervision heartbeat
7. **post_process** — context guard, token management
8. **planner** — break complex task into steps (max 7)
9. **executor** — execute plan steps
10. **replan** — re-evaluate on failure (max 2 attempts)

### 24 Tools

| Category | Tools |
|----------|-------|
| Tasks | task_create, task_list, task_update |
| Calendar | calendar_create, calendar_list |
| Memory | memory_save, memory_search |
| Web | web_search, summarize_url |
| Finance | expense_log, budget_check |
| Knowledge | graph_search |
| Vietnamese | weather_vn, news_vn |
| Google | google_calendar_list, gmail_read, gmail_send |
| Vision | analyze_file, ocr_file |
| Browser | browse_web, browse_click, browse_fill, browse_screenshot |

Pattern: `@tool` decorator + `user_id: Annotated[str, InjectedToolArg]`.

---

## Channels

| # | Channel | Adapter | Verification | Max Response |
|---|---------|---------|-------------|-------------|
| 1 | Zalo OA | `channels/zalo.py` | Zalo OA token | — |
| 2 | Zalo Bot | `channels/zalo_bot.py` | Bot token | — |
| 3 | Telegram | `channels/telegram.py` | HMAC-SHA256 | — |
| 4 | Web | Next.js + WebSocket | JWT (first message) | — |
| 5 | Mini App | HTTP `POST /chat` | Zalo Mini App JWT | — |
| 6 | WhatsApp | `channels/whatsapp.py` | X-Hub-Signature-256 | 4096 chars |
| 7 | Slack | `channels/slack.py` | HMAC v0 signing | — |
| 8 | Discord | `channels/discord.py` | Ed25519 | 2000 chars |

Base class: `ChannelAdapter` (parse_incoming, send_response, verify_webhook).

---

## Proactive Engine

Event bus: Redis Streams (`jarvis:events`). Worker: ARQ with cron jobs.

| Trigger Type | Description | Schedule |
|-------------|-------------|----------|
| morning_briefing | Daily summary (weather, news, tasks, emails) | 08:00 VN |
| deadline_approaching | Task due within N hours | 3x/day |
| budget_exceeded | Daily spending > threshold | On event |
| calendar_conflict | Overlapping events detected | On event |
| memory_insight | LLM-generated proactive suggestions | On session end |
| scheduled_agent | User-defined cron prompts | 3x/day |
| webhook_action | Call external URL on events | On event |

Pattern: `TriggerHandler` + `@register_handler` + `should_fire()` + `build_message()`.

---

## Database Schema (22 Models)

**Users**: User (8 channel IDs, tier, preferences)

**Productivity**: Task, CalendarEvent, Expense, Habit, HabitLog

**Conversations**: Conversation (rolling_summary), Message

**Memory**: Memory (3072-dim embedding), KnowledgeEntity, KnowledgeRelation

**Preferences**: UserPreference, UserPromptRule, UserToolPermission

**Proactive**: ProactiveTrigger, Notification

**Integrations**: GoogleOAuthToken, CustomTool, APIKey, MCPServer

**Analytics**: LLMUsage, EvidenceLog

11 Alembic migrations. Latest: `f6a7b8c9d0e1` (v7_channel_ids).

---

## Frontend

Next.js 15, App Router, Tailwind CSS v4, TypeScript.

### Pages

| Route | Feature |
|-------|---------|
| `/` | Landing page (hero, features, demo, CTA) |
| `/login`, `/register` | Auth (email + password + Google OAuth) |
| `/chat` | Main chat (WebSocket streaming, voice, HITL approval, plan progress) |
| `/tasks` | Task management (create, toggle, filter) |
| `/calendar` | Calendar events |
| `/settings` | 7 tabs: Profile, Preferences, Memory, Connections, Subscription, Tools, Audit |
| `/analytics` | Usage stats, spending, weekly summary |
| `/onboarding` | Setup wizard (triggers, Google OAuth, channel linking) |

### State & Realtime

- **Zustand**: auth store (JWT, auto-refresh), chat store (conversations, messages, streaming)
- **WebSocket**: `createWSClient()` — message types: stream, done, approval_request, plan_progress
- **Voice hooks**: `useTTS()`, `useVoice()` — hands-free loop
- **API client**: typed fetch wrapper, auto-refresh on 401

---

## Security

| Layer | Implementation |
|-------|---------------|
| Auth | JWT + refresh token rotation (Redis jti, one-time use) |
| Password | 8+ chars, digit + letter required |
| Rate limiting | Per-endpoint (voice 5rpm, upload 10rpm, chat 20rpm) |
| Injection | LLM-based detection (score >= 0.8 blocks) |
| Webhooks | HMAC-SHA256, X-Hub-Signature-256, Ed25519 per channel |
| SSRF | URL allowlist, block internal IPs/metadata endpoints |
| Headers | Security headers middleware |
| Secrets | .env never committed, prod validation (SECRET_KEY >= 32 chars) |
| User isolation | user_id on all DB queries |
| Audit | Evidence logging on every tool call |

---

## LLM Integration

All calls via LiteLLM Proxy (`http://litellm:4000`). Never call provider APIs directly.

| Purpose | Model | Method |
|---------|-------|--------|
| Chat (simple) | gemini/gemini-2.0-flash | ChatOpenAI via proxy |
| Chat (complex) | gemini/gemini-1.5-pro, claude-3.5-sonnet | ChatOpenAI via proxy |
| Vision | gemini/gemini-2.0-flash | Multimodal via proxy |
| STT | gemini-stt | Via proxy |
| TTS | vertex-tts | Via proxy |
| Embeddings | gemini-embedding-001 | Direct Google API |

Budget: per-user daily tracking. Router: select model by complexity tier + remaining budget.

---

## Monetization

Stripe integration with 3 tiers:

| Tier | Price | Limits |
|------|-------|--------|
| Free | $0/mo | Basic tools, rate limited |
| Pro | $5/mo | All tools, higher limits |
| Pro+ | $15/mo | Everything + priority, browser automation |

Endpoints: `GET /billing/plans`, `POST /billing/checkout`, `POST /billing/webhook`.

---

## DevOps

| Tool | Usage |
|------|-------|
| Docker Compose | 3-file pattern (base + dev + prod) |
| Cloudflare Tunnel | HTTPS routing, token-based |
| Azure Pipelines | CI/CD (lint + build + deploy) |
| Sentry | Error tracking (backend + frontend, 20% sample) |
| Makefile | `make dev`, `make prod`, `make test`, `make lint` |

Health: `GET /health` (liveness + version), `GET /health/ready` (postgres + redis + minio + litellm).

---

## What's NOT in Scope

Explicitly excluded from V7 scope closure:

- Mobile native app (React Native / Flutter)
- Multi-tenant / team workspaces
- End-to-end encryption
- Offline mode
- i18n (English UI)
- Advanced analytics dashboard (Grafana/Prometheus)
- Load testing / horizontal scaling
- Automated integration test suite (beyond 51 tests)

---

## Key Files

```
backend/
├── main.py                     # FastAPI app entry
├── agent/graph.py              # LangGraph pipeline
├── agent/state.py              # AgentState definition
├── agent/tools/                # 24 tools
├── agent/nodes/                # 10 pipeline nodes
├── api/v1/                     # 54 API endpoints
├── channels/                   # 8 channel adapters
├── llm/gateway.py              # LLM routing via LiteLLM
├── llm/router.py               # Model selection by complexity
├── llm/budget.py               # Per-user daily budget
├── services/proactive.py       # ARQ worker + cron
├── services/handlers/          # 7 trigger handlers
├── core/config.py              # Settings + 15 feature flags
├── db/models/                  # 22 SQLAlchemy models
└── db/migrations/              # 11 Alembic migrations

frontend/
├── app/(auth)/                 # Login, Register
├── app/(app)/                  # Chat, Tasks, Calendar, Settings, Analytics
├── lib/stores/                 # Zustand (auth, chat)
├── lib/api.ts                  # Typed API client
├── lib/ws.ts                   # WebSocket client
└── components/                 # UI + Chat + Layout components

docs/
├── PROJECT_SUMMARY_V7.md       # This document
├── architecture.md             # Technical architecture
├── design-spec.md              # Design specification
├── intelligence-layer-v3.md    # V3 intelligence design
├── v4-plan.md → v6-plan.md     # Version plans
└── zalo-integration.md         # Zalo setup guide
```

---

## Conclusion

MY JARVIS V7.0.0 is a feature-complete Vietnamese-first agentic AI assistant. 44 modules built across 7 versions in 3 months, covering:

- **8 channels** spanning Vietnamese and international platforms
- **24 tools** for productivity, knowledge, services, vision, and browser automation
- **Intelligent agent pipeline** with planning, memory, preferences, and supervision
- **Proactive automation** via event-driven triggers
- **Developer ecosystem** with public API, custom tools SDK, and marketplace
- **Production infrastructure** with security, monitoring, billing, and CI/CD

Scope is closed at V7.0.0. Future work should be driven by real user feedback.
