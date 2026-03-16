# MY JARVIS V5 — Production & Growth Layer

> **Status:** 📋 Plan
> **Date:** 2026-03-16
> **Goal:** Đưa JARVIS từ "dev working" → "production-ready product" — deploy thật, users thật, revenue thật

---

## 1. Tại sao cần V5

V4 hoàn thành 7 modules, 24 tools, nhưng:

| Dimension | V4 Score | Gap |
|---|---|---|
| Features | 9/10 | Voice, vision, browser, proactive, integrations |
| Production Readiness | 3/10 | Missing migrations, no prod deploy, no monitoring |
| AI Quality | 6/10 | Agent chọn tool chưa tốt, RAG basic |
| Growth | 0/10 | 0 users, no onboarding, no billing |

**V5 = làm cho product thật sự chạy được với users thật.**

---

## 2. V5 Modules — Phased

### Phase A: Production Hardening (P0) — Ship trước

| # | Module | Effort | Description |
|---|---|---|---|
| M19 | DB Migrations | 1 sprint | Alembic migrations cho GoogleOAuthToken, trigger engine schema changes |
| M20 | Production Deploy | 2 sprints | Prod compose, Cloudflare Tunnel, SSL, health monitoring |
| M21 | Observability | 1 sprint | Structured logging, Sentry alerts, Redis metrics, uptime checks |
| M22 | Security Audit V4 | 1 sprint | Rate limit voice/file endpoints, sanitize file uploads, CSRF on OAuth |
| M23 | Performance | 1 sprint | Connection pooling, query optimization, CDN for static, lazy tool loading |

### Phase B: AI Quality (P1)

| # | Module | Effort | Description |
|---|---|---|---|
| M24 | Smart Tool Selection | 2 sprints | Few-shot examples, tool description optimization, fallback chains |
| M25 | RAG v2 | 2 sprints | Hybrid search (BM25 + vector), re-ranking, chunk optimization |
| M26 | Agentic Workflows | 2 sprints | Multi-step autonomous tasks, sub-agent orchestration, progress tracking |
| M27 | Vietnamese Prompt Tuning | 1 sprint | System prompts A/B test, response quality benchmarks |

### Phase C: Growth & Monetization (P2)

| # | Module | Effort | Description |
|---|---|---|---|
| M28 | User Onboarding | 1 sprint | Guided setup, preference wizard, demo conversation |
| M29 | Subscription & Billing | 2 sprints | Stripe integration, free/pro/pro+ tiers, usage limits |
| M30 | Landing Page v2 | 1 sprint | SEO, demo video, testimonials, CTA → Zalo Mini App |
| M31 | Analytics Dashboard | 1 sprint | User-facing: usage stats, tool history, cost breakdown |
| M32 | Zalo Mini App Submission | 1 sprint | App review, compliance, store listing, push notifications |

---

## 3. Module Specs

### M19: DB Migrations

**Problem:** V4 added `GoogleOAuthToken` model but no Alembic migration. DB schema out of sync.

**Tasks:**
- Generate migration for `google_oauth_tokens` table
- Verify all existing migrations apply cleanly on fresh DB
- Add migration CI check (prevent deploying without migrations)

---

### M20: Production Deploy

**Problem:** Only running dev compose locally. No real users can access.

**Tasks:**
- `docker-compose.prod.yml` verify all V4 services (voice, worker event consumer)
- Cloudflare Tunnel config for `jarvis.pmai.space`
- Env validation: all required secrets checked at startup
- Zero-downtime deploy script (drain → build → swap → health check)
- Backup strategy: pg_dump cron → MinIO

---

### M21: Observability

**Problem:** Sentry captures errors but no proactive monitoring.

**Tasks:**
- Structured JSON logs with request_id across all services
- Health endpoint v2: `/health/ready` checks DB, Redis, MinIO, LiteLLM
- Sentry performance traces on critical paths (chat, voice, browser)
- Uptime monitoring (external ping → Slack alert)
- Redis metrics: event bus lag, trigger fire rate

---

### M22: Security Audit V4

**Problem:** V4 added file uploads, OAuth flows, browser automation — all attack surfaces.

**Tasks:**
- Rate limit: `/voice/transcribe` (5/min), `/files/upload` (10/min), `/chat` (20/min)
- File upload: virus scan hook, filename sanitization, content-type validation
- OAuth: CSRF state token validation, redirect URI whitelist
- Browser: URL allowlist (no internal IPs/localhost), execution timeout
- Playwright: `--no-sandbox` removal, resource limits

---

### M23: Performance

**Problem:** Cold start slow, no caching strategy for V4 features.

**Tasks:**
- Connection pooling: reuse httpx clients (weather, news, Google APIs)
- Lazy import: Playwright only loaded when browse tools called
- Redis cache: weather (15min TTL), news RSS (5min TTL)
- CDN: static assets via Cloudflare
- DB: index on `google_oauth_tokens.user_id`, `proactive_triggers` compound index

---

### M24: Smart Tool Selection

**Problem:** Agent sometimes picks wrong tool or fails to use tools when it should.

**Tasks:**
- Few-shot examples in system prompt per tool category
- Tool description rewrite: clearer args, when-to-use hints
- Fallback chains: if tool fails, try alternative
- Tool usage analytics: track which tools fail, which are underused

---

### M25: RAG v2

**Problem:** Vector-only search misses keyword matches. No re-ranking.

