"""Tests for agent modules: registry, state, evaluate, delegate, response, graph routing."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from langchain_core.messages import AIMessage, HumanMessage


# === Registry ===

class TestRegistry:
    def test_all_specialists_defined(self):
        from agent.registry import SPECIALISTS
        assert set(SPECIALISTS.keys()) == {"task", "calendar", "research", "finance", "memory"}

    def test_specialist_has_required_fields(self):
        from agent.registry import SPECIALISTS
        for name, spec in SPECIALISTS.items():
            assert "model" in spec, f"{name} missing model"
            assert "tools" in spec, f"{name} missing tools"
            assert "system_prompt" in spec, f"{name} missing system_prompt"

    def test_specialist_tools_exist(self):
        from agent.registry import SPECIALISTS
        from agent.tools import all_tools
        tool_names = {t.name for t in all_tools}
        for name, spec in SPECIALISTS.items():
            for tool in spec["tools"]:
                assert tool in tool_names, f"Specialist {name} references unknown tool: {tool}"

    def test_keywords_cover_all_specialists(self):
        from agent.registry import SPECIALISTS, SPECIALIST_KEYWORDS
        assert set(SPECIALIST_KEYWORDS.keys()) == set(SPECIALISTS.keys())

    def test_keyword_detection(self):
        from agent.nodes.router import _detect_specialist_keyword as _detect_specialist
        with patch("agent.nodes.router.settings") as mock_settings:
            mock_settings.MULTI_AGENT_ENABLED = True
            assert _detect_specialist("tạo task mới cho tôi") == "task"
            assert _detect_specialist("nghiên cứu về AI") == "research"
            assert _detect_specialist("ghi chi tiêu 50k") == "finance"
            assert _detect_specialist("xem lịch hôm nay") == "calendar"
            assert _detect_specialist("tôi đã nói gì trước đó") == "memory"

    def test_no_specialist_for_general_chat(self):
        from agent.nodes.router import _detect_specialist_keyword as _detect_specialist
        with patch("agent.nodes.router.settings") as mock_settings:
            mock_settings.MULTI_AGENT_ENABLED = True
            assert _detect_specialist("xin chào bạn") == ""

    def test_disabled_returns_empty(self):
        from agent.nodes.router import _detect_specialist_keyword as _detect_specialist
        with patch("agent.nodes.router.settings") as mock_settings:
            mock_settings.MULTI_AGENT_ENABLED = False
            assert _detect_specialist("tạo task mới") == ""


# === State ===

class TestState:
    def test_state_has_delegation_fields(self):
        from agent.state import AgentState
        hints = AgentState.__annotations__
        assert "delegation_target" in hints
        assert "delegation_result" in hints
        assert "delegation_count" in hints

    def test_state_has_core_fields(self):
        from agent.state import AgentState
        hints = AgentState.__annotations__
        for field in ["user_id", "intent", "complexity", "selected_model", "injection_score", "retry_count"]:
            assert field in hints, f"Missing field: {field}"


# === Evaluate ===

class TestEvaluate:
    @pytest.mark.asyncio
    async def test_skip_short_response(self):
        from agent.nodes.evaluate import evaluate_node
        state = {"messages": [HumanMessage(content="hi"), AIMessage(content="ok")], "retry_count": 0}
        result = await evaluate_node(state)
        assert result == {}  # skipped, len < 20

    @pytest.mark.asyncio
    async def test_skip_after_retry(self):
        from agent.nodes.evaluate import evaluate_node
        state = {"messages": [HumanMessage(content="test"), AIMessage(content="a" * 50)], "retry_count": 1}
        result = await evaluate_node(state)
        assert result == {}  # already retried

    @pytest.mark.asyncio
    async def test_pass_returns_empty(self):
        from agent.nodes.evaluate import evaluate_node
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=MagicMock(content='{"pass": true, "reason": "ok"}'))
        with patch("agent.nodes.evaluate.get_llm", return_value=mock_llm):
            state = {"messages": [HumanMessage(content="test question"), AIMessage(content="a detailed answer here")], "retry_count": 0}
            result = await evaluate_node(state)
            assert result == {}

    @pytest.mark.asyncio
    async def test_fail_increments_retry(self):
        from agent.nodes.evaluate import evaluate_node
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=MagicMock(content='{"pass": false, "reason": "bad"}'))
        with patch("agent.nodes.evaluate.get_llm", return_value=mock_llm):
            state = {"messages": [HumanMessage(content="test"), AIMessage(content="a bad response here!!")], "retry_count": 0, "complexity": "complex"}
            result = await evaluate_node(state)
            assert result["retry_count"] == 1


# === Response ===

class TestResponse:
    @pytest.mark.asyncio
    async def test_uses_delegation_result(self):
        from agent.nodes.response import response_node
        state = {"messages": [AIMessage(content="agent response")], "delegation_result": "specialist response"}
        result = await response_node(state)
        assert result["final_response"] == "specialist response"

    @pytest.mark.asyncio
    async def test_uses_last_message_without_delegation(self):
        from agent.nodes.response import response_node
        state = {"messages": [AIMessage(content="agent response")], "delegation_result": ""}
        result = await response_node(state)
        assert result["final_response"] == "agent response"

    @pytest.mark.asyncio
    async def test_empty_messages(self):
        from agent.nodes.response import response_node
        state = {"messages": [], "delegation_result": ""}
        result = await response_node(state)
        assert result["final_response"] == ""


# === Delegate ===

class TestDelegate:
    @pytest.mark.asyncio
    async def test_unknown_specialist_returns_empty(self):
        from agent.nodes.delegate import delegate_node
        state = {"delegation_target": "nonexistent", "messages": [HumanMessage(content="test")]}
        result = await delegate_node(state)
        assert result["delegation_result"] == ""

    @pytest.mark.asyncio
    async def test_specialist_returns_text(self):
        from agent.nodes.delegate import delegate_node
        mock_llm = MagicMock()
        mock_resp = MagicMock()
        mock_resp.content = "Đã tạo task cho bạn"
        mock_resp.tool_calls = []
        mock_llm.bind_tools = MagicMock(return_value=mock_llm)
        mock_llm.ainvoke = AsyncMock(return_value=mock_resp)

        with patch("agent.nodes.delegate.get_llm", return_value=mock_llm):
            state = {"delegation_target": "task", "messages": [HumanMessage(content="tạo task mới")], "delegation_count": 0}
            result = await delegate_node(state)
            assert result["delegation_result"] == "Đã tạo task cho bạn"
            assert result["delegation_count"] == 1

    @pytest.mark.asyncio
    async def test_specialist_failure_returns_empty(self):
        from agent.nodes.delegate import delegate_node
        with patch("agent.nodes.delegate.get_llm", side_effect=Exception("LLM down")):
            state = {"delegation_target": "task", "messages": [HumanMessage(content="test")], "delegation_count": 0}
            result = await delegate_node(state)
            assert result["delegation_result"] == ""


# === Graph Routing ===

class TestGraphRouting:
    def test_should_continue_to_tools(self):
        from agent.graph import should_continue
        msg = MagicMock()
        msg.tool_calls = [{"name": "test"}]
        assert should_continue({"messages": [msg]}) == "tools"

    def test_should_continue_to_respond(self):
        from agent.graph import should_continue
        msg = MagicMock()
        msg.tool_calls = []
        assert should_continue({"messages": [msg]}) == "respond"

    def test_route_to_delegate(self):
        from agent.graph import route_after_router
        assert route_after_router({"delegation_target": "research"}) == "delegate"

    def test_route_to_agent_loop(self):
        from agent.graph import route_after_router
        assert route_after_router({"delegation_target": ""}) == "agent_loop"

    def test_delegate_success_to_respond(self):
        from agent.graph import route_after_delegate
        assert route_after_delegate({"delegation_result": "some result"}) == "respond"

    def test_delegate_failure_to_agent_loop(self):
        from agent.graph import route_after_delegate
        assert route_after_delegate({"delegation_result": ""}) == "agent_loop"

    def test_should_retry_on_first_fail(self):
        from agent.graph import should_retry
        assert should_retry({"retry_count": 1}) == "agent_loop"

    def test_no_retry_after_max(self):
        from agent.graph import should_retry
        assert should_retry({"retry_count": 2}) == "post_process"
