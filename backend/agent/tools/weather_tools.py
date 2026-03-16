"""Weather tool — Vietnamese cities via OpenWeather API."""
import httpx
from langchain_core.tools import tool

from core.config import settings

# Map common Vietnamese city names to OpenWeather query format
_CITY_ALIASES = {
    "sg": "Ho Chi Minh City,VN", "sài gòn": "Ho Chi Minh City,VN",
    "saigon": "Ho Chi Minh City,VN", "hcm": "Ho Chi Minh City,VN",
    "tp hcm": "Ho Chi Minh City,VN", "hồ chí minh": "Ho Chi Minh City,VN",
    "hn": "Hanoi,VN", "hà nội": "Hanoi,VN", "hanoi": "Hanoi,VN",
    "đà nẵng": "Da Nang,VN", "da nang": "Da Nang,VN",
    "huế": "Hue,VN", "hue": "Hue,VN",
    "nha trang": "Nha Trang,VN", "đà lạt": "Da Lat,VN",
    "cần thơ": "Can Tho,VN", "hải phòng": "Hai Phong,VN",
    "vũng tàu": "Vung Tau,VN", "quy nhơn": "Quy Nhon,VN",
    "biên hòa": "Bien Hoa,VN", "buôn ma thuột": "Buon Ma Thuot,VN",
}

_WEATHER_VI = {
    "clear sky": "trời quang", "few clouds": "ít mây",
    "scattered clouds": "mây rải rác", "broken clouds": "nhiều mây",
    "overcast clouds": "u ám", "light rain": "mưa nhỏ",
    "moderate rain": "mưa vừa", "heavy intensity rain": "mưa lớn",
    "thunderstorm": "giông bão", "mist": "sương mù",
    "haze": "sương mờ", "fog": "sương mù dày",
}


def _resolve_city(city: str) -> str:
    lower = city.lower().strip()
    return _CITY_ALIASES.get(lower, f"{city},VN")


@tool
async def weather_vn(city: str) -> str:
    """Xem thời tiết hiện tại ở Việt Nam. Args: city (tên thành phố)."""
    if not settings.OPENWEATHER_API_KEY:
        return "Chưa cấu hình OpenWeather API key."

    query = _resolve_city(city)
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": query, "appid": settings.OPENWEATHER_API_KEY,
        "units": "metric", "lang": "vi",
    }

    # Check Redis cache first (15min TTL)
    import core.redis as redis_pool
    cache_key = f"weather:{query}"
    try:
        r = redis_pool.get()
        cached = await r.get(cache_key)
        if cached:
            import json
            data = json.loads(cached)
            name = data.get("name", city)
            main = data.get("main", {})
            weather = data.get("weather", [{}])[0]
            wind = data.get("wind", {})
            desc_en = weather.get("description", "")
            desc = _WEATHER_VI.get(desc_en, weather.get("description", ""))
            temp = main.get("temp", "?")
            feels = main.get("feels_like", "?")
            humidity = main.get("humidity", "?")
            wind_speed = wind.get("speed", "?")
            return (
                f"🌤 Thời tiết {name}: {desc}\n"
                f"🌡 Nhiệt độ: {temp}°C (cảm giác {feels}°C)\n"
                f"💧 Độ ẩm: {humidity}%\n"
                f"💨 Gió: {wind_speed} m/s"
            )
    except Exception:
        pass

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params=params)
        if resp.status_code == 404:
            return f"Không tìm thấy thành phố: {city}"
        if resp.status_code != 200:
            return f"Lỗi API thời tiết (HTTP {resp.status_code})"
        data = resp.json()

    # Cache for 15 minutes
    try:
        import json
        await r.setex(cache_key, 900, json.dumps(data))
    except Exception:
        pass

    name = data.get("name", city)
    main = data.get("main", {})
    weather = data.get("weather", [{}])[0]
    wind = data.get("wind", {})

    desc_en = weather.get("description", "")
    desc = _WEATHER_VI.get(desc_en, weather.get("description", ""))
    temp = main.get("temp", "?")
    feels = main.get("feels_like", "?")
    humidity = main.get("humidity", "?")
    wind_speed = wind.get("speed", "?")

    return (
        f"🌤 Thời tiết {name}: {desc}\n"
        f"🌡 Nhiệt độ: {temp}°C (cảm giác {feels}°C)\n"
        f"💧 Độ ẩm: {humidity}%\n"
        f"💨 Gió: {wind_speed} m/s"
    )
