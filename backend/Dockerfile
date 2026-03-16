FROM python:3.12-slim AS base
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY pyproject.toml .
RUN uv pip install --system .
# Install Playwright Chromium + system deps
RUN playwright install --with-deps chromium

# --- Dev target ---
FROM base AS dev
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# --- Prod target ---
FROM base AS prod
COPY . .
RUN adduser --system --no-create-home appuser
USER appuser
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
