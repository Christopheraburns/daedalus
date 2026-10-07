# Control plane and API access policies

Daedalus is the control plane for MCP servers created in a Cloudera AI Workbench project. The Builder owns desired state, governance, releases, deployment, and observability. Each generated MCP Server application owns the request path: MCP protocol handling, authentication, local policy enforcement, tool validation, API calls, timeouts, circuit breakers, and health reporting.

The control plane publishes immutable releases and policy versions. A server applies the last-known-good configuration locally and continues serving if the control plane is temporarily unavailable. The server must revalidate origins and tool bundles before activation; it must not depend on a control-plane request for every tool call.

## API access policies

Approved API origins are project/server-scoped records managed from the Builder's **API access policies** screen. Each record contains an origin, description, enabled state, revision, and audit history. Origins are scheme and host only, for example `https://api.example.com`; paths, credentials, queries, and fragments are rejected.

The Builder API and MCP Server read the same policy records. The environment variable `FACTORY_ALLOWED_API_ORIGINS` remains a bootstrap fallback for initial environments and migration. Existing bootstrap origins are seeded into the initial policy set and can be edited or removed through the UI after the migration.

Policy changes are administrator/author actions, increment the server revision, and are enforced by connection validation, tool validation, test compilation, release compilation, and server startup/reconciliation. A policy change should be followed by validation and a new release when it affects an active server.

## Lifecycle ownership

The control plane manages server workspaces, tools, connections, origin policies, secret references, validation, testing, publishing, deployment, rollback, RBAC, audit, health, metrics, and drift detection. The generated server manages the MCP endpoint, client authentication, request routing, argument/schema validation, origin and timeout enforcement, tool execution, runtime resilience, and telemetry emission.

Secrets are referenced by identifier and supplied through Cloudera or a vault; raw credentials do not belong in tool definitions, browser state, or release bundles. Control-plane policy changes should be versioned, auditable, and delivered to the server as desired state. The server remains the final enforcement point.
