FROM python:3.13-slim AS astrocollector

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the application into the container.
COPY . /app

# Install the application dependencies.
WORKDIR /app
ENV UV_HTTP_TIMEOUT=120
RUN uv sync --frozen --no-cache
ENV PATH="/app/.venv/bin:$PATH"

RUN chmod +x /app/entrypoint.sh
#CMD ["/app/entrypoint.sh"]
