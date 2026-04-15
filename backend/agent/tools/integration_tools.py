"""M60+M61: Notion Sync + GitHub Integration via MCP gateway."""
from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedToolArg


@tool
async def notion_search(query: str, user_id: Annotated[str, InjectedToolArg]) -> str:
    """Tìm kiếm trong Notion — pages, databases, notes. Args: query."""
    from mcp.client import call_mcp_tool
    result = await call_mcp_tool(user_id, "notion", "search", {"query": query})
    return result or "Không tìm thấy. Kiểm tra Notion API key trong Settings > Integrations."


@tool
async def notion_create_page(title: str, content: str, user_id: Annotated[str, InjectedToolArg]) -> str:
    """Tạo trang mới trong Notion. Args: title, content (markdown)."""
    from mcp.client import call_mcp_tool
    result = await call_mcp_tool(user_id, "notion", "create_page", {"title": title, "content": content})
    return result or "Không tạo được. Kiểm tra Notion API key."


@tool
async def github_search(query: str, scope: str = "code", user_id: Annotated[str, InjectedToolArg] = "") -> str:
    """Tìm kiếm trên GitHub — code, issues, PRs. Args: query, scope (code|issues|pulls)."""
    from mcp.client import call_mcp_tool
    result = await call_mcp_tool(user_id, "github", "search", {"query": query, "scope": scope})
    return result or "Không tìm thấy. Kiểm tra GitHub token trong Settings > Integrations."


@tool
async def github_create_issue(repo: str, title: str, body: str, user_id: Annotated[str, InjectedToolArg] = "") -> str:
    """Tạo issue trên GitHub. Args: repo (owner/name), title, body."""
    from mcp.client import call_mcp_tool
    result = await call_mcp_tool(user_id, "github", "create_issue", {"repo": repo, "title": title, "body": body})
    return result or "Không tạo được issue. Kiểm tra GitHub token."
