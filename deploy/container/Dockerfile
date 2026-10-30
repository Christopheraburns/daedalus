# Daedalus as a plain container: the Builder (UI + API) and the Server (controller + agentgateway) in one image.
# Build from the repository root:  docker build -f deploy/container/Dockerfile -t daedalus:local .
# Nothing here depends on Cloudera AI Workbench; the Workbench runtime is runtime/Dockerfile.
ARG PYTHON_IMAGE=python:3.12-slim-bookworm
ARG NODE_IMAGE=node:22-bookworm-slim

# ── 1. Build the Builder UI ──────────────────────────────────────────────────────────────────
FROM ${NODE_IMAGE} AS ui
WORKDIR /ui
COPY apps/builder-ui/package.json apps/builder-ui/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY apps/builder-ui/ ./
RUN npm run build

# ── 2. Runtime ───────────────────────────────────────────────────────────────────────────────
FROM ${PYTHON_IMAGE}
ARG TARGETARCH
ARG AGENTGATEWAY_VERSION=1.6.0
ARG AGENTGATEWAY_SHA256_AMD64=496ed27e6a96b55a9ad7cabe5c2be7172511f44a3cb113e533d22bf93a7f079d
ARG AGENTGATEWAY_SHA256_ARM64=b59ecac31103bb317d1377fd42b0cb25cd9a21f8c3f1d9ee14c3ff05f3f91abf
ARG GIT_REVISION=unknown

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

# agentgateway, pinned by version and checksum for both architectures.
RUN set -eu; case "${TARGETARCH}" in amd64) sum="${AGENTGATEWAY_SHA256_AMD64}";; arm64) sum="${AGENTGATEWAY_SHA256_ARM64}";; *) echo "unsupported TARGETARCH ${TARGETARCH}" >&2; exit 1;; esac; \
    mkdir -p /opt/mcp-factory/bin /opt/mcp-factory/licenses; \
    curl --fail --show-error --silent --location --retry 3 \
        "https://github.com/agentgateway/agentgateway/releases/download/v${AGENTGATEWAY_VERSION}/agentgateway-linux-${TARGETARCH}" \
        --output /tmp/agentgateway; \
    printf '%s  %s\n' "${sum}" /tmp/agentgateway | sha256sum --check --strict -; \
    install -m 0755 /tmp/agentgateway /opt/mcp-factory/bin/agentgateway; rm /tmp/agentgateway
COPY runtime/licenses/agentgateway-LICENSE /opt/mcp-factory/licenses/agentgateway-LICENSE

# The same locked Python set as the Workbench runtime, installed into a venv.
COPY runtime/requirements.lock /opt/mcp-factory/requirements.lock
RUN python3 -m venv /opt/mcp-factory/venv \
    && /opt/mcp-factory/venv/bin/python -m pip install --no-cache-dir --require-hashes --only-binary=:all: -r /opt/mcp-factory/requirements.lock \
    && /opt/mcp-factory/venv/bin/python -m pip check

# An unprivileged user; /tmp holds the Server's per-release state and the Builder's candidate gateways.
RUN groupadd --gid 10001 daedalus && useradd --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin daedalus

WORKDIR /app
COPY --chown=daedalus:daedalus services/ /app/services/
COPY --chown=daedalus:daedalus schemas/ /app/schemas/
COPY --chown=daedalus:daedalus --from=ui /ui/dist/ /app/apps/builder-ui/dist/
COPY --chown=daedalus:daedalus deploy/container/entrypoint.sh /app/entrypoint.sh
RUN chmod 0755 /app/entrypoint.sh && find /app/services -name __pycache__ -prune -exec rm -rf {} +

ENV PATH="/opt/mcp-factory/venv/bin:/opt/mcp-factory/bin:${PATH}" \
    PYTHONPATH=/app/services \
    PYTHONUNBUFFERED=1 \
    MCP_FACTORY_PYTHON=/opt/mcp-factory/venv/bin/python \
    FACTORY_GATEWAY_BINARY=/opt/mcp-factory/bin/agentgateway \
    FACTORY_CODE_REVISION=${GIT_REVISION}

USER 10001:10001  # numeric, so Kubernetes can verify runAsNonRoot
EXPOSE 8000 8081
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["builder"]
