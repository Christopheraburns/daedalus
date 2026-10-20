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

The Builder has a **Deploy** panel with three providers (`FACTORY_DEPLOYMENT_PROVIDER`):

- `manual` (default) records a reviewable application intent and returns
  `ready_to_deploy`; create the application from the template by hand.
- `cloudera-ai` creates and manages the Server application through the
  Workbench API v2 from inside the project: Deploy creates the application (or
  updates and restarts it for a newer release), Refresh reads its live status,
  Stop and Delete act on it. Configuration defaults to what Workbench sets in a
  session: `CDSW_DOMAIN`, `CDSW_APIV2_KEY`, `CDSW_PROJECT_ID`. The Server's runtime is
  the Builder's own, looked up in the Runtime Catalog by its `ML_RUNTIME_*`
  metadata (or `MCP_FACTORY_RUNTIME_IMAGE` locally); override any of them with
  `FACTORY_CAI_API_URL`, `FACTORY_CAI_API_KEY`, `FACTORY_CAI_PROJECT_ID`,
  `FACTORY_CAI_RUNTIME_IDENTIFIER`, `FACTORY_CAI_SCRIPT` (the Server script as a path from the project
  root; by default worked out from where the repository sits, e.g. `daedalus/mcp_server_app.py`), and size with `FACTORY_CAI_CPU` /
  `FACTORY_CAI_MEMORY`. Set `FACTORY_CAI_BYPASS_AUTH=true` when MCP clients
  authenticate with a Knox JWT instead of a Workbench login. The deployed
  application pins `FACTORY_DEPLOYED_RELEASE_ID`; deploy again to roll a newer
  release out. The provider is tested against a fake of the API and still needs
  verification on the target Workbench release.
- `cloudera-bridge` sends a versioned request to
  `FACTORY_CLOUDERA_API_BASE_URL/v1/daedalus/applications`, a customer-supplied
  bridge.

**Updating Daedalus in Workbench:** `git pull`; run
`PYTHONPATH=services /opt/mcp-factory/venv/bin/python -m factory.migrate` if new
migrations arrived; `npm run build` in `apps/builder-ui` if the UI changed; then
restart the Builder and Server applications (stop and start if a restart does not
take). The Builder's `/healthz` reports the code revision its process loaded, so you
can confirm the restart picked up the pull.

Both launchers relay the Builder's or controller's output into the application log and keep a copy in project storage (`~/.daedalus/logs/builder.log` and `~/.daedalus/logs/server-<first 8 characters of FACTORY_SERVER_ID>.log`, with the previous run kept as `*.previous.log`; override the folder with `FACTORY_LOG_DIR`). When the child exits with an error, the launcher's error message ends with its last 40 lines.

The launchers require Workbench's `CDSW_APP_PORT`. They default to loopback
binding; verify the deployment's ingress requirements before overriding
`FACTORY_BUILDER_BIND` or `FACTORY_GATEWAY_BIND`. Gateway admin remains loopback
only. Actual Workbench ingress, registration, authentication, and MCP protocol
qualification remain unverified; see [compatibility.yaml](compatibility.yaml).

## Export and import

**Export** (header, any role) downloads the selected server as
`<name>.daedalus.json` (format `daedalus-server/v1`): approved origins,
connections with secret *names* only, tools, canvas layout, MCP connections'
discovered tools, and the source of the project packs its tools use. Record IDs
are replaced by references (`c1`, `t1`, …) and records are listed by name, so the
same server always exports to the same file. **Import** (administrators) creates
a new server workspace from a file: fresh IDs, imported tools untested, project
packs written to this project (a pack with different code is replaced only when
you choose to), and a list of the secrets to set on the Server application.
Release history is not carried over: test and publish in the new environment.
The API equivalents are `GET /api/export?server_id=…` and
`POST /api/servers/import`.

## Deleting a server

**Delete** (header, administrators) removes the selected server workspace and
everything in it: tools, connections, approved origins, canvas layout, releases
and the deployment record. Project tool packs are kept, because other servers may
use them. The dialog shows what will be deleted, offers an Export first, and asks
you to type the server's name. If Daedalus deployed the server to a Workbench
application, *Also delete its Workbench application* (on by default) deletes that
application too; otherwise the deletion is refused while any Server process still
serves the server (the message names it), so stop that application first. The
default server workspace cannot be deleted. Each deletion is audited
(`server.delete`). API: `DELETE /api/servers/{id}?delete_application=true` with
`If-Match: <server revision>`.

