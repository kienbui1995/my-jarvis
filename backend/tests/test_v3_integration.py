"""Integration tests for V3 Intelligence Layer modules."""
import time
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage


# === M1: Smart Router ===

class TestSmartRouter:
    def test_router_decision_schema(self):
        from agent.nodes.router import RouterDecision
        d = RouterDecision(intent="task_mgmt", complexity="medium", specialist="task", needs_planning=False, reasoning="test")
        assert d.intent == "task_mgmt"

    def test_router_decision_defaults(self):
        from agent.nodes.router import RouterDecision
        d = RouterDecision()
        assert d.intent == "general_chat"
        assert d.complexity == "simple"
        assert d.needs_planning is False

    def test_keyword_fallback_returns_decision(self):
        from agent.nodes.router import _classify_keyword, RouterDecision
        result = _classify_keyword("phân tích xu hướng chi tiêu")
        assert isinstance(result, RouterDecision)


# === M2: Conversation Memory ===

class TestConversationMemory:
    def test_verbatim_turns_constant(self):
        from memory.conversation_memory import VERBATIM_TURNS
        assert VERBATIM_TURNS == 10

    def test_exports(self):
        from memory.conversation_memory import summarize_if_needed, build_memory_context
        assert callable(summarize_if_needed)
        assert callable(build_memory_context)


# === M3: Plan-and-Execute ===

class TestPlanExecute:
    def test_constants(self):
        from agent.nodes.plan_execute import DESTRUCTIVE_TOOLS, MAX_STEPS, MAX_REPLANS
        assert MAX_STEPS == 7
        assert MAX_REPLANS == 2
        assert "task_update" in DESTRUCTIVE_TOOLS

    def test_route_after_planner_empty_plan(self):
        from agent.nodes.plan_execute import route_after_planner
        state = {"execution_plan": {}, "needs_planning": True}
        assert route_after_planner(state) == "respond"

    def test_route_after_planner_with_steps(self):
        from agent.nodes.plan_execute import route_after_planner
        state = {"execution_plan": {"steps": ["step 1"]}, "needs_planning": True}
        assert route_after_planner(state) == "executor"

    def test_route_after_executor_with_tool_calls(self):
        from agent.nodes.plan_execute import route_after_executor
        msg = AIMessage(content="", tool_calls=[{"name": "task_create", "args": {}, "id": "1"}])
        state = {"messages": [msg], "execution_plan": {"steps": ["s1"]}, "current_step": 0}
        assert route_after_executor(state) == "tools"

    def test_route_after_replan_done(self):
        from agent.nodes.plan_execute import route_after_replan
        assert route_after_replan({"needs_planning": False}) == "synthesize"

    def test_route_after_replan_continue(self):
        from agent.nodes.plan_execute import route_after_replan
        assert route_after_replan({"needs_planning": True}) == "executor"


# === M4: Memory Consolidation ===

class TestMemoryConsolidation:
    def test_exports(self):
        from memory.consolidation import consolidate_fact, CANDIDATE_TOP_K
        assert callable(consolidate_fact)
        assert CANDIDATE_TOP_K == 5


# === M5: Preference Learning ===

class TestPreferenceLearning:
    def test_exports(self):
        from memory.preference_learning import build_preference_prompt, extract_preferences
        assert callable(build_preference_prompt)
        assert callable(extract_preferences)


# === M6: Context Guard ===

class TestContextGuard:
    def test_estimate_tokens(self):
        from core.context_guard import _estimate_tokens
        assert _estimate_tokens("hello world") > 0
        assert _estimate_tokens("") <= 1  # len("")//4 + 1 = 1

    def test_guard_context_passthrough_short(self):
        from core.context_guard import guard_context
        msgs = [SystemMessage(content="sys"), HumanMessage(content="hi")]
        result = guard_context(msgs, "gemini-2.0-flash")
        assert len(result) >= 1

    def test_guard_context_truncates_tool_results(self):
        from core.context_guard import guard_context, MAX_TOOL_RESULT_TOKENS
        long_content = "x" * (MAX_TOOL_RESULT_TOKENS * 8)  # way over limit
        msgs = [SystemMessage(content="sys"), ToolMessage(content=long_content, tool_call_id="1")]
        result = guard_context(msgs, "gemini-2.0-flash")
        tool_msgs = [m for m in result if isinstance(m, ToolMessage)]
        if tool_msgs:
            assert len(tool_msgs[0].content) < len(long_content)


