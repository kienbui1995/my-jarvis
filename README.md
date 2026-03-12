# MY JARVIS 🤖

> **Hiểu bạn. Làm thay bạn. Dữ liệu thuộc về bạn.**

Vietnamese-first agentic personal AI assistant — multi-channel (Zalo, Telegram, Web), smart LLM routing, persistent memory, proactive actions.

**V3 Intelligence Layer** — Smart Router, Plan-and-Execute, Conversation Memory, Memory Consolidation, Preference Learning, HITL, Evidence Logging, Supervision. [Full changelog →](CHANGELOG.md)

## Architecture

See [`docs/architecture.md`](docs/architecture.md) for full technical design.

```
Zalo / Telegram / Web
        │
   API Gateway (Traefik)
        │
   FastAPI Backend
        │
   LangGraph Agent ──► Tools (Tasks, Calendar, Finance, Memory, Web)
        │
   LLM Gateway (Gemini / Claude / DeepSeek)
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
# MinIO:    http://localhost:9001
```

## Commands

```bash
make help          # Show all commands
make up            # Start services
make down          # Stop services
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
├── frontend/         # Next.js dashboard
├── docs/             # Architecture, ADRs
├── infra/            # Traefik, Dockerfiles
├── financial-model/  # Business projections
└── pitch-deck/       # Investor materials
```

## License

Proprietary — All rights reserved.
