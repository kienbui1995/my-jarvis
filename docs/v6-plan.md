# MY JARVIS V6 — Autonomy & Ecosystem Layer

> **Status:** 📋 Plan
> **Date:** 2026-03-16
> **Goal:** Biến JARVIS từ "assistant trả lời" → "agent tự hành động" + mở ecosystem cho developers

---

## 1. Tại sao cần V6

V5 hoàn thành Production & Growth — billing, analytics, security. Nhưng:

| Dimension | V5 Score | Gap |
|---|---|---|
| Production | 8/10 | Deployed, billing, monitoring |
| AI Quality | 7/10 | Hybrid RAG, workflow templates |
| Autonomy | 4/10 | Agent chỉ làm 1 task/lần, không tự chủ động liên tục |
| Ecosystem | 0/10 | Không có API cho devs, không có plugin marketplace |
| Retention | 5/10 | Users thử rồi quên — thiếu daily habits |

**Đối thủ đang ở đâu (Q3 2026):**
- Lindy: autonomous agents chạy background weeks, 50+ integrations
- Manus: deploy code, browse web autonomously, multi-hour tasks
- ChatGPT: GPTs marketplace, 1M+ custom agents, memory across sessions

**V6 gap:** JARVIS chưa thể tự chạy tasks phức tạp không cần user. Chưa có ecosystem.

---

## 2. V6 Modules

### Phase A: Deep Autonomy (P0)

| # | Module | Effort | Description |
|---|---|---|---|
| M33 | Long-running Agent Tasks | 3w | Background agent tasks (research, monitoring), progress tracking, auto-resume |
| M34 | Scheduled Agents | 2w | User-defined recurring agent tasks ("mỗi sáng tóm tắt email", "mỗi tối review chi tiêu") |
| M35 | Multi-agent Collaboration | 2w | Parallel sub-agents cho complex tasks, result aggregation |
| M36 | Agent Memory v2 | 2w | Cross-session context, user profile evolution, long-term goal tracking |

### Phase B: Developer Ecosystem (P1)

| # | Module | Effort | Description |
|---|---|---|---|
| M37 | Public API | 2w | REST API cho developers: chat, tools, memory, triggers. API keys, rate limits, docs |
| M38 | Custom Tools SDK | 2w | User/dev tự tạo tool (Python function → agent tool), sandbox execution |
| M39 | Plugin Marketplace | 3w | Publish/install tools, ratings, revenue share |
| M40 | Webhook Actions | 1w | Trigger → call external webhook (IFTTT-style) |

### Phase C: Retention & Engagement (P2)

| # | Module | Effort | Description |
|---|---|---|---|
| M41 | Daily Habits | 1w | Habit tracker, streak counter, daily check-in prompts |
| M42 | Shared Spaces | 2w | Multi-user shared tasks/calendar/notes (family, team) |
| M43 | Achievement System | 1w | Gamification: badges, milestones, usage rewards |
| M44 | Export & Portability | 1w | Export all data (JSON/CSV), import from other assistants |

---

## 3. Module Specs

### M33: Long-running Agent Tasks

**Problem:** Agent xử lý 1 request → trả lời → xong. Không thể "nghiên cứu topic này trong 30 phút rồi gửi kết quả".

**Solution:**
- `backend/services/agent_tasks.py` — queue long-running tasks via ARQ
- Agent chạy trong background, gửi progress updates via notifications
- User xem status, cancel, resume qua API + UI
- Max duration: 30 phút (configurable)

**API:**
```
POST /api/v1/agent-tasks      — {prompt, max_duration_minutes}
GET  /api/v1/agent-tasks      — list running/completed tasks
GET  /api/v1/agent-tasks/:id  — status + partial results
DELETE /api/v1/agent-tasks/:id — cancel
```

**Use cases:**
- "Nghiên cứu về thị trường fintech VN, gửi tôi báo cáo"
- "Monitor trang web này, báo khi có thay đổi"
- "Phân tích 50 email gần nhất, tìm action items"

---

### M34: Scheduled Agents

**Problem:** Proactive triggers (M14) chỉ có built-in types. User không tạo được custom recurring tasks.

**Solution:**
- Extend trigger engine: `trigger_type="scheduled_agent"` với `config.prompt`
- User tạo: "Mỗi sáng 8h, tóm tắt email và tạo task list"
- ARQ cron emit event → trigger engine → invoke agent → send result

**Config example:**
```json
{
  "trigger_type": "scheduled_agent",
  "config": {
    "prompt": "Tóm tắt email mới và tạo task cho email cần reply",
    "schedule": "0 8 * * *",
    "channels": ["zalo", "web"]
  }
}
```

---

### M35: Multi-agent Collaboration

**Problem:** Agent loop chạy sequential — 1 tool 1 lần. Complex tasks cần parallel.

