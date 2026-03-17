"""Curated MCP server registry — pre-configured servers users can enable."""
from core.config import settings

CURATED_SERVERS = [
    # --- Productivity ---
    {
        "id": "google-workspace",
        "name": "Google Workspace",
        "description": "Google Calendar, Gmail, Drive — quản lý lịch, email, tài liệu",
        "transport": "sse",
        "default_config": {"url": "https://mcp.googleapis.com/v1"},
        "required_fields": ["api_key"],
        "icon": "google",
        "category": "productivity",
        "shared_key_env": "",
    },
    {
        "id": "notion",
        "name": "Notion",
        "description": "Pages, Databases, Blocks — ghi chú và quản lý kiến thức",
        "transport": "sse",
        "default_config": {"url": "https://mcp.notion.so/v1"},
        "required_fields": ["api_key"],
        "icon": "notion",
        "category": "productivity",
        "shared_key_env": "",
    },
    {
        "id": "trello",
        "name": "Trello",
        "description": "Boards, Lists, Cards — quản lý dự án trực quan",
        "transport": "sse",
        "default_config": {"url": "https://mcp.trello.com/v1"},
        "required_fields": ["api_key"],
        "icon": "trello",
        "category": "productivity",
        "shared_key_env": "MCP_TRELLO_KEY",
    },
    # --- Developer ---
    {
        "id": "github",
        "name": "GitHub",
        "description": "Repositories, Issues, PRs — quản lý code và dự án",
        "transport": "sse",
        "default_config": {"url": "https://api.githubcopilot.com/mcp"},
        "required_fields": ["api_key"],
        "icon": "github",
        "category": "developer",
        "shared_key_env": "MCP_GITHUB_KEY",
    },
    {
        "id": "linear",
        "name": "Linear",
        "description": "Issues, Projects, Cycles — quản lý dự án cho dev teams",
        "transport": "sse",
        "default_config": {"url": "https://mcp.linear.app/v1"},
        "required_fields": ["api_key"],
        "icon": "linear",
        "category": "developer",
        "shared_key_env": "MCP_LINEAR_KEY",
    },
    {
        "id": "sentry",
        "name": "Sentry",
        "description": "Errors, Performance, Releases — monitoring và debug",
        "transport": "sse",
        "default_config": {"url": "https://mcp.sentry.io/v1"},
        "required_fields": ["api_key"],
        "icon": "sentry",
        "category": "developer",
        "shared_key_env": "MCP_SENTRY_KEY",
    },
]


def get_registry() -> list[dict]:
    """Return registry with shared key availability info."""
    result = []
    for s in CURATED_SERVERS:
        entry = {**s}
        entry["has_shared_key"] = bool(s["shared_key_env"] and getattr(settings, s["shared_key_env"], ""))
        entry.pop("shared_key_env", None)
        result.append(entry)
    return result


def get_curated_server(server_id: str) -> dict | None:
    return next((s for s in CURATED_SERVERS if s["id"] == server_id), None)


def get_shared_key(server_id: str) -> str:
    """Get operator's shared API key for a curated server, if configured."""
    server = get_curated_server(server_id)
    if not server or not server.get("shared_key_env"):
        return ""
    return getattr(settings, server["shared_key_env"], "")
