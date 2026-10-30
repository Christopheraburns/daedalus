# Daedalus burndown

The ordered list of what is left to ship. One line per item, ticked when it is
merged and verified. Feature status and evidence stay in
[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md); per-tool decisions stay in
[api-catalog/](api-catalog/README.md). Last updated: 2026-10-30.

**Delivery model.** Every tool pack ships in the code as a *seed pack*
(`services/factory/seedpacks/`). A seed is inert until an administrator enables
it (TOOL PACKS → ⚙ Seed packs, or `FACTORY_PACKS_ENABLED`), and a published
server carries only the tools dragged onto its canvas. So shipping all packs
costs a customer nothing until they switch one on, and no server exposes tools
nobody asked for. Each pack below is one seed, tested against a fake of its API
in the mock service, with real-endpoint verification recorded when the customer
environment allows it.

## 1. Tool packs to ship as seeds (151 `keep` tools, 45 provided so far)

Order follows the customer's goal: files first, then who-may-see-what, then the
catalogue, then Ozone inventory and table maintenance.

| # | Seed pack | Tools | Source API | State |
|---|---|---|---|---|
| 1 | `webhdfs_admin` | 21 new (33 keep, 12 in `hdfs` and the seed) | WebHDFS / HttpFS | [x] 2026-10-30: paging, quotas, home and trash, xattrs, ACL and access checks, storage policy, snapshots (list, diff, create, rename, delete), set times, append, concat, filesystem status |
| 2 | `s3_extras` | 5 new (12 keep, 7 in `s3`) | Ozone S3 Gateway | [x] 2026-10-30: bucket access check, bulk delete, object tags (get, set with merge or replace, delete all or named) |
| 3 | `ranger_public` | 31 | Ranger public API v2 | [ ] read-only: policies, roles, services, service defs, security zones |
| 4 | `atlas_discovery` | 13 | Atlas v2 search | [ ] basic, DSL, full-text, quick, attribute, relationship, saved searches, suggestions |
| 5 | `atlas_entities` | 13 | Atlas v2 entity and lineage | [ ] by guid, by unique attribute, headers, classifications, audit, lineage, relationships |
| 6 | `atlas_glossary` | 13 | Atlas v2 glossary | [ ] glossaries, categories, terms, assigned entities |
| 7 | `atlas_types` | 5 | Atlas v2 types | [ ] type definitions needed to write DSL searches |
| 8 | `ozone_recon` | 13 | Ozone Recon | [ ] volumes, buckets, keys, namespace usage, quota, file size distribution, cluster state |
| 9 | `cdp_lakehouseopt` | 14 | CDP Lakehouse Optimizer | [ ] environments, namespaces, tables, policies, associations, tasks (reads) |
| 10 | `cdp_datacatalog` | 4 | CDP Data Catalog | [ ] data shares, FGAC status, suggested tags |

Each pack also needs: a fake of its API in `services/factory/mock_api.py` for
tests and the playground, a backend test through the executor and gateway, the
pack's connection probe, and a row in the status document. Packs that use a new
connection protocol (Ranger, Atlas, Recon and the CDP control plane are plain
REST with their own authentication) must declare it and the connection dialog
must offer it.

## 2. Customer environment dependencies

Nothing here is code. Each is a value or an endpoint we need from the customer
before the matching feature can be verified for real.

- [ ] Knox JWT issuer and JWKS URL, so the gateway's `jwtAuth` can be configured
  against the real identity provider (today: a generated issuer in tests).
- [ ] A reachable HttpFS or WebHDFS endpoint through Knox, to verify the `hdfs`
  pack and the `webhdfs_admin` seed against a real cluster.
- [ ] Ozone S3 Gateway endpoint and per-user S3 credentials, or confirmation of
  the credential model (question B4), for the `s3` pack.
- [ ] Confirmation that the Server's proxy principal is authorised for doAs on
  their cluster, and the keytab delivery path.
- [ ] Ranger, Atlas and Recon endpoints and the authentication each expects
  (needed before packs 3 to 8 can be verified beyond the fakes).
- [ ] Which Cloudera AI Workbench version they run, for `compatibility.yaml`.

Send the customer a one-page list of these; it is the longest lead time in the
project.

## 3. Platform verification and packaging

- [ ] Pull the current code on the Workbench project, build the UI, restart the
  Builder and walk through publish, Deploy, Stop, Delete and the seed-pack toggle
  on the real `cloudera-ai` provider (only fakes so far).
- [ ] Record the Workbench version and the runtime image digest in
  `compatibility.yaml`.
- [ ] Publish the generic container image to a registry and tag it, so the
  compose file and `deploy/kubernetes/builder.yaml` do not depend on a local
  build.
- [ ] Document the upgrade path: run the `migrate` entrypoint before starting a
  new Builder; confirm a Builder from the previous version starts against the
  upgraded schema or refuses cleanly.
- [ ] Delete the local kind cluster (`kind delete cluster --name daedalus`) once
  the kubernetes provider needs no more local runs.

## 4. Phase 2: tables and catalogue

- [ ] Turn the Standalone Governed Iceberg server (`standalone/`) into a seed pack
  so Impala and Iceberg table tools sit in the same server as the file tools,
  with the same Knox identity and doAs.
- [ ] Revisit the 356 `later` rows in the catalogue with the customer: Atlas
  tagging and term assignment, Lakehouse Optimizer execute and pause, Data
  Warehouse, Data Engineering jobs, the Workbench API.

## 5. Hardening carried over from the developer plan

- [ ] Production OAuth/OIDC on the public port and per-tool caller authorisation
  (Claude Desktop needs OAuth; Copilot and n8n work with a bearer header).
- [ ] Backend credential and secret providers beyond environment variables.
- [ ] General OpenAPI import and further REST and schema mapping profiles.
- [ ] Full MCP protocol conformance for both profiles and ingress failure paths.
- [ ] Concurrent-writer, response-boundary and audit-event test coverage.
- [ ] Keyboard and accessibility coverage; browser checks for custom operation
  authoring, edge reconnection and connection editing.
- [ ] SBOM and vulnerability scan of the deployed image.
- [ ] Native review of the Korean UI wording.
- [ ] Fix the pre-existing browser test "drag an operation, search tools, and
  enforce read-only browser controls", which clicks a Sign out button that
  open-admin mode hides.

## Done since the original milestones

Kept here so the list above reads as what is left, not what was done.

- Local Docker environment, contracts, canvas authoring, testing and
  publication (the four original milestones, 2026-10-06).
- Multi-server workspaces, deployment records, Stop and Delete, default
  workspace emptying.
- Python tool packs and the executor; `hdfs`, `s3`, `rest`, `demo` built-ins.
- Packs in the registry; seed packs with enablement and forking.
- Connection protocols and probes; federated MCP connections; individual MCP
  tools; export and import.
- Platform-neutral configuration, the generic image, and the deployment provider
  interface with docker and kubernetes providers verified for real.
- Cloudera API catalogue: 98 packs and 3,684 tools triaged to 151 `keep`.
