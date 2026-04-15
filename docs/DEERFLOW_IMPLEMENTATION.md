# DeerFlow Implementation — my-jarvis

> Central patterns reference: `~/.kiro/docs/DEERFLOW_PATTERNS.md`
> Backend path: `backend/`

## 1. Business Spec

### Nghiệp vụ cần build

**Memory Consolidation (weekly)**: Batch job hàng tuần compress memories cũ, extract important facts, xóa outdated/contradictory entries. Đã có `memory/consolidation.py` — cần wire vào ARQ worker.

**Deep Research Node**: Agent có thể chạy multi-step research (search → verify → cross-check → cite) với confidence scoring thay vì 1 lần web search.

**Adaptive Execution**: Trong plan-and-execute, user có thể feedback mid-plan → agent replan thay vì chạy hết kế hoạch cũ.

**Sandbox Execution**: User tạo automation script → agent chạy trong Docker sandbox an toàn.

### User stories

- *"Nghiên cứu cho tôi về market size AI coding tools 2025"* → Deep Research chạy 3-5 web searches, cross-check sources, trả về báo cáo với confidence scores.
- *"Giúp tôi schedule meeting"*: Agent lên plan → user nói *"bỏ bước send email đi"* → agent replan on-the-fly.
- *"Chạy script backup database hàng ngày cho tôi"* → Sandbox execute, trả về stdout/stderr.
- Hàng tuần: ARQ job consolidate memories → user nhận thấy jarvis hiểu mình tốt hơn theo thời gian.

### Lợi ích

- Research chất lượng cao hơn vs. single web search
- Plan linh hoạt hơn vs. rigid execution
- Memory sạch hơn, relevant hơn theo thời gian

---

## 2. Current State

### Đang có

| File | Trạng thái | Ghi chú |
|------|-----------|---------|
| `agent/graph.py` | Hoạt động | route → agent_loop → tools → delegate → respond → evaluate → post_process |
| `agent/state.py` | Hoạt động | AgentState với v2+v3 fields đầy đủ |
| `agent/nodes/plan_execute.py` | Hoạt động | planner → executor → replan → synthesize |
| `memory/service.py` | Hoạt động | Hot memory (Redis 5min) + Cold memory (pgvector) |
| `memory/consolidation.py` | **CÓ nhưng chưa wire** | `consolidate_fact()` function hoàn chỉnh |
| `memory/extraction.py` | ? | Cần kiểm tra |
| `db/models/memory.py` | Hoạt động | `Memory` model: id, user_id, content, embedding, importance, last_accessed |
| `services/proactive.py` | Hoạt động | ARQ worker: morning briefing, deadline reminders |
| `mcp/` | Hoạt động | MCP client integration |

### Missing

- `memory/consolidation.py` chưa được schedule trong ARQ worker
- Không có `agent/nodes/research.py` — web search là tool đơn giản
- Plan-and-execute chưa có mid-plan user interrupt handling
- Không có sandbox execution tool
- `Memory.decay_factor` field chưa có trong schema (chỉ có `importance`)

---

## 3. Technical Design

### Patterns áp dụng

| Pattern | Áp dụng thế nào |
|---------|----------------|
| P1: Multi-Agent Hierarchy | Research: Director → [WebSearcher, FactVerifier, Synthesizer] |
| P2: Middleware Pipeline | Existing pipeline, thêm research node |
| P3: Sandbox Execution | Docker-based script execution tool |
| P4: Long-term Memory | Đã có. Thêm decay_factor + wire consolidation |
| P5: Skills System | Đã có cơ sở từ MCP skills — extend |
| P6: MCP Integration | Đã có. Wire thêm tools qua MCP |
| P10: Lazy Loading | get_pipeline() singleton đã có |

### Deep Research flow