## Languages

The Builder is available in English and Korean. The selector next to the signed-in
user switches languages and remembers the choice per browser; the default follows
the browser language. Strings live in
[apps/builder-ui/src/locales](apps/builder-ui/src/locales): `en.ts` is the key
list, `ko.ts` must define every key (TypeScript enforces this), and `errors.ts`
translates backend messages by exact text or pattern. Help pages are per language
under `apps/builder-ui/public/help/`. Tool names, descriptions and pack docstrings
are user content and stay in whatever language they are written in.

## Connection authentication and caller identity

Each connection has a `protocol` (`rest`, `webhdfs`, `s3`) that says what the
endpoint speaks; packs declare the protocol their tools need with a module-level
`PROTOCOL`, and the canvas, the inspector and the compiler only accept matching
pairs. A failed test shows on the canvas as a red dashed edge and a *Failed*
status.

**Connection checks.** Saving a connection (or **Check connection** in the
inspector) runs the matching pack's `probe(ctx)` through an isolated candidate:
`rest` answers any HTTP status, `hdfs` describes `/`, `s3` lists buckets. The
verdict is stored on the connection and shown in the inspector and as the
connection node's status dot. Packs declare a probe with `@pack_probe`.

**Federated MCP servers.** A connection with protocol `mcp` (base URL
including the `/mcp` path, authentication as usual) is another MCP server, for
example one built by Daedalus. Checking it discovers its tools; with *Serve this
server's tools from here* enabled, releases include them as an agentgateway
`mcp` target behind this server's authentication, and tool names must stay
unique across local and federated tools. The upstream must speak the client's
MCP protocol profile, because agentgateway forwards it unchanged.

**MCP tools.** To use *some* tools of another MCP server, or to rename,
re-describe or reclassify them, add them individually instead: each tool listed
under an `mcp` connection in the palette (click, drag or **Add all**) becomes a
`kind: mcp` tool node with its own name, description and read/write effect. Its
input schema is copied from the connection's discovery. Calls run in the
executor through Daedalus's own MCP client, which speaks the latest protocol
profile and falls back to the earlier session-based profile, so servers built on
older SDKs work too. The connection's credentials and the caller's identity are
applied per call, and results that arrive as a single JSON text block are
returned as structured data. Upstream servers that nest inputs under `body`
(agentgateway, so any Daedalus server) are unwrapped automatically. The mock
API hosts an SDK-built upstream at `http://mock-api:8080/upstream/mcp`. Each connection also has an `auth_mode` (see [services/factory/auth.py](services/factory/auth.py)):

| Mode | What a tool call sends to the API | Where the credential lives |
| --- | --- | --- |
| `none` | nothing | — |
| `static` | `Authorization: Bearer <secret>` | a `FACTORY_SECRET_*` variable on the Server application; the registry stores only its name |
| `forward-token` | the caller's own bearer token | the client's request; requires caller identity below |
| `proxy-doas` | `doAs=<caller>` as a fixed service principal (Python tools only) | keytab reference; the Kerberos exchange is integrated per cluster |

Python tools get this through `ctx.client()`; REST tools get the equivalent
agentgateway backend policy, with static secrets written as 0600 files per
release. A missing secret fails the test or release with its name.

**Caller identity.** Set `FACTORY_JWT_ISSUER`, optionally `FACTORY_JWT_AUDIENCE`,
and `FACTORY_JWT_JWKS_FILE` (the issuer's JWKS, for example Knox's) on the Server
application. The public MCP port then accepts only that issuer's JWTs, the
verified `sub` becomes `ctx.caller.username` for every tool, `forward-token`
connections pass the JWT to backends, and the controller verifies the live
catalog through a loopback probe port (`FACTORY_PROBE_PORT`, default 15001)
with its own token. Without an issuer the behaviour is unchanged: one static
MCP token and the `development` caller.

## HDFS pack

The built-in `hdfs` pack manages files over the WebHDFS REST API, which HDFS
exposes natively and Ozone exposes through HttpFS. Create a connection whose
base URL is the HttpFS, NameNode or Knox origin, then add the tools you want:
`list_directory`, `get_file_status`, `make_directory`, `move`, `delete`,
`download_file`, `upload_file`, `copy`. Per-tool configuration (inspector →
Configuration JSON):

