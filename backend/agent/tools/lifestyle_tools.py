"""M62: Spotify/Music + M63: Restaurant Finder + M65: Traffic & Navigation."""
from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedToolArg


@tool
async def spotify_control(action: str, query: str = "", user_id: Annotated[str, InjectedToolArg] = "") -> str:
    """Điều khiển Spotify — play, pause, next, search. Args: action (play|pause|next|search|recommend), query."""
    import httpx
    from core.config import settings

    if not settings.SPOTIFY_CLIENT_ID:
        return "⚠️ Chưa cấu hình Spotify. Thêm SPOTIFY_CLIENT_ID/SECRET trong Settings."

    # Get user's Spotify access token from DB
    from db.session import async_session
    from db.models import UserPreference
    from sqlalchemy import select
    from uuid import UUID

    async with async_session() as db:
        pref = (await db.execute(
            select(UserPreference).where(UserPreference.user_id == UUID(user_id), UserPreference.key == "spotify_token")
        )).scalar_one_or_none()

    if not pref:
        return "⚠️ Chưa kết nối Spotify. Vào Settings > Integrations > Spotify để đăng nhập."

    token = pref.value
    headers = {"Authorization": f"Bearer {token}"}
    base = "https://api.spotify.com/v1"

    async with httpx.AsyncClient() as client:
        if action == "search":
            r = await client.get(f"{base}/search", params={"q": query, "type": "track", "limit": 5}, headers=headers)
            if r.status_code != 200:
                return "Lỗi Spotify API. Token có thể hết hạn."
            tracks = r.json().get("tracks", {}).get("items", [])
            return "\n".join(f"🎵 {t['name']} — {t['artists'][0]['name']}" for t in tracks) or "Không tìm thấy."
        elif action == "play":
            if query:
                r = await client.get(f"{base}/search", params={"q": query, "type": "track", "limit": 1}, headers=headers)
                tracks = r.json().get("tracks", {}).get("items", [])
                if tracks:
                    await client.put(f"{base}/me/player/play", json={"uris": [tracks[0]["uri"]]}, headers=headers)
                    return f"▶️ Đang phát: {tracks[0]['name']} — {tracks[0]['artists'][0]['name']}"
            await client.put(f"{base}/me/player/play", headers=headers)
            return "▶️ Đã resume phát nhạc."
        elif action == "pause":
            await client.put(f"{base}/me/player/pause", headers=headers)
            return "⏸️ Đã tạm dừng."
        elif action == "next":
            await client.post(f"{base}/me/player/next", headers=headers)
            return "⏭️ Bài tiếp theo."
        elif action == "recommend":
            r = await client.get(f"{base}/me/top/tracks", params={"limit": 5}, headers=headers)
            tracks = r.json().get("items", [])
            return "🎶 Gợi ý:\n" + "\n".join(f"  • {t['name']} — {t['artists'][0]['name']}" for t in tracks)
    return f"Action '{action}' không hỗ trợ. Dùng: play, pause, next, search, recommend."


@tool
async def find_restaurant(query: str, location: str = "", user_id: Annotated[str, InjectedToolArg] = "") -> str:
    """Tìm nhà hàng/quán ăn gần đây. Args: query (ví dụ: 'phở ngon'), location (optional: 'quận 1')."""
    import httpx
    from core.config import settings

    if not settings.GOOGLE_PLACES_API_KEY:
        # Fallback to LLM recommendation
        from llm.gateway import get_llm
        llm = get_llm("gemini-2.0-flash")
        resp = await llm.ainvoke(f"Gợi ý nhà hàng/quán ăn: {query}{f' ở {location}' if location else ''} tại Việt Nam. Top 5, kèm giá trung bình.")
        return resp.content

    async with httpx.AsyncClient() as client:
        params = {"query": f"{query} restaurant {location}", "key": settings.GOOGLE_PLACES_API_KEY, "language": "vi"}
        r = await client.get("https://maps.googleapis.com/maps/api/place/textsearch/json", params=params)
        places = r.json().get("results", [])[:5]

    if not places:
        return "Không tìm thấy nhà hàng nào."
    return "\n".join(
        f"🍽️ {p['name']} — ⭐ {p.get('rating', '?')} ({p.get('user_ratings_total', 0)} reviews)\n   📍 {p.get('formatted_address', '')}"
        for p in places
    )


@tool
async def get_directions(origin: str, destination: str, user_id: Annotated[str, InjectedToolArg] = "") -> str:
    """Chỉ đường + thời gian di chuyển. Args: origin, destination."""
    import httpx
    from core.config import settings

    if not settings.GOOGLE_MAPS_API_KEY:
        from llm.gateway import get_llm
        llm = get_llm("gemini-2.0-flash")
        resp = await llm.ainvoke(f"Chỉ đường từ {origin} đến {destination} tại Việt Nam. Ước tính thời gian, khoảng cách, gợi ý phương tiện.")
        return resp.content

    async with httpx.AsyncClient() as client:
        params = {"origin": origin, "destination": destination, "key": settings.GOOGLE_MAPS_API_KEY, "language": "vi", "alternatives": "true"}
        r = await client.get("https://maps.googleapis.com/maps/api/directions/json", params=params)
        routes = r.json().get("routes", [])

    if not routes:
        return "Không tìm được đường đi."
    lines = []
    for i, route in enumerate(routes[:3]):
        leg = route["legs"][0]
        lines.append(f"🛣️ Tuyến {i+1}: {leg['distance']['text']} — {leg['duration']['text']}")
        if "duration_in_traffic" in leg:
            lines.append(f"   🚗 Có kẹt xe: {leg['duration_in_traffic']['text']}")
    return "\n".join(lines)
