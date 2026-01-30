FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=0
WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

ADD . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

FROM python:3.12-slim-bookworm
LABEL org.opencontainers.image.source="https://github.com/Kuass/oracle-db-mcp"
LABEL org.opencontainers.image.description="Oracle Database MCP Server"
LABEL org.opencontainers.image.licenses="MIT"

RUN apt-get update && apt-get install -y \
    libaio1 \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

RUN wget https://download.oracle.com/otn_software/linux/instantclient/2350000/instantclient-basic-linux.x64-23.5.0.24.07.zip -O /tmp/instantclient.zip \
    && unzip /tmp/instantclient.zip -d /opt/oracle \
    && rm /tmp/instantclient.zip \
    && echo /opt/oracle/instantclient_23_5 > /etc/ld.so.conf.d/oracle-instantclient.conf \
    && ldconfig

ENV LD_LIBRARY_PATH=/opt/oracle/instantclient_23_5:$LD_LIBRARY_PATH

COPY --from=builder --chown=app:app /app /app
ENV PATH="/app/.venv/bin:$PATH"

RUN useradd -m -u 1000 app
COPY docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh
USER app

EXPOSE 8000
ENTRYPOINT ["/app/docker-entrypoint.sh", "oracle-db-mcp"]
CMD []
