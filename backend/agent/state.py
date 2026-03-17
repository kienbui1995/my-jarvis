"""Agent state schema — shared across all LangGraph nodes."""
from langgraph.graph import MessagesState


class AgentState(MessagesState):
    """Extended MessagesState for MY JARVIS agent pipeline.

    Inherits `messages: list[BaseMessage]` from MessagesState.
    """
    # --- v2 fields ---
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

    # --- v3 fields ---
    mcp_tools: list = []
    conversation_id: str = ""
    needs_planning: bool = False
    execution_plan: dict = {}
    current_step: int = 0
    step_results: list[str] = []
    replan_count: int = 0
    user_preferences: str = ""
