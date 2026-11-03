# Daedalus burndown

The ordered list of what is left to ship. One line per item, ticked when it is
merged and verified. Feature status and evidence stay in
[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md); per-tool decisions stay in
[api-catalog/](api-catalog/README.md). Last updated: 2026-11-02.

**Delivery model.** Every tool pack ships in the code as a *seed pack*
(`services/factory/seedpacks/`). A seed is inert until an administrator enables
it (TOOL PACKS → ⚙ Seed packs, or `FACTORY_PACKS_ENABLED`), and a published
server carries only the tools dragged onto its canvas. So shipping all packs
costs a customer nothing until they switch one on, and no server exposes tools
nobody asked for. Each pack below is one seed, tested against a fake of its API
in the mock service, with real-endpoint verification recorded when the customer
environment allows it.

## 1. Tool packs to ship as seeds (151 `keep` tools, 147 provided so far)

Order follows the customer's goal: files first, then who-may-see-what, then the
catalogue, then Ozone inventory and table maintenance.

| # | Seed pack | Tools | Source API | State |
|---|---|---|---|---|
| 1 | `webhdfs_admin` | 21 new (33 keep, 12 in `hdfs` and the seed) | WebHDFS / HttpFS | [x] 2026-10-30: paging, quotas, home and trash, xattrs, ACL and access checks, storage policy, snapshots (list, diff, create, rename, delete), set times, append, concat, filesystem status |
| 2 | `s3_extras` | 5 new (12 keep, 7 in `s3`) | Ozone S3 Gateway | [x] 2026-10-30: bucket access check, bulk delete, object tags (get, set with merge or replace, delete all or named) |
| 3 | `ranger_public` | 31 | Ranger public API v2 | [x] 2026-10-30. Read-only: service types, services, policies, roles, security zones. Flexible by configuration, not by customer profile: `prefix` (direct Ranger Admin or a Knox path), connection `auth_mode` (basic, forward-token, static; kerberos later), `scope` `all` or `caller` (policy and role answers narrowed to the calling user), version tolerance (roles and zones endpoints missing on Ranger 1.x produce a clear message, and the probe reports which feature groups answered). The fake serves two prefixes, Basic and Bearer credentials, an auditor and a limited account. |
| 4 | `atlas_discovery` | 13 | Atlas v2 search | [x] 2026-10-30: basic, filtered (SearchParameters), DSL (entities or a select table), full-text, quick with per-type counts, attribute prefix, relationship and related-entity search, saved searches (list, show, run by name or guid), suggestions. `prefix` for direct or Knox; identity filtering is Atlas's own, so forward-token gives the caller's view; quick, relations, related-entity and suggestions report an Atlas-before-2.1 message when missing. Fake at direct, Knox and old prefixes with per-identity visibility. |
| 5 | `atlas_entities` | 13 | Atlas v2 entity and lineage | [x] 2026-10-30: full entity and header by guid or by type and qualified name, several at once, recently classified entities, classifications (own and propagated), change history with paging, lineage upstream, downstream or both as datasets, processes and edges, relationship by guid. Same `prefix` and identity model as atlas_discovery; `max_lineage_depth` caps how far an agent may walk. The Atlas fake gained full entities, propagated classifications, audit events, a four-step lineage and the entity, lineage and relationship endpoints. |
| 6 | `atlas_glossary` | 13 | Atlas v2 glossary | [x] 2026-10-30: glossaries (list with name filter, one, detailed), categories (full, names, one, parent and children, its terms), terms (full, names, one, related terms by relation, assigned entities). Same `prefix` and identity model; glossary objects are public to Atlas users while assigned entities follow the caller's view. The Atlas fake gained two glossaries with a category hierarchy, related terms and term assignments. |
| 7 | `atlas_types` | 5 | Atlas v2 types | [x] 2026-11-02: type names by category, service type or name part; full definitions filtered by category, super type or service type; one type of any category (enum values, struct attributes, relationship ends, business metadata applicability); an entity type with its inherited attributes marked by origin, its relationship attributes and a DSL hint for atlas_discovery; a classification with the entity types it may be applied to. Same `prefix` model; types are not identity-filtered. The Atlas fake gained a type system (nine entity types with inheritance, three classifications, an enum, a struct, four relationships and a business metadata type absent on the old prefix). |
| 8 | `ozone_recon` | 13 | Ozone Recon | [x] 2026-11-02: volumes and buckets with quotas, ACLs, layout and replication (paged with Recon's prevKey), keys under a prefix filtered by replication type, size and creation time, what a path is and what it holds, disk usage by child largest first (files and replicated sizes on request), quota usage, file size distribution in size bands, cluster state, storage distribution per datanode, file counts per bucket and band, open-key and pending-deletion summaries. Flexible by configuration: `prefix` (direct or Knox), connection auth none/basic/forward-token, `simple_user` for a Recon whose simple authentication refuses anonymous callers (caller's name or a fixed one), tolerance for Recon before key listing, the storage distribution and the deleted-directory summary existed, and for the older flat namespace summary shape. The fake serves three prefixes (anonymous simple, Knox, old with user.name) over three volumes, four buckets and six keys. |
| 9 | `cdp_lakehouseopt` | 14 | CDP Lakehouse Optimizer | [x] 2026-11-02: environments with their Optimizer Data Hub CRN, namespaces, table names and tables with status, policies (list, names, one in full with decoded arguments and associations), a table's policies and its status explanation (paused since and why, or the last task's actions), associations by policy (tables, namespaces and tables with flags, the whole overview), tasks with decoded details and paging. Needs the new `cdp-apikey` connection mode (section 5). `datahub_crn` in the tool configuration spares agents the CRN on every call. The control plane fake verifies the Ed25519 signature of every request. |
| 10 | `cdp_datacatalog` | 4 | CDP Data Catalog | [ ] data shares, FGAC status, suggested tags |

