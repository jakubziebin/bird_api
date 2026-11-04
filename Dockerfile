FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.7 /uv /uvx /bin/

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN uv sync --frozen --no-cache


EXPOSE 8000

CMD ["uv", "run", "uvicorn", "src.bird_api.main:bird_app", "--host", "0.0.0.0", "--port", "8000"]
