# Changelog

## [6.0.0] — 2026-03-16

### Phase A: Deep Autonomy
- **M33 Long-running Tasks**: background agent execution (30min timeout), progress tracking, cancel support. `POST/GET/DELETE /api/v1/agent-tasks`
- **M34 Scheduled Agents**: new trigger type `scheduled_agent` — user-defined cron prompts ("mỗi sáng tóm tắt email"). Runs 3x/day
- **M35 Multi-agent Collaboration**: parallel sub-agents via `asyncio.gather`, decompose → execute → aggregate pipeline
- **M36 Agent Memory v2**: auto-maintained user profile (job, location, goals, hobbies, communication style), cross-session context

### Phase B: Developer Ecosystem
- **M37 Public API**: `/api/public/v1/` with API key auth (`X-API-Key`), endpoints: `POST /chat`, `GET /tools`, `POST /tools/:name/invoke`, `GET /memory/search`. `APIKey` DB model with request counting
- **M38 Custom Tools SDK**: upload Python function, AST validation (block os/sys/subprocess), restricted builtins, 30s execution timeout. `CustomTool` DB model
- **M39 Plugin Marketplace**: publish/browse/install custom tools, API key management (create/list/revoke). `POST/GET/DELETE /marketplace/tools`, `/api-keys`
- **M40 Webhook Actions**: new trigger type `webhook_action` — call external URL on events, 3 retries with exponential backoff

### Phase C: Retention & Engagement
- **M41 Daily Habits**: habit tracker with streak counting, best streak, daily check-in. `Habit` + `HabitLog` DB models
- **M43 Achievements**: 6 badges (first_chat, streak_7, streak_30, task_master, power_user, explorer), stats-based checking
- **M44 Data Export**: full user data export as JSON (tasks, calendar, expenses, memories, conversations, preferences)
- API: `POST/GET /habits`, `POST /habits/:id/check-in`, `GET /achievements`, `GET /export`

## [5.0.0] — 2026-03-16

### Phase A: Production Hardening
- **M19**: Alembic migration for `google_oauth_tokens` table
- **M20**: Prod compose — backend memory 512M→1G for Playwright
- **M21**: `/health/ready` deep health check (postgres, redis, minio, litellm)
- **M22**: Per-endpoint rate limits (voice 5rpm, upload 10rpm, chat 20rpm), browser SSRF protection (URL allowlist, block internal IPs/metadata)
- **M23**: Weather Redis cache (15min TTL)

### Phase B: AI Quality
- **M24 Smart Tool Selection**: keyword→tool mapping hints in system prompt, "always prefer tool" rule
- **M25 RAG v2**: hybrid search (vector cosine + keyword ILIKE) with Reciprocal Rank Fusion (RRF k=60)
- **M26 Agentic Workflows**: 4 workflow templates (research, trip_planning, weekly_review, email_digest) injected into planner
- **M27 Vietnamese Prompt Tuning**: evaluate criteria expanded — Vietnamese naturalness check, tool usage validation

### Phase C: Growth & Monetization
- **M28 Onboarding**: auto-create default triggers (morning_briefing + deadline_approaching) on wizard completion
- **M29 Billing**: Stripe checkout + webhook, 3 tiers (free $0, pro $5/mo, pro+ $15/mo), `GET /billing/plans`, `POST /billing/checkout`
- **M30 Landing Page v2**: updated to 18 modules, 24 tools, voice + vision + proactive demos
- **M31 Analytics Digest**: `GET /analytics/digest` — weekly summary (messages, cost, top tools)
- **M32 Zalo Submission**: privacy policy page, app-config metadata, store listing ready

## [4.0.0] — 2026-03-16

### M12: Advanced Voice Pipeline
- Backend STT via Gemini 2.0 Flash (`gemini-stt`) through LiteLLM Proxy
- Backend TTS via Vertex AI Chirp3 HD (`vertex-tts`) through LiteLLM Proxy
- `POST /api/v1/voice/transcribe` — audio upload → text transcription
- `GET /api/v1/voice/speak` — text → streaming WAV audio (HTTP chunked)
- Frontend: MediaRecorder-based recording → backend transcribe → fallback Web Speech API
- Frontend: Backend TTS with Piper WASM fallback
- Feature flag `VOICE_ENABLED`, 10MB upload limit, 2000 char TTS limit
- 10 tests (4 unit + 6 API)