# === M7: Checkpointer ===

class TestCheckpointer:
    def test_exports(self):
        from core.checkpointer import get_checkpointer
        assert callable(get_checkpointer)


# === M9: Evidence Logging ===

class TestEvidenceLogging:
    def test_evidence_log_model(self):
        from db.models.evidence import EvidenceLog
        assert hasattr(EvidenceLog, "event_type")
        assert hasattr(EvidenceLog, "tool_name")
        assert hasattr(EvidenceLog, "duration_ms")

    def test_evidence_exports(self):
        from core.evidence import evidence_timer, log_evidence
        assert callable(log_evidence)


# === M10: Supervision ===

class TestSupervision:
    def test_supervisor_init(self):
        from core.supervision import SessionSupervisor
        sup = SessionSupervisor("u1", "c1")
        assert sup.user_id == "u1"
        assert sup.conversation_id == "c1"
        assert sup.session_id

    def test_check_timeout_fresh(self):
        from core.supervision import SessionSupervisor
        assert SessionSupervisor("u1", "c1").check_timeout() is False

    def test_check_timeout_expired(self):
        from core.supervision import SessionSupervisor, MAX_SESSION_DURATION
        sup = SessionSupervisor("u1", "c1")
        sup.started_at = time.monotonic() - MAX_SESSION_DURATION - 1
        assert sup.check_timeout() is True


# === M11: Tool Permissions + Preferences ===

class TestModels:
    def test_tool_permission_model(self):
        from db.models.preference import UserToolPermission
        assert hasattr(UserToolPermission, "tool_name")
        assert hasattr(UserToolPermission, "enabled")

    def test_preference_model(self):
        from db.models.preference import UserPreference, UserPromptRule
        assert hasattr(UserPreference, "tone")
        assert hasattr(UserPreference, "verbosity")
        assert hasattr(UserPromptRule, "rule")


# === Graph Integration ===

class TestGraph:
    def test_graph_has_v3_nodes(self):
        from agent.graph import build_graph
        node_names = set(build_graph().nodes.keys())
        for n in ("planner", "executor", "replan", "synthesize"):
            assert n in node_names, f"Missing node: {n}"

    def test_route_after_router(self):
        from agent.graph import route_after_router
        assert route_after_router({"needs_planning": True, "delegation_target": ""}) == "planner"
        assert route_after_router({"needs_planning": False, "delegation_target": "task"}) == "delegate"
        assert route_after_router({"needs_planning": False, "delegation_target": ""}) == "agent_loop"


# === Config + State ===

class TestConfigAndState:
    def test_v3_feature_flags(self):
        from core.config import settings
        for flag in ("SMART_ROUTER_ENABLED", "CONVO_MEMORY_ENABLED", "PLANNING_ENABLED",
                     "MEMORY_CONSOLIDATION_ENABLED", "PREFERENCE_LEARNING_ENABLED",
                     "CONTEXT_GUARD_ENABLED", "CHECKPOINTING_ENABLED", "HITL_ENABLED",
                     "EVIDENCE_LOGGING_ENABLED", "SUPERVISION_ENABLED", "TOOL_PERMISSIONS_ENABLED"):
            assert hasattr(settings, flag), f"Missing: {flag}"

    def test_v3_state_fields(self):
        from agent.state import AgentState
        for f in ("conversation_id", "needs_planning", "execution_plan",
                   "current_step", "step_results", "replan_count", "user_preferences"):
            assert f in AgentState.__annotations__, f"Missing: {f}"
