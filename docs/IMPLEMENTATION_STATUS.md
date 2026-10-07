# Daedalus implementation tracker

Last updated: 2026-10-06.

**The four initial local Builder milestones and the multi-server deployment
foundation are complete and locally verified.**
This is the first implementation slice, not completion of the full developer
plan. Actual Cloudera deployment and production authentication remain outstanding.

Status rules: **Verified** means the stated acceptance check passed;
**Implemented** means code exists without completed acceptance; **Remaining**
means additional implementation or qualification is required. Verification is
limited to the behaviors listed, not exhaustive conformance.

## Milestone burndown — 4 of 4 complete

- [x] **1. Local Docker environment** — PostgreSQL, migrations, mock REST APIs,
  Builder API, Server/controller, and React development server.
- [x] **2. Contracts and management foundation** — durable records, separate
  layout, optimistic revisions, role checks, and input validation.
- [x] **3. Persistent canvas authoring** — click/drag tool creation, inspector,
  saved layout, search, list view, and browser reload persistence.
- [x] **4. Testing and publication** — isolated tool tests, publish review,
  verified activation, live reload, removal, rollback, and restart recovery.

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

## Remaining developer-plan work

- [ ] Deploy and qualify the two applications in actual Cloudera Workbench.
- [ ] Install/configure and qualify the versioned Cloudera deployment bridge for
  this Workbench environment, then create a dedicated Server Application from
  Builder and exercise deploy/refresh/stop/delete against it.
- [ ] Verify Workbench ingress, registration, and protocol behavior; record exact
  deployment versions and immutable runtime image digest in `compatibility.yaml`.
- [ ] Production OAuth/OIDC and per-tool caller authorization.
- [ ] Backend credential/secret providers and enterprise network enforcement.
- [ ] General OpenAPI import and additional REST/schema mapping profiles.
- [ ] Full modern/legacy MCP conformance and ingress failure-path qualification.
- [ ] Broader concurrent-writer, response-boundary, and audit-event tests.
- [ ] Full keyboard/accessibility coverage and browser checks for custom operation
  authoring, edge reconnection, and connection editing.
- [ ] SBOM and vulnerability qualification for the deployed artifact.

This first slice supports one logical server, unauthenticated backend connections,
GET/POST JSON REST tools, scalar path/query parameters, and a restricted object
body schema. It uses explicit development tokens and approved API origins.

## Keeping this updated

For each feature, update its row and add the command/outcome when marking it
Verified. Check a milestone only after its acceptance checks pass. Keep local
verification separate from production and Cloudera qualification. See the
[root README](../README.md) for reproducible startup, test, and deployment steps.
