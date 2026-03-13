# MY JARVIS 🤖

> **Hiểu bạn. Làm thay bạn. Dữ liệu thuộc về bạn.**

Vietnamese-first agentic personal AI assistant — multi-channel (Zalo, Telegram, Web), smart LLM routing, persistent memory, proactive actions.

**V3 Intelligence Layer** — Smart Router, Plan-and-Execute, Conversation Memory, Memory Consolidation, Preference Learning, HITL, Evidence Logging, Supervision. [Full changelog →](CHANGELOG.md)

## Architecture

See [`docs/architecture.md`](docs/architecture.md) for full technical design.

```
Zalo / Telegram / Web
        │
   Cloudflare Tunnel (SSL + routing)
        │
   ┌────┴────┐
   │ Next.js │ ← Frontend (port 3000)
   │ FastAPI │ ← Backend  (port 8000)
   └────┬────┘
        │
   LangGraph Agent ──► Tools (Tasks, Calendar, Finance, Memory, Web)
        │
   LiteLLM Proxy ──► Gemini / Claude / DeepSeek
        │
   PostgreSQL + pgvector │ Redis │ MinIO
```

## Quick Start

```bash
cp .env.example .env
# Fill in API keys in .env

make build
make up
make db-upgrade

# Backend:  http://localhost:8000
# Frontend: http://localhost:3000
```

## Production Deploy

```bash
cp .env.example .env.prod
# Fill in strong passwords + API keys

make build
make prod          # Uses .env.prod + docker-compose.prod.yml
```

## Commands

```bash
make help          # Show all commands
make up            # Start dev services
make down          # Stop services
make prod          # Start production
make logs s=backend # Tail logs
make db-migrate m="description"  # Create migration
make db-upgrade    # Apply migrations
make lint          # Run linters
make test          # Run tests
```

## Project Structure

```
my-jarvis/
├── backend/          # FastAPI + LangGraph
├── frontend/         # Next.js 15 dashboard
├── docs/             # Architecture, design specs
├── infra/            # Cloudflare Tunnel config, backup script
├── scripts/          # Setup scripts
└── azure-pipelines.yml  # CI/CD
```

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | Next.js 15, Tailwind, Piper TTS (Vietnamese) |
| Backend | FastAPI, LangGraph, Python 3.12 |
| LLM | LiteLLM Proxy → Gemini, Claude, DeepSeek |
| Database | PostgreSQL + pgvector, Redis |
| Storage | MinIO (S3-compatible) |
| Monitoring | Sentry (backend + frontend) |
| Deploy | Docker Compose, Cloudflare Tunnel |
| CI/CD | Azure Pipelines |

## License

Proprietary — All rights reserved.
