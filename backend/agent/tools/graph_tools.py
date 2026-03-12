"""Knowledge graph search tool for the agent."""
from typing import Annotated
from langchain_core.tools import tool, InjectedToolArg

from db.session import async_session
from memory.knowledge_graph import search_graph


@tool
async def graph_search(query: str, user_id: Annotated[str, InjectedToolArg] = "") -> str:
    """Tìm kiếm trong knowledge graph của user — trả về entities và relationships liên quan.
    Dùng khi cần tìm thông tin về người, dự án, tổ chức mà user đã đề cập trước đó."""
    if not user_id:
        return "Cần user_id để tìm kiếm knowledge graph."
    async with async_session() as db:
        results = await search_graph(user_id, query, db)
    if not results:
        return "Không tìm thấy thông tin liên quan trong knowledge graph."
    lines = [f"- {r['name']} ({r['type']}): {r.get('description', '')}" for r in results]
    return "Knowledge graph:\n" + "\n".join(lines)
