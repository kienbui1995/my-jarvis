"""Curated MCP server registry — pre-configured servers users can enable."""

CURATED_SERVERS = [
    {
        "id": "google-workspace",
        "name": "Google Workspace",
        "description": "Google Calendar, Gmail, Drive — quản lý lịch, email, tài liệu",
        "transport": "sse",
        "default_config": {"url": "https://mcp.googleapis.com/v1"},
        "required_fields": ["api_key"],
        "icon": "google",
        "category": "productivity",
    },
    {
        "id": "github",
        "name": "GitHub",
        "description": "Repositories, Issues, PRs — quản lý code và dự án",
        "transport": "sse",
        "default_config": {"url": "https://api.githubcopilot.com/mcp"},
        "required_fields": ["api_key"],
        "icon": "github",
        "category": "developer",
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
    },
]


def get_registry() -> list[dict]:
    return CURATED_SERVERS


def get_curated_server(server_id: str) -> dict | None:
    return next((s for s in CURATED_SERVERS if s["id"] == server_id), None)
