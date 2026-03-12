# MY JARVIS v3 — Intelligence Layer Architecture

> **Status:** 📋 Draft
> **Author:** Architect Agent
> **Date:** 2026-03-12
> **Scope:** 5-module intelligence upgrade — LLM Router, Conversation Memory, Plan-and-Execute, Memory Consolidation, User Preference Learning
> **Prerequisite:** v2 complete (Security, KG, MCP, Evaluate, Multi-Agent)

---

## 1. Executive Summary

MY JARVIS v2 có kiến trúc vững (LangGraph pipeline, multi-model, multi-agent, KG) nhưng "trí thông minh" thực tế còn hạn chế. Document này thiết kế 5 module nâng cấp Intelligence Layer, biến JARVIS từ "framework tốt" thành "assistant thật sự thông minh".

### Problem Statement

| # | Vấn đề | Hệ quả |
|---|--------|--------|
| 1 | Router keyword-based | Misroute ~40% requests, model selection sai |
| 2 | Không quản lý conversation history | Context overflow ở turn 20+, mất thông tin |
| 3 | Không có planning | Không xử lý được yêu cầu multi-step |
| 4 | Memory không deduplicate | Dữ liệu trùng lặp, mâu thuẫn tích lũy |
| 5 | Không học từ user | Mọi user nhận cùng trải nghiệm |

### Solution: 5 Intelligence Modules

```
┌─────────────────────────────────────────────────────────────────┐
│                    INTELLIGENCE LAYER v3                         │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ M1: Smart    │  │ M2: Convo    │  │ M3: Plan-and-Execute │  │
│  │    Router    │  │    Memory    │  │                      │  │
│  │              │  │              │  │ Planner → Executor   │  │
│  │ LLM classify │  │ Window +     │  │ → Replan loop        │  │
│  │ + model pick │  │ Summarize    │  │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                 │
│  ┌──────────────────────┐  ┌──────────────────────────────┐    │
│  │ M4: Memory           │  │ M5: User Preference          │    │
│  │     Consolidation    │  │     Learning                 │    │
│  │                      │  │                              │    │
│  │ Dedup + merge +      │  │ Track style + adapt prompt   │    │
│  │ contradiction resolve│  │ + procedural memory          │    │
│  └──────────────────────┘  └──────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Current Architecture (v2 Baseline)

```
User Message
    │
    ▼
route (keyword classify + model select + memory load)
    │
    ├── delegate (specialist sub-agent) ──┐
    │                                      │
    └── agent_loop ⇄ tools (12) ──────────┤
                                           │
                                    respond → evaluate → post_process → END
                                                           │
                                                    memory extraction
                                                    KG extraction
```

### Gaps Analysis (chi tiết)

**Router (`agent/nodes/router.py`):**
```python
# Hiện tại: keyword matching
COMPLEX_KW = {"phân tích", "nghiên cứu", "viết bài"...}
if any(w in lower for w in COMPLEX_KW):
    return "complex", "research"
```
- Không phân biệt được "phân tích cảm xúc" (complex) vs "phân tích xem mấy giờ rồi" (simple)
- Specialist routing cũng keyword-based → false positives cao

**Conversation Memory:**
- `agent_loop_node` đổ toàn bộ `state["messages"]` vào LLM
- Không sliding window, không summarize, không token counting
- Turn 30+ → context overflow hoặc truncation mất thông tin quan trọng

**Planning:**
- Agent chỉ có ReAct loop (call tool → observe → call tool)
- "Lên kế hoạch đi Đà Nẵng tuần sau" → gọi 1 tool rồi trả lời, không decompose

**Memory Extraction (`memory/extraction.py`):**
- Extract facts mỗi turn, không check existing memories
- "Tôi thích cà phê" nói 10 lần → 10 bản ghi giống nhau
- Không resolve: "Tôi thích trà" sau "Tôi thích cà phê"

**User Preferences:**
- System prompt cố định cho mọi user
- Không adapt tone, verbosity, response style

---

## 3. Module 1: Smart LLM Router

### 3.1 Design

Thay keyword matching bằng LLM-based classification sử dụng cheap model (Gemini Flash) với structured output.

```
User Message
    │
    ▼
┌──────────────────────────────────────┐
│         SMART ROUTER                  │
│                                       │
│  1. LLM Classifier (Gemini Flash)     │
│     → intent, complexity, specialist  │
│     → structured JSON output          │
│                                       │
│  2. Model Selector                    │
│     → pick model based on complexity  │
│     → check budget + availability     │
│                                       │
│  3. Context Loader                    │
│     → hot memory + cold memory        │
│     → user preferences                │
│                                       │
│  Latency budget: <200ms               │
│  Cost: ~$0.00001/request              │
└──────────────────────────────────────┘
```

### 3.2 Classification Schema

```python
class RouterDecision(BaseModel):
    """Structured output from LLM classifier."""
    intent: Literal[
        "general_chat",    # Chào hỏi, tán gẫu
        "task_mgmt",       # CRUD tasks
        "calendar_mgmt",   # CRUD calendar
        "research",        # Tìm hiểu, phân tích sâu
        "finance",         # Chi tiêu, ngân sách
        "memory_query",    # Hỏi về thông tin đã lưu
        "planning",        # Yêu cầu multi-step (NEW)
        "creative",        # Viết bài, sáng tạo
    ] = "general_chat"

    complexity: Literal["simple", "medium", "complex"] = "simple"

    specialist: Literal["", "task", "calendar", "research", "finance", "memory"] = ""

    needs_planning: bool = False  # True nếu cần plan-and-execute

    reasoning: str = ""  # 1 câu giải thích (for debugging)
```

### 3.3 Classification Prompt

```python
ROUTER_SYSTEM = """Bạn là router phân loại intent cho AI assistant.
Phân tích message và trả về JSON với các field:
- intent: loại yêu cầu
- complexity: simple (1 bước, trả lời ngay) | medium (cần tool) | complex (cần suy luận sâu)
- specialist: domain chuyên biệt (nếu có)
- needs_planning: true nếu yêu cầu cần nhiều bước phối hợp
- reasoning: 1 câu giải thích ngắn

Ví dụ:
- "Mấy giờ rồi?" → simple, general_chat
- "Tạo task review code" → medium, task_mgmt, specialist=task
- "Lên kế hoạch đi Đà Nẵng tuần sau" → complex, planning, needs_planning=true
- "Phân tích xu hướng chi tiêu 3 tháng qua" → complex, finance, specialist=finance"""
```

### 3.4 Caching Strategy

Để giữ latency <200ms, cache classification results:

```python
# Redis cache: router:{hash(message_prefix)} → RouterDecision
# TTL: 1 hour (same-ish messages get same routing)
# Key: first 100 chars of message (normalized lowercase, stripped)
```

Fallback: nếu LLM classifier timeout (>500ms) → fall back to keyword matching (v2 logic).

### 3.5 ADR-010: LLM Classifier vs Embedding Classifier vs Fine-tuned Model

| Approach | Accuracy | Latency | Cost | Maintenance |
|----------|----------|---------|------|-------------|
| Keyword matching (v2) | ~60% | <1ms | $0 | Thêm keyword thủ công |
| **LLM classifier (chosen)** | **~90%** | **~150ms** | **~$0.00001** | **Update prompt** |
| Embedding + kNN | ~80% | ~50ms | ~$0.00001 | Cần labeled dataset |
| Fine-tuned small model | ~95% | ~20ms | $0 (self-host) | Cần training pipeline |

**Decision:** LLM classifier. Lý do: accuracy cao nhất trong nhóm zero-maintenance, không cần labeled data, dễ thêm intent mới (chỉ update prompt). Khi scale lên 10K+ users/day → migrate sang fine-tuned model.

### 3.6 Integration

```python
# agent/nodes/router.py — thay thế _classify()
async def _classify_llm(text: str) -> RouterDecision:
    """LLM-based intent classification with cache + fallback."""
    cache_key = f"router:{hashlib.md5(text[:100].lower().encode()).hexdigest()}"
    cached = await redis.get(cache_key)
    if cached:
        return RouterDecision.model_validate_json(cached)

    try:
        llm = get_llm("gemini-2.0-flash").with_structured_output(RouterDecision)
        result = await asyncio.wait_for(
            llm.ainvoke([SystemMessage(content=ROUTER_SYSTEM), HumanMessage(content=text[:500])]),
            timeout=0.5,
        )
        await redis.setex(cache_key, 3600, result.model_dump_json())
        return result
    except (asyncio.TimeoutError, Exception):
        # Fallback to keyword matching
        complexity, intent = _classify_keyword(text)
        return RouterDecision(intent=intent, complexity=complexity)
