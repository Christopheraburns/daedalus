# Daedalus MCP Builder

Build and test MCP tools locally with a persistent canvas, PostgreSQL registry,
and a supervised Agent Gateway. Track completed features and remaining work in
[the implementation tracker](docs/IMPLEMENTATION_STATUS.md).

## Local development

Prerequisites: Docker Desktop with Compose, Python 3 for setup, and the custom
runtime image described in [runtime/README.md](runtime/README.md).

```sh
python3 scripts/dev_setup.py
docker compose up --build -d
```

Open **http://localhost:5173**. The local Compose stack uses
`FACTORY_AUTH_MODE=development-open`, so the Builder enters as an administrator
without a management token. It binds every exposed port to `127.0.0.1` only.
The setup script preserves an existing `.env`; keep it private because it still
contains the separate MCP endpoint token. Set `MCP_FACTORY_RUNTIME_IMAGE` if your
runtime image has a different tag.

1. Add an API connection using `http://mock-api:8080`.
2. Click or drag **Find inventory item** onto the canvas.
3. Edit and save the tool, then validate it and run it in the test playground.
4. Review and publish. Wait for the release to become active.

Use **Import OpenAPI** in the left panel to inspect a Swagger/OpenAPI URL. The
Builder lists supported GET and POST operations without creating tools. Select
an operation to reuse an existing connection or create a new approved connection
and add that operation as a draft. The left building-blocks panel and right
inspector can be collapsed with their header controls for a wider canvas view.

The live MCP endpoint is **http://localhost:8081/mcp** and uses the separate
`FACTORY_MCP_TOKEN` as a Bearer token. Management tokens cannot access it.
Draft tests use isolated candidate gateways; saving a draft does not publish it.
Moving nodes only changes the saved layout. Release history can restore a
previous published snapshot while keeping the current drafts.

Backend source and UI source are mounted into Docker with reload enabled.
PostgreSQL data survives `docker compose down` and subsequent startup.
`docker compose down -v` deletes the local database and dependency volumes.
After changing frontend dependencies, run `docker compose exec ui npm ci`.

```sh
docker compose ps
docker compose logs --tail=100 api server
docker compose exec ui npm run build
```

If a release is blocked, test every included tool after changing its definition
or connection. For a revision conflict, reload before saving. Add real backend
origins to `FACTORY_ALLOWED_API_ORIGINS` and recreate the API and Server services;
the same allowlist must apply to both. Browser origins are configured separately.

## Checks

Use a separate Compose project and ports to preserve your working drafts:

```sh
docker compose -p daedalus-checks --env-file .env --env-file tests/ports.env up --build -d
docker compose -p daedalus-checks --env-file .env --env-file tests/ports.env exec -T ui npm run build
docker compose -p daedalus-checks --env-file .env --env-file tests/ports.env restart api
docker compose -p daedalus-checks --env-file .env --env-file tests/ports.env exec -T api /opt/mcp-factory/venv/bin/python -m pytest -q -p no:cacheprovider tests
cd apps/builder-ui
npm ci
npx playwright install chromium
npm run test:e2e
cd ../..
python3 tests/check_restart.py
docker compose -p daedalus-checks --env-file .env --env-file tests/ports.env down
```

Backend tests create and remove unique PostgreSQL schemas. Browser tests author
fixtures in the separate test project's database. Never point these tests at a
shared deployment. Screenshots are stored under `apps/builder-ui/test-results/`;
request traces are disabled because requests contain local credentials.
For a fresh test database, use `down -v` with the same `-p daedalus-checks`
and environment-file arguments before starting the test project again.

## Cloudera Workbench preparation

The runtime image supplies dependencies; this repository supplies application
code. Pull the repository into the Workbench project, select the custom runtime,
and build the frontend:

```sh
cd apps/builder-ui
npm ci
npm run build
cd ../..
PYTHONPATH=services /opt/mcp-factory/venv/bin/python -m factory.migrate
```

Before migration and startup, configure `DATABASE_URL` as a
`postgresql+psycopg://...` URL for an external PostgreSQL database. Both
applications must use the same registry. Configure the management role tokens,
`FACTORY_MCP_TOKEN`, `FACTORY_ALLOWED_API_ORIGINS`, `FACTORY_BROWSER_ORIGINS`, and
`FACTORY_PUBLIC_MCP_URL`. This evaluation build requires an explicit
authentication mode: local Compose uses `development-open`; Workbench must use
`development-token` until production identity integration is implemented.
The Docker-only hostname `mock-api` will not exist in Workbench.

### PostgreSQL inside the Workbench project

When no external PostgreSQL is available, host the registry in a third
application. This needs a runtime built from the current `runtime/Dockerfile`
(it adds the PostgreSQL 16 server) and direct pod-to-pod networking in the
cluster.

1. Set `FACTORY_PG_PASSWORD` (16+ characters) as a project environment variable
   and leave `DATABASE_URL` unset.
2. Create an application with the script `postgres_app.py` and start it first.
   It initializes the data directory in project storage (`~/.daedalus/postgres`)
   and writes its current `IP:port` to `~/.daedalus/postgres-host`.
3. Run the migration command above, then start the Builder and Server
   applications. They read that file to build their database URL.

The pod IP changes whenever the PostgreSQL application restarts, so restart the
Builder and Server applications after it. Connections are password-protected
but not encrypted, and the data lives on network project storage: use this for
evaluation, not production.

Create one Builder application and one Server application for each deployed MCP
server in the same Workbench project. A dedicated Server application must set
`FACTORY_SERVER_ID` to the workspace ID shown in the Builder's server picker.
Use [the Server Application template](deploy/workbench/server-application.template.yaml)
to configure its runtime, launcher, registry access, and endpoint.

For the Builder application, set the Workbench application script to the
repository-root `app.py`. It delegates to `deploy/workbench/launch_builder.py`,
uses the `CDSW_APP_PORT` supplied by Workbench, and serves the built UI and
management API. Each generated MCP Server is a separate application; use
`mcp_server_app.py` or the rendered `deploy/workbench/launch_server.py` launcher
for that application, with its own `FACTORY_SERVER_ID`, release, database, and
MCP token settings.

Create the applications using these scripts:

- Builder: `deploy/workbench/launch_builder.py` serves the built UI and management
  API on the same application port.
- Server: `deploy/workbench/launch_server.py` runs the controller and MCP gateway.

The Builder has a **Deploy** panel. With `FACTORY_DEPLOYMENT_PROVIDER=manual`
it records a reviewable application intent and returns `ready_to_deploy`; create
the application from the template. With `cloudera-bridge`, the Builder sends a
versioned request to `FACTORY_CLOUDERA_API_BASE_URL/v1/daedalus/applications`.
That bridge must be supplied and qualified for the installed Workbench version;
its credentials belong in Workbench secret management, never in Git or a release.

The launchers require Workbench's `CDSW_APP_PORT`. They default to loopback
binding; verify the deployment's ingress requirements before overriding
`FACTORY_BUILDER_BIND` or `FACTORY_GATEWAY_BIND`. Gateway admin remains loopback
only. Actual Workbench ingress, registration, authentication, and MCP protocol
qualification remain unverified; see [compatibility.yaml](compatibility.yaml).

## Current scope

This is a local evaluation implementation: one server, reusable unauthenticated
REST connections, GET/POST JSON tools, scalar path/query inputs, and a restricted
object body schema. Production OAuth/OIDC, backend secret providers, per-tool
caller authorization, general OpenAPI import, comprehensive protocol conformance,
and enterprise network enforcement are remaining developer-plan work.
