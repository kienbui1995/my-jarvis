# Migration: API Design & Error Handling Standard — My Jarvis

## Hien trang (da co gi)

| Component | Status | File |
|---|---|---|
| RequestIDMiddleware | Chua co | — |
| Global exception handler | Chua co | — |
| SecurityHeadersMiddleware | Co | `backend/core/headers.py` |
| RateLimitMiddleware | Co, tier-based, tra `{detail: "..."}` | `backend/core/rate_limit.py` |
| Version header middleware | Co | `backend/main.py:99-103` |
| Frontend ApiError | Chua co (dung generic Error) | `frontend/lib/api.ts` |
| Sentry | Co | `backend/main.py` |
| Middleware stack | SecurityHeaders → CORS → RateLimit | `backend/main.py:84-96` |

## Can thay doi

### 1. Backend: Tao `backend/core/errors.py`

```python
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message


def not_found(resource: str = "Resource") -> AppError:
    return AppError(404, "NOT_FOUND", f"{resource} not found")

def unauthorized(message: str = "Authentication required") -> AppError:
    return AppError(401, "UNAUTHORIZED", message)

def forbidden(message: str = "Permission denied") -> AppError:
    return AppError(403, "FORBIDDEN", message)

def conflict(message: str = "Resource already exists") -> AppError:
    return AppError(409, "CONFLICT", message)

def bad_request(message: str = "Bad request") -> AppError:
    return AppError(400, "BAD_REQUEST", message)

def rate_limited(message: str = "Too many requests") -> AppError:
    return AppError(429, "RATE_LIMITED", message)


def _get_request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _error_body(code: str, message: str, request_id: str | None, **extra) -> dict:
    """Build error response with backward-compatible `detail` field."""
    return {
        "detail": message,  # backward compat — xoa sau khi frontend migrate xong
        "error": {"code": code, "message": message, "request_id": request_id, **extra},
    }


def setup_error_handlers(app: FastAPI):
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.code, exc.message, _get_request_id(request)),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        code_map = {400: "BAD_REQUEST", 401: "UNAUTHORIZED", 403: "FORBIDDEN", 404: "NOT_FOUND", 409: "CONFLICT", 429: "RATE_LIMITED"}
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(code_map.get(exc.status_code, "HTTP_ERROR"), exc.detail, _get_request_id(request)),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        details = [{"field": ".".join(str(l) for l in e["loc"][1:]), "message": e["msg"]} for e in exc.errors()]
        return JSONResponse(
            status_code=422,
            content=_error_body("VALIDATION_ERROR", "Invalid input data", _get_request_id(request), details=details),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        import logging
        logging.getLogger(__name__).error(f"Unhandled error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=_error_body("INTERNAL_ERROR", "Internal server error", _get_request_id(request)),
        )
```

### 2. Backend: Tao `backend/core/request_id.py`

```python
from uuid import uuid4
from starlette.types import ASGIApp, Receive, Scope, Send


class RequestIDMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = dict(scope.get("headers", [])).get(b"x-request-id", str(uuid4()).encode()).decode()
        scope.setdefault("state", {})["request_id"] = request_id

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode()))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)
```

### 3. Backend: Sua `backend/main.py`

Them RequestIDMiddleware vao middleware stack va setup error handlers:

```python
from core.request_id import RequestIDMiddleware
from core.errors import setup_error_handlers

# --- Middleware --- (sua lai section nay)
app.state._debug = settings.DEBUG
app.add_middleware(RequestIDMiddleware)      # <-- THEM (dat dau tien, truoc SecurityHeaders)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else [f"https://{settings.DOMAIN}"],
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=not settings.DEBUG,
    max_age=600,
)
if settings.RATE_LIMIT_ENABLED:
    app.add_middleware(RateLimitMiddleware)

# Error handlers (dat SAU middleware, TRUOC routes)
setup_error_handlers(app)
```

Luu y middleware order: RequestID phai chay TRUOC cac middleware khac de moi middleware/handler deu co request_id.

