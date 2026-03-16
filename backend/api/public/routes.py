"""Public API routes — external developer access."""
from fastapi import APIRouter, Depends, HTTPException
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from agent.graph import get_jarvis_graph
from agent.tools import all_tools
from api.public.auth import get_api_key_user

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


class ToolInvokeRequest(BaseModel):
    args: dict


@router.post("/chat")
async def public_chat(
    body: ChatRequest,
    user_id: str = Depends(get_api_key_user),
):
    """Send a message to JARVIS. Returns full response."""
    if not body.message.strip():
        raise HTTPException(400, "Empty message")

    graph = await get_jarvis_graph()
    config = {"configurable": {"thread_id": body.conversation_id or f"api-{user_id}"}}
    result = await graph.ainvoke({
        "messages": [HumanMessage(content=body.message)],
        "user_id": user_id,
        "user_tier": "pro",
        "channel": "api",
        "conversation_id": body.conversation_id or "",
    }, config=config)

    return {
        "response": result.get("final_response", ""),
        "model": result.get("selected_model", ""),
    }


@router.get("/tools")
async def list_tools(user_id: str = Depends(get_api_key_user)):
    """List all available tools."""
    return {
        "tools": [
            {"name": t.name, "description": t.description}
            for t in all_tools
        ]
    }


@router.post("/tools/{tool_name}/invoke")
async def invoke_tool(
    tool_name: str,
    body: ToolInvokeRequest,
    user_id: str = Depends(get_api_key_user),
):
    """Invoke a specific tool directly."""
    tool = next((t for t in all_tools if t.name == tool_name), None)
    if not tool:
        raise HTTPException(404, f"Tool not found: {tool_name}")

    args = {**body.args, "user_id": user_id}
    try:
        result = await tool.ainvoke(args)
        return {"result": result}
    except Exception as e:
        raise HTTPException(500, f"Tool error: {e}")


@router.get("/memory/search")
async def search_memory(
    query: str,
    limit: int = 5,
    user_id: str = Depends(get_api_key_user),
):
    """Search user's memory."""
    from agent.tools.memory_tools import memory_search
    result = await memory_search.ainvoke({
        "query": query, "limit": limit, "user_id": user_id,
    })
    return {"result": result}
