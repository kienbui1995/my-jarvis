# MY JARVIS v2 — Technical Design Document

> **Status:** ✅ Implemented (All 3 Phases Complete)
> **Author:** Architect Agent
> **Date:** 2026-03-10
> **Completed:** 2026-03-11
> **Inspired by:** GoClaw feature analysis
> **Scope:** 3-phase upgrade — Security → Intelligence → Multi-Agent

---

## 1. Current Architecture (v1)

```
WebSocket/HTTP → FastAPI → LangGraph StateGraph → LLM → Response
                    │
                    ├── route → agent_loop ⇄ tools → respond → post_process
                    │
                    ├── LLM Gateway: 3 providers (Google, Anthropic, OpenAI/DeepSeek)
                    ├── Memory: Hot Redis (5min TTL) + Cold pgvector (cosine)
                    ├── Tools: 11 (task, calendar, memory, web, finance)
                    └── Security: JWT + bcrypt only
```

### Gaps Identified (vs GoClaw)

| Area | Current | Target |
|------|---------|--------|
| Security | JWT auth only, CORS `*` | 5-layer defense |
| LLM Providers | 4 (hardcoded) | 13+ via OpenRouter |
| Prompt Caching | None | Anthropic `cache_control` |
| Memory | Flat vector search | + Knowledge Graph |
| Tool Extensibility | Hardcoded Python | + MCP Protocol |
| Output Quality | No validation | Evaluate step |
| Agent Architecture | Single agent | Specialized sub-agents |

---

## 2. Phase 1 — Security Hardening + Cost Optimization

**Timeline:** 1-2 tuần | **Risk:** Low | **Impact:** High
**Status:** ✅ Complete — Verified with tests (rate limit 429 at request #31, injection WARNING logged)

### 2.1 Rate Limiting

**Approach:** Token bucket per user, implemented as FastAPI middleware + Redis.

**Tại sao Redis token bucket?** Stateless across workers, O(1) per request, đã có Redis.

```
┌─────────┐     ┌──────────────┐     ┌─────────┐
│ Request  │────▶│ RateLimiter  │────▶│ Handler │
└─────────┘     │  (middleware) │     └─────────┘
                │              │
                │  Redis EVAL  │
                │  bucket check│
                └──────────────┘
                       │ 429 Too Many Requests
                       ▼
                   Rejected
```

**Limits by tier:**

| Tier | HTTP RPM | WS messages/min | Daily LLM calls |
|------|----------|-----------------|-----------------|
| free | 30 | 20 | 50 |
| pro | 120 | 60 | 500 |
| pro_plus | 300 | 120 | unlimited |

**Integration point:** `main.py` — add middleware before routers.

```python
# core/rate_limit.py
# Redis key: rate:{user_id}:{window}
# Algorithm: sliding window counter via INCR + EXPIRE

TIER_LIMITS = {
    "free": {"rpm": 30, "ws_pm": 20, "daily": 50},
    "pro": {"rpm": 120, "ws_pm": 60, "daily": 500},
    "pro_plus": {"rpm": 300, "ws_pm": 120, "daily": -1},
}
```

**Files to modify:**
- `core/rate_limit.py` — NEW: sliding window counter
- `main.py` — add `RateLimitMiddleware`
- `api/v1/ws.py` — per-message rate check

### 2.2 Prompt Injection Detection

**Approach:** Regex scanner (detection + log, never block) — same strategy as GoClaw.

**Tại sao detection-only?** False positives sẽ block legitimate requests. Log để monitor, alert khi spike.

```python
# core/injection.py
PATTERNS = [
    r"ignore\s+(previous|above|all)\s+instructions",
    r"you\s+are\s+now\s+(?:a|an)\s+",
    r"system\s*:\s*",
    r"<\|im_start\|>",
    r"```\s*system",
    r"ADMIN\s*OVERRIDE",
]
# Returns: (is_suspicious: bool, matched_pattern: str | None)
```

**Integration point:** `agent/nodes/router.py` — scan input before routing.

**Data model addition:**

```sql
-- New column on messages table
ALTER TABLE messages ADD COLUMN injection_score FLOAT DEFAULT 0;
```

### 2.3 Anthropic Prompt Caching

**Approach:** Inject `cache_control: {"type": "ephemeral"}` on system prompt + tool definitions for Anthropic models. Giảm ~90% cost cho repeated context.

**Tại sao chỉ Anthropic?** Anthropic là provider duy nhất hỗ trợ explicit `cache_control`. OpenAI/Google tự động cache internally.

```
Không cache:
  System prompt (2K tokens) × mỗi request = tính tiền đầy đủ

