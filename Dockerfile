# ---------- ASTMA backend (FastAPI + agents) ----------
FROM python:3.13-slim

RUN pip install --no-cache-dir uv==0.13.9

WORKDIR /app

# Install dependencies first (cached unless pyproject/uv.lock change)
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev

# Then copy the code
COPY . .

EXPOSE 8000

# Bring the database up to date, then start the API.
# The MCP server (started by the executor) calls this same API at 127.0.0.1:8000.
CMD ["sh", "-c", "uv run --no-sync alembic upgrade head && uv run --no-sync uvicorn app.main:app --host 0.0.0.0 --port 8000"]