```

**Files thay đổi:**
- `agent/nodes/router.py` — thay `_classify()` bằng `_classify_llm()`
- `agent/state.py` — thêm `needs_planning: bool = False`

---

## 4. Module 2: Conversation Memory Manager

### 4.1 Design: SummaryBufferMemory Pattern

Giữ N turns gần nhất verbatim + rolling summary cho turns cũ hơn. Industry consensus cho production systems.

```
┌─────────────────────────────────────────────────────────┐
│              CONVERSATION MEMORY                         │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Rolling Summary (compressed older turns)        │    │
│  │  "User hỏi về lịch tuần, tạo 2 tasks,          │    │
│  │   thảo luận budget tháng 3..."                   │    │
│  │  ~200 tokens                                     │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Recent Window (last K turns, verbatim)          │    │
│  │  [Human]: Nhắc tôi họp lúc 3h chiều             │    │
│  │  [AI]: Đã tạo nhắc nhở họp lúc 15:00...         │    │
│  │  [Human]: Thêm ghi chú "mang laptop"            │    │
│  │  [AI]: Đã thêm ghi chú...                       │    │
│  │  ~800 tokens                                     │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
│  Token budget: ~1000 tokens total                        │
│  Window size: 10 turns (5 pairs)                         │
│  Summarize trigger: khi window đầy                       │
└─────────────────────────────────────────────────────────┘
```

### 4.2 Data Model

```sql
-- Thêm column vào conversations table
ALTER TABLE conversations ADD COLUMN rolling_summary TEXT DEFAULT '';
ALTER TABLE conversations ADD COLUMN summary_turn_count INT DEFAULT 0;
ALTER TABLE conversations ADD COLUMN total_turns INT DEFAULT 0;
```

### 4.3 Core Logic

```python
# memory/conversation_memory.py

WINDOW_SIZE = 10  # Keep last 10 messages verbatim
MAX_CONTEXT_TOKENS = 1000  # Token budget for conversation context
SUMMARIZE_MODEL = "gemini-2.0-flash"

SUMMARIZE_PROMPT = """Tóm tắt ngắn gọn đoạn hội thoại sau thành 2-3 câu.
Giữ lại: facts quan trọng, decisions đã đưa ra, action items.
Bỏ qua: chào hỏi, filler, chi tiết không quan trọng.

Summary trước đó: {previous_summary}

Đoạn hội thoại mới cần tóm tắt:
{messages_to_summarize}"""


class ConversationMemoryManager:
    """SummaryBuffer: recent window verbatim + rolling summary for older turns."""

    async def prepare_messages(
        self, conversation_id: str, new_messages: list[BaseMessage], db: AsyncSession
    ) -> list[BaseMessage]:
        """Return optimized message list for LLM context."""
        conv = await db.get(Conversation, conversation_id)
        all_messages = new_messages

        if len(all_messages) <= WINDOW_SIZE:
            # Chưa cần summarize
            result = all_messages
            if conv.rolling_summary:
                summary_msg = SystemMessage(
                    content=f"[Tóm tắt hội thoại trước]: {conv.rolling_summary}"
                )
                result = [summary_msg] + result
            return result

        # Cần summarize: lấy messages ngoài window
        to_summarize = all_messages[:-WINDOW_SIZE]
        window = all_messages[-WINDOW_SIZE:]

        # Generate summary
        new_summary = await self._summarize(
            conv.rolling_summary, to_summarize
        )

        # Persist
        conv.rolling_summary = new_summary
        conv.summary_turn_count += len(to_summarize)
        await db.commit()

        summary_msg = SystemMessage(
            content=f"[Tóm tắt hội thoại trước ({conv.summary_turn_count} turns)]: {new_summary}"
        )
        return [summary_msg] + window

    async def _summarize(
        self, previous_summary: str, messages: list[BaseMessage]
    ) -> str:
        """Incrementally summarize messages into rolling summary."""
        msgs_text = "\n".join(f"{m.type}: {m.content}" for m in messages)
        llm = get_llm(SUMMARIZE_MODEL)
        resp = await llm.ainvoke(
            SUMMARIZE_PROMPT.format(
                previous_summary=previous_summary or "(không có)",
                messages_to_summarize=msgs_text,
            )
        )
        return resp.content
```

### 4.4 Integration vào Agent Loop

```python
# agent/nodes/agent_loop.py — thay đổi
async def agent_loop_node(state: AgentState) -> dict:
    model = state.get("selected_model", "gemini-2.0-flash")
    llm = get_llm(model).bind_tools(all_tools)

    # NEW: Prepare messages with conversation memory
    conv_memory = ConversationMemoryManager()
    managed_messages = await conv_memory.prepare_messages(
        state.get("conversation_id", ""),
        state["messages"],
        db,
    )

    sys_prompt = SYSTEM_PROMPT.format(
        hot_memory=state.get("hot_memory", ""),
        cold_memory=state.get("cold_memory", ""),
        user_preferences=state.get("user_preferences", ""),  # NEW: M5
    )

    messages = [SystemMessage(content=sys_prompt)] + managed_messages
    messages = with_cache_control(messages, model)
    response = await llm.ainvoke(messages)
    return {"messages": [response]}
```

### 4.5 ADR-011: SummaryBuffer vs Sliding Window vs Full History

| Approach | Pros | Cons |
|----------|------|------|
| Full history | Không mất thông tin | Context overflow, cost tăng linear |
| Sliding window only | Đơn giản, fast | Mất hoàn toàn context cũ |
| **SummaryBuffer (chosen)** | **Giữ context cũ dạng nén + recent verbatim** | **Thêm 1 LLM call khi summarize** |
| Hierarchical summary | Nhiều level compression | Phức tạp, overkill cho personal assistant |

**Decision:** SummaryBuffer. Lý do: balance tốt nhất giữa context retention và cost. Summarize call chỉ xảy ra khi window đầy (~mỗi 10 turns), dùng cheap model.

---

## 5. Module 3: Plan-and-Execute Engine

### 5.1 Design

Khi router detect `needs_planning=true`, chuyển sang plan-and-execute flow thay vì ReAct loop thông thường.

```
                    ┌─────────────────┐
                    │  Router detects  │
                    │  needs_planning  │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │    PLANNER      │
                    │                 │
                    │ Decompose task  │
                    │ into steps      │
                    │ (structured)    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   EXECUTOR      │◄──────┐
                    │                 │       │
                    │ Execute step i  │       │
                    │ using tools     │       │
                    │ or sub-agent    │       │
                    └───┬─────────┬───┘       │
                        │         │           │
                   Done all    More steps     │
                        │         │           │
                        │    ┌────▼────┐      │
                        │    │ REPLAN  │      │
                        │    │         │      │
                        │    │ Adjust  │──────┘
                        │    │ plan if │  (update remaining steps)
                        │    │ needed  │
                        │    └─────────┘
                        │
               ┌────────▼────────┐
               │   SYNTHESIZE    │
               │                 │
               │ Combine results │
               │ into response   │
               └─────────────────┘
```

### 5.2 Plan Schema

```python
class PlanStep(BaseModel):
    """A single step in the execution plan."""
    step_id: int
    description: str  # Mô tả ngắn gọn
    tool_hint: str = ""  # Tool gợi ý (optional)
    depends_on: list[int] = []  # Step IDs phải hoàn thành trước

class ExecutionPlan(BaseModel):
    """Multi-step plan generated by planner."""
    goal: str  # Mục tiêu tổng thể
    steps: list[PlanStep]
    estimated_complexity: Literal["medium", "complex"] = "medium"
```

### 5.3 Planner Prompt

```python
PLANNER_PROMPT = """Bạn là planner cho AI assistant. Phân rã yêu cầu thành các bước cụ thể.

Available tools: {tool_descriptions}

Quy tắc:
- Mỗi step phải actionable (có thể thực hiện bằng 1 tool call hoặc 1 LLM reasoning)
- Tối đa 7 steps (nếu cần nhiều hơn → chia thành sub-goals)
- Ghi rõ depends_on nếu step cần kết quả từ step trước
- tool_hint: gợi ý tool nào nên dùng (optional)

User context:
{hot_memory}

User request: {user_message}

Trả về ExecutionPlan JSON."""
```

### 5.4 Executor Logic

```python
# agent/nodes/plan_execute.py

MAX_PLAN_STEPS = 7
MAX_REPLAN_ROUNDS = 2

async def planner_node(state: AgentState) -> dict:
    """Generate execution plan from user request."""
    llm = get_llm("gemini-2.0-flash").with_structured_output(ExecutionPlan)
    user_msg = state["messages"][-1].content

    plan = await llm.ainvoke([
        SystemMessage(content=PLANNER_PROMPT.format(
            tool_descriptions=get_tool_descriptions(),
            hot_memory=state.get("hot_memory", ""),
            user_message=user_msg,
        ))
    ])

    return {
        "execution_plan": plan.model_dump(),
        "current_step": 0,
        "step_results": [],
    }