**Solution:**
- Planner phân task thành independent sub-tasks
- Dispatch sub-agents via `asyncio.gather()` cho parallel execution
- Aggregator node tổng hợp kết quả
- Graph: `planner → [sub_agent_1, sub_agent_2, ...] → aggregator → respond`

---

### M36: Agent Memory v2

**Problem:** Memory chỉ lưu facts. Không track goals, projects, relationships theo thời gian.

**Solution:**
- **User Profile**: auto-maintained JSON profile (job, family, habits, preferences)
- **Goal Tracking**: user đặt goals, agent track progress, weekly review
- **Relationship Graph**: knowledge graph extended — people, projects, timelines
- Cross-session: agent tự nhớ "hôm qua bạn nói sẽ..."

---

### M37: Public API

**Solution:**
- API Gateway: `/api/public/v1/` prefix, separate from internal API
- Auth: API keys (not JWT), rate limited per key
- Endpoints: `/chat`, `/tools/:name/invoke`, `/memory/search`, `/triggers`
- OpenAPI docs at `/api/public/v1/docs`
- Usage tracking per API key for billing

---

### M38: Custom Tools SDK

**Solution:**
- User uploads Python function → sandboxed execution in Docker
- Tool metadata: name, description, args schema (auto-extracted from type hints)
- Storage: MinIO for tool code, DB for metadata
- Execution: isolated container per invocation, 30s timeout

```python
# User writes:
def stock_price(symbol: str) -> str:
    """Xem giá cổ phiếu. Args: symbol (VN stock code)."""
    import httpx
    r = httpx.get(f"https://api.example.com/stock/{symbol}")
    return f"Giá {symbol}: {r.json()['price']}đ"
```

---

### M39: Plugin Marketplace

**Solution:**
- Publish: upload tool + metadata + icon → review → list
- Install: 1-click add to user's tool set
- Categories: finance, productivity, entertainment, data
- Revenue: 70/30 split (developer/platform)
- Rating + review system

---

### M40: Webhook Actions

**Solution:**
- New trigger action type: `action="webhook"` with `url`, `method`, `headers`, `body_template`
- User configures: "Khi task được tạo → POST webhook tới Slack"
- Retry: 3 attempts with exponential backoff
- Logging: all webhook calls logged in evidence

---

### M41-M44: Retention modules

Simpler features focused on daily engagement:
- **M41 Daily Habits**: habit model, streak tracking, morning/evening check-in
- **M42 Shared Spaces**: invitation system, shared task lists, multi-user conversations
- **M43 Achievements**: badge system (first task, 7-day streak, 100 messages, etc.)
- **M44 Export**: full data export (JSON), conversation history download

---

## 4. Roadmap

```
2026 Q3 (Jul-Sep)
┌─────────────────────────────────┐
│ Phase A: Deep Autonomy          │
│ M33 Long-running Tasks (3w)    │
│ M34 Scheduled Agents (2w)      │
│ M35 Multi-agent (2w)           │
│ M36 Memory v2 (2w)             │
│ ─── MILESTONE: Autonomous GA ── │
└─────────────────────────────────┘

2026 Q4 (Oct-Dec)
┌─────────────────────────────────┐
│ Phase B: Developer Ecosystem    │
│ M37 Public API (2w)            │
│ M38 Custom Tools SDK (2w)      │
│ M39 Plugin Marketplace (3w)    │
│ M40 Webhook Actions (1w)       │
│ ─── MILESTONE: API Launch ──── │
└─────────────────────────────────┘

2027 Q1 (Jan-Mar)
┌─────────────────────────────────┐
│ Phase C: Retention              │
│ M41-M44 (4w)                   │
│ ─── MILESTONE: Ecosystem Live ─ │
└─────────────────────────────────┘
```

## 5. Success Metrics

| Metric | V5 Baseline | V6 Target |
|---|---|---|
| DAU | 500 | 5,000 |
| Paying users | 50 | 500 |
| MRR | $500 | $5,000 |
| Background tasks/day | 0 | 1,000 |
| API developer accounts | 0 | 100 |
| Published plugins | 0 | 20 |
| Avg session duration | 3min | 10min |
| D30 retention | ~20% | 45% |

## 6. Dependencies

```
M33 (Long-running) ──→ M34 (Scheduled) ──→ M35 (Multi-agent)
                                               │
M36 (Memory v2) ── independent                 │
                                               │
M37 (Public API) ── independent                │
M38 (Custom Tools) ──→ M39 (Marketplace)       │
M40 (Webhook) ── depends on M14 (triggers)     │
                                               │
M41-M44 ── independent                         │
```

Critical path: **M33 → M34 → M35 (autonomous agents) + M37 → M38 → M39 (ecosystem)**