### 4. Backend: Sua `backend/core/rate_limit.py`

Doi error response tu `{detail: "..."}` sang format chuan.

Truoc:
```python
        # Per-endpoint stricter limits
        ...
        if endpoint_limit and not await _check_rate(...):
            return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)

        # Read vs write RPM
        ...
        if not await _check_rate(redis, rpm_key, rpm_limit):
            return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)

        # Daily limit
        if is_write and not await _check_rate(...):
            return JSONResponse({"detail": "Daily limit exceeded"}, status_code=429)
```

Sau — tao helper va thay tat ca JSONResponse:
```python
def _rate_limit_response(request: Request, message: str = "Rate limit exceeded") -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        {"error": {"code": "RATE_LIMITED", "message": message, "request_id": request_id}},
        status_code=429,
    )

# Thay cac cho:
return _rate_limit_response(request)
return _rate_limit_response(request)
return _rate_limit_response(request, "Daily limit exceeded")
```

### 5. Frontend: Sua `frontend/lib/api.ts`

Luu y: path la `frontend/lib/` (khong phai `frontend/src/lib/`).

Them ApiError class va update error handling:

Truoc (`api.ts`):
```typescript
  if (!res.ok) throw new Error(await res.text());
```

Sau:
```typescript
export class ApiError extends Error {
  status: number;
  code: string;
  requestId: string | null;

  constructor(status: number, message: string, code = "UNKNOWN", requestId: string | null = null) {
    super(message);
    this.status = status;
    this.code = code;
    this.requestId = requestId;
  }
}

// Trong function request<T>():
  if (!res.ok) {
    let message = `API error: ${res.status}`;
    let code = "UNKNOWN";
    let requestId: string | null = null;
    try {
      const body = await res.json();
      if (body.error) {
        message = body.error.message || message;
        code = body.error.code || code;
        requestId = body.error.request_id || null;
      } else if (typeof body === "string") {
        message = body;
      } else {
        message = body.detail || message;
      }
    } catch {
      // Response khong phai JSON — fallback text
      try { message = await res.text(); } catch {}
    }
    throw new ApiError(res.status, message, code, requestId);
  }
```

## Checklist migration

- [ ] Tao `backend/core/errors.py` (AppError + helpers + setup_error_handlers)
- [ ] Tao `backend/core/request_id.py` (RequestIDMiddleware)
- [ ] Sua `backend/main.py`: them RequestIDMiddleware + setup_error_handlers
- [ ] Sua `backend/core/rate_limit.py`: doi 3 cho JSONResponse sang format chuan
- [ ] Them `ApiError` class vao `frontend/lib/api.ts`
- [ ] Update error handling trong `request<T>()` function
- [ ] Test: rate limit → nhan `{error: {code: "RATE_LIMITED", ...}}`
- [ ] Test: 401 auto-refresh → van hoat dong
- [ ] Test: API binh thuong → response khong thay doi

## Luu y

- **Middleware order**: RequestID → SecurityHeaders → CORS → RateLimit — RequestID phai dau tien. `scope["state"]` tu ASGI middleware truyen duoc vao `request.state` cua BaseHTTPMiddleware
- **Backward compatible**: Response giu ca `detail` (cho frontend cu) lan `error` (format moi)
- `SecurityHeadersMiddleware` giu nguyen, khong thay doi
- Version header middleware giu nguyen
- Tier-based rate limiter phuc tap (free/pro/pro_plus) — chi doi response format, logic giu nguyen
- WebSocket rate limiting (`check_ws_rate()`) doc lap, khong bi anh huong boi RequestIDMiddleware (chi chay tren HTTP scope)
- Frontend dung `localStorage` cho token (khac SaleAI dung cookie) — giu nguyen pattern nay
- Frontend path la `frontend/lib/` (khong co `src/`)
- Public API (`/api/public/v1/`) — kiem tra xem co external consumer nao khong truoc khi deploy. `detail` field giu backward compat
- Sentry van capture exceptions binh thuong