async def executor_node(state: AgentState) -> dict:
    """Execute current step of the plan."""
    plan = state["execution_plan"]
    step_idx = state["current_step"]
    steps = plan["steps"]

    if step_idx >= len(steps):
        return {}  # All done

    step = steps[step_idx]
    previous_results = state.get("step_results", [])

    # Build context for this step
    context = f"Goal: {plan['goal']}\nCurrent step: {step['description']}"
    if previous_results:
        context += f"\nPrevious results:\n" + "\n".join(
            f"Step {i+1}: {r}" for i, r in enumerate(previous_results)
        )

    # Execute via agent_loop (reuse existing tool-calling logic)
    llm = get_llm(state.get("selected_model", "gemini-2.0-flash")).bind_tools(all_tools)
    resp = await llm.ainvoke([
        SystemMessage(content=f"Thực hiện bước sau. {context}"),
        HumanMessage(content=step["description"]),
    ])

    new_results = previous_results + [resp.content]
    return {
        "step_results": new_results,
        "current_step": step_idx + 1,
        "messages": [resp],
    }


async def replan_node(state: AgentState) -> dict:
    """Check if plan needs adjustment based on execution results."""
    plan = state["execution_plan"]
    step_idx = state["current_step"]
    results = state.get("step_results", [])
    replan_count = state.get("replan_count", 0)

    if step_idx >= len(plan["steps"]) or replan_count >= MAX_REPLAN_ROUNDS:
        return {}

    # Ask LLM if plan needs adjustment
    llm = get_llm("gemini-2.0-flash")
    check = await llm.ainvoke(
        f"Goal: {plan['goal']}\n"
        f"Completed steps: {results}\n"
        f"Remaining: {[s['description'] for s in plan['steps'][step_idx:]]}\n"
        f"Kế hoạch còn lại có cần điều chỉnh không? Trả lời 'OK' nếu không."
    )

    if "OK" in check.content.upper():
        return {}

    # Replan remaining steps
    new_plan = await get_llm("gemini-2.0-flash").with_structured_output(ExecutionPlan).ainvoke(
        f"Điều chỉnh kế hoạch. Goal: {plan['goal']}\n"
        f"Đã hoàn thành: {results}\n"
        f"Vấn đề: {check.content}\n"
        f"Tạo plan mới cho phần còn lại."
    )

    return {
        "execution_plan": new_plan.model_dump(),
        "current_step": 0,
        "replan_count": replan_count + 1,
    }


async def synthesize_node(state: AgentState) -> dict:
    """Combine all step results into final response."""
    plan = state["execution_plan"]
    results = state.get("step_results", [])

    llm = get_llm(state.get("selected_model", "gemini-2.0-flash"))
    response = await llm.ainvoke(
        f"Tổng hợp kết quả thực hiện kế hoạch.\n"
        f"Goal: {plan['goal']}\n"
        f"Results:\n" + "\n".join(f"- {r}" for r in results) +
        f"\n\nTrả lời user ngắn gọn, thân thiện."
    )

    return {"messages": [response]}
```

### 5.5 Graph Integration

```python
# agent/graph.py — thêm plan-and-execute subgraph

def route_after_router(state: AgentState) -> str:
    if state.get("needs_planning"):
        return "planner"  # NEW
    if state.get("delegation_target"):
        return "delegate"
    return "agent_loop"

def should_continue_plan(state: AgentState) -> str:
    plan = state.get("execution_plan", {})
    step_idx = state.get("current_step", 0)
    if step_idx < len(plan.get("steps", [])):
        return "executor"  # More steps
    return "synthesize"  # All done

# New nodes
graph.add_node("planner", planner_node)
graph.add_node("executor", executor_node)
graph.add_node("replan", replan_node)
graph.add_node("synthesize", synthesize_node)

# New edges
graph.add_conditional_edges("route", route_after_router, {
    "planner": "planner",
    "delegate": "delegate",
    "agent_loop": "agent_loop",
})
graph.add_edge("planner", "executor")
graph.add_edge("executor", "replan")
graph.add_conditional_edges("replan", should_continue_plan, {
    "executor": "executor",
    "synthesize": "synthesize",
})
graph.add_edge("synthesize", "respond")
```

### 5.6 ADR-012: Plan-and-Execute vs ReWOO vs LLMCompiler

| Pattern | Parallel | Complexity | Fit for JARVIS |
|---------|----------|------------|----------------|
| **Plan-and-Execute (chosen)** | **No (sequential)** | **Low** | **Best — personal tasks are sequential** |
| ReWOO | No (but variable refs) | Medium | Good but variable syntax adds complexity |
| LLMCompiler | Yes (DAG) | High | Overkill — personal tasks rarely parallelizable |

**Decision:** Plan-and-Execute with replan. Lý do: personal assistant tasks (trip planning, weekly review, project setup) hầu hết sequential. Parallel execution (LLMCompiler) thêm complexity mà ít benefit. Có thể upgrade sau nếu cần.

---

## 6. Module 4: Memory Consolidation

### 6.1 Problem

Hiện tại `memory/extraction.py` extract facts mỗi turn nhưng:
- Không check trùng lặp → "Tôi thích cà phê" × 10 = 10 records
- Không resolve mâu thuẫn → "Tôi thích cà phê" + "Tôi bỏ cà phê rồi" cùng tồn tại
- Không decay → memories cũ 6 tháng có weight bằng memories mới
- Không merge → "Kiên làm ở FPT" + "Kiên là developer" = 2 records thay vì 1

### 6.2 Design: Memory Manager with CRUD Operations

Lấy cảm hứng từ LangMem SDK — memory manager có khả năng INSERT, UPDATE, DELETE memories thay vì chỉ INSERT.

```
New facts extracted from conversation
    │
    ▼
┌──────────────────────────────────────┐
│       MEMORY CONSOLIDATION           │
│                                       │
│  1. Extract new facts (existing)      │
│                                       │
│  2. Search existing memories          │
│     (semantic similarity)             │
│                                       │
│  3. LLM decides per fact:             │
│     ┌─────────────────────────────┐  │
│     │ INSERT: new unique fact     │  │
│     │ UPDATE: merge with existing │  │
│     │ DELETE: contradicted/stale  │  │
│     │ SKIP: already exists        │  │
│     └─────────────────────────────┘  │
│                                       │
│  4. Apply operations to DB            │
│  5. Update embeddings                 │
└──────────────────────────────────────┘
```

### 6.3 Consolidation Prompt

```python
CONSOLIDATION_PROMPT = """So sánh fact mới với memories hiện có của user.

Fact mới: {new_fact}

Memories hiện có (liên quan):
{existing_memories}

Quyết định:
- INSERT: fact mới, chưa có trong memories
- UPDATE: fact bổ sung/cập nhật memory hiện có (ghi rõ memory_id + nội dung mới)
- DELETE: fact mâu thuẫn với memory cũ → xóa memory cũ (ghi rõ memory_id)
- SKIP: fact đã tồn tại, không cần thêm

Trả về JSON:
{{"action": "INSERT|UPDATE|DELETE|SKIP", "memory_id": "uuid hoặc null", "content": "nội dung mới nếu INSERT/UPDATE", "reason": "giải thích ngắn"}}"""
```

### 6.4 Core Logic

```python
# memory/consolidation.py

SIMILARITY_THRESHOLD = 0.85  # Cosine similarity threshold for "similar" memories

class MemoryConsolidator:
    """Manages memory lifecycle: insert, update, delete, skip."""

    async def consolidate(
        self, user_id: str, new_facts: list[str], db: AsyncSession
    ) -> dict:
        """Process new facts against existing memories."""
        stats = {"inserted": 0, "updated": 0, "deleted": 0, "skipped": 0}

        for fact in new_facts:
            fact_emb = await embed_text(fact)

            # Find similar existing memories
            similar = await search_cold_memory(user_id, fact_emb, db, limit=3)

            if not similar:
                # No similar memories → INSERT
                await save_memory(user_id, fact, "semantic", fact_emb, db)
                stats["inserted"] += 1
                continue

            # Check if exact duplicate (high similarity)
            top_sim = self._cosine_similarity(fact_emb, similar[0].get("embedding"))
            if top_sim > SIMILARITY_THRESHOLD:
                stats["skipped"] += 1
                continue

            # Ask LLM to decide
            existing_str = "\n".join(
                f"[{m['type']}] (id={m.get('id','?')}): {m['content']}"
                for m in similar
            )
            decision = await self._decide(fact, existing_str)

            if decision["action"] == "INSERT":
                await save_memory(user_id, fact, "semantic", fact_emb, db)
                stats["inserted"] += 1
            elif decision["action"] == "UPDATE" and decision.get("memory_id"):
                await self._update_memory(
                    decision["memory_id"], decision["content"], db
                )
                stats["updated"] += 1
            elif decision["action"] == "DELETE" and decision.get("memory_id"):
                await self._delete_memory(decision["memory_id"], db)
                # Insert the new fact as replacement
                await save_memory(user_id, fact, "semantic", fact_emb, db)
                stats["deleted"] += 1
            else:
                stats["skipped"] += 1

        return stats

    async def _decide(self, new_fact: str, existing: str) -> dict:
        llm = get_llm("gemini-2.0-flash")
        resp = await llm.ainvoke(
            CONSOLIDATION_PROMPT.format(
                new_fact=new_fact, existing_memories=existing
            )
        )
        return json.loads(resp.content.strip())