Each pack also needs: a fake of its API in `services/factory/mock_api.py` for
tests and the playground, a backend test through the executor and gateway, the
pack's connection probe, and a row in the status document. Packs that use a new
connection protocol (Ranger, Atlas, Recon and the CDP control plane are plain
REST with their own authentication) must declare it and the connection dialog
must offer it.

## 2. Environment dependencies for real verification

Daedalus is built for any Hadoop, Ozone, Ranger or S3 deployment, with Cloudera
customers first. Every pack is therefore configurable for the common variants
(direct or proxied endpoint, each authentication mode, service account or
caller identity, TLS, product version) and tested against fakes of each. What
remains is verifying against real installations. Nothing here is code; each is
an endpoint or a value from whichever environment we verify in first.

- [ ] Knox JWT issuer and JWKS URL, so the gateway's `jwtAuth` can be configured
  against the real identity provider (today: a generated issuer in tests).
- [ ] A reachable HttpFS or WebHDFS endpoint through Knox, to verify the `hdfs`
  pack and the `webhdfs_admin` seed against a real cluster.
- [ ] Ozone S3 Gateway endpoint and per-user S3 credentials, or confirmation of
  the credential model (question B4), for the `s3` pack.
- [ ] Confirmation that the Server's proxy principal is authorised for doAs on
  their cluster, and the keytab delivery path.
- [ ] Ranger, Atlas and Recon endpoints and the authentication each expects
  (needed before packs 3 to 8 can be verified beyond the fakes). For Ranger:
  direct or through Knox; Basic, Knox JWT or Kerberos; the role of the service
  account (Auditor is the read-only fit); whether every caller may read every
  policy or only their own (`scope`); CA certificate and Ranger version.
- [ ] Which Cloudera AI Workbench version they run, for `compatibility.yaml`.

A one-page list of these goes to each environment owner; it is the longest lead
time in the project.

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

## 5. Connection capabilities every pack shares

- [x] **Basic authentication mode** (`basic`, 2026-10-30): `FACTORY_SECRET_<NAME>` holding
  `user:password`, sent as an `Authorization: Basic` header by Python tools and
  by the gateway for REST tools. Needed by Ranger, Atlas, Recon and most
  non-Cloudera REST APIs with local or LDAP users. Also: checking a connection
  now runs the probe of a pack whose tools use it, so Ranger connections are
  checked by the Ranger probe rather than the generic REST one.
- [x] **CDP API key mode** (`cdp-apikey`, 2026-11-02): `FACTORY_SECRET_<NAME>` holding
  `ACCESS_KEY_ID:PRIVATE_KEY` from the credentials file the CDP console issues; every
  request to the control plane is signed per CDP request signing V1 (`x-altus-date`,
  `x-altus-auth`), Ed25519 seeds as `ed25519v1` and RSA PEM keys as `rsav1`, using the
  `cryptography` library already in the runtime. Python pack tools only; the gateway
  cannot sign for REST tools, and the Builder says so when such a tool is tested.
  Needed by the Lakehouse Optimizer and Data Catalog packs and any other CDP service.
- [ ] **Kerberos SPNEGO mode** (`kerberos`): a service keytab from a secret
  reference, a ticket obtained in the Server process, SPNEGO negotiation per
  request. Needed for Ranger, WebHDFS and Atlas on Kerberized clusters without
  Knox, and the step the `proxy-doas` stub is waiting on. Larger: needs a
  Kerberos client in the image and a fake KDC for tests.
- [ ] **CA bundle per connection**: today `ctx.client()` and the gateway trust
  only the system store. Add an optional `FACTORY_CA_<NAME>` reference (PEM) on
  the connection, used by the executor's HTTP client and the gateway backend
  TLS settings, so private certificate authorities work without rebuilding the
  image.

## 6. Hardening carried over from the developer plan

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
