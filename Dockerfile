FROM python:3.12-slim AS builder

WORKDIR /build

# Build deps for psycopg binary and native extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip hatchling \
    && pip install --no-cache-dir .

# ────────────────────────────────────────
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY src/ src/
COPY doc/ doc/
COPY AGENTS.md AGENTS.md
COPY skills/ skills/

ENV PYTHONPATH=/app/src

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "ai_agent.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
