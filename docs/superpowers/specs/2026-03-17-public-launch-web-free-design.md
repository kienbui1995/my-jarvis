# Public Launch — Web, Free-only

> Date: 2026-03-17 | Status: Approved

## Goal

Deploy MY JARVIS V7.0.0 to production at `jarvis.pmai.space`. Public registration, web channel only, free tier only.

## Current State

- Dev containers running with V3 images, V7 code mounted
- Backend crashing: `ModuleNotFoundError: No module named 'nacl'` (PyNaCl for Discord)
- Worker running OK (morning briefings active)
- `.env.prod` exists
- Cloudflare Tunnel configured for `jarvis.pmai.space`

## Changes Required

### 1. Hide Billing UI (frontend only)

- Settings page: hide "Goi" (Subscription) tab
- No backend changes — billing routes stay, just UI hidden
- Default tier remains `free` (already the default in User model)

### 2. Rate limit registration

- Add `/api/v1/auth/register` to endpoint rate limits: 3 requests/minute per IP
- Prevents mass account creation (no CAPTCHA needed for launch)

### 3. Verify .env.prod

Confirm these are set correctly:
- `APP_ENV=production`
- `DEBUG=false`
- `SECRET_KEY` = strong random (>= 32 chars)
- `POSTGRES_PASSWORD`, `REDIS_PASSWORD`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY` = strong
- `LITELLM_API_KEY` = valid
- `GOOGLE_API_KEY` = valid (for Gemini)
- `DOMAIN=jarvis.pmai.space`

### 4. Deploy Steps

```bash
# 1. Stop dev
make dev-down

# 2. Build + start infra only (postgres, redis, minio)
PROD="docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml"
$PROD up -d postgres redis minio

# 3. Run migrations BEFORE backend starts
$PROD run --rm backend alembic upgrade head

# 4. Start all services
make prod

# 5. Verify
curl https://jarvis.pmai.space/health
curl https://jarvis.pmai.space/health/ready
```

### 5. Smoke Test

- [ ] Landing page loads at `jarvis.pmai.space`
- [ ] Register (email + password)
- [ ] Login -> onboarding wizard
- [ ] Chat (text) -> agent responds
- [ ] Tool call (weather, task create)
- [ ] Settings page (no billing tab visible)
- [ ] WebSocket chat works (`wss://jarvis.pmai.space/api/v1/ws/chat`)
- [ ] Unauthenticated request to `/api/v1/conversations` returns 401
- [ ] Rate limit works (rapid requests get 429)

### Rollback

```bash
make prod-down && make dev
```

## Out of Scope

- Other channels (Zalo, Telegram, WhatsApp, Slack, Discord)
- Paid tiers / Stripe
- Monitoring dashboard (Grafana/Prometheus)
- Email verification (fast-follow)
- CAPTCHA (fast-follow if abuse detected)

## Risks

| Risk | Mitigation |
|------|-----------|
| Single server | Acceptable for initial launch |
| LLM costs | Free tier budget $0.02/day/user |
| Registration abuse | Rate limit 3/min per IP |
| Unused webhooks exposed | Handlers reject when tokens empty (existing behavior) |
| MinIO creds | Prod compose does not expose ports externally |
