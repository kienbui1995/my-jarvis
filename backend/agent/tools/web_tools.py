"""Web tools — real web search + URL summarization via httpx + LLM."""
import httpx
from langchain_core.tools import tool

from llm.gateway import get_llm

SEARCH_URL = "https://html.duckduckgo.com/html/"


@tool
async def web_search(query: str) -> str:
    """Tìm kiếm thông tin trên web. Args: query."""
    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        resp = await client.post(SEARCH_URL, data={"q": query}, headers={"User-Agent": "Mozilla/5.0"})
        # Extract text snippets from DuckDuckGo HTML results
        from html.parser import HTMLParser

        class SnippetParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.results, self._in_result, self._buf = [], False, ""
            def handle_starttag(self, tag, attrs):
                if tag == "a" and any(c == "result__snippet" for _, c in attrs):
                    self._in_result = True
            def handle_data(self, data):
                if self._in_result:
                    self._buf += data
            def handle_endtag(self, tag):
                if self._in_result and tag == "a":
                    self.results.append(self._buf.strip())
                    self._buf, self._in_result = "", False

        parser = SnippetParser()
        parser.feed(resp.text)
        snippets = parser.results[:5]
        if not snippets:
            return f"Không tìm thấy kết quả cho: {query}"
        return "\n".join(f"{i+1}. {s}" for i, s in enumerate(snippets))


@tool
async def summarize_url(url: str) -> str:
    """Tóm tắt nội dung một URL. Args: url."""
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        # Strip HTML tags, take first 3000 chars
        import re
        text = re.sub(r"<[^>]+>", " ", resp.text)
        text = re.sub(r"\s+", " ", text).strip()[:3000]

    if not text:
        return "Không thể đọc nội dung URL."

    llm = get_llm("gemini-2.0-flash")
    resp = await llm.ainvoke(f"Tóm tắt ngắn gọn bằng tiếng Việt (tối đa 200 từ):\n\n{text}")
    return resp.content