```

### 6.5 Importance Decay

Memories cũ không được access nên giảm importance theo thời gian:

```python
# Chạy daily via ARQ cron
async def decay_memories(ctx: dict):
    """Reduce importance of old, unaccessed memories."""
    async with async_session() as db:
        await db.execute(text("""
            UPDATE memories
            SET importance = importance * 0.95
            WHERE last_accessed < NOW() - INTERVAL '30 days'
              AND importance > 0.1
        """))
        await db.commit()
```

### 6.6 Integration

Thay thế `extract_memories()` trong `post_process_node`:

```python
# agent/nodes/post_process.py — thay đổi
async def post_process_node(state: AgentState) -> dict:
    # ... existing usage logging ...

    # NEW: Extract + Consolidate (thay vì chỉ extract)
    try:
        if user_id and len(state["messages"]) >= 2:
            raw_facts = await extract_memories(state["messages"], user_id)
            if raw_facts.get("facts"):
                consolidator = MemoryConsolidator()
                stats = await consolidator.consolidate(
                    user_id, raw_facts["facts"], db
                )
                logger.info(f"Memory consolidation: {stats}")
            await extract_kg(state["messages"], user_id)
    except Exception:
        logger.exception("Memory consolidation failed")

    return {}
```

---

## 7. Module 5: User Preference Learning

### 7.1 Design: Two-Level Preference System

Lấy cảm hứng từ Me-Agent (two-level habit learning) và LangMem (procedural memory + prompt optimizer).

```
┌─────────────────────────────────────────────────────────┐
│           USER PREFERENCE LEARNING                       │
│                                                          │
│  Level 1: Explicit Preferences (Semantic Memory)         │
│  ┌─────────────────────────────────────────────────┐    │
│  │ • Tone: formal / casual / friendly              │    │
│  │ • Language: Vietnamese / English / mixed         │    │
│  │ • Verbosity: concise / detailed                  │    │
│  │ • Interests: tech, finance, travel...            │    │
│  │ • Work context: role, company, team              │    │
│  │                                                  │    │
│  │ Storage: user_preferences table (structured)     │    │
│  │ Update: extracted from conversations             │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
│  Level 2: Behavioral Patterns (Procedural Memory)        │
│  ┌─────────────────────────────────────────────────┐    │
│  │ • Response patterns that user liked/disliked     │    │
│  │ • Prompt rules learned from feedback             │    │
│  │ • Interaction style adaptations                  │    │
│  │                                                  │    │
│  │ Storage: user_prompt_rules table                 │    │
│  │ Update: periodic optimization from trajectories  │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### 7.2 Data Model

```sql
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) UNIQUE,
    tone VARCHAR(20) DEFAULT 'friendly',        -- formal, casual, friendly
    verbosity VARCHAR(20) DEFAULT 'concise',    -- concise, balanced, detailed
    language VARCHAR(20) DEFAULT 'vi',          -- vi, en, mixed
    interests JSONB DEFAULT '[]',               -- ["tech", "finance", "travel"]
    work_context JSONB DEFAULT '{}',            -- {"role": "developer", "company": "..."}
    custom_rules JSONB DEFAULT '[]',            -- ["Luôn dùng emoji", "Gọi tôi là anh"]
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE user_prompt_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    rule TEXT NOT NULL,                          -- "Khi user hỏi về code, luôn kèm ví dụ"
    confidence FLOAT DEFAULT 0.5,               -- 0-1, tăng khi rule được validate
    source VARCHAR(50) DEFAULT 'learned',       -- learned, explicit, default
    created_at TIMESTAMPTZ DEFAULT now(),
    last_validated TIMESTAMPTZ DEFAULT now()
);
```

### 7.3 Preference Extraction

```python
# memory/preference_learning.py

PREFERENCE_EXTRACT_PROMPT = """Phân tích hội thoại và trích xuất preferences của user.

Hội thoại:
{conversation}

Preferences hiện tại:
{current_preferences}

Trả về JSON với các thay đổi (chỉ ghi field cần update):
{{"tone": "...", "verbosity": "...", "interests_add": [...], "custom_rules_add": [...], "work_context_update": {{...}}}}

Nếu không phát hiện preference mới: {{}}"""


class PreferenceLearner:
    """Extract and update user preferences from conversations."""

    async def learn_from_conversation(
        self, messages: list[BaseMessage], user_id: str, db: AsyncSession
    ) -> dict:
        """Analyze conversation for preference signals."""
        if len(messages) < 4:  # Need enough context
            return {}

        current = await self._load_preferences(user_id, db)
        conversation = "\n".join(
            f"{m.type}: {m.content}" for m in messages[-10:]
        )

        llm = get_llm("gemini-2.0-flash")
        resp = await llm.ainvoke(
            PREFERENCE_EXTRACT_PROMPT.format(
                conversation=conversation,
                current_preferences=json.dumps(current, ensure_ascii=False),
            )
        )

        updates = json.loads(resp.content.strip())
        if updates:
            await self._apply_updates(user_id, updates, db)
        return updates

    async def build_preference_prompt(
        self, user_id: str, db: AsyncSession
    ) -> str:
        """Build preference section for system prompt."""
        prefs = await self._load_preferences(user_id, db)
        rules = await self._load_rules(user_id, db)

        parts = []
        if prefs.get("tone"):
            parts.append(f"Tone: {prefs['tone']}")
        if prefs.get("verbosity"):
            parts.append(f"Verbosity: {prefs['verbosity']}")
        if prefs.get("interests"):
            parts.append(f"Interests: {', '.join(prefs['interests'])}")
        if prefs.get("work_context"):
            ctx = prefs["work_context"]
            parts.append(f"Work: {ctx.get('role', '')} @ {ctx.get('company', '')}")
        if prefs.get("custom_rules"):
            for rule in prefs["custom_rules"]:
                parts.append(f"Rule: {rule}")

        # Add learned behavioral rules (high confidence only)
        for rule in rules:
            if rule["confidence"] >= 0.7:
                parts.append(f"Learned: {rule['rule']}")

        if not parts:
            return ""
        return "[User Preferences]\n" + "\n".join(parts)
```

### 7.4 Behavioral Pattern Learning (Procedural Memory)

```python
# Chạy weekly via ARQ cron
async def optimize_user_prompts(ctx: dict):
    """Analyze recent conversations to learn behavioral rules."""
    async with async_session() as db:
        users = (await db.execute(select(User))).scalars().all()

        for user in users:
            # Load recent conversations with implicit feedback signals
            # (user corrections, re-asks, explicit feedback)
            trajectories = await _load_trajectories(user.id, db, days=7)
            if len(trajectories) < 5:
                continue

            # Use LLM to identify patterns
            llm = get_llm("gemini-2.0-flash")
            resp = await llm.ainvoke(
                f"Phân tích {len(trajectories)} cuộc hội thoại gần đây.\n"
                f"Tìm patterns: user thường phải hỏi lại điều gì? "
                f"User thích kiểu trả lời nào? User không thích gì?\n"
                f"Trả về list rules dạng JSON: "
                f'[{{"rule": "...", "confidence": 0.5-1.0}}]'
            )

            rules = json.loads(resp.content.strip())
            for rule in rules:
                # Upsert rule
                existing = await db.execute(
                    select(UserPromptRule).where(
                        UserPromptRule.user_id == user.id,
                        UserPromptRule.rule == rule["rule"],
                    )
                )
                if existing.scalar():
                    # Increase confidence
                    await db.execute(
                        update(UserPromptRule)
                        .where(UserPromptRule.rule == rule["rule"])
                        .values(
                            confidence=min(1.0, UserPromptRule.confidence + 0.1),
                            last_validated=datetime.utcnow(),
                        )
                    )
                else:
                    db.add(UserPromptRule(
                        user_id=user.id,
                        rule=rule["rule"],
                        confidence=rule.get("confidence", 0.5),
                    ))
            await db.commit()
```

### 7.5 Integration vào System Prompt

```python
# agent/nodes/agent_loop.py — SYSTEM_PROMPT updated
SYSTEM_PROMPT = """Bạn là MY JARVIS — trợ lý AI cá nhân thông minh.

{user_preferences}

Nguyên tắc:
- Trả lời theo tone và verbosity preferences của user
- Dùng tool khi cần hành động
- Luôn nhớ context từ memory
- Nếu không chắc, hỏi lại

{hot_memory}
{cold_memory}"""
```

### 7.6 ADR-013: Preference Learning Approach

| Approach | Personalization | Cost | Privacy |
|----------|----------------|------|---------|
| **Explicit extraction (chosen L1)** | **Medium** | **Low** | **Good — user controls** |
| **Behavioral learning (chosen L2)** | **High** | **Medium (weekly batch)** | **Good — on-premise** |
| Fine-tune per user | Very high | Very high | Risk — model contains user data |
| Collaborative filtering | Medium | Low | Risk — cross-user data |