```
agent gọi research_tool(query)
  │
  └─ ResearchGraph (internal)
       ├─ [1] plan_searches   → LLM tạo 3-5 search queries
       ├─ [2] execute_searches → parallel web searches
       ├─ [3] verify_facts    → cross-check sources, detect conflicts
       ├─ [4] score_confidence → per-fact confidence 0-1
       └─ [5] synthesize      → structured report với citations + confidence
```

### Adaptive Execution flow

```
plan → executor → [mid-plan check for user feedback] → continue OR replan
         │
         ├─ [HITL enabled] → pause + ask user
         │     └─ user approves → continue
         │     └─ user modifies → replan_node
         └─ [HITL disabled] → continue as-is
```

---

## 4. Implementation Plan

### Step 1: Wire `memory/consolidation.py` vào ARQ worker

Đây là quick win — code đã có, chỉ cần schedule.

**File:** `services/proactive.py` — thêm consolidation job:

```python
# services/proactive.py — thêm vào cuối file

from memory.consolidation import consolidate_fact
from db.models.memory import Memory
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)

async def weekly_memory_consolidation(ctx):
    """ARQ job: chạy hàng tuần, consolidate memories cho tất cả users.

    Đây là batch job nhẹ — chỉ process memories chưa consolidate.
    memory/consolidation.py đã có logic đầy đủ.
    """
    from db.session import async_session
    from db.models.user import User

    async with async_session() as db:
        # Get all users
        users = (await db.execute(select(User))).scalars().all()

        for user in users:
            try:
                # Get unprocessed memories (last 7 days)
                from datetime import datetime, timedelta
                cutoff = datetime.utcnow() - timedelta(days=7)
                memories = (await db.execute(
                    select(Memory)
                    .where(
                        Memory.user_id == user.id,
                        Memory.created_at >= cutoff,
                    )
                    .order_by(Memory.created_at.desc())
                    .limit(50)  # process max 50 per user per run
                )).scalars().all()

                consolidated = 0
                for memory in memories:
                    action = await consolidate_fact(str(user.id), memory.content, db)
                    if action != "SKIP":
                        consolidated += 1

                if consolidated > 0:
                    logger.info(f"Consolidated {consolidated} memories for user {user.id}")

            except Exception as e:
                logger.error(f"Consolidation failed for user {user.id}: {e}")


# Thêm vào ARQ cron schedule
# Tìm class WorkerSettings hoặc CRON_JOBS list trong services/proactive.py
# Thêm:
# cron(weekly_memory_consolidation, weekday=0, hour=3, minute=0)  # Monday 3AM UTC
```

**Tìm và cập nhật cron schedule config:**

```python
# Trong services/proactive.py, tìm class WorkerSettings hoặc functions list
# Thêm weekly_memory_consolidation vào cron_jobs:

class WorkerSettings:
    functions = [morning_briefing, deadline_reminder, weekly_memory_consolidation]
    cron_jobs = [
        # existing crons...
        cron(weekly_memory_consolidation, weekday=0, hour=3, minute=0),
    ]
```

### Step 2: Tạo `agent/nodes/research.py`

**File:** `agent/nodes/research.py`

