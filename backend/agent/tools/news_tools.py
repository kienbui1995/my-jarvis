"""News tool — Vietnamese news from VnExpress RSS + LLM summary."""
import re
from xml.etree import ElementTree

import httpx
from langchain_core.tools import tool

from llm.gateway import get_llm

VNEXPRESS_RSS = "https://vnexpress.net/rss/tin-moi-nhat.rss"

CATEGORY_FEEDS = {
    "thời sự": "https://vnexpress.net/rss/thoi-su.rss",
    "thế giới": "https://vnexpress.net/rss/the-gioi.rss",
    "kinh doanh": "https://vnexpress.net/rss/kinh-doanh.rss",
    "công nghệ": "https://vnexpress.net/rss/khoa-hoc.rss",
    "thể thao": "https://vnexpress.net/rss/the-thao.rss",
    "giải trí": "https://vnexpress.net/rss/giai-tri.rss",
    "sức khỏe": "https://vnexpress.net/rss/suc-khoe.rss",
    "giáo dục": "https://vnexpress.net/rss/giao-duc.rss",
}


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def _parse_rss(xml_text: str, limit: int = 5) -> list[dict]:
    root = ElementTree.fromstring(xml_text)
    items = []
    for item in root.findall(".//item")[:limit]:
        title = item.findtext("title", "")
        desc = _strip_html(item.findtext("description", ""))
        link = item.findtext("link", "")
        pub = item.findtext("pubDate", "")
        items.append({"title": title, "desc": desc, "link": link, "pub": pub})
    return items


@tool
async def news_vn(
    category: str = "",
    summarize: bool = False,
) -> str:
    """Đọc tin tức Việt Nam từ VnExpress.

    Args:
        category: chuyên mục (thời sự, thế giới, kinh doanh, công nghệ,
                  thể thao, giải trí, sức khỏe, giáo dục). Để trống = tin mới nhất.
        summarize: True để tóm tắt bằng AI, False để liệt kê tiêu đề.
    """
    feed_url = CATEGORY_FEEDS.get(category.lower().strip(), VNEXPRESS_RSS)

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(feed_url, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code != 200:
            return f"Không thể lấy tin tức (HTTP {resp.status_code})"

    articles = _parse_rss(resp.text, limit=7)
    if not articles:
        return "Không có tin tức mới."

    if not summarize:
        label = f" ({category})" if category else ""
        lines = [f"📰 Tin tức VnExpress{label}:"]
        for i, a in enumerate(articles, 1):
            lines.append(f"{i}. {a['title']}")
        return "\n".join(lines)

    # Summarize with LLM
    content = "\n\n".join(
        f"**{a['title']}**: {a['desc']}" for a in articles
    )
    llm = get_llm("gemini-2.0-flash")
    resp = await llm.ainvoke(
        f"Tóm tắt các tin tức sau bằng tiếng Việt, ngắn gọn (tối đa 200 từ),"
        f" nêu điểm chính của từng tin:\n\n{content}"
    )
    return f"📰 Tóm tắt tin tức:\n\n{resp.content}"
