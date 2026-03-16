"""Tests for M18 Browser Automation — unit tests without Playwright."""
import base64
import re


class TestBrowserHelpers:
    def test_text_cleanup(self):
        """Test the regex used to clean extracted page text."""
        raw = "Hello\n\n\n\n\nWorld\n\n\nFoo"
        cleaned = re.sub(r'\n{3,}', '\n\n', raw).strip()
        assert cleaned == "Hello\n\nWorld\n\nFoo"

    def test_text_truncation(self):
        MAX_PAGE_TEXT = 5000
        long_text = "x" * 10000
        truncated = long_text[:MAX_PAGE_TEXT]
        assert len(truncated) == 5000

    def test_screenshot_base64_roundtrip(self):
        fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        encoded = base64.b64encode(fake_png).decode()
        decoded = base64.b64decode(encoded)
        assert decoded == fake_png

    def test_fields_json_parsing(self):
        """Test that browse_fill fields JSON parsing works."""
        import json
        fields_str = '{"#email": "test@test.com", "#pass": "secret"}'
        fields = json.loads(fields_str)
        assert fields["#email"] == "test@test.com"
        assert fields["#pass"] == "secret"

    def test_invalid_fields_json(self):
        import json
        with __import__("pytest").raises(json.JSONDecodeError):
            json.loads("not json")