**Tasks:**
- Hybrid search: BM25 (pg_trgm) + vector (pgvector) with RRF fusion
- Re-ranking: Gemini-based relevance scoring on top-K results
- Chunk optimization: smart splitting for Vietnamese text
- Memory dedup: detect near-duplicate memories before storing

---

### M26: Agentic Workflows

**Problem:** Agent does 1 thing at a time. Can't orchestrate complex multi-step tasks.

**Tasks:**
- Workflow templates: "research and summarize", "plan trip", "weekly review"
- Sub-agent delegation with progress callbacks
- Long-running task queue (ARQ) with status tracking
- User approval gates for destructive workflow steps

---

### M27: Vietnamese Prompt Tuning

**Problem:** System prompts are generic. Vietnamese responses could be more natural.

**Tasks:**
- A/B test system prompts (measure response quality via feedback buttons)
- Vietnamese-specific: dấu câu, xưng hô, regional slang handling
- Tool-specific prompts: weather format, news summary style
- Benchmark: 100 test queries, measure accuracy + user satisfaction

---

### M28: User Onboarding

**Tasks:**
- First-login wizard: name, timezone, interests, preferred channels
- Demo conversation: guided tour of key features
- Default triggers: auto-create morning_briefing + deadline_approaching
- Welcome notification via connected channels

---

### M29: Subscription & Billing

**Tasks:**
- Stripe integration: checkout session, webhook, customer portal
- Tiers: Free (5 msg/day, basic tools), Pro (100 msg/day, all tools, $5/mo), Pro+ (unlimited, priority, $15/mo)
- Usage enforcement: check tier before tool execution
- Billing dashboard: current plan, usage, upgrade CTA

---

### M30: Landing Page v2

**Tasks:**
- Hero: demo video/GIF showing voice chat
- Feature grid: 24 tools organized by category
- Social proof: testimonials, user count
- CTA: "Dùng miễn phí trên Zalo" → deep link
- SEO: Vietnamese keywords, meta tags, schema.org

---

### M31: Analytics Dashboard

**Tasks:**
- User-facing page: messages/day, tools used, cost breakdown
- Weekly email digest (via proactive trigger)
- Most-used tools chart, conversation topics breakdown
- Export data (CSV)

---

### M32: Zalo Mini App Submission

**Tasks:**
- Zalo Developer compliance review
- Privacy policy, terms of service pages
- App icon, screenshots, store description
- Push notification integration (Zalo template messages)
- Beta test with 100 users → feedback → fix → submit

---

## 4. Roadmap

```
2026 Q1 (Jan-Mar)     ← V3 + V4 DONE
2026 Q2 (Apr-Jun)
┌─────────────────────────────────┐
│ Phase A: Production Hardening   │
│ M19 Migrations (1w)            │
│ M20 Prod Deploy (2w)           │
│ M21 Observability (1w)         │
│ M22 Security Audit (1w)        │
│ M23 Performance (1w)           │
│ ─── MILESTONE: Production GA ── │
│ Phase B start:                  │
│ M24 Smart Tool Selection (2w)  │
│ M27 Vietnamese Prompts (1w)    │
└─────────────────────────────────┘

2026 Q3 (Jul-Sep)
┌─────────────────────────────────┐
│ Phase B: AI Quality             │
│ M25 RAG v2 (2w)                │
│ M26 Agentic Workflows (2w)     │
│ Phase C start:                  │
│ M28 User Onboarding (1w)       │
│ M29 Subscription (2w)          │
│ M30 Landing Page v2 (1w)       │
└─────────────────────────────────┘

2026 Q4 (Oct-Dec)
┌─────────────────────────────────┐
│ Phase C: Growth                 │
│ M31 Analytics Dashboard (1w)   │
│ M32 Zalo Submission (1w)       │
│ ─── MILESTONE: Public Launch ── │
│ Growth: marketing, feedback,   │
│ iterate based on user data     │
└─────────────────────────────────┘
```

## 5. Success Metrics

| Metric | V4 Baseline | V5 Target |
|---|---|---|
| Production uptime | 0% (dev only) | 99.5% |
| P95 chat latency | unmeasured | < 3s |
| DAU | 0 | 500 |
| Paying users | 0 | 50 |
| MRR | $0 | $500 |
| Tool success rate | unmeasured | > 90% |
| User retention D7 | N/A | 40% |
| Zalo Mini App rating | N/A | 4.5+ |
| NPS | N/A | 50+ |

## 6. Risks

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Playwright resource usage in prod | High | Medium | Lazy load, resource limits, max concurrent sessions |
| Stripe VN payment methods | Medium | High | Support MoMo/VNPay via Stripe alternative or direct |
| Zalo app rejection | Medium | High | Submit early, have web fallback |
| LLM cost at scale | Medium | High | Aggressive caching, model routing by complexity |
| User acquisition | High | High | Zalo distribution, content marketing, referral program |

## 7. Dependencies

```
M19 (Migrations) ──→ M20 (Prod Deploy) ──→ M32 (Zalo Submission)
                          │
M21 (Observability) ──────┘
M22 (Security) ───────────┘
M23 (Performance) ────────┘

M24 (Tool Selection) ── independent
M25 (RAG v2) ── independent
M26 (Agentic) ── depends on M24
M27 (Prompts) ── independent

M28 (Onboarding) ── depends on M20
M29 (Billing) ── depends on M20
M30 (Landing) ── independent
M31 (Analytics) ── depends on M20
```

Critical path: **M19 → M20 → M22 → Production GA → M28/M29 → M32 → Public Launch**