**Decision:** Two-level approach. L1 (explicit) chạy mỗi conversation, cost thấp. L2 (behavioral) chạy weekly batch, phát hiện patterns sâu hơn. Không fine-tune per user (quá đắt, privacy risk).

---

## 8. Updated Agent Graph (v3)

### 8.1 Complete Flow

```
User Message
    │
    ▼
┌──────────────────────────────────────────────────────────────────┐
│  ROUTE (M1: Smart Router)                                        │
│  LLM classify → intent, complexity, specialist, needs_planning   │
│  Select model → load memory → load preferences                   │
└──────────┬───────────────────┬──────────────────┬────────────────┘
           │                   │                  │
     needs_planning      specialist          default
           │                   │                  │
           ▼                   ▼                  ▼
    ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
    │   PLANNER    │   │  DELEGATE    │   │  AGENT_LOOP  │
    │   (M3)       │   │  (v2)       │   │  (v2)        │
    │              │   │              │   │              │
    │  Decompose   │   │  Specialist  │   │  ReAct loop  │
    │  into steps  │   │  sub-agent   │   │  with tools  │
    └──────┬───────┘   └──────┬───────┘   └──────┬───────┘
           │                   │                  │
           ▼                   │                  │
    ┌──────────────┐           │                  │
    │  EXECUTOR    │◄──┐       │                  │
    │  (M3)        │   │       │                  │
    │  Run step i  │   │       │                  │
    └──────┬───────┘   │       │                  │
           │           │       │                  │
           ▼           │       │                  │
    ┌──────────────┐   │       │                  │
    │  REPLAN      │───┘       │                  │
    │  (M3)        │           │                  │
    │  Adjust?     │           │                  │
    └──────┬───────┘           │                  │
           │ done              │                  │
           ▼                   │                  │
    ┌──────────────┐           │                  │
    │  SYNTHESIZE  │           │                  │
    │  (M3)        │           │                  │
    └──────┬───────┘           │                  │
           │                   │                  │
           └───────────────────┴──────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │  RESPOND            │
                    │  (M2: managed msgs) │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  EVALUATE (v2)      │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  POST_PROCESS       │
                    │  • M4: Consolidate  │
                    │  • M5: Learn prefs  │
                    │  • KG extraction    │
                    │  • Usage logging    │
                    └─────────────────────┘
```

### 8.2 State Extension

```python
class AgentState(MessagesState):
    # --- v2 fields (unchanged) ---
    user_id: str = ""
    user_tier: str = "free"
    channel: str = ""
    intent: str = ""
    complexity: str = "simple"
    selected_model: str = ""
    hot_memory: str = ""
    cold_memory: str = ""
    tool_calls_count: int = 0
    budget_remaining: float = 0.0
    injection_score: float = 0.0
    retry_count: int = 0
    delegation_target: str = ""
    delegation_result: str = ""
    delegation_count: int = 0
    final_response: str = ""

    # --- v3 new fields ---
    conversation_id: str = ""           # M2: track conversation
    needs_planning: bool = False        # M1/M3: router → planner
    execution_plan: dict = {}           # M3: current plan
    current_step: int = 0              # M3: step index
    step_results: list[str] = []       # M3: results per step
    replan_count: int = 0              # M3: replan counter
    user_preferences: str = ""          # M5: preference prompt section
```

---

## 9. Data Model Changes (All Modules)

```sql
-- M2: Conversation Memory
ALTER TABLE conversations ADD COLUMN rolling_summary TEXT DEFAULT '';
ALTER TABLE conversations ADD COLUMN summary_turn_count INT DEFAULT 0;
ALTER TABLE conversations ADD COLUMN total_turns INT DEFAULT 0;

-- M5: User Preferences
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) UNIQUE,
    tone VARCHAR(20) DEFAULT 'friendly',
    verbosity VARCHAR(20) DEFAULT 'concise',
    language VARCHAR(20) DEFAULT 'vi',
    interests JSONB DEFAULT '[]',
    work_context JSONB DEFAULT '{}',
    custom_rules JSONB DEFAULT '[]',
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE user_prompt_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    rule TEXT NOT NULL,
    confidence FLOAT DEFAULT 0.5,
    source VARCHAR(50) DEFAULT 'learned',
    created_at TIMESTAMPTZ DEFAULT now(),
    last_validated TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_upr_user ON user_prompt_rules(user_id);
CREATE INDEX idx_upr_confidence ON user_prompt_rules(user_id, confidence);
```

---

## 10. Implementation Plan (Intelligence Modules M1-M5)

> ⚠️ **Note:** This is the original plan for M1-M5 only. See **Section 24** for the full revised plan including operational modules M6-M11.

### Phase Ordering (dependency-based)

```
Phase A (Week 1-2): M1 Smart Router + M2 Conversation Memory
    → Không dependency, cải thiện ngay chất lượng routing + context management
    → Foundation cho M3 (router detect needs_planning)

Phase B (Week 2-3): M4 Memory Consolidation
    → Cải thiện memory quality trước khi thêm features mới
    → Không dependency ngoài existing memory system

Phase C (Week 3-4): M3 Plan-and-Execute
    → Cần M1 (router detect needs_planning)
    → Cần M2 (conversation memory cho multi-turn plans)

Phase D (Week 4-5): M5 User Preference Learning
    → Cần M4 (clean memory để learn preferences chính xác)
    → Cần đủ conversation data để learn patterns
```

### Effort Estimation

| Module | New Files | Modified Files | Est. LOC | Est. Days |
|--------|-----------|---------------|----------|-----------|
| M1: Smart Router | 0 | 2 (router.py, state.py) | ~80 | 1 |
| M2: Conversation Memory | 1 (conversation_memory.py) | 2 (agent_loop.py, graph.py) | ~120 | 2 |
| M3: Plan-and-Execute | 1 (plan_execute.py) | 2 (graph.py, state.py) | ~200 | 3 |
| M4: Memory Consolidation | 1 (consolidation.py) | 1 (post_process.py) | ~150 | 2 |
| M5: User Preference Learning | 1 (preference_learning.py) | 2 (agent_loop.py, proactive.py) | ~180 | 3 |
| DB Migrations | 1 | 0 | ~40 | 0.5 |
| **Total** | **5** | **7** | **~770** | **~11.5 days** |

---

## 11. Cost Impact Analysis

### Per-request cost change

| Component | v2 Cost | v3 Cost | Delta |
|-----------|---------|---------|-------|
| Router | $0 (keyword) | ~$0.00001 (LLM classify) | +$0.00001 |
| Conversation Memory | $0 | ~$0.00002 (summarize every 10 turns) | +$0.00002 |
| Plan-and-Execute | $0 | ~$0.0001 (planner + replan, only for complex) | +$0.0001 |
| Memory Consolidation | ~$0.00003 (extract only) | ~$0.00005 (extract + consolidate) | +$0.00002 |
| Preference Learning | $0 | ~$0.00001 (extract per convo) | +$0.00001 |
| **Total per request** | **~$0.0001** | **~$0.00016** | **+60%** |

### Monthly cost projection (1000 users, 10 msgs/day)

| | v2 | v3 |
|---|---|---|
| LLM costs | ~$30/mo | ~$48/mo |
| Quality improvement | Baseline | ~2.5x better routing, planning, personalization |

**Verdict:** +$18/mo cho quality improvement đáng kể. ROI rất cao.

---

## 12. Migration Strategy

| Module | Feature Flag | Rollback |
|--------|-------------|----------|
| M1: Smart Router | `SMART_ROUTER_ENABLED` | Fall back to keyword `_classify()` |
| M2: Conversation Memory | `CONVO_MEMORY_ENABLED` | Pass raw messages (v2 behavior) |
| M3: Plan-and-Execute | `PLANNING_ENABLED` | Route to agent_loop (v2 behavior) |
| M4: Memory Consolidation | `MEMORY_CONSOLIDATION_ENABLED` | Extract-only (v2 behavior) |
| M5: Preference Learning | `PREFERENCE_LEARNING_ENABLED` | Empty preferences string |

Mỗi module có flag riêng → deploy incrementally, A/B test, rollback independently.

---

## 13. Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| LLM router adds latency | User feels slow | Medium | Cache + 500ms timeout + keyword fallback |
| Summarization loses critical info | Wrong context | Medium | Keep 10 recent turns verbatim, only summarize older |
| Planner generates bad plans | Wasted tool calls | Medium | Max 7 steps, max 2 replans, human-in-the-loop for destructive actions |
| Memory consolidation deletes valid memory | Data loss | Low | Soft delete (mark as archived), review log |
| Preference learning creates wrong rules | Bad UX | Low | Confidence threshold (0.7), weekly review, user can override |

---

## 14. Success Metrics

| Metric | v2 Baseline | v3 Target | How to Measure |
|--------|-------------|-----------|----------------|
| Router accuracy | ~60% (estimated) | >90% | Sample 100 requests, manual label |
| Context overflow rate | ~15% at 30+ turns | <1% | Monitor truncation events |
| Multi-step task completion | 0% (not supported) | >70% | Test suite of 20 planning scenarios |
| Memory duplicate rate | ~40% (estimated) | <5% | Count near-duplicate memories per user |
| User satisfaction (implicit) | Baseline | +30% | Track re-ask rate, conversation length |

