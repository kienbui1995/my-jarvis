# MY JARVIS

> **Hieu ban. Lam thay ban. Du lieu thuoc ve ban.**

Vietnamese-first agentic personal AI assistant — 8 channels, smart LLM routing, persistent memory, proactive automation, developer ecosystem.

**V8.0.0** — 50 modules, 28 tools, 8 channels. [Full changelog](CHANGELOG.md) | [Project summary](docs/PROJECT_SUMMARY_V7.md) | [Roadmap V8-V14](docs/ROADMAP_V8_V14.md)

## Architecture

```
Zalo OA / Zalo Bot / Telegram / WhatsApp / Slack / Discord / Web / Mini App
        |
   Cloudflare Tunnel (HTTPS)
        |
   Next.js 15 (frontend)  +  FastAPI (backend)
        |
   LangGraph Agent Pipeline (10 nodes)
        |
   LiteLLM Proxy  -->  Gemini / Claude / DeepSeek / GPT
        |
   PostgreSQL+pgvector | Redis | MinIO
```

## Quick Start

```bash
cp .env.example .env
# Fill in API keys in .env

make build
make dev             # Dev: backend :8002, frontend :3002
make db-upgrade      # Apply migrations
```

## Production

```bash
cp .env.example .env.prod
# Fill in strong passwords + API keys

make build
make prod            # Uses .env.prod + docker-compose.prod.yml
```

## Commands

```bash
make help              # Show all commands
make dev               # Start dev services
make dev-down          # Stop dev services
make prod              # Start production
make prod-down         # Stop production
make dev-logs s=backend  # Tail logs
make db-migrate m="description"  # Create migration
make db-upgrade        # Apply migrations
make lint              # ruff check (backend)
make test              # pytest (backend, in Docker)
```

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | Next.js 15, Tailwind CSS v4, TypeScript, Zustand |
| Backend | FastAPI, LangGraph, Python 3.12 |
| LLM | LiteLLM Proxy -> Gemini, Claude, DeepSeek, GPT |
| Database | PostgreSQL + pgvector, Redis |
| Storage | MinIO (S3-compatible) |
| Voice | Gemini STT, Vertex TTS, Piper WASM (fallback) |
| Monitoring | Sentry (backend + frontend) |
| Deploy | Docker Compose, Cloudflare Tunnel |
| CI/CD | Azure Pipelines |
| Billing | Stripe |

## Project Structure

```
my-jarvis/
├── backend/           # FastAPI + LangGraph (155+ files)
│   ├── agent/         # Pipeline, tools, nodes
│   ├── api/v1/        # 54 API endpoints
│   ├── channels/      # 8 channel adapters
│   ├── llm/           # Gateway, router, budget
│   ├── services/      # Proactive engine, handlers
│   └── db/            # Models (22), migrations (11)
├── frontend/          # Next.js 15 (50+ files)
│   ├── app/           # Pages (chat, tasks, calendar, settings, analytics)
│   ├── components/    # UI + chat + layout
│   └── lib/           # API client, WebSocket, stores
├── docs/              # Architecture, specs, summary
├── infra/             # Cloudflare Tunnel, backup
└── scripts/           # Setup scripts
```

## License

Proprietary — All rights reserved.