Có cache:
  System prompt cached → chỉ tính 10% giá
  Tool definitions cached → chỉ tính 10% giá
  Tiết kiệm: ~90% cho phần context không đổi
```

**Integration point:** `llm/gateway.py` — wrap Anthropic calls.

```python
# llm/cache.py
def with_cache_control(messages: list, model: str) -> list:
    """Inject cache_control for Anthropic models."""
    if "claude" not in model:
        return messages
    # Mark system prompt + last tool result as cacheable
    if messages and messages[0].type == "system":
        messages[0].additional_kwargs["cache_control"] = {"type": "ephemeral"}
    return messages
```

**Files to modify:**
- `llm/cache.py` — NEW (đã có file rỗng, implement logic)
- `agent/nodes/agent_loop.py` — call `with_cache_control()` before `llm.ainvoke()`

### 2.4 OpenRouter Provider

**Approach:** Thêm OpenRouter như 1 provider trong gateway. 1 API key = 30+ models.

**Tại sao OpenRouter thay vì thêm từng provider?** Single integration, unified billing, automatic fallback, access to Llama, Mixtral, Qwen, etc.

```
Trước:  4 providers × 4 API keys × 4 integrations
Sau:    4 providers + OpenRouter (1 key → 30+ models)
```

**Integration point:** `llm/gateway.py` + `core/config.py`

```python
# Thêm vào config.py
OPENROUTER_API_KEY: str = ""

# Thêm vào gateway.py MODEL_PROVIDERS
"llama-3.3-70b": ("openrouter", "meta-llama/llama-3.3-70b-instruct"),
"mixtral-8x22b": ("openrouter", "mistralai/mixtral-8x22b-instruct"),
"qwen-2.5-72b": ("openrouter", "qwen/qwen-2.5-72b-instruct"),

# _init_provider thêm case:
elif provider == "openrouter":
    return ChatOpenAI(
        model=model_name,
        openai_api_key=settings.OPENROUTER_API_KEY,
        openai_api_base="https://openrouter.ai/api/v1",
    )
```

**Router update:** Thêm OpenRouter models vào `TIER_MODELS`:

```python
TIER_MODELS = {
    "simple": ["gemini-2.0-flash", "deepseek-v3.2", "llama-3.3-70b"],
    "medium": ["claude-haiku-4.5", "gemini-2.5-flash", "mixtral-8x22b"],
    "complex": ["claude-sonnet-4.6", "gpt-5.2", "qwen-2.5-72b"],
}
```

### Phase 1 — Summary

```
Files NEW:     core/rate_limit.py, core/injection.py
Files MODIFY:  main.py, llm/gateway.py, llm/cache.py, llm/router.py,
               core/config.py, agent/nodes/agent_loop.py, agent/nodes/router.py,
               api/v1/ws.py
DB Migration:  messages.injection_score (nullable float)
Config:        OPENROUTER_API_KEY, RATE_LIMIT_ENABLED
```

---

## 3. Phase 2 — Knowledge Graph + MCP + Output Validation

**Timeline:** 2-4 tuần | **Risk:** Medium | **Impact:** High
**Status:** ✅ Complete — KG entities/relations persisted, MCP CRUD working, evaluate pass/fail verified

> **Implementation note:** `gemini-embedding-001` returns 3072-dim vectors. All `Vector(1536)` columns updated to `Vector(3072)` in both `memories` and `knowledge_entities` tables.

### 3.1 Knowledge Graph

**Approach:** LLM-powered entity/relationship extraction từ conversations → store trong PostgreSQL → graph traversal via recursive CTE.

**Tại sao PostgreSQL thay vì Neo4j?** Đã có PG, không thêm infra. Recursive CTE đủ cho depth ≤ 3. GoClaw cũng dùng PG.

```
Conversation → LLM Extract → Entities + Relations → PostgreSQL
                                                         │