### M16: Auto-TTS (Hands-free Voice Loop)
- Voice mode toggle (headphones icon) in chat input
- When ON: AI responses auto-play TTS → auto-start mic → transcribe → auto-send → loop
- `useTTS(onEnd?)` callback for chaining TTS → STT
- Auto-send STT results in voice mode (no manual send needed)

### M14: Event-driven Proactive Engine
- **Event Bus**: Redis Streams (`jarvis:events`), `emit()` from any endpoint/tool
- **Trigger Engine**: `TriggerHandler` base class + `@register_handler` decorator pattern
- **5 built-in triggers**:
  - `deadline_approaching`: task due within N hours → notify (default 2h)
  - `budget_exceeded`: daily spending exceeds threshold → alert (default 500K VND)
  - `calendar_conflict`: overlapping events detected → ask user
  - `memory_insight`: conversation patterns → LLM-generated proactive suggestions
  - `morning_briefing`: daily summary (migrated from V3 cron to event-driven)
- **CRUD API**: `POST/GET/PATCH/DELETE /api/v1/triggers` + `GET /types`
- **Event emitters** wired into: task create/update, calendar create, expense_log, WS conversation end
- ARQ worker: event consumer as background task + cron jobs emit into bus
- Extensibility: new trigger = 1 file + `@register_handler`

### M13: Zalo Mini App
- **HTTP chat endpoint** `POST /api/v1/chat` — synchronous graph invocation for environments without WebSocket
- **ZMP auth** `POST /auth/zalo-miniapp` — exchange Zalo Mini App access token for JWT via Zalo Graph API
- **Chat page**: voice recording (MediaRecorder → backend STT), TTS playback on AI messages, 4 quick actions (weather, news, tasks, calendar)
- **Tasks page**: inline task creation, toggle done/todo
- **API client**: token auto-refresh, voice transcribe/speak helpers
- 4 pages: Chat (voice-first), Tasks, Calendar, Notifications with bottom navigation

### M15: Vietnamese Service Integrations
- **5 new agent tools** (13 → 18 total):
  - `weather_vn`: OpenWeather API, 15+ Vietnamese city aliases, formatted tiếng Việt
  - `news_vn`: VnExpress RSS (8 chuyên mục: thời sự, thế giới, kinh doanh, công nghệ, thể thao, giải trí, sức khỏe, giáo dục), optional LLM summary
  - `google_calendar_list`: read events from user's Google Calendar via OAuth2
  - `gmail_read`: list recent emails with metadata via Gmail API
  - `gmail_send`: send email via Gmail API
- **Google OAuth2 per-user consent flow**: authorization code → access_token + refresh_token, auto-refresh with 5min buffer
- **GoogleOAuthToken** DB model for per-user token storage
- **API endpoints**: `GET /google/auth-url`, `GET /google/callback`, `GET /google/status`, `DELETE /google/disconnect`
- Config: `OPENWEATHER_API_KEY`, `GOOGLE_CLIENT_SECRET`

### M17: File & Image Understanding
- **File upload** `POST /api/v1/files/upload` — MinIO storage, supports images/PDF/docs (max 20MB)
- **Vision module** `services/vision.py` — Gemini 2.0 Flash multimodal via LiteLLM proxy
  - `analyze_image()`: general image analysis with custom prompts
  - `ocr_document()`: text extraction from receipts, invoices, screenshots
- **2 new agent tools** (18 → 20 total): `analyze_file`, `ocr_file`
- **HTTP chat** accepts `file_key` for image-attached messages
- **Mini App**: file attach button (📎), image preview in bubbles, pending file indicator

### M18: Browser Automation
- **4 new agent tools** (20 → 24 total):
  - `browse_web`: navigate URL + extract text, optional LLM Q&A about page content
  - `browse_click`: navigate + click element (CSS selector) + extract result
  - `browse_fill`: navigate + fill form fields (JSON) + submit
  - `browse_screenshot`: capture page screenshot + analyze with Gemini vision
- **Playwright Chromium** headless, shared instance with asyncio.Lock
- Dockerfile updated: `playwright install --with-deps chromium`

### V3 Codebase Review (16 fixes)
- P0: prod backend/worker missing litellm-net network, webhook using non-checkpointed graph, refresh token UUID mismatch, webhook missing conversation_id
- P1: webhook channels upgraded to full V3 features, WS auto-reconnect (exponential backoff), streaming state reset on disconnect
- P2: embeddings through LiteLLM proxy, post_process fire-and-forget, checkpointer asyncio.Lock, injection blocking (score >= 0.8), datetime.utcnow → timezone-aware, cache_control immutable, MinIO healthcheck

## [3.0.0] — 2026-03-12

