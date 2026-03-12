"""E2E test — full chat flow via WebSocket."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import ASGITransport, AsyncClient


class TestE2EChat:
    """End-to-end WebSocket chat tests using mocked LLM."""

    async def _get_token(self, client, email="e2e@jarvis.vn"):
        reg = await client.post("/api/v1/auth/register", json={
            "email": email, "password": "pass1234", "name": "E2E"
        })
        if reg.status_code == 400:  # already registered
            resp = await client.post("/api/v1/auth/login", json={
                "email": email, "password": "pass1234"
            })
            return resp.json()["access_token"]
        return reg.json()["access_token"]

    @pytest.mark.asyncio
    async def test_ws_rejects_no_token(self, client):
        """WebSocket without token should be rejected."""
        from main import app
        from starlette.testclient import TestClient
        with TestClient(app) as tc:
            with tc.websocket_connect("/api/v1/ws/chat") as ws:
                data = ws.receive_json()
                assert data["type"] == "error"
                assert "Unauthorized" in data["content"]

    @pytest.mark.asyncio
    async def test_ws_rejects_bad_token(self, client):
        """WebSocket with invalid token should be rejected."""
        from main import app
        from starlette.testclient import TestClient
        with TestClient(app) as tc:
            with tc.websocket_connect("/api/v1/ws/chat?token=invalid") as ws:
                data = ws.receive_json()
                assert data["type"] == "error"

    @pytest.mark.asyncio
    async def test_full_chat_flow(self, client):
        """Register → get token → WS connect → send message → receive stream + done."""
        token = await self._get_token(client, "chat-flow@jarvis.vn")

        # Mock the LangGraph to avoid real LLM calls
        mock_events = [
            {"event": "on_chat_model_stream", "metadata": {"langgraph_node": "agent_loop"},
             "data": {"chunk": MagicMock(content="Xin chào!")}},
        ]

        async def mock_astream_events(*args, **kwargs):
            for e in mock_events:
                yield e

        from main import app
        from starlette.testclient import TestClient

        with patch("api.v1.ws.jarvis_graph") as mock_graph:
            mock_graph.astream_events = mock_astream_events

            with TestClient(app) as tc:
                with tc.websocket_connect(f"/api/v1/ws/chat?token={token}") as ws:
                    ws.send_json({"content": "xin chào"})

                    messages = []
                    for _ in range(10):
                        data = ws.receive_json()
                        messages.append(data)
                        if data.get("type") == "done":
                            break

                    types = [m["type"] for m in messages]
                    assert "stream" in types
                    assert "done" in types

                    # Verify streamed content
                    stream_msgs = [m for m in messages if m["type"] == "stream"]
                    assert any("Xin chào" in m["content"] for m in stream_msgs)

    @pytest.mark.asyncio
    async def test_chat_filters_evaluate_json(self, client):
        """Evaluate node output should NOT appear in stream."""
        token = await self._get_token(client, "filter@jarvis.vn")

        mock_events = [
            {"event": "on_chat_model_stream", "metadata": {"langgraph_node": "agent_loop"},
             "data": {"chunk": MagicMock(content="Câu trả lời")}},
            # This should be filtered out
            {"event": "on_chat_model_stream", "metadata": {"langgraph_node": "evaluate"},
             "data": {"chunk": MagicMock(content='{"pass": true}')}},
            {"event": "on_chat_model_stream", "metadata": {"langgraph_node": "post_process"},
             "data": {"chunk": MagicMock(content='{"entities": []}')}},
        ]

        async def mock_astream_events(*args, **kwargs):
            for e in mock_events:
                yield e

        from main import app
        from starlette.testclient import TestClient

        with patch("api.v1.ws.jarvis_graph") as mock_graph:
            mock_graph.astream_events = mock_astream_events

            with TestClient(app) as tc:
                with tc.websocket_connect(f"/api/v1/ws/chat?token={token}") as ws:
                    ws.send_json({"content": "test"})

                    full = ""
                    for _ in range(10):
                        data = ws.receive_json()
                        if data["type"] == "stream":
                            full += data["content"]
                        if data["type"] == "done":
                            break

                    assert "Câu trả lời" in full
                    assert '{"pass"' not in full
                    assert '{"entities"' not in full
