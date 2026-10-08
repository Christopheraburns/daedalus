# Build from the repository root; see runtime/README.md.
# Cloudera PBJ Workbench Python 3.12 Standard 2026.08.1-b5, pinned by digest.
ARG BASE_IMAGE=docker.repository.cloudera.com/cloudera/cdsw/ml-runtime-pbj-workbench-python3.12-standard:2026.08.1-b5@sha256:106220420aa35e733fe362a07a0f14af11d2d27f58aa527fa13d931598ef7262
FROM ${BASE_IMAGE}

ARG BASE_IMAGE
ARG TARGETARCH
ARG RUNTIME_SHORT_VERSION=0.1
ARG RUNTIME_MAINTENANCE_VERSION=1
ARG AGENTGATEWAY_VERSION=1.6.0
ARG AGENTGATEWAY_SHA256=496ed27e6a96b55a9ad7cabe5c2be7172511f44a3cb113e533d22bf93a7f079d
ARG NODE_VERSION=22.23.3
ARG NODE_SHA256=df450af89261115ef9f9e3830c3eeb2cc9213b63c720b1af623cb5dcbe2e02de

USER root

# Fail before downloading if the selected base does not match the locked profile.
RUN test "${TARGETARCH}" = amd64 \
    && printf '%s' "${BASE_IMAGE}" | grep -Eq '@sha256:[a-f0-9]{64}$' \
    && test "$(id -u cdsw)" = 8536 \
    && test "$(id -g cdsw)" = 8536 \
    && test -n "${ML_RUNTIME_EDITOR}" \
    && python3 -c 'import sys; assert sys.version_info[:2] == (3, 12), "Select a Python 3.12 Cloudera runtime"' \
    && . /etc/os-release && test "${ID}" = ubuntu

# Development tools for Python/TypeScript work; no nested Docker. The PostgreSQL server is
# only started by deploy/workbench/launch_postgres.py, as cdsw, with data in project storage.
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        ca-certificates curl git build-essential libpq-dev xz-utils postgresql-16 \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/mcp-factory/bin /opt/mcp-factory/node /opt/mcp-factory/licenses \
    && curl --fail --show-error --silent --location --retry 3 \
        "https://github.com/agentgateway/agentgateway/releases/download/v${AGENTGATEWAY_VERSION}/agentgateway-linux-amd64" \
        --output /tmp/agentgateway \
    && printf '%s  %s\n' "${AGENTGATEWAY_SHA256}" /tmp/agentgateway | sha256sum --check --strict - \
    && install -m 0755 /tmp/agentgateway /opt/mcp-factory/bin/agentgateway \
    && curl --fail --show-error --silent --location --retry 3 \
        "https://nodejs.org/download/release/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.xz" \
        --output /tmp/node.tar.xz \
    && printf '%s  %s\n' "${NODE_SHA256}" /tmp/node.tar.xz | sha256sum --check --strict - \
    && tar -xJf /tmp/node.tar.xz -C /opt/mcp-factory/node --strip-components=1 \
    && rm /tmp/agentgateway /tmp/node.tar.xz

COPY runtime/requirements.lock /opt/mcp-factory/requirements.lock
# Do not replace the platform Python, Jupyter packages, kernel, or pip settings.
# Cloudera's pip configuration may default to --user; disable it for this venv only.
RUN python3 -m venv /opt/mcp-factory/venv \
    && PIP_CONFIG_FILE=/dev/null PIP_USER=false \
        /opt/mcp-factory/venv/bin/python -m pip install \
        --no-cache-dir --require-hashes --only-binary=:all: \
        -r /opt/mcp-factory/requirements.lock \
    && /opt/mcp-factory/venv/bin/python -m pip check \
    && /opt/mcp-factory/venv/bin/python -m pip inspect \
        > /opt/mcp-factory/python-packages.json

COPY runtime/bin/mcp-factory-python /opt/mcp-factory/bin/mcp-factory-python
COPY runtime/smoke_check.py /opt/mcp-factory/smoke_check.py
COPY runtime/licenses/agentgateway-LICENSE /opt/mcp-factory/licenses/agentgateway-LICENSE
RUN chmod 0755 /opt/mcp-factory/bin/mcp-factory-python \
    && chmod -R a+rX /opt/mcp-factory

# Preserve inherited editor, kernel, metadata version, startup command and workdir.
ENV PATH="/opt/mcp-factory/bin:/opt/mcp-factory/node/bin:${PATH}" \
    MCP_FACTORY_PYTHON="/opt/mcp-factory/venv/bin/python" \
    ML_RUNTIME_EDITION="MCP Factory Development" \
    ML_RUNTIME_SHORT_VERSION="${RUNTIME_SHORT_VERSION}" \
    ML_RUNTIME_MAINTENANCE_VERSION="${RUNTIME_MAINTENANCE_VERSION}" \
    ML_RUNTIME_DESCRIPTION="MCP Factory development: agentgateway, isolated Python backend tools, Node.js"
ENV ML_RUNTIME_FULL_VERSION="${ML_RUNTIME_SHORT_VERSION}.${ML_RUNTIME_MAINTENANCE_VERSION}"

LABEL com.cloudera.ml.runtime.edition="${ML_RUNTIME_EDITION}" \
      com.cloudera.ml.runtime.short-version="${ML_RUNTIME_SHORT_VERSION}" \
      com.cloudera.ml.runtime.maintenance-version="${ML_RUNTIME_MAINTENANCE_VERSION}" \
      com.cloudera.ml.runtime.full-version="${ML_RUNTIME_FULL_VERSION}" \
      com.cloudera.ml.runtime.description="${ML_RUNTIME_DESCRIPTION}" \
      org.opencontainers.image.title="MCP Factory development runtime" \
      org.opencontainers.image.version="${ML_RUNTIME_FULL_VERSION}" \
      org.opencontainers.image.base.name="${BASE_IMAGE}" \
      dev.mcp-factory.agentgateway.version="${AGENTGATEWAY_VERSION}" \
      dev.mcp-factory.agentgateway.sha256="${AGENTGATEWAY_SHA256}" \
      dev.mcp-factory.node.version="${NODE_VERSION}" \
      dev.mcp-factory.node.sha256="${NODE_SHA256}"

USER cdsw
RUN /opt/mcp-factory/venv/bin/python /opt/mcp-factory/smoke_check.py

# Workbench owns process startup and supplies CDSW_APP_PORT to each Application.
# Application source and launchers belong in the mounted project, not /home/cdsw
# image layers. No ENTRYPOINT, CMD, fixed EXPOSE, or gateway autostart here.