User query → Entity match → Recursive CTE (depth 3) → Context
```

**Data model:**

```sql
CREATE TABLE knowledge_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,  -- person, place, project, concept
    description TEXT,
    embedding VECTOR(1536),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, name, entity_type)
);

CREATE TABLE knowledge_relations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    source_id UUID NOT NULL REFERENCES knowledge_entities(id),
    target_id UUID NOT NULL REFERENCES knowledge_entities(id),
    relation_type VARCHAR(100) NOT NULL,  -- works_at, knows, interested_in
    weight FLOAT DEFAULT 1.0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_ke_user ON knowledge_entities(user_id);
CREATE INDEX idx_ke_embedding ON knowledge_entities USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_kr_source ON knowledge_relations(source_id);
CREATE INDEX idx_kr_target ON knowledge_relations(target_id);
```

**Extraction prompt (chạy trong post_process, cùng lúc memory extraction):**

```python
GRAPH_EXTRACTION_PROMPT = """Trích xuất entities và relationships từ hội thoại.

Trả về JSON:
{
  "entities": [
    {"name": "...", "type": "person|place|project|concept", "description": "..."}
  ],
  "relations": [
    {"source": "entity_name", "target": "entity_name", "type": "works_at|knows|..."}
  ]
}

Hội thoại:
{conversation}"""
```

**Graph traversal (recursive CTE, max depth 3):**

```sql
WITH RECURSIVE graph AS (
    -- Base: entities matching query
    SELECT e.id, e.name, e.entity_type, e.description, 0 AS depth
    FROM knowledge_entities e
    WHERE e.user_id = :user_id
      AND (e.name ILIKE :query OR e.embedding <=> :query_embedding < 0.3)

    UNION ALL

    -- Recursive: follow relations up to depth 3
    SELECT e2.id, e2.name, e2.entity_type, e2.description, g.depth + 1
    FROM graph g
    JOIN knowledge_relations r ON r.source_id = g.id OR r.target_id = g.id
    JOIN knowledge_entities e2 ON e2.id = CASE
        WHEN r.source_id = g.id THEN r.target_id ELSE r.source_id END
    WHERE g.depth < 3 AND e2.user_id = :user_id
)
SELECT DISTINCT ON (id) * FROM graph ORDER BY id, depth;
```

**Integration points:**
- `memory/knowledge_graph.py` — NEW: extract + store + query
- `agent/nodes/post_process.py` — call graph extraction alongside memory extraction
- `memory/context_builder.py` — inject graph context into agent prompt
- `agent/tools/` — NEW tool: `knowledge_graph_search`

### 3.2 MCP Protocol Support

**Approach:** MY JARVIS as MCP client — connect to external MCP servers (stdio/SSE) to discover and call their tools at runtime.

**Tại sao MCP?** Industry standard 2026. Cho phép user kết nối tools bên ngoài (GitHub, Notion, Google Drive) mà không cần code custom.

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  MY JARVIS   │────▶│  MCP Client  │────▶│  MCP Server  │
│  Agent Loop  │     │  (runtime)   │     │  (external)  │
└──────────────┘     └──────────────┘     └──────────────┘
                            │                     │
                     Tool Discovery          Tool Execution
                     (list_tools)            (call_tool)
```

**Data model:**

