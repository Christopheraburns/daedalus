#!/bin/sh
# Daedalus container entrypoint.
#   builder   run registry migrations, then serve the Builder UI and API (FACTORY_BUILDER_PORT, default 8000)
#   server    serve one MCP server: the controller supervising agentgateway (FACTORY_GATEWAY_PORT, default 8081)
#   migrate   run registry migrations and exit
#   anything else is executed as a command inside the image (e.g. `python -m pytest`).
set -eu
command="${1:-builder}"
[ "$#" -gt 0 ] && shift

# In a container the process must listen on all interfaces; the Workbench adapter overrides this with loopback.
export FACTORY_BUILDER_BIND="${FACTORY_BUILDER_BIND:-0.0.0.0}"
export FACTORY_GATEWAY_BIND="${FACTORY_GATEWAY_BIND:-0.0.0.0}"

case "$command" in
  builder)
    python -m factory.migrate
    exec python -m uvicorn factory.api:create_app --factory --host "$FACTORY_BUILDER_BIND" --port "${FACTORY_BUILDER_PORT:-8000}" --no-access-log "$@"
    ;;
  server)
    : "${FACTORY_SERVER_ID:?Set FACTORY_SERVER_ID to the server workspace this container serves}"
    exec python -m factory.controller "$@"
    ;;
  migrate)
    exec python -m factory.migrate "$@"
    ;;
  *)
    exec "$command" "$@"
    ;;
esac
