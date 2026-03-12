"""Integration tests — API endpoints: auth, tasks, health, MCP."""
import pytest


class TestHealth:
    @pytest.mark.asyncio
    async def test_health_ok(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestAuth:
    @pytest.mark.asyncio
    async def test_register_new_user(self, client):
        import uuid
        email = f"new-{uuid.uuid4().hex[:6]}@jarvis.vn"
        resp = await client.post("/api/v1/auth/register", json={
            "email": email, "password": "pass1234", "name": "New"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client):
        payload = {"email": "dup@jarvis.vn", "password": "pass1234", "name": "Dup"}
        await client.post("/api/v1/auth/register", json=payload)
        resp = await client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_login_success(self, client):
        await client.post("/api/v1/auth/register", json={
            "email": "login@jarvis.vn", "password": "pass1234", "name": "Login"
        })
        resp = await client.post("/api/v1/auth/login", json={
            "email": "login@jarvis.vn", "password": "pass1234"
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client):
        await client.post("/api/v1/auth/register", json={
            "email": "wrong@jarvis.vn", "password": "pass1234", "name": "Wrong"
        })
        resp = await client.post("/api/v1/auth/login", json={
            "email": "wrong@jarvis.vn", "password": "badpass"
        })
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client):
        resp = await client.post("/api/v1/auth/login", json={
            "email": "ghost@jarvis.vn", "password": "pass1234"
        })
        assert resp.status_code == 401


class TestTasks:
    @pytest.mark.asyncio
    async def test_create_and_list_tasks(self, client):
        import uuid
        email = f"tasks-{uuid.uuid4().hex[:6]}@jarvis.vn"
        reg = await client.post("/api/v1/auth/register", json={
            "email": email, "password": "pass1234", "name": "Tasks"
        })
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create task
        resp = await client.post("/api/v1/tasks/", json={
            "title": "Test task", "priority": "high"
        }, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["title"] == "Test task"

        # List tasks
        resp = await client.get("/api/v1/tasks/", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    @pytest.mark.asyncio
    async def test_tasks_unauthorized(self, client):
        resp = await client.get("/api/v1/tasks/")
        assert resp.status_code in (401, 403)


class TestMCP:
    @pytest.mark.asyncio
    async def test_mcp_crud(self, client):
        import uuid
        email = f"mcp-{uuid.uuid4().hex[:6]}@jarvis.vn"
        reg = await client.post("/api/v1/auth/register", json={
            "email": email, "password": "pass1234", "name": "MCP"
        })
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # List empty
        resp = await client.get("/api/v1/mcp/", headers=headers)
        assert resp.status_code == 200
        assert resp.json() == []

        # Create
        resp = await client.post("/api/v1/mcp/", json={
            "name": "test-server", "transport": "stdio",
            "config": {"command": "node", "args": ["server.js"]}
        }, headers=headers)
        assert resp.status_code == 200
        server_id = resp.json()["id"]
        assert resp.json()["name"] == "test-server"

        # List with 1 item
        resp = await client.get("/api/v1/mcp/", headers=headers)
        assert len(resp.json()) == 1

        # Delete
        resp = await client.delete(f"/api/v1/mcp/{server_id}", headers=headers)
        assert resp.status_code == 200

        # List empty again
        resp = await client.get("/api/v1/mcp/", headers=headers)
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_mcp_unauthorized(self, client):
        resp = await client.get("/api/v1/mcp/")
        assert resp.status_code in (401, 403)