```sql
CREATE TABLE mcp_servers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR(100) NOT NULL,
    transport VARCHAR(20) NOT NULL,  -- stdio, sse
    config JSONB NOT NULL,           -- {"command": "...", "args": [...]} or {"url": "..."}
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

**Runtime flow:**

```python
# mcp/client.py
class MCPClient:
    """Manages connections to user's MCP servers."""

    async def discover_tools(self, server_id: str) -> list[Tool]:
        """Call MCP server's list_tools, return as LangChain tools."""

    async def call_tool(self, server_id: str, tool_name: str, args: dict) -> str:
        """Proxy tool call to MCP server."""
```

**Integration points:**
- `mcp/client.py` — NEW: MCP client (stdio + SSE transport)
- `agent/nodes/agent_loop.py` — dynamically bind MCP tools alongside built-in tools
- `api/v1/mcp.py` — NEW: CRUD endpoints for user's MCP servers
- `agent/state.py` — add `mcp_tools: list` to AgentState

**Trade-off:** MCP servers run as child processes (stdio) or HTTP connections (SSE). Security concern: user-provided MCP servers could be malicious. Mitigation: sandbox stdio processes, timeout, resource limits.

### 3.3 Output Validation (Evaluate Step)

**Approach:** Thêm `evaluate` node vào LangGraph giữa `respond` và `post_process`. Dùng cheap model (Gemini Flash) để validate output quality.

**Tại sao lightweight evaluate thay vì full evaluate loop?** Personal assistant cần low latency. Full generator-evaluator cycle (như GoClaw) thêm 2-5s. Single-pass validation chỉ thêm ~500ms.

```
Trước:  route → agent_loop ⇄ tools → respond → post_process → END
Sau:    route → agent_loop ⇄ tools → respond → evaluate → post_process → END
                                                    │
                                              Nếu FAIL → agent_loop (retry 1 lần)
```

**Evaluate criteria:**

```python
EVALUATE_PROMPT = """Đánh giá response của AI assistant. Trả về JSON:
{"pass": true/false, "reason": "...", "issues": ["..."]}

Criteria:
1. Có trả lời đúng câu hỏi không?
2. Có chứa thông tin sai/hallucination rõ ràng không?
3. Có chứa nội dung không phù hợp không?
4. Response có bị cắt giữa chừng không?

User message: {user_message}
AI response: {ai_response}"""
```

**Integration points:**
- `agent/nodes/evaluate.py` — NEW: evaluate node
- `agent/graph.py` — add evaluate node + conditional edge (pass → post_process, fail → agent_loop)
- `agent/state.py` — add `retry_count: int = 0` (max 1 retry)

### Phase 2 — Summary

```
Files NEW:     memory/knowledge_graph.py, mcp/client.py, api/v1/mcp.py,
               agent/nodes/evaluate.py, agent/tools/graph_search.py
Files MODIFY:  agent/graph.py, agent/state.py, agent/nodes/agent_loop.py,
               agent/nodes/post_process.py, memory/context_builder.py
DB Migration:  knowledge_entities, knowledge_relations, mcp_servers tables
Config:        MCP_ENABLED, EVALUATE_ENABLED
```

---

## 4. Phase 3 — Multi-Agent Specialization

**Timeline:** 4-6 tuần | **Risk:** High | **Impact:** Medium
**Status:** ✅ Complete — 5 specialists (task, calendar, research, finance, memory), delegation routing verified

> **Implementation note:** All specialists use `gemini-2.0-flash` (only available model with API key). Design specified Claude Haiku/Sonnet but those require Anthropic API key. Models can be swapped when keys are added.

### 4.1 Architecture: Delegation Pattern

**Approach:** Giữ 1 Lead Agent (orchestrator) + spawn specialized sub-agents cho complex tasks. Không dùng full team/mailbox pattern (overkill cho personal assistant).

**Tại sao delegation thay vì full teams?** MY JARVIS là 1-user product. Không cần shared task board hay inter-agent messaging. Delegation đủ: Lead phân task → Specialist xử lý → trả kết quả.

```
User ──▶ Lead Agent (Gemini Flash — fast routing)
              │
              ├──▶ Task Specialist (Claude Haiku)
              │         └── task CRUD, prioritization, deadline logic
              │
              ├──▶ Calendar Specialist (Claude Haiku)
              │         └── scheduling, conflict detection, reminders
              │
              ├──▶ Research Specialist (Claude Sonnet)
              │         └── web search, summarization, deep analysis
              │
              ├──▶ Finance Specialist (Gemini Flash)
              │         └── expense tracking, budget analysis, reports
              │
              └──▶ Memory Specialist (Gemini Flash)
                        └── knowledge graph queries, memory search