---

## 15. Future Considerations (v4+)

- **Fine-tuned router model**: Khi có đủ labeled data (10K+ requests) → train small classifier thay LLM
- **Parallel plan execution**: LLMCompiler pattern cho tasks có thể chạy song song
- **Cross-user learning**: Aggregate patterns across users (with privacy) để improve default behavior
- **Voice preference**: Adapt response length/style cho voice vs text channels
- **Proactive planning**: JARVIS tự suggest plans dựa trên patterns (e.g., "Thứ 2 nào bạn cũng review tasks, tạo sẵn nhé?")

---

## 16. Module Classification: UI/UX vs Technical-Only

| Module | Type | UI/UX Component | Technical Component |
|--------|------|----------------|---------------------|
| M1: Smart Router | 🔧 Technical-only | — | LLM classifier thay keyword matching |
| M2: Conversation Memory | 🔧 Technical-only | — | SummaryBuffer, invisible to user |
| M3: Plan-and-Execute | 🎨 UI/UX + Technical | Progress indicator: "Đang thực hiện bước 2/5..." | Planner → Executor → Replan loop |
| M4: Memory Consolidation | 🔧 Technical-only | — | Dedup + merge chạy background |
| M5: User Preference Learning | 🎨 UI/UX + Technical | Settings page: tone, verbosity, interests | Auto-extract + behavioral learning |
| M6: Context Window Guard | 🔧 Technical-only | — | Token counting + auto-compact |
| M7: Checkpointing | 🎨 UI/UX + Technical | "Tiếp tục từ lần trước" button | LangGraph persistent checkpointer |
| M8: Human-in-the-Loop | 🎨 UI/UX (primary) | Approval dialog: "Tạo 3 tasks — Đồng ý?" | LangGraph interrupt API |
| M9: Evidence Logging | 🎨 UI/UX + Technical | Audit trail page: xem lịch sử tool calls | JSONL structured logging |
| M10: Supervision | 🔧 Technical-only | — | Heartbeat + watchdog + auto-recover |
| M11: Tool Permissions | 🎨 UI/UX (primary) | Settings > Tools: enable/disable per tool | Permission model + allowlist |

---

## 17. Module 6: Context Window Guard (🔧 Technical-only)

### 17.1 Problem

Agent loop đổ toàn bộ messages vào LLM mà không check token limit. Long conversations hoặc nhiều tool results → vượt context window → crash hoặc silent truncation mất thông tin.

OpenClaw giải quyết bằng Context Window Guard kiểm tra trước mỗi LLM call.

### 17.2 Design

```
Messages + System Prompt + Tools
    │
    ▼
┌──────────────────────────────────┐
│     CONTEXT WINDOW GUARD         │
│                                   │
│  1. Count tokens (tiktoken)       │
│  2. Compare vs model max_tokens   │
│  3. If over budget:               │
│     a. Summarize old messages     │
│     b. Trim tool results          │
│     c. Drop low-priority context  │
│  4. Pass to LLM                   │
└──────────────────────────────────┘
```

### 17.3 Token Budget Allocation

```python
MODEL_CONTEXT_LIMITS = {
    "gemini-2.0-flash": 1_000_000,
    "gemini-2.5-flash": 1_000_000,
    "claude-haiku-4.5": 200_000,
    "claude-sonnet-4.6": 200_000,
    "gpt-5.2": 128_000,
    "deepseek-v3.2": 64_000,
}

# Budget allocation (% of context window)
BUDGET = {
    "system_prompt": 0.10,    # 10% — system + tools + preferences
    "hot_memory": 0.05,       # 5% — profile, tasks, calendar
    "cold_memory": 0.05,      # 5% — retrieved memories
    "conversation": 0.60,     # 60% — messages (summary + window)
    "output_reserve": 0.20,   # 20% — reserved for model output
}
```

### 17.4 Core Logic

```python
# core/context_guard.py
import tiktoken

class ContextWindowGuard:
    """Ensure assembled context fits within model's token limit."""

    def __init__(self, model: str):
        self.model = model
        self.max_tokens = MODEL_CONTEXT_LIMITS.get(model, 128_000)
        self.encoder = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        return len(self.encoder.encode(text))

    def guard(self, messages: list, tools: list, reserve: int = 4096) -> list:
        """Trim messages to fit within context window."""
        total = sum(self.count_tokens(m.content) for m in messages)
        tool_tokens = self.count_tokens(str(tools))
        available = self.max_tokens - tool_tokens - reserve

        if total <= available:
            return messages  # Fits fine

        # Strategy: keep system + last N messages, summarize rest
        system_msgs = [m for m in messages if m.type == "system"]
        other_msgs = [m for m in messages if m.type != "system"]

        # Trim tool results first (often verbose)
        for i, m in enumerate(other_msgs):
            if m.type == "tool" and self.count_tokens(m.content) > 500:
                other_msgs[i].content = m.content[:2000] + "\n...[truncated]"

        # If still over, keep only recent window
        while sum(self.count_tokens(m.content) for m in other_msgs) > available * 0.8:
            if len(other_msgs) > 4:
                other_msgs.pop(0)  # Remove oldest
            else:
                break

        return system_msgs + other_msgs
```

### 17.5 Integration

```python
# agent/nodes/agent_loop.py — thêm guard trước LLM call
guard = ContextWindowGuard(model)
messages = guard.guard(messages, all_tools)
response = await llm.ainvoke(messages)
```

**Files:** `core/context_guard.py` (NEW), `agent/nodes/agent_loop.py` (MODIFY)
**Effort:** 1 day

---

## 18. Module 7: LangGraph Checkpointing (🎨 UI/UX + Technical)

### 18.1 Problem

Agent state mất khi server restart. User không thể resume conversation từ điểm dừng. Không có time-travel debugging.

### 18.2 Design

LangGraph có built-in checkpointing — chỉ cần plug in persistent checkpointer (PostgreSQL).

```
┌──────────────────────────────────────────┐
│          CHECKPOINTING                    │
│                                           │
│  Technical:                               │
│  • PostgreSQL checkpointer (built-in)     │
│  • Auto-save state at every node          │
│  • Resume from last checkpoint on restart │
│                                           │
│  UI/UX:                                   │
│  • "Tiếp tục cuộc trò chuyện" button     │
│  • Conversation history persists          │
│  • Time-travel: xem state tại mỗi step   │
└──────────────────────────────────────────┘
```

### 18.3 Implementation

```python
# agent/graph.py — thay compile() thành compile(checkpointer=...)
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

async def get_checkpointer():
    return AsyncPostgresSaver.from_conn_string(settings.DATABASE_URL)

async def build_compiled_graph():
    checkpointer = await get_checkpointer()
    graph = build_graph()
    return graph.compile(checkpointer=checkpointer)
```

### 18.4 UI/UX: Resume Conversation

```
Frontend (Next.js)
┌─────────────────────────────────────┐
│  Conversations                       │
│  ┌─────────────────────────────────┐│
│  │ 📝 Lên kế hoạch đi Đà Nẵng    ││
│  │    Bước 3/5 — 2 giờ trước      ││
│  │    [Tiếp tục] [Xem lại]        ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │ 💰 Phân tích chi tiêu tháng 3  ││
│  │    Hoàn thành — Hôm qua        ││
│  │    [Xem lại]                    ││
│  └─────────────────────────────────┘│
└─────────────────────────────────────┘
```

**API endpoint:**
```python
# api/v1/conversations.py
@router.post("/{conversation_id}/resume")
async def resume_conversation(conversation_id: str):
    """Resume from last checkpoint."""
    config = {"configurable": {"thread_id": conversation_id}}
    state = await jarvis_graph.aget_state(config)
    return {"state": state, "can_resume": True}
```

**Files:** `agent/graph.py` (MODIFY), `api/v1/conversations.py` (MODIFY), frontend conversation list (MODIFY)
**Effort:** 1 day (backend) + 0.5 day (frontend)
**Dependency:** `langgraph-checkpoint-postgres` package

---

## 19. Module 8: Human-in-the-Loop (🎨 UI/UX Primary)

### 19.1 Problem

Agent thực hiện actions (tạo task, gửi message, xóa data) mà không hỏi user. Với plan-and-execute, agent có thể chain nhiều destructive actions liên tiếp.

OpenClaw pattern: Plan → Pause → Approve → Execute.

### 19.2 Design

Sử dụng LangGraph `interrupt()` API — pause execution, gửi approval request về frontend, resume khi user approve.

```
Agent generates plan: "Tạo 3 tasks + đặt lịch họp + gửi nhắc nhở"
    │
    ▼
┌──────────────────────────────────────────┐
│  HUMAN-IN-THE-LOOP                        │
│                                           │
│  Trigger conditions:                      │
│  • Plan có ≥3 steps                       │
│  • Action là destructive (delete, send)   │
│  • Cost estimate > threshold              │
│  • User preference: always_ask = true     │
│                                           │
│  Flow:                                    │
│  1. Agent generates plan/action           │
│  2. interrupt() → pause graph             │
│  3. Send approval request to frontend     │
│  4. User: Approve / Edit / Reject         │
│  5. Resume graph with user's decision     │
└──────────────────────────────────────────┘
```

