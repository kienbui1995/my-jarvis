# Public Launch — Web, Free-only Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy MY JARVIS V7.0.0 to production at `jarvis.pmai.space` — public registration, web channel only, free tier only.

**Architecture:** Version bump, hide billing tab, add register rate limit, then rebuild Docker images and deploy production compose with migrations-first ordering. Rebuild also fixes the PyNaCl crash (already in `pyproject.toml`, just needs image rebuild).

**Tech Stack:** Docker Compose, Makefile, Next.js (frontend), FastAPI (backend), Cloudflare Tunnel

---

## File Structure

| Action | File | Purpose |
|--------|------|---------|
| Modify | `backend/pyproject.toml` | Bump version 6.0.0 → 7.0.0 |
| Modify | `frontend/package.json` | Bump version 6.0.0 → 7.0.0 |
| Modify | `frontend/app/(app)/settings/page.tsx` | Remove billing tab |
| Modify | `backend/core/rate_limit.py` | Add register endpoint rate limit |

4 files changed. Rest is deploy/verify.

---

### Task 1: Version Bump

**Files:**
- Modify: `backend/pyproject.toml` (version field)
- Modify: `frontend/package.json` (version field)

- [ ] **Step 1: Bump backend version**

In `backend/pyproject.toml`, change:
```
version = "6.0.0"
```
to:
```
version = "7.0.0"
```

- [ ] **Step 2: Bump frontend version**

In `frontend/package.json`, change:
```json
"version": "6.0.0"
```
to:
```json
"version": "7.0.0"
```

- [ ] **Step 3: Commit**

```bash
git add backend/pyproject.toml frontend/package.json
git commit -m "chore: bump version to 7.0.0"
```

---

### Task 2: Hide Billing Tab

**Files:**
- Modify: `frontend/app/(app)/settings/page.tsx:8` (import)
- Modify: `frontend/app/(app)/settings/page.tsx:10-18` (tabs array)
- Modify: `frontend/app/(app)/settings/page.tsx:267-283` (subscription panel + tab indices)

- [ ] **Step 1: Remove "Goi" tab from tabs array and CreditCard import**

In `frontend/app/(app)/settings/page.tsx`:

Line 8 — remove `CreditCard` from import:
```tsx
import { X, Plus, Shield, Sliders, Brain, Link2, Wrench, ClipboardList } from "lucide-react";
```

Lines 10-18 — remove the billing entry from `tabs`:
```tsx
const tabs = [
  { label: "Hồ sơ", icon: null },
  { label: "Tùy chọn", icon: Sliders },
  { label: "Bộ nhớ", icon: Brain },
  { label: "Kết nối", icon: Link2 },
  { label: "Tools", icon: Wrench },
  { label: "Audit", icon: ClipboardList },
] as const;
```

- [ ] **Step 2: Remove subscription panel and fix tab indices**

Delete the subscription panel block (lines 268-280):
```tsx
{tab === 4 && (
  <div className="space-y-4">
    ...entire subscription UI...
  </div>
)}
```

Update remaining tab indices:
- `{tab === 5 && <ToolPermissionsTab />}` → `{tab === 4 && <ToolPermissionsTab />}`
- `{tab === 6 && <AuditTab />}` → `{tab === 5 && <AuditTab />}`

- [ ] **Step 3: Commit**

```bash
git add frontend/app/\(app\)/settings/page.tsx
git commit -m "feat: hide billing tab for free-only launch"
```

---

### Task 3: Rate Limit Registration

**Files:**
- Modify: `backend/core/rate_limit.py:21-31`

- [ ] **Step 1: Move register out of SKIP_PREFIXES**

In `backend/core/rate_limit.py`, the entire `/api/v1/auth/` prefix is currently skipped (line 22). Change to skip only specific auth endpoints, not register:

```python
SKIP_PREFIXES = ("/api/v1/auth/login", "/api/v1/auth/refresh", "/api/v1/auth/google", "/api/v1/auth/zalo-miniapp", "/api/v1/webhooks/")
```

- [ ] **Step 2: Add register to ENDPOINT_LIMITS**

Add the register endpoint with a 3 rpm limit:

```python
ENDPOINT_LIMITS = {
    "/api/v1/auth/register": 3,
    "/api/v1/voice/transcribe": 5,
    "/api/v1/voice/speak": 10,
    "/api/v1/files/upload": 10,
    "/api/public/v1/chat": 10,
    "/api/public/v1/tools": 30,
    "/api/v1/chat": 20,
}
```

Note: unauthenticated requests use IP as identity (`cf-connecting-ip` → `x-forwarded-for` → `client.host`). Register also gets the general free-tier write limit (30 rpm), but the 3 rpm endpoint limit is the binding constraint.

- [ ] **Step 3: Commit**

```bash
git add backend/core/rate_limit.py
git commit -m "feat: rate limit registration 3rpm per IP"
```

---

### Task 4: Deploy Production

**Prerequisites:** Tasks 1-3 committed. `.env.prod` verified:
- `APP_ENV=production`, `DEBUG=false` — confirmed
- `SECRET_KEY` = 64 chars — confirmed
- `DOMAIN=jarvis.pmai.space` — confirmed
- All infra passwords set (POSTGRES_PASSWORD, REDIS_PASSWORD, MINIO_ACCESS_KEY, MINIO_SECRET_KEY)

Note: The rebuild will fix the PyNaCl crash — `pyproject.toml` already has the dependency, the old V3 image just didn't have it.

- [ ] **Step 1: Stop dev containers**

```bash
make dev-down
```

Expected: All 6 containers stop.

- [ ] **Step 2: Start infra only**

```bash
PROD="docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml"
$PROD up -d postgres redis minio
```

Expected: postgres, redis, minio start and become healthy.

- [ ] **Step 3: Build backend image**

```bash
$PROD build backend
```

Expected: Image built with V7 code + all dependencies (PyNaCl included).

- [ ] **Step 4: Run migrations before backend starts**

```bash
$PROD run --rm backend alembic upgrade head
```

Expected: 11 migrations applied (or "Already at head" if DB was already migrated from dev).

- [ ] **Step 5: Start all services**

```bash
make prod
```

Expected: All 6 services running. `docker compose ps` shows all healthy.

- [ ] **Step 6: Verify health**

```bash
# Wait for services to be ready (healthcheck interval 30s)
sleep 35

# Check from host
curl -s https://jarvis.pmai.space/health
```

Expected: `{"status": "ok", "version": "7.0.0"}`

```bash
curl -s https://jarvis.pmai.space/health/ready
```

Expected: All dependencies healthy (postgres, redis, minio, litellm).

If Cloudflare Tunnel isn't routing yet, check directly:
```bash
docker exec my-jarvis-backend-1 python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/health').read().decode())"
```

---

### Task 5: Smoke Test

All tests on `https://jarvis.pmai.space`.

- [ ] **Step 1: Landing page**

Open `https://jarvis.pmai.space` in browser.
Expected: Landing page loads with hero, features, CTA.

- [ ] **Step 2: Register**

Create account with email + password (8+ chars, digit + letter).
Expected: Account created, redirected to onboarding.

- [ ] **Step 3: Onboarding**

Complete wizard.
Expected: Default triggers created (morning_briefing + deadline_approaching).

- [ ] **Step 4: Chat**

Send: "Xin chao JARVIS"
Expected: Agent responds in Vietnamese via WebSocket streaming.

- [ ] **Step 5: Tool call**

Send: "Thoi tiet Ha Noi hom nay"
Expected: weather_vn tool called, returns weather data.

- [ ] **Step 6: Settings — no billing tab**

Navigate to Settings.
Expected: 6 tabs (Hồ sơ, Tùy chọn, Bộ nhớ, Kết nối, Tools, Audit). NO "Gói" tab.

- [ ] **Step 7: Auth protection**

```bash
curl -s https://jarvis.pmai.space/api/v1/conversations
```
Expected: 401 Unauthorized.

- [ ] **Step 8: Rate limit on register**

```bash
for i in {1..5}; do
  curl -s -o /dev/null -w "%{http_code}\n" -X POST \
    https://jarvis.pmai.space/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d '{"email":"ratelimit'$i'@test.com","password":"Test1234"}'
done
```
Expected: First 3 return 200 (success), requests 4-5 return 429 (rate limited).

- [ ] **Step 9: Clean up test accounts**

Delete test accounts created during smoke test from database.

---

### Rollback Plan

If anything goes wrong:

```bash
make prod-down && make dev
```

Stops production and restarts dev mode immediately.