```

### 4.2 Agent Registry

```python
# agent/registry.py
SPECIALISTS = {
    "task": {
        "model": "claude-haiku-4.5",
        "tools": ["create_task", "update_task", "list_tasks"],
        "system_prompt": "Bạn là chuyên gia quản lý task...",
    },
    "calendar": {
        "model": "claude-haiku-4.5",
        "tools": ["create_event", "list_events"],
        "system_prompt": "Bạn là chuyên gia lịch trình...",
    },
    "research": {
        "model": "claude-sonnet-4.6",
        "tools": ["web_search", "web_fetch", "memory_search"],
        "system_prompt": "Bạn là chuyên gia nghiên cứu...",
    },
    "finance": {
        "model": "gemini-2.0-flash",
        "tools": ["log_expense", "budget_report"],
        "system_prompt": "Bạn là chuyên gia tài chính cá nhân...",
    },
}
```

### 4.3 Modified Graph

```
route → classify_intent
            │
            ├── simple → agent_loop (Lead, all tools) → respond
            │
            └── specialized → delegate
                                 │
                                 ├── spawn Specialist(intent)
                                 │      └── specialist_loop ⇄ tools → result
                                 │
                                 └── Lead synthesizes → respond
```

**Key design decisions:**
- Lead Agent luôn là entry point — giữ conversation coherence
- Specialist chạy isolated (fresh context, chỉ nhận task description)
- Lead tổng hợp kết quả từ Specialist trước khi trả user
- Max 1 delegation per turn (tránh latency explosion)
- Fallback: nếu Specialist fail → Lead tự xử lý

### 4.4 State Extension

```python
class AgentState(MessagesState):
    # ... existing fields ...
    delegation_target: str = ""        # specialist name
    delegation_result: str = ""        # specialist response
    delegation_count: int = 0          # max 1 per turn
```

### Phase 3 — Summary

```
Files NEW:     agent/registry.py, agent/nodes/delegate.py,
               agent/nodes/specialist_loop.py
Files MODIFY:  agent/graph.py, agent/state.py, agent/nodes/router.py
DB Migration:  None (stateless delegation)
Config:        MULTI_AGENT_ENABLED
```

---

## 5. Data Model Changes (All Phases)

```sql
-- Phase 1
ALTER TABLE messages ADD COLUMN injection_score FLOAT DEFAULT 0;

-- Phase 2
CREATE TABLE knowledge_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    description TEXT,
    embedding VECTOR(1536),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, name, entity_type)
);

CREATE TABLE knowledge_relations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    source_id UUID NOT NULL REFERENCES knowledge_entities(id) ON DELETE CASCADE,
    target_id UUID NOT NULL REFERENCES knowledge_entities(id) ON DELETE CASCADE,
    relation_type VARCHAR(100) NOT NULL,
    weight FLOAT DEFAULT 1.0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE mcp_servers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR(100) NOT NULL,
    transport VARCHAR(20) NOT NULL,
    config JSONB NOT NULL,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 6. Config Changes

```python
# core/config.py — additions (actual implementation)
OPENROUTER_API_KEY: str = ""
RATE_LIMIT_ENABLED: bool = True
MULTI_AGENT_ENABLED: bool = True
```

Feature flags cho phép enable/disable rate limiting và multi-agent independently.

---

## 7. Updated Architecture (v2 — Implemented)

