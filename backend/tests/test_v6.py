"""Tests for V5/V6 modules — pure logic tests without DB model imports."""
import ast

import pytest


class TestCustomToolsSecurity:
    """Test custom tool validation using raw AST logic (no DB import)."""

    BLOCKED_IMPORTS = {"os", "sys", "subprocess", "shutil", "pathlib", "socket", "ctypes"}

    def _validate(self, code):
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return f"Syntax error: {e}"
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] in self.BLOCKED_IMPORTS:
                        return f"Import not allowed: {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.split(".")[0] in self.BLOCKED_IMPORTS:
                    return f"Import not allowed: {node.module}"
        funcs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        if len(funcs) != 1:
            return "Code must contain exactly one function"
        return None

    def test_blocks_os_import(self):
        assert self._validate("import os\ndef f(): pass") is not None

    def test_blocks_subprocess(self):
        assert "not allowed" in self._validate("import subprocess\ndef f(): pass")

    def test_allows_safe_code(self):
        assert self._validate("def greet(name: str):\n    return f'Hi {name}'") is None

    def test_requires_one_function(self):
        assert "one function" in self._validate("x = 1")

    def test_rejects_multiple_functions(self):
        assert "one function" in self._validate("def a(): pass\ndef b(): pass")

    def test_blocks_socket(self):
        assert "not allowed" in self._validate("import socket\ndef f(): pass")

    def test_allows_json_import(self):
        assert self._validate("import json\ndef f():\n    return json.dumps({})") is None

    def test_extract_metadata(self):
        code = 'def my_tool(x: int, y: str):\n    """My description."""\n    pass'
        tree = ast.parse(code)
        func = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
        assert func.name == "my_tool"
        assert ast.get_docstring(func) == "My description."
        args = [a.arg for a in func.args.args]
        assert args == ["x", "y"]

    @pytest.mark.asyncio
    async def test_safe_import_enforcement(self):
        """Verify _safe_import blocks unauthorized modules at runtime."""
        ALLOWED = {"json", "re", "math", "datetime"}

        def _safe_import(name, *args, **kwargs):
            if name.split(".")[0] not in ALLOWED:
                raise ImportError(f"Import not allowed: {name}")
            return __import__(name, *args, **kwargs)

        ns = {"__builtins__": {"__import__": _safe_import}}
        with pytest.raises(ImportError, match="not allowed"):
            exec("import os", ns)

        # Allowed import should work
        exec("import json", {**ns, "__builtins__": {**ns["__builtins__"],
             "json": __import__("json")}})


class TestBrowserSecurity:
    def test_blocks_localhost(self):
        from services.browser import _validate_url
        assert _validate_url("http://localhost:8000") is not None
        assert _validate_url("http://127.0.0.1/admin") is not None

    def test_blocks_metadata(self):
        from services.browser import _validate_url
        assert _validate_url("http://169.254.169.254/metadata") is not None

    def test_blocks_file_scheme(self):
        from services.browser import _validate_url
        assert _validate_url("file:///etc/passwd") is not None

    def test_allows_https(self):
        from services.browser import _validate_url
        assert _validate_url("https://google.com") is None
        assert _validate_url("https://vnexpress.net") is None

    def test_blocks_internal(self):
        from services.browser import _validate_url
        assert _validate_url("http://10.0.0.1/api") is not None
        assert _validate_url("http://app.internal/") is not None

    def test_blocks_unusual_ports(self):
        from services.browser import _validate_url
        assert _validate_url("http://example.com:6379") is not None

    def test_allows_standard_ports(self):
        from services.browser import _validate_url
        assert _validate_url("http://example.com:80") is None
        assert _validate_url("https://example.com:443") is None


class TestRateLimitConfig:
    def test_endpoint_limits_exist(self):
        from core.rate_limit import ENDPOINT_LIMITS
        assert "/api/v1/voice/transcribe" in ENDPOINT_LIMITS
        assert "/api/v1/files/upload" in ENDPOINT_LIMITS
        assert "/api/v1/chat" in ENDPOINT_LIMITS
        assert "/api/public/v1/chat" in ENDPOINT_LIMITS

    def test_skip_paths(self):
        from core.rate_limit import SKIP_PATHS
        assert "/health" in SKIP_PATHS
        assert "/health/ready" in SKIP_PATHS

    def test_tier_limits_structure(self):
        from core.rate_limit import TIER_LIMITS
        for tier in ("free", "pro", "pro_plus"):
            assert "read_rpm" in TIER_LIMITS[tier]
            assert "write_rpm" in TIER_LIMITS[tier]
            assert "daily_write" in TIER_LIMITS[tier]
        # Pro should be more generous than free
        assert TIER_LIMITS["pro"]["read_rpm"] > TIER_LIMITS["free"]["read_rpm"]