| Key | Default | Meaning |
| --- | --- | --- |
| `prefix` | `/webhdfs/v1` | Path prefix on the connection; Knox uses `/gateway/<topology>/webhdfs/v1` |
| `follow_redirects` | `false` | Follow NameNode 307 redirects to DataNodes for reads and writes. HttpFS needs none and keeps traffic inside the approved origin |
| `pseudo_auth` | `false` | Send `user.name=<caller>` for clusters without Kerberos |
| `allow_recursive_delete` | `false` | Permit deleting non-empty directories |
| `max_download_bytes` / `max_upload_bytes` / `max_copy_bytes` | 256 KiB / 1 MiB / 64 MiB | Size caps; downloads are sliced with `offset` and `max_bytes` |

Text comes back as UTF-8 and other data as base64; uploads accept either.
Credentials come from the connection's authentication mode, so the same tools
run with a static Knox token, the caller's forwarded token, or a proxy identity.
The mock API hosts an in-memory WebHDFS (`/webhdfs/v1`, and `/webhdfs-nn/v1`
with NameNode-style redirects) for tests and the playground.

## S3 / Ozone pack

The built-in `s3` pack manages objects through the S3 API, which the Ozone S3
Gateway, MinIO and AWS S3 all speak. Create a connection with `auth_mode`
`s3-sigv4` whose secret reference holds `ACCESS_KEY:SECRET_KEY` (for Ozone,
the pair from `ozone s3 getsecret`), base URL = the S3 Gateway origin, then add
tools: `list_buckets`, `list_objects` (folder-style with `delimiter`, paged with
`continuation_token`), `get_object_info`, `download_object` (sliced, UTF-8 or
base64), `upload_object` (inline content), `copy_object`, `move_object`,
`delete_object`. Copies are server-side; objects above `multipart_threshold`
(default 64 MiB) copy as a multipart upload of `part_size` parts, so large
files never pass through the executor. Requests are signed with AWS Signature
Version 4 using the standard library; no SDK is needed in the runtime image.
Per-tool configuration: `region`, `max_download_bytes`, `max_upload_bytes`,
`multipart_threshold`, `part_size`, `max_copy_bytes`.

Locally, `docker compose up -d s3` starts a SeaweedFS S3 gateway
(`http://s3:8333`, access key `daedalus`, secret `daedalus-secret-key` from
`tests/s3-identities.json`) that verifies signatures as Ozone does; approve its
origin in Policies and set `FACTORY_SECRET_S3=daedalus:daedalus-secret-key` on
the stack to try it in the playground. Ozone's per-user S3 credentials are the one part that waits for the
customer environment (question B4).

## Python tool packs

Tools that need more than one API call, binary data, or computation are Python
functions in a *pack* under `services/factory/packs/`. A tool record with
`kind: python` names the pack and function; the function's typed parameters become
the MCP input schema and its docstring the description. `GET /api/packs` lists what
is available. The `demo` pack (`echo`, `whoami`, `fetch_json`) exercises the path.

Packs come from two places. *Built-in* packs ship in the runtime image and are
read-only. *Project* packs are written by administrators in the Builder (TOOL
PACKS → +), stored as files under `FACTORY_PACKS_DIR` (default
`~/daedalus-packs`, which Workbench shares between the Builder and Server
applications), validated in an isolated subprocess on save, and visible in the
palette immediately: no push, image rebuild or application restart. Every release
snapshots the project pack code it uses, so editing a pack later invalidates test
evidence for its tools but never changes a published server. Anyone can view pack
and tool source from the palette or the inspector. The in-app guide for writing
packs is served at `/help/tool-packs.html` (source:
[apps/builder-ui/public/help/tool-packs.html](apps/builder-ui/public/help/tool-packs.html))
and linked from the Builder's header and the pack editor.

Each release that contains Python tools starts an *executor*: a loopback HTTP
service (`factory.executor`) that the Server controller supervises next to the
gateway and swaps atomically between releases. agentgateway reaches it as an
OpenAPI target with a per-process key, so Python tools get the same discovery,
protocol handling, argument shape (`body` for JSON inputs) and verification as HTTP
tools. Tool code receives the caller identity and connection through a
`ToolContext` and never reads headers or credentials itself; registry credentials
and management tokens are withheld from the executor process.

## Current scope

This is a local evaluation implementation: one server, reusable unauthenticated
REST connections, GET/POST JSON tools, scalar path/query inputs, and a restricted
object body schema. Production OAuth/OIDC, backend secret providers, per-tool
caller authorization, general OpenAPI import, comprehensive protocol conformance,
and enterprise network enforcement are remaining developer-plan work.
