FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY mystgate ./mystgate
RUN uv sync --frozen --no-dev --no-editable \
 && uv pip install --python /app/.venv/bin/python pproxy

FROM python:3.14-slim-bookworm

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ca-certificates \
      curl \
      iproute2 \
      iptables \
      openresolv \
      wireguard-tools \
 && rm -rf /var/lib/apt/lists/* \
 && mkdir -p /data/state /data/logs /etc/wireguard

COPY --from=builder /app/.venv /app/.venv
COPY docker/gateway.sh /usr/local/bin/mystgate-gateway
RUN chmod 755 /usr/local/bin/mystgate-gateway

ENV PATH="/app/.venv/bin:${PATH}" \
    MYSTGATE_STATE_DIRECTORY=/data/state \
    MYSTGATE_LOG_DIRECTORY=/data/logs \
    PYTHONUNBUFFERED=1

WORKDIR /data
VOLUME ["/data/state", "/data/logs"]
EXPOSE 1080 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
  CMD curl -fsS --interface wg0 --max-time 8 https://1.1.1.1/cdn-cgi/trace >/dev/null || exit 1

ENTRYPOINT ["/usr/local/bin/mystgate-gateway"]