```
                    ┌─────────────────────────────────────────┐
                    │            Security Layer               │
                    │  Rate Limit → Injection Scan → CORS     │
                    └──────────────────┬──────────────────────┘
                                       │
WebSocket/HTTP ──▶ FastAPI ──▶ LangGraph StateGraph (v2)
                                       │
    ┌──────────────────────────────────┼──────────────────────┐
    │                                  │                      │
    ▼                                  ▼                      ▼
  route ──▶ agent_loop ⇄ tools ──▶ respond ──▶ evaluate ──▶ post_process
    │           │          │                                   │
    │           │          ├── Built-in (12)                   ├── Usage log
    │           │          ├── MCP tools (runtime)             ├── Memory extraction
    │           │          └── Knowledge graph search          └── Graph extraction
    │           │
    │           └── Prompt cache (Anthropic)
    │
    ├── Delegate to Specialist (5 domains)
    │     └── Isolated context + tool loop → result or fallback
    │
    └── LLM Router
         ├── Gemini Flash / 2.5 (Google)
         ├── Claude Haiku / Sonnet (Anthropic)
         ├── GPT-5.2 (OpenAI)
         ├── DeepSeek v3.2
         └── OpenRouter (30+ models)

Memory Layer:
    ├── Hot: Redis (5min TTL)
    ├── Cold: pgvector (cosine similarity, 3072-dim)
    └── Graph: knowledge_entities + knowledge_relations (recursive CTE, depth 3)
```

---

## 8. Migration Strategy

| Phase | Prerequisite | Rollback |
|-------|-------------|----------|
| 1 - Security | None | Disable middleware via config flag |
| 1 - Prompt Cache | Anthropic API key | Remove `cache_control` kwargs |
| 1 - OpenRouter | OpenRouter API key | Remove from MODEL_PROVIDERS |
| 2 - Knowledge Graph | Phase 1 done | Drop tables, disable extraction |
| 2 - MCP | Phase 1 done | Disable via MCP_ENABLED flag |
| 2 - Evaluate | Phase 1 done | Remove node from graph |
| 3 - Multi-Agent | Phase 2 done | Disable via MULTI_AGENT_ENABLED |

Mỗi feature có flag riêng → có thể deploy incrementally, rollback independently.

---

## 9. Trade-offs & Decisions

### ADR-006: PostgreSQL Knowledge Graph vs Neo4j

**Decision:** PostgreSQL recursive CTE
**Context:** GoClaw dùng PG cho knowledge graph. MY JARVIS đã có PG + pgvector.
**Pros:** Không thêm infra, transactional consistency, vector search cùng DB
**Cons:** Graph queries chậm hơn Neo4j ở depth > 5
**Mitigation:** Cap depth = 3, index on foreign keys

### ADR-007: MCP Client-only vs Client+Server

**Decision:** Client-only (MY JARVIS connects TO MCP servers)
**Context:** GoClaw hỗ trợ cả client và server. MY JARVIS là consumer product.
**Pros:** Simpler, user connects external tools
**Cons:** Không expose MY JARVIS tools cho external agents
**Mitigation:** Thêm server mode sau nếu cần

### ADR-008: Delegation vs Full Agent Teams

**Decision:** Simple delegation (Lead → Specialist → Lead)
**Context:** GoClaw có full teams (task board, mailbox, handoff). MY JARVIS là 1-user.
**Pros:** Low latency, simple state, no inter-agent coordination overhead
**Cons:** Không hỗ trợ parallel multi-agent execution
**Mitigation:** Upgrade to parallel delegation nếu cần

### ADR-009: Evaluate Step vs Full Evaluate Loop

**Decision:** Single-pass evaluate + 1 retry
**Context:** GoClaw có generator-evaluator loop (max 5 rounds). Personal assistant cần speed.
**Pros:** +500ms thay vì +5s, catches obvious errors
**Cons:** Không iterate đến perfect output
**Mitigation:** Tăng max_retries cho complex tier nếu cần

---

## 10. Effort Estimation