```python
"""Deep Research node — multi-step research với confidence scoring."""
import asyncio
import json
import logging
from datetime import datetime
from agent.state import AgentState
from llm.gateway import get_llm
from agent.tools.web_search import web_search  # existing tool

logger = logging.getLogger(__name__)

PLAN_SEARCHES_PROMPT = """Tạo kế hoạch research cho câu hỏi sau.
Câu hỏi: {query}
Tạo tối đa 4 search queries cụ thể để tìm thông tin đầy đủ.
Trả về JSON: {{"queries": ["query1", "query2", ...]}}"""

VERIFY_FACTS_PROMPT = """Cross-check các thông tin từ nhiều sources.
Sources:
{sources}
Xác định:
1. Thông tin nào nhất quán giữa các sources (confidence cao)
2. Thông tin nào mâu thuẫn (cần flag)
3. Thông tin nào chỉ có 1 source (confidence thấp)
Trả về JSON: {{"facts": [{{"content": "...", "confidence": 0.0-1.0, "sources": [...], "conflicted": false}}]}}"""

SYNTHESIZE_RESEARCH_PROMPT = """Tổng hợp research report từ các facts đã verify.
Query: {query}
Facts: {facts}
Viết báo cáo có cấu trúc với:
- Executive summary
- Key findings (với confidence scores)
- Sources (citations)
- Caveats (nếu có conflicting info)"""


async def research_node(state: AgentState) -> dict:
    """Multi-step research với confidence scoring.

    Được gọi khi intent == 'deep_research' hoặc agent quyết định cần research sâu.
    """
    # Extract research query từ last message
    last_msg = ""
    for msg in reversed(state["messages"]):
        if hasattr(msg, "type") and msg.type == "human":
            last_msg = msg.content
            break

    if not last_msg:
        return {}

    llm = get_llm(complexity="medium")

    # Step 1: Plan searches
    plan_resp = await llm.ainvoke(PLAN_SEARCHES_PROMPT.format(query=last_msg))
    try:
        plan = json.loads(plan_resp.content)
        queries = plan.get("queries", [last_msg])[:4]
    except Exception:
        queries = [last_msg]

    # Step 2: Execute searches in parallel
    search_tasks = [web_search(q, user_id=state["user_id"]) for q in queries]
    search_results = await asyncio.gather(*search_tasks, return_exceptions=True)

    # Compile sources
    sources = []
    for i, result in enumerate(search_results):
        if isinstance(result, Exception):
            logger.warning(f"Search {i} failed: {result}")
            continue
        sources.append({"query": queries[i], "result": str(result)[:2000]})

    if not sources:
        return {"final_response": "Không tìm được thông tin để research."}

    # Step 3: Verify facts
    verify_resp = await llm.ainvoke(VERIFY_FACTS_PROMPT.format(
        sources=json.dumps(sources, ensure_ascii=False)
    ))
    try:
        verified = json.loads(verify_resp.content)
        facts = verified.get("facts", [])
    except Exception:
        facts = [{"content": s["result"], "confidence": 0.5, "sources": [s["query"]]} for s in sources]

    # Step 4: Synthesize
    synth_resp = await llm.ainvoke(SYNTHESIZE_RESEARCH_PROMPT.format(
        query=last_msg,
        facts=json.dumps(facts, ensure_ascii=False),
    ))

    # Save research to memory
    from memory.service import save_cold_memory
    from db.session import async_session
    async with async_session() as db:
        await save_cold_memory(
            user_id=state["user_id"],
            content=f"Research: {last_msg}\n\nSummary: {synth_resp.content[:500]}",
            importance=0.7,
            db=db,
        )

    return {
        "final_response": synth_resp.content,
        "step_results": [f"Research completed: {len(facts)} facts found"],
    }
```

### Step 3: Cập nhật `agent/state.py`

```python
# agent/state.py — thêm fields cho research + adaptive execution

class AgentState(MessagesState):
    # ... existing fields (giữ nguyên tất cả) ...

    # NEW: Research fields
    confidence_scores: dict = {}          # {"fact_1": 0.9, "fact_2": 0.6}
    research_queries: list[str] = []      # queries được thực hiện

    # NEW: Adaptive execution
    plan_interrupted: bool = False        # True khi user feedback mid-plan
    pending_user_feedback: str = ""       # feedback từ user trong lúc execute

    # NEW: Consolidation trigger
    consolidation_trigger: bool = False   # True khi memories cần consolidate
```

### Step 4: Tạo Sandbox Execution tool

**File:** `agent/tools/sandbox.py`

