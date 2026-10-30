# Daedalus implementation tracker

Last updated: 2026-10-30. What is left to do lives in [BURNDOWN.md](BURNDOWN.md); this file records what exists and how it was verified.

**The four initial local Builder milestones and the multi-server deployment
foundation are complete and locally verified.**
This is the first implementation slice, not completion of the full developer
plan. Actual Cloudera deployment and production authentication remain outstanding.

Status rules: **Verified** means the stated acceptance check passed;
**Implemented** means code exists without completed acceptance; **Remaining**
means additional implementation or qualification is required. Verification is
limited to the behaviors listed, not exhaustive conformance.

## Milestones

The four original local Builder milestones (Docker environment, contracts,
canvas authoring, testing and publication) were completed on 2026-10-06. Everything
since is tracked in [BURNDOWN.md](BURNDOWN.md).

## Feature inventory

| Feature | Status | Evidence / scope |
| --- | --- | --- |
| Cloudera Python 3.12 custom runtime | Verified locally | Image build and runtime smoke checks against `2026.08.1-b5`. |
| Docker startup and initial migration | Verified | Clean isolated project became healthy and bootstrapped an empty catalog. |
| PostgreSQL registry and persistent volume | Verified | Entire test stack recreated; definitions, evidence, layout, releases, and active snapshot matched. |
| FastAPI and React source reload | Verified | API and Vite operated with mounted project source. |
| Frontend production build | Verified | TypeScript and Vite succeeded in the pinned runtime. |
| Single-port Builder UI/API | Verified locally | Chromium loaded built assets and authenticated workspace from port 18000. |
| Random credentials and gitignored `.env` | Verified | Setup generates credentials and preserves existing configuration. |
| Server, connection, tool contracts | Verified | Backend tests exercise accepted definitions and invalid inputs. |
| Optimistic revisions | Verified | Missing/stale `If-Match` rejected; a second edit with an old revision fails. |
| Separate layout revisions | Verified | Browser drag persisted without changing server or tool revisions. |
| Administrator/author/publisher/viewer checks | Verified | Backend allow/deny cases and browser viewer controls. |
| Origin and destination checks | Verified | Untrusted browser Origins and unapproved backend URLs rejected. |
| Request size limit | Verified | Oversized management request returned 413. |
| Audit records | Verified in part | Creation records and configured-token redaction asserted; full audit-event coverage remains. |
| Reusable connections and inspector | Verified | Browser connection creation, tool editing, save, and reload. |
| Click and drag tool creation | Verified | Inventory added by click; support operation added by drag. |
| Canvas selection and saved positions | Verified | Move, reload, select, and compare saved layout. |
| Search and list view | Verified | Browser filtering and list selection. |
| Draft/tested/active status | Verified | API compares current tool plus connection fingerprint to published snapshot; draft edits clear active status. |
| Connection changes invalidate test evidence | Verified | Updated connection requires another successful tool test. |
| Desktop and narrow-screen rendering | Verified in part | Screenshots inspected at 1440px and 390px; no horizontal overflow. Full accessibility review remains. |
| Deterministic curated OpenAPI compiler | Verified | Stable output, excluded operations, name conflicts, unsupported paths and schemas tested. |
| Pinned gateway config validation | Verified | Candidate and live configs validated against vendored schema and gateway binary. |
| Isolated draft testing | Verified | Candidate invokes API while live catalog stays empty and direct draft calls fail. |
| Inventory/support read fixtures | Verified | Native tool calls returned inventory and support ticket responses. |
| Write tests require confirmation | Verified | Unconfirmed POST rejected; confirmed fixture write passed. |
| Playground and structured result preview | Verified | Browser validate/test flow displays successful API result. |
| Basic modern MCP discovery | Verified | `2026-07-28` catalog metadata/result/cache fields checked. Full conformance remains. |
| Basic legacy MCP discovery | Verified | `2025-11-25` initialization and listing checked. Full conformance remains. |
| Publish review and test requirement | Verified | Browser release review; backend rejects untested definitions. |
| Immutable release snapshots | Verified | Publish creates snapshot; restore creates new release and preserves drafts. |
| Controller activation verification | Verified | Private effective config and live catalog verified before activation. |
| Reload without gateway restart | Verified | PID and start time preserved across add/change/remove and rollback. |
| Removal blocks stale direct calls | Verified | Excluded tool disappears from catalog and direct invocation fails. |
| Failed release recovery | Verified | Injected checksum failure marked failed; prior active catalog retained. |
| Rollback | Verified | Prior snapshot restored through both API and browser. |
| Server restart recovery | Verified | Controller process restart restores active snapshot; Docker recreation also passed. |
| Private gateway admin | Verified locally | Loopback admin config; authenticated public `/ui` and `/config_dump` returned 404. |
| Workbench launcher scripts | Implemented | Environment/migration instructions documented; actual Workbench execution unverified. |
| Multi-server workspaces | Verified locally | Server picker and creation API isolate connections, tools, layouts, releases, audits, and active snapshots by server ID. |
| Dedicated Server Application record | Verified locally | One deployment record per server tracks desired/deployed releases, application identity, endpoint, state, message, and bridge metrics. |
| Deployment lifecycle controls | Verified locally | Deploy, refresh, stop, and delete actions use revision checks and audit records. Manual mode intentionally records reviewable intent. |
| Dedicated application manifest | Implemented | Template pins server ID and immutable release ID for `launch_server.py`. |
| Deployment/monitoring UI | Verified locally | Browser creates and selects an isolated server workspace and inspects its deployment state; Builder surfaces release identity, lifecycle controls, endpoint, and bridge metrics. |
| Cloudera deployment bridge adapter | Implemented | Explicit `cloudera-bridge` integration point sends a versioned, authenticated request; the installed Workbench control-plane contract is not yet qualified. |
| Python tool packs and executor | Verified locally | `kind: python` tools compile into an executor OpenAPI target; tests cover pack validation, key enforcement, gateway serving under both protocol profiles, Builder test/publish flow, and controller executor switching and retirement across releases. Builder palette lists packs with click/drag creation, Add all, inspector for Python tools, and a prefilled playground. |
| Project packs authored in the browser | Verified locally | Administrators create, edit, view and delete project packs from the Builder; saves are validated in an isolated subprocess (syntax, decorator, parameter types, hostile exit), catalogued without restart, snapshotted into releases, and pack edits invalidate tool test evidence. Backend and browser tests cover the flow. |
| In-app help | Verified locally | Tool-pack how-to guide served at `/help/tool-packs.html` (English and Korean), linked from the header, pack editor and palette; browser test checks both the dev server and the application port. |
| English and Korean UI | Implemented | 274 UI strings plus ~60 backend messages translated; language selector in the header with per-browser persistence and browser-language default; browser test switches languages. Korean wording awaits native review. |
| Connection authentication modes | Verified locally | `none`, `static` (secret reference, gateway backend policy and `ctx.client()`), `basic` (`FACTORY_SECRET_*` holding `user:password`, sent as an Authorization: Basic header by `ctx.client()` and by a gateway header policy for REST tools; the generated gateway configuration is written 0600), `forward-token`, `proxy-doas` stub (Python only; Kerberos step integrated on-cluster). Secrets never enter the registry; missing secrets fail tests and releases by name. Connection dialog and inspector expose the modes. |
| Caller identity (JWT) | Verified locally | Optional `jwtAuth` on the public port from a configured issuer/JWKS; `jwt.sub` reaches tools as `ctx.caller.username`, caller tokens forward to backends, Daedalus probes use a loopback port. Tested with a generated issuer; Knox issuer values pending from the customer. |
| HDFS file pack | Verified locally | Eight WebHDFS tools (list, status, mkdir, move, delete, download, upload, copy) with size caps, slice reads, base64 for binary, recursive-delete opt-in, NameNode redirect handling and pseudo auth; tested against an in-memory WebHDFS fake in HttpFS and NameNode modes and through the gateway. Real HttpFS/Knox verification pending the customer environment. |
| Cloudera AI deployment provider | Implemented | `cloudera-ai` creates, updates/restarts, refreshes, stops and deletes the Server application through the Workbench API v2 with session-provided defaults; tested against a fake of the API (payload fields, status mapping, key handling, error reporting). Live Workbench verification pending. |
| S3 / Ozone object pack | Verified locally | Eight S3 tools with SigV4 signing from the standard library, paged folder-style listing, sliced reads, inline uploads, server-side copy with multipart UploadPartCopy for large objects, move and delete; tested against a SeaweedFS S3 gateway in Docker (signature-verifying), including a multipart copy and serving through the gateway. Ozone S3 Gateway per-user credentials pending the customer environment. |
| Protocol-typed connections and test evidence on the canvas | Verified locally | Connections carry a protocol (rest, webhdfs, s3); packs declare theirs; Add all, the connection picker, drag-to-connect and the compiler reject mismatches with a named reason; failed tests show as a Failed status and a red dashed edge. Backend and browser tests cover both. |
| Connection checks (pack probes) | Verified locally | Hidden `probe(ctx)` per pack (`rest`, `hdfs`, `s3`) runs through an isolated candidate on save or on demand; verdict stored on the connection, shown in the inspector and as the node's status dot; failures carry the reason (unset secret, rejected signature). |
| Federated MCP connections | Verified locally | Protocol `mcp` connections are discovered by the check and served as agentgateway `mcp` targets in releases, behind this server's auth, with name-collision and discovery-before-publish checks; tested end to end through two gateways. Upstream protocol-profile compatibility is the caveat. |
| Server export and import | Verified locally | Portable `daedalus-server/v1` file per server (origins, connections with secret names only, tools, layout, discovered MCP tools, project-pack source; no IDs or secret values); administrator import creates a new workspace with untested tools, pack-conflict protection, required-secret list and all-or-nothing creation. Round-trip, conflict, permission and malformed-file tests in backend and browser. |
| Deployment provider interface with docker and kubernetes providers | Verified locally | `factory.providers`: manual, docker (Engine API; container per server, label-based adoption, stable host port), kubernetes (Deployment + Service per server, merge-patch redeploy, scale-to-zero stop), cloudera-ai, cloudera-bridge behind one interface; the workspace carries provider facts and the Deploy dialog is provider-neutral. Tests drive docker and kubernetes against fakes of their APIs. Both also ran for real: the docker provider against the local daemon (container joined the dev stack and came online), the kubernetes provider with the Builder itself running in a kind cluster from `deploy/kubernetes/builder.yaml` (Deploy created the Deployment and Service, the Server came online and answered `tools/list` through the Service, Stop scaled to zero, Delete removed both objects, and the default workspace was emptied). That run found that `runAsNonRoot` needs a numeric user in the image, so the Dockerfile now ends with `USER 10001:10001`. |
| Platform-neutral configuration and generic container image | Verified locally | Services read `FACTORY_*` and `DATABASE_URL` only; `deploy/workbench/workbench_env.py` translates `CDSW_*` and the project Postgres host file for the Workbench launchers; `deploy/container/Dockerfile` (python:3.12-slim, UI built in a Node stage, agentgateway pinned for amd64 and arm64, revision baked in) with `builder`/`server`/`migrate` entrypoint and a reference compose. Tests cover the adapter and that settings ignore `CDSW_*`. The Builder deploys Servers itself through the docker and kubernetes providers (next row). UI wording is provider-neutral: messages name what the provider creates (container, Deployment, Workbench application) or say "process" in manual mode. |
| Packs in the registry and seed packs | Verified locally | Project packs stored in `packs`, seed enablement in `pack_settings` (environment default `FACTORY_PACKS_ENABLED`, administrator toggle overrides), inspection cached by digest in `pack_inspections`; the executor imports release snapshots from memory; rollback uses the release's own pack code; legacy pack files imported once; launcher log files opt-in. Backend tests cover enable/disable/fork/revert, environment bootstrap, cache, legacy import, export/import of seeds; browser test toggles a seed. |
| WebHDFS admin seed pack | Verified locally | `webhdfs_admin` (first catalogue seed, 26 tools): content summary, quota usage, filesystem status, checksum, paged listing, home and trash directories, permission, owner, ACL status, access check, replication, storage policy, set times, extended attributes, snapshots (list snapshottable, list, diff, create, rename, delete), append and concat. The in-memory WebHDFS fake gained every operation (including redirecting APPEND on the NameNode path and snapshot state). `tests/test_webhdfs_admin.py` drives all 26 through the executor against the fake; real HttpFS/Knox verification pending the customer environment. |
| S3 extras seed pack | Verified locally | `s3_extras` (5 tools): bucket access check (exists, denied or usable), bulk delete with Content-MD5 and a configurable key limit, object tags read, set (merge by default, replace on request, S3 limits enforced) and delete (all or named). Reuses the `s3` pack's signing, URL and XML helpers. `tests/test_s3_extras.py` drives all five through the executor against the SeaweedFS gateway; Ozone S3 Gateway verification pending the customer environment. |
| Ranger read-only seed pack | Verified locally | `ranger_public` (31 tools): service types, services, service tags, policy search and lookups by id, name, guid and resource, roles, security zones (v1 and v2). Configuration covers the deployment variants: `prefix` (direct or Knox path), `scope` `all` or `caller` (policy and role answers narrowed to the calling user through Ranger's `user` search filter and `roles/user`), version tolerance (HTML 404 on roles or zones reported as a Ranger-before-2.0 message), compact result shapes with secret-looking service configs redacted. The mock service hosts a Ranger fake at the direct, Knox and old-Ranger prefixes with Basic (auditor and limited accounts) and Bearer JWT identity. `tests/test_ranger.py` drives all 31 tools through the executor in every combination and checks a Ranger connection through the Builder with the pack's own probe (connection checks now prefer the probe of a pack in use). Real Ranger verification pending an environment. |
| Atlas discovery seed pack | Verified locally | `atlas_discovery` (13 tools): basic, filtered (comma-separated `attribute operator value` or SearchParameters JSON), DSL (entities, or columns and rows for a select clause), full-text, quick with per-type counts, attribute prefix, relationship and related-entity search, saved searches (list, show, run by name or guid), suggestions. `prefix` for direct or Knox paths, `page_size`, `include_deleted`; version tolerance for the Atlas 2.1 endpoints; compact entity headers. The mock service hosts an Atlas fake (direct, Knox and old prefixes; Basic and Bearer identity; per-identity visibility; a small DSL subset). `tests/test_atlas.py` drives all 13 tools, the forwarded-token view, the old Atlas and a Builder connection check with the pack's probe. Real Atlas verification pending an environment. |
| Server deletion | Verified locally | Administrator-only header action with a type-the-name confirmation and Export-first option; deletes tools, connections, origins, layout, releases and the deployment record (packs kept), optionally deletes what the provider created (container, Deployment, Workbench application) or, when that is kept, requires it to be stopped first; refuses while another Server process serves the server; empties the default workspace instead of removing it (`server.empty`) and audits `server.delete`. Backend tests (including a fake Workbench: running refused, stopped allowed, deleted with the server) and a browser test. |
| Individual MCP tools | Verified locally | `kind: mcp` tools pick single tools from an `mcp` connection, with local name, description and effect; schema copied from discovery server-side; executed by the executor's MCP client with latest-profile and session-based fallback, connection credentials and caller identity; JSON-text results returned as structured data; agentgateway body nesting unwrapped. Tested against an SDK server on 2025-11-25 and a Daedalus server on 2026-07-28. |

## Acceptance evidence

All completed on 2026-10-06 using the separate `daedalus-checks` Compose project.
The existing `daedalus` workspace was not used for mutation/failure tests.

- `python -m pytest -q -p no:cacheprovider tests` inside the isolated deployment
  test API container: **8 passed**. Includes multi-server isolation and manual
  deployment intent/lifecycle checks, plus actual candidate/live gateway coverage.
  One non-failing Starlette/httpx deprecation warning remains.
- `npm run test:e2e`: **4 passed** in Chromium. Covers author/save/move/reload,
  validate/test/publish/restore, drag/search/viewer controls, dedicated workspace
  creation/deployment status, and built UI/API on one port. No browser JavaScript
  errors in the main authoring and production asset workflows.
- `npm run build` inside the test UI container: **passed** after the server picker
  and deployment/monitoring controls were added.
- `python3 tests/check_restart.py`: **passed**. Recreated the isolated Docker
  containers without deleting the PostgreSQL volume; persisted workspace matched.
- Browser screenshots: `apps/builder-ui/test-results/` (ignored generated artifacts).

The previous automatic approval interruption was resolved on retry. The earlier
release was confirmed active; publication, recovery, and browser verification
are no longer blocked.

## Remaining work

See [BURNDOWN.md](BURNDOWN.md). The developer-plan items that are still open are
listed there under "Hardening carried over from the developer plan".

This first slice supports one logical server, unauthenticated backend connections,
GET/POST JSON REST tools, scalar path/query parameters, and a restricted object
body schema. It uses explicit development tokens and approved API origins.

## Keeping this updated

For each feature, update its row and add the command/outcome when marking it
Verified. Check a milestone only after its acceptance checks pass. Keep local
verification separate from production and Cloudera qualification. See the
[root README](../README.md) for reproducible startup, test, and deployment steps.
