# Changelog

## [3.0.0] — 2026-03-12

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
