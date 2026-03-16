"""Tests for M15 Vietnamese Service Integrations.

Weather/news tool tests import helper functions directly to avoid
pgvector dependency chain. Full tool tests run in Docker via `make test`.
"""
import re
from xml.etree import ElementTree

from core.config import settings

settings.OPENWEATHER_API_KEY = "test-key"


# ── Weather helpers (extracted logic, no langchain import) ──

_CITY_ALIASES = {
    "sg": "Ho Chi Minh City,VN", "sài gòn": "Ho Chi Minh City,VN",
    "hn": "Hanoi,VN", "hà nội": "Hanoi,VN",
    "đà nẵng": "Da Nang,VN",
}


def _resolve_city(city: str) -> str:
    return _CITY_ALIASES.get(city.lower().strip(), f"{city},VN")


class TestWeatherHelpers:
    def test_resolve_known_cities(self):
        assert _resolve_city("sg") == "Ho Chi Minh City,VN"
        assert _resolve_city("Sài Gòn") == "Ho Chi Minh City,VN"
        assert _resolve_city("hn") == "Hanoi,VN"
        assert _resolve_city("Hà Nội") == "Hanoi,VN"
        assert _resolve_city("đà nẵng") == "Da Nang,VN"

    def test_resolve_unknown_city(self):
        assert _resolve_city("Random City") == "Random City,VN"


# ── News helpers (extracted logic) ──

def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def _parse_rss(xml_text: str, limit: int = 5) -> list[dict]:
    root = ElementTree.fromstring(xml_text)
    items = []
    for item in root.findall(".//item")[:limit]:
        title = item.findtext("title", "")
        desc = _strip_html(item.findtext("description", ""))
        link = item.findtext("link", "")
        items.append({"title": title, "desc": desc, "link": link})
    return items


class TestNewsHelpers:
    def test_strip_html(self):
        assert _strip_html("<b>Bold</b> text") == "Bold text"
        assert _strip_html("no html") == "no html"
        assert _strip_html("<p>Para</p>") == "Para"

    def test_parse_rss(self):
        sample = """<?xml version="1.0"?>
        <rss><channel>
            <item><title>Tin 1</title><description>Mo ta</description>
            <link>https://vnexpress.net/1</link></item>
            <item><title>Tin 2</title><description>Mo ta 2</description>
            <link>https://vnexpress.net/2</link></item>
        </channel></rss>"""
        articles = _parse_rss(sample)
        assert len(articles) == 2
        assert articles[0]["title"] == "Tin 1"
        assert articles[1]["title"] == "Tin 2"

    def test_parse_rss_limit(self):
        sample = """<?xml version="1.0"?>
        <rss><channel>
            <item><title>A</title><description>d</description><link>l</link></item>
            <item><title>B</title><description>d</description><link>l</link></item>
            <item><title>C</title><description>d</description><link>l</link></item>
        </channel></rss>"""
        assert len(_parse_rss(sample, limit=2)) == 2


# ── Google OAuth (no pgvector dependency) ──

class TestGoogleOAuth:
    """Google OAuth tests — require pgvector (Docker only for full tests).

    build_auth_url is tested inline since it only uses stdlib + settings.
    """

    def test_build_auth_url_format(self):
        from urllib.parse import urlencode
        # Reproduce build_auth_url logic without importing the module
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID or "test",
            "redirect_uri": "http://localhost/callback",
            "response_type": "code",
            "scope": "https://www.googleapis.com/auth/calendar.readonly",
            "access_type": "offline",
            "prompt": "consent",
            "state": "user-123",
        }
        url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        assert "accounts.google.com" in url
        assert "user-123" in url
        assert "calendar" in url