### 19.3 UI/UX: Approval Dialog

```
┌─────────────────────────────────────────┐
│  🤖 JARVIS muốn thực hiện:              │
│                                          │
│  📋 Kế hoạch (3 bước):                  │
│  ✅ 1. Tạo task "Book vé máy bay"       │
│  ✅ 2. Tạo task "Đặt khách sạn"         │
│  ✅ 3. Thêm lịch "Bay đi Đà Nẵng 15/3" │
│                                          │
│  [✅ Đồng ý]  [✏️ Chỉnh sửa]  [❌ Hủy] │
└─────────────────────────────────────────┘
```

### 19.4 Implementation

```python
# agent/nodes/plan_execute.py — thêm interrupt cho plans
from langgraph.types import interrupt

DESTRUCTIVE_TOOLS = {"task_create", "task_update", "calendar_create", "expense_log"}

async def executor_node(state: AgentState) -> dict:
    plan = state["execution_plan"]
    step = plan["steps"][state["current_step"]]

    # Check if needs approval
    needs_approval = (
        len(plan["steps"]) >= 3
        or step.get("tool_hint") in DESTRUCTIVE_TOOLS
        or state.get("user_preferences", {}).get("always_ask", False)
    )

    if needs_approval and not state.get("user_approved"):
        # Pause and ask user
        approval = interrupt({
            "type": "plan_approval",
            "plan": plan,
            "current_step": state["current_step"],
            "message": f"Thực hiện {len(plan['steps'])} bước?",
        })

        if approval.get("action") == "reject":
            return {"messages": [AIMessage(content="Đã hủy kế hoạch.")]}
        if approval.get("action") == "edit":
            return {"execution_plan": approval["edited_plan"], "current_step": 0}

    # Proceed with execution...
    return await _execute_step(state)
```

### 19.5 WebSocket Protocol

```json
// Server → Client: approval request
{
  "type": "approval_request",
  "request_id": "req-123",
  "plan": {"goal": "...", "steps": [...]},
  "message": "Thực hiện 3 bước?"
}

// Client → Server: user response
{
  "type": "approval_response",
  "request_id": "req-123",
  "action": "approve" | "edit" | "reject",
  "edited_plan": null | {...}
}
```

**Files:** `agent/nodes/plan_execute.py` (MODIFY), `api/v1/ws.py` (MODIFY), frontend approval component (NEW)
**Effort:** 1 day (backend) + 1 day (frontend)

---

## 20. Module 9: Structured Evidence Logging (🎨 UI/UX + Technical)

### 20.1 Problem

Hiện tại chỉ có Python `logging` — không structured, không queryable, không hiển thị cho user. User không biết agent đã làm gì, gọi tool nào, kết quả ra sao.

OpenClaw pattern: JSONL append-only transcript cho mỗi session.

### 20.2 Design

```
┌──────────────────────────────────────────┐
│       EVIDENCE LOGGING                    │
│                                           │
│  Technical:                               │
│  • JSONL per session (append-only)        │
│  • Structured: timestamp, agent, tool,    │
│    input, output, cost, duration          │
│  • PostgreSQL table for queryable access  │
│                                           │
│  UI/UX:                                   │
│  • Audit trail page: timeline of actions  │
│  • Per-conversation: "Xem chi tiết"       │
│  • Cost breakdown per conversation        │
└──────────────────────────────────────────┘
```

### 20.3 Data Model

```sql
CREATE TABLE evidence_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    conversation_id UUID REFERENCES conversations(id),
    session_id VARCHAR(100) NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT now(),
    node VARCHAR(50) NOT NULL,       -- "router", "agent_loop", "executor", "delegate"
    event_type VARCHAR(30) NOT NULL, -- "llm_call", "tool_call", "plan_created", "approval"
    tool_name VARCHAR(100),
    tool_input JSONB,
    tool_output JSONB,
    model_used VARCHAR(50),
    tokens_used INT DEFAULT 0,
    cost FLOAT DEFAULT 0,
    duration_ms INT DEFAULT 0,
    error TEXT
);

CREATE INDEX idx_el_user_time ON evidence_logs(user_id, timestamp DESC);
CREATE INDEX idx_el_conversation ON evidence_logs(conversation_id);
```

### 20.4 Core Logic

```python
# core/evidence.py
class EvidenceLogger:
    """Structured logging for every agent action."""

    async def log(self, user_id: str, conversation_id: str, **kwargs):
        async with async_session() as db:
            db.add(EvidenceLog(
                user_id=UUID(user_id),
                conversation_id=UUID(conversation_id) if conversation_id else None,
                session_id=kwargs.get("session_id", ""),
                node=kwargs.get("node", ""),
                event_type=kwargs.get("event_type", ""),
                tool_name=kwargs.get("tool_name"),
                tool_input=kwargs.get("tool_input"),
                tool_output=kwargs.get("tool_output"),
                model_used=kwargs.get("model_used"),
                tokens_used=kwargs.get("tokens_used", 0),
                cost=kwargs.get("cost", 0),
                duration_ms=kwargs.get("duration_ms", 0),
                error=kwargs.get("error"),
            ))
            await db.commit()

evidence = EvidenceLogger()
```

### 20.5 UI/UX: Audit Trail

```
┌─────────────────────────────────────────────┐
│  📋 Audit Trail — "Kế hoạch đi Đà Nẵng"    │
│                                              │
│  10:15:03  🧠 Router → complex, planning     │
│  10:15:04  📝 Planner → 5 steps generated    │
│  10:15:05  ✅ User approved plan              │
│  10:15:06  🔧 calendar_list → 3 events found │
│  10:15:07  🔧 task_create → "Book vé"        │
│  10:15:08  🔧 task_create → "Đặt KS"        │
│  10:15:09  🔧 calendar_create → "Bay 15/3"   │
│  10:15:10  📊 Synthesize → response           │
│                                              │
│  💰 Total cost: $0.0003 | ⏱ 7.2s            │
└─────────────────────────────────────────────┘
```

**Files:** `core/evidence.py` (NEW), `db/models/system.py` (MODIFY), `api/v1/audit.py` (NEW), frontend audit page (NEW)
**Effort:** 1 day (backend + DB) + 1 day (frontend)

---

## 21. Module 10: Agent Supervision (🔧 Technical-only)

### 21.1 Problem

Long-running agent tasks (plan-and-execute, research) có thể hang, loop vô hạn, hoặc fail silently. Không có mechanism detect và recover.

### 21.2 Design

```
┌──────────────────────────────────────────┐
│       AGENT SUPERVISION                   │
│                                           │
│  Heartbeat:                               │
│  • Agent gửi heartbeat mỗi 10s           │
│  • Redis key: heartbeat:{session_id}      │
│  • TTL: 30s — miss 3 beats = unhealthy   │
│                                           │
│  Watchdog:                                │
│  • Monitor active sessions                │
│  • Kill sessions > max_duration (5 min)   │
│  • Alert on repeated failures             │
│                                           │
│  Recovery:                                │
│  • Resume from last checkpoint            │
│  • Notify user: "Đã gặp lỗi, thử lại"   │
│  • Dead-letter queue for failed tasks     │
└──────────────────────────────────────────┘
```

### 21.3 Implementation

```python
# core/supervision.py
MAX_SESSION_DURATION = 300  # 5 minutes
HEARTBEAT_INTERVAL = 10    # seconds
HEARTBEAT_TTL = 30         # 3 missed beats = dead

class AgentSupervisor:
    async def heartbeat(self, session_id: str):
        r = redis_pool.get()
        await r.setex(f"heartbeat:{session_id}", HEARTBEAT_TTL, "alive")

    async def is_healthy(self, session_id: str) -> bool:
        r = redis_pool.get()
        return await r.exists(f"heartbeat:{session_id}")

    async def check_timeout(self, session_id: str, started_at: float) -> bool:
        elapsed = time.time() - started_at
        if elapsed > MAX_SESSION_DURATION:
            await self._kill_session(session_id)
            return False
        return True

    async def _kill_session(self, session_id: str):
        r = redis_pool.get()
        await r.delete(f"heartbeat:{session_id}")
        await r.publish("session_killed", session_id)
```

**Files:** `core/supervision.py` (NEW), `agent/graph.py` (MODIFY — inject heartbeat in nodes)
**Effort:** 1 day

---

## 22. Module 11: Tool Permission Model (🎨 UI/UX Primary)

### 22.1 Problem

Tất cả 12 tools đều accessible cho mọi user. Không có cách disable tool, không có per-tool permission. MCP tools từ bên ngoài cũng không có sandbox.

### 22.2 Design