| Task | Files | Est. LOC | Actual LOC | Est. Days | Actual |
|------|-------|----------|------------|-----------|--------|
| **Phase 1** | | | | | |
| Rate limiting | 2 new + 2 modify | ~80 | ~80 | 1 | ✅ |
| Injection detection | 1 new + 1 modify | ~40 | ~40 | 0.5 | ✅ |
| Prompt caching | 1 modify | ~20 | ~20 | 0.5 | ✅ |
| OpenRouter provider | 2 modify | ~30 | ~30 | 0.5 | ✅ |
| **Phase 1 total** | | **~170** | **~170** | **2.5** | **✅** |
| **Phase 2** | | | | | |
| Knowledge Graph | 3 new + 3 modify + migration | ~250 | ~250 | 5 | ✅ |
| MCP Protocol | 2 new + 2 modify + migration | ~200 | ~180 | 5 | ✅ |
| Output Validation | 1 new + 2 modify | ~60 | ~60 | 1 | ✅ |
| **Phase 2 total** | | **~510** | **~490** | **11** | **✅** |
| **Phase 3** | | | | | |
| Agent Registry | 1 new | ~40 | ~55 | 0.5 | ✅ |
| Delegation node | 1 new + 1 modify | ~150 | ~65 | 3 | ✅ |
| Graph rewiring | 2 modify | ~30 | ~65 | 1 | ✅ |
| **Phase 3 total** | | **~220** | **~185** | **4.5** | **✅** |
| **Bug fixes** | | | **~30** | | ✅ |
| **Grand total** | | **~900** | **~875** | **18 days** | **2 days** |

---

## 11. Implementation Notes (Post-completion)

### Bugs Fixed During Implementation

| Bug | Root Cause | Fix |
|-----|-----------|-----|
| Embedding dimension mismatch | `gemini-embedding-001` returns 3072-dim, DB had `Vector(1536)` | ALTER columns to `Vector(3072)` |
| JSON leaking into chat stream | `astream_events` captured all LLM calls (evaluate, post_process) | Filter streaming to `agent_loop` + `delegate` nodes only |
| `memory_save` invalid user_id | LLM didn't know user's UUID | Inject `user_id` into system prompt |
| Gemini 2.5 Flash model name | Used `-preview-04-17` suffix (deprecated) | Removed suffix |
| Router selects unavailable models | No API key check before selection | Added `_is_available()` gate |
| `chunk.content` is list | Gemini 2.5 Flash returns list instead of string | Handle list type in `ws.py` |

### Deviations from Design

| Design | Actual | Reason |
|--------|--------|--------|
| `specialist_loop.py` separate file | Tool loop inline in `delegate.py` | Simpler, ~65 LOC total |
| Claude Haiku/Sonnet for specialists | All use `gemini-2.0-flash` | Only Google API key available |
| `MCP_ENABLED`, `EVALUATE_ENABLED` flags | Not added (always on) | Simpler, no need to toggle individually |
| `Vector(1536)` for embeddings | `Vector(3072)` | Gemini embedding model outputs 3072 dims |

### Final Architecture (Verified)

```
route → detect specialist + classify intent
          │
          ├── no specialist → agent_loop ⇄ tools (12) → respond
          │
          └── specialist → delegate (isolated sub-agent, max 5 tool steps)
                              │
                              ├── result → respond
                              └── empty → fallback to agent_loop
                                                  │
                                        respond → evaluate → post_process → END
                                                     │         ├── memory extraction
                                                     │         └── KG extraction
                                                fail + retry ≤ 1 → agent_loop
```

### Services Running

| Service | Container Port | Host Port | Status |
|---------|---------------|-----------|--------|
| PostgreSQL + pgvector | 5432 | 5435 | ✅ |
| Redis | 6379 | 6381 | ✅ |
| MinIO | 9000/9001 | 9000/9001 | ✅ |
| Backend (FastAPI) | 8000 | 8002 | ✅ |
| Frontend (Next.js) | 3000 | 3002 | ✅ |
| Worker (ARQ cron) | — | — | ✅ |