### Post-release (2026-03-13)

#### Security Hardening
- Untrack `.env.prod` from git, gitignore all `.env.*` files
- Strong passwords for PostgreSQL, Redis, MinIO in production
- Refresh token rotation (one-time use via Redis jti tracking)
- WebSocket auth via first-message token (no longer in URL query param)
- Telegram webhook: dedicated secret with `hmac.compare_digest`
- Register: email validation + password strength (8+ chars, digit, letter)
- Frontend Dockerfile: build args instead of hardcoded values
- Git history cleaned of all secrets via `git filter-repo`

#### Features
- Piper TTS: Vietnamese voice (`vi_VN-vais1000-medium`) running in browser via WASM
- Landing page with hero, 6 feature cards, demo conversation flow, CTA
- Feedback buttons (👍👎) on AI messages
- Sentry integration (backend + frontend error tracking)
- LiteLLM Proxy: all LLM calls routed through unified proxy
- Rate limiting redesign: split read (120rpm) / write (30rpm) limits

#### Infrastructure
- Azure Pipelines CI/CD (lint + build + deploy)
- Cloudflare Tunnel (replaced Traefik)
- `make prod` uses `--env-file .env.prod` for proper secret isolation
- Removed unused Traefik config

#### Bug Fixes
- `column conversations.rolling_summary does not exist` — applied 3 Alembic migrations
- `AsyncPostgresSaver` context manager fix + dead connection reconnect
- `get_current_user` → `get_current_user_id` in feedback endpoint
- `429 Too Many Requests` on `/users/me` — rate limit redesigned

### Intelligence Layer (11 modules)
- **M1 Smart Router**: LLM-based intent classification, complexity detection, model selection, Redis cache 1h, keyword fallback
- **M2 Conversation Memory**: SummaryBuffer (10 turns verbatim + rolling summary), Redis lock for race conditions
- **M3 Plan-and-Execute**: 4-node LangGraph flow (planner → executor → replan → synthesize), max 7 steps, max 2 replans
- **M4 Memory Consolidation**: LLM-based INSERT/UPDATE/DELETE/SKIP with candidate retrieval, safe UUID parsing
- **M5 Preference Learning**: Auto-extract preferences from conversations, build preference prompt, dedup rules
- **M6 Context Guard**: Token estimation, tool result truncation, oldest message dropping, 20% output reserve
- **M7 Checkpointing**: AsyncPostgresSaver singleton for conversation state persistence
- **M8 HITL**: WebSocket approval flow for destructive tool calls, interrupt() mechanism
- **M9 Evidence Logging**: log_evidence() + evidence_timer() context manager, audit API with filters
- **M10 Supervision**: SessionSupervisor with heartbeat (10s), timeout (5min), stale session cleanup
- **M11 Tool Permissions**: Per-user tool enable/disable, Redis-cached (60s)

### Frontend
- Approval dialog for HITL (WebSocket-driven)
- Plan progress indicator ("Bước 2/5: description")
- Conversation resume with rolling summary badge
- Settings page: 7 tabs (Profile, Preferences, Memory, Connections, Subscription, Tools, Audit)
- Voice I/O: STT (vi-VN) mic button + TTS speaker button on AI messages

### Infrastructure
- 11 feature flags in config
- 3 Alembic migrations (evidence_log, conversation_memory, preferences)
- 28 integration tests (test_v3_integration.py)

### Bug Fixes (2 code review rounds, 13 fixes)
- Context guard: no longer mutates messages in-place
- Graph: cached singleton, proper UUID import
- Consolidation: safe UUID parsing on LLM hallucination
- Conversation memory: Redis lock for race conditions
- Plan-execute: HITL checks actual tool_calls, rejection short-circuit
- Preference learning: dedup prompt rules before insert
- Supervision: correct stale session cleanup logic
- Tool permissions: Redis cache 60s

## [2.0.0] — 2026-02

### Core
- LangGraph agent pipeline with multi-agent delegation
- Multi-model LLM gateway (Gemini, Claude, DeepSeek, GPT)
- Knowledge graph (pgvector 3072-dim)
- Security: injection detection, rate limiting, budget control
- MCP client integration

### Channels
- Zalo OA + Zalo Bot
- Telegram Bot
- Web (Next.js 15)

### Tools (13)
- task_create, task_list, task_update
- calendar_create, calendar_list
- memory_save, memory_search
- web_search, summarize_url
- expense_log, budget_check
- graph_search

## [1.0.0] — 2026-01

- Initial release: FastAPI backend, Next.js frontend, basic chat