```
┌──────────────────────────────────────────┐
│       TOOL PERMISSIONS                    │
│                                           │
│  Per-user tool allowlist:                 │
│  • Default: all built-in tools enabled    │
│  • User can disable specific tools        │
│  • MCP tools: disabled by default         │
│                                           │
│  Permission levels:                       │
│  • read: query data (task_list, etc.)     │
│  • write: create/modify (task_create)     │
│  • delete: remove data                    │
│  • external: web_search, MCP tools        │
│                                           │
│  UI: Settings > Tools page                │
└──────────────────────────────────────────┘
```

### 22.3 Data Model

```sql
CREATE TABLE user_tool_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    tool_name VARCHAR(100) NOT NULL,
    enabled BOOLEAN DEFAULT true,
    permission_level VARCHAR(20) DEFAULT 'write', -- read, write, delete, external
    requires_approval BOOLEAN DEFAULT false,       -- trigger HITL for this tool
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, tool_name)
);
```

### 22.4 UI/UX: Settings > Tools

```
┌─────────────────────────────────────────────┐
│  ⚙️ Settings > Tools                        │
│                                              │
│  Built-in Tools                              │
│  ┌─────────────────────────────────────────┐│
│  │ ✅ task_create      [write] [approval ☐]││
│  │ ✅ task_list         [read]              ││
│  │ ✅ task_update       [write] [approval ☐]││
│  │ ✅ calendar_create   [write] [approval ☑]││
│  │ ✅ calendar_list     [read]              ││
│  │ ✅ memory_save       [write]             ││
│  │ ✅ memory_search     [read]              ││
│  │ ✅ web_search        [external]          ││
│  │ ☐  summarize_url    [external]          ││
│  │ ✅ expense_log       [write] [approval ☑]││
│  │ ✅ budget_check      [read]              ││
│  │ ✅ graph_search      [read]              ││
│  └─────────────────────────────────────────┘│
│                                              │
│  MCP Tools (external)                        │
│  ┌─────────────────────────────────────────┐│
│  │ ☐ github_create_issue  [external]       ││
│  │ ☐ notion_add_page      [external]       ││
│  └─────────────────────────────────────────┘│
└─────────────────────────────────────────────┘
```

### 22.5 Integration vào Agent Loop

```python
# agent/nodes/agent_loop.py — filter tools based on permissions
async def _get_allowed_tools(user_id: str, db: AsyncSession) -> list:
    perms = await db.execute(
        select(UserToolPermission).where(
            UserToolPermission.user_id == UUID(user_id),
            UserToolPermission.enabled.is_(True),
        )
    )
    allowed = {p.tool_name for p in perms.scalars()}
    if not allowed:  # No permissions set → default all enabled
        return all_tools
    return [t for t in all_tools if t.name in allowed]
```

**Files:** `db/models/system.py` (MODIFY), `api/v1/settings.py` (MODIFY), `agent/nodes/agent_loop.py` (MODIFY), frontend settings page (MODIFY)
**Effort:** 0.5 day (backend) + 0.5 day (frontend)

---

## 23. Updated Scorecard: JARVIS v3 Full (M1-M11) vs OpenClaw vs GoClaw

| Dimension | OpenClaw | GoClaw | JARVIS v2 | JARVIS v3 (M1-M5) | JARVIS v3 Full (M1-M11) |
|-----------|---------|--------|-----------|-------------------|------------------------|
| Intelligence | 5 | 6 | 4 | **9** | **9** |
| Personalization | 3 | 3 | 1 | **8** | **8** |
| Operational reliability | **8** | **9** | 4 | 4 | **8** |
| Security & permissions | 6 | **9** | 6 | 6 | **8** |
| Observability & audit | **7** | **8** | 2 | 2 | **8** |
| Human oversight | 5 | 6 | 0 | 0 | **7** |
| Cost efficiency | 3 | 4 | 7 | **8** | **8** |
| Tool ecosystem | **8** | **8** | 4 | 4 | 5 |
| Proactive capability | 1 | 2 | 5 | **7** | **7** |
| Vietnamese NLP | 0 | 0 | **8** | **9** | **9** |
| **Overall (avg)** | **4.6** | **5.5** | **3.6** | **5.5** | **7.7** |

---

## 24. Revised Implementation Plan (Full 11 Modules)

### Phase Overview

```
Phase A (Week 1):     M1 Smart Router + M6 Context Guard
Phase B (Week 1-2):   M2 Conversation Memory + M7 Checkpointing
Phase C (Week 2-3):   M4 Memory Consolidation + M9 Evidence Logging
Phase D (Week 3-4):   M3 Plan-and-Execute + M8 Human-in-the-Loop
Phase E (Week 4-5):   M5 User Preference Learning + M11 Tool Permissions
Phase F (Week 5):     M10 Supervision + Integration Testing + Polish
```

### Detailed Effort

| Phase | Modules | Backend (days) | Frontend (days) | DB Migration | Total |
|-------|---------|---------------|-----------------|-------------|-------|
| A | M1 + M6 | 2 | 0 | 0 | **2 days** |
| B | M2 + M7 | 2.5 | 0.5 | 1 migration | **3 days** |
| C | M4 + M9 | 2 | 1 | 1 migration | **3 days** |
| D | M3 + M8 | 3 | 1.5 | 0 | **4.5 days** |
| E | M5 + M11 | 2.5 | 1 | 1 migration | **3.5 days** |
| F | M10 + testing | 1.5 | 1 | 0 | **2.5 days** |
| **Total** | **11 modules** | **13.5** | **5** | **3 migrations** | **18.5 days** |

### Dependency Graph

```
M1 (Router) ──────────────────────────────┐
M6 (Context Guard) ──┐                    │
                      ├── M2 (Convo Memory)│
M7 (Checkpointing) ──┘         │          │
                                │          │
M9 (Evidence Logging) ─────────┤          │
                                │          │
M4 (Memory Consolidation) ─────┤          │
                                │          │
                      ┌─────────┘          │
                      │                    │
                      ▼                    ▼
              M3 (Plan-and-Execute) ── M8 (HITL)
                      │
                      ▼
              M5 (Preference Learning)
              M11 (Tool Permissions)
              M10 (Supervision)
```

### Frontend Components Needed

| Module | Component | Page | Priority |
|--------|-----------|------|----------|
| M3 | PlanProgressIndicator | Chat | P1 |
| M5 | PreferenceSettings | Settings > Preferences | P2 |
| M7 | ConversationResume | Conversations list | P1 |
| M8 | ApprovalDialog | Chat (modal) | P0 |
| M9 | AuditTrailPage | New page: /audit | P2 |
| M9 | ConversationDetail | Conversation > Detail | P2 |
| M11 | ToolPermissionsPage | Settings > Tools | P2 |

---

## 25. Config Changes (Full v3)

```python
# core/config.py — all new flags
SMART_ROUTER_ENABLED: bool = True
CONVO_MEMORY_ENABLED: bool = True
PLANNING_ENABLED: bool = True
MEMORY_CONSOLIDATION_ENABLED: bool = True
PREFERENCE_LEARNING_ENABLED: bool = True
CONTEXT_GUARD_ENABLED: bool = True
CHECKPOINTING_ENABLED: bool = True
HITL_ENABLED: bool = True
EVIDENCE_LOGGING_ENABLED: bool = True
SUPERVISION_ENABLED: bool = True
TOOL_PERMISSIONS_ENABLED: bool = True
```

---

## References

- [LangGraph Plan-and-Execute](https://blog.langchain.com/planning-agents/) — Plan-and-Solve, ReWOO, LLMCompiler patterns
- [LangMem SDK](https://blog.langchain.com/langmem-sdk-launch/) — Semantic, episodic, procedural memory + prompt optimizer
- [SummaryBufferMemory](https://genmind.ch/posts/Your-LLM-Has-Amnesia-A-Production-Guide-to-Memory-That-Actually-Works/) — Production guide to conversation memory
- [Arch-Router](https://emergentmind.com/topics/arch-router) — Preference-aligned LLM routing
- [Me-Agent](https://arxiv.org/html/2601.20162v1) — Two-level user habit learning for personalization
- [Context Window Management](https://arunbaby.com/ai-agents/0012-context-window-management/) — Sliding window, summarization, entity extraction strategies
- [OpenClaw Architecture](https://www.roborhythms.com/how-openclaw-ai-agent-works/) — Gateway, Agent Runner, Agentic Loop, Context Window Guard
- [Clawdbot Best Practices](https://skywork.ai/blog/clawdbot-agent-design-best-practices/) — Evidence logging, planner-executor, heartbeat, security
- [GoClaw Enterprise Platform](https://goclaw.sh/) — Multi-tenant isolation, 5-layer security
- [LangGraph Interrupt API](https://blog.langchain.dev/making-it-easier-to-build-human-in-the-loop-agents-with-interrupt/) — Human-in-the-loop pattern
- [LangGraph State Management](https://sparkco.ai/blog/mastering-langgraph-state-management-in-2025) — Checkpointing, persistent memory, parallel execution

Content was rephrased for compliance with licensing restrictions.