```python
"""Sandbox execution tool — chạy user scripts trong Docker."""
import asyncio
import logging
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

SAFE_IMAGES = {"python:3.12-slim", "node:20-slim", "bash:5"}

@tool
async def sandbox_execute(
    code: str,
    runtime: str = "python",
    user_id: str = "",
) -> str:
    """Chạy code/script trong Docker sandbox an toàn.

    Args:
        code: Code để chạy
        runtime: 'python' | 'node' | 'bash'
        user_id: User ID (inject từ state)

    Returns:
        stdout output hoặc error message
    """
    from core.config import settings
    if not settings.ENABLE_SANDBOX:
        return "Sandbox execution chưa được bật. Set ENABLE_SANDBOX=true."

    # Runtime → image mapping
    images = {
        "python": "python:3.12-slim",
        "node": "node:20-slim",
        "bash": "bash:5",
    }
    image = images.get(runtime, "python:3.12-slim")
    if image not in SAFE_IMAGES:
        return f"Runtime '{runtime}' không được hỗ trợ."

    commands = {
        "python": ["python", "-c", code],
        "node": ["node", "-e", code],
        "bash": ["bash", "-c", code],
    }
    cmd = commands.get(runtime, ["python", "-c", code])

    try:
        import docker
        client = docker.from_env()
        container = client.containers.run(
            image=image,
            command=cmd,
            mem_limit="128m",
            cpu_quota=50000,    # 50% CPU
            network_mode="none",
            read_only=True,
            detach=True,
        )
        result = container.wait(timeout=30)
        stdout = container.logs(stdout=True, stderr=False).decode()[:5000]
        stderr = container.logs(stdout=False, stderr=True).decode()[:1000]
        container.remove(force=True)

        if result["StatusCode"] != 0:
            return f"Error (exit {result['StatusCode']}):\n{stderr}"
        return stdout or "(no output)"

    except Exception as e:
        logger.error(f"Sandbox error for user {user_id}: {e}")
        return f"Sandbox error: {str(e)[:200]}"
```

### Step 5: Wire research node vào `agent/graph.py`

```python
# agent/graph.py — thêm research node
from agent.nodes.research import research_node
from core.config import settings

# Trong build_graph() function:
if settings.ENABLE_DEEP_RESEARCH:
    graph.add_node("research", research_node)
    # Route từ router_node: nếu intent == "deep_research" → research
    # Thêm vào conditional_edges của router:
    # "deep_research": "research"
    graph.add_edge("research", "respond")
```

### Step 6: Thêm `sandbox_execute` vào tools list

```python
# agent/tools/__init__.py
from agent.tools.sandbox import sandbox_execute

# Thêm vào all_tools list:
all_tools = [
    # ... existing tools ...
    sandbox_execute,
]
```

### Step 7: Thêm env vars

```bash
# .env
ENABLE_DEEP_RESEARCH=false   # enable sau khi test
ENABLE_SANDBOX=false         # enable sau khi verify Docker socket
MEMORY_CONSOLIDATION_ENABLED=true  # đã có flag, wire xong bật luôn
```

### Thứ tự implement

1. **Quick win**: Wire `memory/consolidation.py` vào ARQ worker (Step 1) → test bằng cách trigger job thủ công
2. Thêm `confidence_scores` vào `agent/state.py` (backward compatible — default `{}`)
3. Tạo `agent/nodes/research.py` → test standalone với 1 query
4. Thêm research node vào `agent/graph.py` với `ENABLE_DEEP_RESEARCH=false` → verify pipeline không break
5. Enable `ENABLE_DEEP_RESEARCH=true` trong dev → test với query research
6. Tạo `agent/tools/sandbox.py` → test với simple Python script
7. Verify Docker socket accessible từ backend container (`docker ps` trong container)
8. Enable `ENABLE_SANDBOX=true` → test với user script

### Không cần sửa

- `memory/consolidation.py` — code đã đủ, chỉ wire vào ARQ
- `memory/service.py` — hot/cold memory đã hoạt động
- `db/models/memory.py` — `importance` field đã có, đủ cho decay (không cần thêm `decay_factor` riêng)
- `mcp/` — MCP integration đã hoạt động, không cần thay đổi
