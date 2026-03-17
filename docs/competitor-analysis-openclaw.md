# MY JARVIS vs OpenClaw — Competitor Analysis

> Date: 2026-03-17

## Overview

| | MY JARVIS | OpenClaw |
|---|-----------|----------|
| **GitHub Stars** | Private repo | 319K |
| **License** | Proprietary | MIT |
| **Language** | Python + TypeScript | Node.js + TypeScript |
| **Target** | Vietnamese users, personal productivity | Global, developer/power users |
| **Hosting** | Cloud (Docker Compose) | Local-first (self-hosted) |
| **Status** | Production (jarvis.pmai.space) | Viral open-source project |

## Feature Comparison

### Channels

| Channel | MY JARVIS | OpenClaw |
|---------|-----------|----------|
| Web UI | Yes | Yes (WebChat) |
| WhatsApp | Yes (Business Cloud API) | Yes (Baileys) |
| Telegram | Yes (Bot API) | Yes (grammY) |
| Slack | Yes (Events API) | Yes (Bolt) |
| Discord | Yes (Interactions API) | Yes (discord.js) |
| Zalo OA | Yes | Yes |
| Zalo Bot | Yes | No |
| Zalo Mini App | Yes | No |
| iMessage | No | Yes (BlueBubbles) |
| Signal | No | Yes |
| Google Chat | No | Yes |
| Microsoft Teams | No | Yes |
| IRC / Matrix | No | Yes |
| LINE / Feishu | No | Yes |
| **Total** | **8** | **20+** |

**Verdict**: OpenClaw thắng về số lượng (20+ vs 8). MY JARVIS mạnh hơn ở Zalo ecosystem (OA + Bot + Mini App) — quan trọng cho thị trường Việt Nam.

### AI & Agent Pipeline

| Feature | MY JARVIS | OpenClaw |
|---------|-----------|----------|
| LLM Routing | Smart Router (LLM-based intent + complexity) | Model failover + multi-agent routing |
| Plan-and-Execute | Yes (planner → executor → replan → synthesize) | No (skill-based) |
| Memory | pgvector embeddings + rolling summary + consolidation | Session persistence + context compacting |
| Preference Learning | Auto-extract from conversations | Learns over time (details unclear) |
| HITL Approval | WebSocket-based interrupt for destructive tools | DM pairing approval |
| Supervision | Heartbeat + timeout + stale cleanup | Not mentioned |
| Context Guard | Token estimation + truncation + 20% reserve | /compact command |
| Evidence Logging | Every tool call logged with audit API | Not mentioned |
| Injection Detection | LLM-based scoring (>0.8 blocks) | Not mentioned |
| Multi-agent | Parallel sub-agents (asyncio.gather) | Multi-agent routing |

**Verdict**: MY JARVIS có agent pipeline phức tạp hơn (10 nodes, plan-execute, supervision, injection detection). OpenClaw thiên về simplicity + extensibility.

### Tools & Skills

| Feature | MY JARVIS | OpenClaw |
|---------|-----------|----------|
| Built-in tools | 24 | 50+ integrations |
| Custom tools | SDK + AST validation + marketplace | Community skills (ClawHub) |
| Skill marketplace | Plugin Marketplace (M39) | ClawHub registry (3000+ skills) |
| Task management | Built-in (CRUD + AI-created) | Via skills |
| Calendar | Built-in (CRUD) | Via skills |
| Finance tracking | Built-in (expense_log, budget_check) | Via skills |
| Weather | weather_vn (Vietnamese cities) | Via skills |
| News | news_vn (VnExpress RSS) | Via skills |
| Vision/OCR | Gemini multimodal | Via skills |
| Browser automation | Playwright (4 tools) | Built-in browser tools |
| Voice I/O | STT + TTS + hands-free loop | Voice Wake + Talk Mode |
| File management | MinIO upload + analysis | Direct file system access |

**Verdict**: OpenClaw có ecosystem lớn hơn nhiều (3000+ community skills vs 24 built-in). MY JARVIS tích hợp sâu hơn cho productivity (task/calendar/finance built-in, không cần install skill).

### Platform & Deployment

| Feature | MY JARVIS | OpenClaw |
|---------|-----------|----------|
| macOS app | No | Yes (menu bar) |
| iOS app | No | Yes (native node) |
| Android app | No | Yes (native node) |
| Linux | Yes (Docker) | Yes (Gateway) |
| Windows | No | Yes (WSL2) |
| Cloud deploy | Docker Compose + CF Tunnel | Fly.io, Render, Vercel |
| Self-hosted | Yes (single server) | Yes (local-first) |

**Verdict**: OpenClaw thắng hoàn toàn — native apps cho macOS/iOS/Android. MY JARVIS chỉ có web + Docker.

