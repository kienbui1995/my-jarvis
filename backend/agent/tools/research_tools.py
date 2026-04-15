"""M48 Deep Research — multi-step search → verify → cross-check → cite.

Instead of a single web_search, this tool:
1. Plans 3-5 diverse search queries from the research question
2. Executes searches in parallel
3. Cross-checks facts across sources
4. Synthesizes a structured report with citations + confidence scores
"""
import asyncio
import json
import logging
from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedToolArg

from llm.gateway import get_llm

logger = logging.getLogger(__name__)

PLAN_QUERIES_PROMPT = """Bạn là research planner. Tạo 3-5 search queries đa dạng để nghiên cứu chủ đề.

Chủ đề: "{topic}"

Trả về JSON (KHÔNG markdown):
{{"queries": ["query1", "query2", "query3"], "aspects": ["khía cạnh 1", "khía cạnh 2"]}}

Rules:
- Queries phải đa dạng góc nhìn (definition, statistics, trends, opinions, comparisons)
- Ưu tiên tiếng Anh cho topics quốc tế, tiếng Việt cho topics VN
- 3 queries tối thiểu, 5 tối đa"""

VERIFY_PROMPT = """Bạn là fact checker. Phân tích các kết quả tìm kiếm và đánh giá độ tin cậy.

Chủ đề nghiên cứu: "{topic}"

Kết quả tìm kiếm:
{search_results}

Trả về JSON (KHÔNG markdown):
{{"facts": [{{"claim": "fact", "confidence": 0.0-1.0, "sources": [1, 2], "conflicts": "mâu thuẫn nếu có"}}], "gaps": ["thông tin còn thiếu"]}}

Rules:
- confidence 0.9+: nhiều nguồn xác nhận
- confidence 0.5-0.8: 1 nguồn, chưa verify
- confidence <0.5: mâu thuẫn hoặc không rõ ràng
- Ghi nhận conflicts giữa các nguồn"""

SYNTHESIZE_PROMPT = """Bạn là research synthesizer. Tổng hợp thành báo cáo nghiên cứu.

Chủ đề: "{topic}"
Facts đã verify: {verified_facts}
Gaps: {gaps}

Viết báo cáo ngắn gọn bằng tiếng Việt:
- Tóm tắt chính (3-5 bullet points)
- Số liệu quan trọng (nếu có)
- Mâu thuẫn/tranh cãi (nếu có)
- Kết luận + confidence tổng thể
- Ghi chú: thông tin còn thiếu

Format: markdown, ngắn gọn, có citations [1], [2]..."""


async def _parallel_search(queries: list[str]) -> list[dict]:
    """Execute multiple web searches in parallel."""
    from agent.tools.web_tools import web_search

    async def _search(i: int, q: str) -> dict:
        try:
            result = await web_search.ainvoke({"query": q})
            return {"index": i + 1, "query": q, "results": result}
        except Exception as e:
            return {"index": i + 1, "query": q, "results": f"Error: {e}"}

    tasks = [_search(i, q) for i, q in enumerate(queries)]
    return await asyncio.gather(*tasks)


@tool
async def deep_research(
    topic: str,
    user_id: Annotated[str, InjectedToolArg],
) -> str:
    """Nghiên cứu sâu một chủ đề: tìm kiếm đa nguồn, cross-check, tổng hợp với citations. Dùng khi cần phân tích kỹ, không phải câu hỏi đơn giản."""
    llm = get_llm("gemini-2.0-flash")

    # Step 1: Plan search queries
    try:
        resp = await llm.ainvoke(PLAN_QUERIES_PROMPT.format(topic=topic))
        plan = json.loads(resp.content.strip().removeprefix("```json").removesuffix("```").strip())
        queries = plan.get("queries", [topic])[:5]
    except Exception:
        queries = [topic, f"{topic} statistics 2024 2025", f"{topic} Vietnam"]

    # Step 2: Execute parallel searches
    search_results = await _parallel_search(queries)
    results_str = "\n\n".join(
        f"[Nguồn {r['index']}] Query: {r['query']}\n{r['results']}"
        for r in search_results
    )

    # Step 3: Verify + cross-check
    try:
        resp = await llm.ainvoke(VERIFY_PROMPT.format(topic=topic, search_results=results_str))
        verified = json.loads(resp.content.strip().removeprefix("```json").removesuffix("```").strip())
    except Exception:
        verified = {"facts": [], "gaps": ["Không thể verify — trả về raw results"]}

    # Step 4: Synthesize report
    resp = await llm.ainvoke(SYNTHESIZE_PROMPT.format(
        topic=topic,
        verified_facts=json.dumps(verified.get("facts", []), ensure_ascii=False),
        gaps=json.dumps(verified.get("gaps", []), ensure_ascii=False),
    ))

    return resp.content