### Vietnamese-specific Features

| Feature | MY JARVIS | OpenClaw |
|---------|-----------|----------|
| Vietnamese UI | Yes (primary language) | No |
| Vietnamese NLP | Tuned prompts, handles no-diacritics | No special support |
| Vietnamese services | weather_vn, news_vn (VnExpress) | No |
| Zalo ecosystem | OA + Bot + Mini App | Zalo (basic) |
| Vietnamese voice | Gemini STT + Vertex TTS | No |
| VND currency | Built-in finance tracking | No |

**Verdict**: MY JARVIS thắng tuyệt đối ở Vietnamese market. OpenClaw không có bất kỳ Vietnamese-specific feature nào.

### Security & Privacy

| Feature | MY JARVIS | OpenClaw |
|---------|-----------|----------|
| Hosting model | Cloud (server-side) | Local-first (your machine) |
| Data ownership | Server-side (user trusts operator) | User's machine (full control) |
| Auth | JWT + refresh token rotation | DM pairing codes |
| Rate limiting | Per-endpoint + per-tier | Not mentioned |
| Injection detection | LLM-based scoring | Not mentioned |
| Webhook verification | HMAC/Ed25519 per channel | DM pairing approval |
| Audit trail | Evidence logging API | Not mentioned |
| Encryption | PostgreSQL at rest | Local filesystem |

**Verdict**: Khác approach. OpenClaw = local-first (user giữ data). MY JARVIS = cloud (operator giữ data) nhưng có security layers mạnh hơn (injection detection, audit, rate limiting).

### Monetization

| Feature | MY JARVIS | OpenClaw |
|---------|-----------|----------|
| Model | SaaS (free/pro $5/pro+ $15) | Open-source (MIT) |
| Revenue | Stripe subscriptions | Sponsors (OpenAI, Vercel) |
| User pays for | Service subscription | Own LLM API costs |

### Third-party Integration & Extensibility

| Capability | MY JARVIS | OpenClaw |
|-----------|-----------|----------|
| **MCP Client** | Yes (V2) — connect MCP servers | Yes (via MCPPorter bridge) |
| **Custom Code** | Python SDK + AST validation (M38) | Any language, no sandbox |
| **Marketplace** | Plugin Marketplace (M39) — empty | ClawHub — 13,700+ skills |
| **Workflow Engine** | Webhook Actions (M40) — event → HTTP | Clawflows + cron + webhooks |
| **External API** | Public API (M37) — apps gọi vào JARVIS | REST API |
| **Zapier** | No | Yes — 8,000+ apps via Zapier MCP |
| **n8n** | No | Yes — n8n-claw, full workflow builder |
| **No-code connector** | No | Composio — 860+ tools, zero auth code |
| **Self-writing skills** | No | Yes — agent tự viết code tạo skill mới |
| **Smart home** | No | Hue, Elgato, Home Assistant |
| **Note apps** | No | Obsidian, Notion, Apple Notes, Bear |
| **Social media** | No | Simplified (multi-platform posting) |
| **Music/Audio** | No | Spotify, Apple Music |
| **Security model** | AST validation, restricted builtins, 30s timeout | No sandbox — skill có full access |
| **Malicious risk** | Low (sandboxed) | High — CVE-2026-25253, 341 malicious skills found |

**Verdict**: OpenClaw thắng về breadth (13,700+ skills, Zapier, n8n, Composio). MY JARVIS thắng về security (sandboxed, AST validation). OpenClaw's "god mode" = powerful nhưng là "security nightmare" (42K exposed instances, data exfiltration incidents).

### Integration Architecture So sánh

```
OpenClaw:
  User → Gateway → Agent → [Skills | MCP | Zapier | n8n | Composio]
                              ↓
                    ClawHub (13,700+ skills, NO sandbox)
                    Malicious skill = full system access

MY JARVIS:
  User → Web/Zalo → Agent Pipeline → [24 Built-in Tools | Custom SDK | MCP | Webhooks]
                                        ↓
                              Marketplace (sandboxed, AST validated)
                              Public API (external apps → JARVIS)
```

### MY JARVIS Integration Gaps (V8 Roadmap)

Để cạnh tranh với OpenClaw về extensibility mà không sacrifice security:

**Priority 1 — MCP Gateway (biggest impact)**
- Hiện tại: MCP client chỉ connect 1:1 từ settings
- Cần: MCP Gateway tích hợp sẵn các MCP servers phổ biến (Google Workspace, Notion, GitHub, Slack tools)
- User chọn enable/disable từng MCP server, không cần cài gì
- Tương tự Composio nhưng built-in, không cần third-party

**Priority 2 — n8n/Zapier Webhook Bridge**
- Hiện tại: Webhook Actions (M40) chỉ gửi đi (JARVIS → external)
- Cần: Nhận webhook từ n8n/Zapier → trigger JARVIS action
- User flow: Zapier trigger → webhook JARVIS → agent xử lý → response
- Ví dụ: Email mới → Zapier → JARVIS tóm tắt + phân loại

**Priority 3 — Visual Connector (no-code)**
- Settings UI: danh sách connectors (Google, Notion, Trello, Shopee...)
- Click "Kết nối" → OAuth flow → JARVIS tự thêm tools
- Không cần code, không cần biết MCP là gì
- Target: non-tech users (chị Hoa persona)

**Priority 4 — Agent Self-Extend (có kiểm soát)**
- OpenClaw: agent tự viết skill → dangerous
- MY JARVIS: agent đề xuất skill → user review + approve → sandbox execute
- Giữ human-in-the-loop cho security, nhưng cho phép AI extend capabilities

### Security Advantage

OpenClaw's extensibility = security nightmare:
- CVE-2026-25253 (CVSS 8.8) — RCE qua malicious skill
- 341 malicious skills trên ClawHub (Koi Security audit)
- Skill có full access: file system, env vars (API keys), network
- Chinese gov đã cấm OpenClaw trong cơ quan nhà nước (March 2026)

MY JARVIS's approach = secure by default:
- Custom tools: AST validation block os/sys/subprocess
- Restricted builtins, 30s execution timeout
- Sandbox execution, không access file system
- Plugin review trước khi publish lên marketplace

**Đây là selling point cho B2B**: doanh nghiệp không muốn "god mode" AI, họ cần controllable AI.

---

## SWOT Analysis — MY JARVIS vs OpenClaw

### Strengths (MY JARVIS)
- Vietnamese-first: UI, NLP, services, voice — không đối thủ nào có
- Deep agent pipeline: plan-execute, supervision, HITL, injection detection
- Integrated productivity: task/calendar/finance built-in, không cần install
- Production-ready SaaS: billing, onboarding, analytics có sẵn
- Security layers: rate limiting, audit trail, webhook verification

### Weaknesses (MY JARVIS)
- Ít channels hơn (8 vs 20+)
- Không có native app (macOS/iOS/Android)
- Skill ecosystem nhỏ (24 vs 13,700+), marketplace trống
- Thiếu no-code connector (Zapier/n8n/Composio)
- Cloud-only — user phải trust operator với data
- Single server, không horizontal scaling

### Opportunities
- **Zalo Mini App** — 80M+ Zalo users ở VN, OpenClaw không có
- **Vietnamese market** — không ai focus VN như MY JARVIS
- **B2B pivot** — team workspace cho doanh nghiệp VN
- **Tích hợp VN services** — ngân hàng, VNPAY, Shopee, Grab

### Threats
- OpenClaw thêm Vietnamese support → mất competitive edge
- OpenClaw community quá lớn (319K stars) → mindshare dominance
- Local-first trend → users prefer self-hosted over cloud
- LLM costs giảm → free tier không còn là differentiator

---

## Strategic Recommendations

### 1. Double down on Vietnamese (moat)
OpenClaw KHÔNG có Vietnamese support. Đây là moat mạnh nhất:
- Vietnamese voice (STT/TTS) quality
- Zalo deep integration (Mini App đặc biệt)
- VN services (ngân hàng, VNPAY, Shopee tracking)
- Tiếng Việt không dấu handling

### 2. Don't compete on channel count
OpenClaw có 20+ channels vì community contribute. Thay vì thêm channels, focus làm 8 channels hiện tại excellent.

### 3. Highlight agent intelligence
MY JARVIS có plan-execute, supervision, HITL, injection detection — OpenClaw không có. Market messaging nên focus vào "smart" không chỉ "connected".

### 4. Consider hybrid model
Offer cả cloud (current) và self-hosted option. Giải quyết privacy concern mà giữ convenience.

### 5. Zalo Mini App = killer feature
80M Zalo users. OpenClaw không thể có Zalo Mini App (cần Zalo developer account VN). Đây là distribution channel mà OpenClaw không thể replicate.

### 6. Secure extensibility = B2B moat
OpenClaw bị gọi "security nightmare" — CVE-2026-25253, 341 malicious skills, Chinese gov ban. MY JARVIS có sandboxed execution, AST validation. V8 nên mở rộng integration nhưng giữ security:
- MCP Gateway (curated servers, user toggle)
- Zapier/n8n webhook bridge (inbound + outbound)
- Visual connector (no-code OAuth flow)
- Agent self-extend có HITL approval

**Positioning**: "Powerful như OpenClaw, an toàn cho doanh nghiệp"
