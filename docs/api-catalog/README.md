# Cloudera API tool catalog

Every documented REST operation across Cloudera's products, grouped into proposed Daedalus tool packs with one tool per API operation.
Extracted by script from Cloudera's published specs and reference pages on 2026-10-20; recovered into this folder on 2026-10-29.

**Working file for triage:** [cloudera-api-tools.csv](cloudera-api-tools.csv) has one row per tool with a filled `decision` column
(`keep`, `deprecated`, `later`, `skip`; see Decisions below) and a `notes` column. `deprecated_upstream` is what the vendor spec itself
marks deprecated; `in_builtin_pack` marks operations the existing `hdfs` and `s3` packs already cover; `partial_source` marks packs whose
list came from HTML reference pages rather than a machine-readable spec and may be missing operations.

Searchable page with the same data: https://claude.ai/artifact/3BByd4yHG4xTeAWvWeBFUa

**Totals:** 98 packs, 3684 tools.

## Triage buckets

Assumes every solution is deployed as a Cloudera AI Workbench application. The `bucket` and `bucket_reason` columns in the CSV carry this per tool.

| Bucket | Packs | Tools | Meaning |
|---|---|---|---|
| A platform/infra | 37 | 1,331 | Ruled out by the Workbench deployment model: cluster and platform administration a pod must not perform, compute paths Workbench replaces (YARN, Livy, Oozie), internal UI APIs (Hue), Knox administration |
| B admin surface | 23 | 869 | Reachable, but administrative write surfaces unsuitable for an MCP acting as an analyst: Ranger and Atlas administration, Kafka operations, NiFi and SSB administration, Flink cluster control |
| C out of scope | 23 | 834 | Fine in Workbench, not part of the lakehouse file and table goal: NiFi flows, streaming SQL, Solr, HBase, DataFlow, Operational Database, Replication Manager |
| candidate | 15 | 650 | The realistic Daedalus backlog: WebHDFS, Ozone S3 and Recon, Atlas catalog reads, Ranger reads, Data Warehouse lifecycle, Iceberg optimisation, Data Catalog, Workbench API, CDE jobs. Applying "reads plus the few writes the use case needs" takes this to roughly 250-300 tools |

## Decisions (first pass, 2026-10-30)

The `decision` column is filled for every row. Buckets A, B and C are `skip`. For the 650 candidates: `keep` is reads plus the writes file management needs,
`later` is what the customer may ask for in phase 2 (tables, catalog tagging, Data Warehouse, Data Engineering, the Workbench API), `skip` is administration,
duplicates and plumbing, and `deprecated` follows the vendor spec. The `notes` column gives the reason per tool. Tools the built-in `hdfs` and `s3` packs or the
`webhdfs_admin` seed pack already provide are `keep` with a note saying so.

| Pack | keep | later | skip | deprecated |
|---|---|---|---|---|
| `atlas_discovery` | 13 | 3 | 8 | 0 |
| `atlas_entities` | 13 | 14 | 18 | 0 |
| `atlas_glossary` | 13 | 3 | 16 | 0 |
| `atlas_types` | 5 | 11 | 4 | 0 |
| `cde_jobs` | 0 | 70 | 0 | 2 |
| `cdp_datacatalog` | 4 | 17 | 0 | 0 |
| `cdp_dw` | 0 | 88 | 0 | 1 |
| `cdp_lakehouseopt` | 14 | 15 | 1 | 0 |
| `cml_workbench_admin` | 0 | 32 | 0 | 0 |
| `cml_workbench_models` | 0 | 41 | 0 | 0 |
| `cml_workbench_projects` | 0 | 33 | 0 | 0 |
| `ozone_recon` | 13 | 5 | 31 | 1 |
| `ozone_s3` | 12 | 4 | 10 | 0 |
| `ranger_public` | 31 | 1 | 39 | 0 |
| `webhdfs` | 33 | 19 | 12 | 0 |
| **total** | **151** | **356** | **139** | **4** |

So the Daedalus backlog is **151 tools** across 10 packs, of which 120 already exist: the `hdfs` and `s3` packs and the `webhdfs_admin`, `s3_extras`, `ranger_public`, `atlas_discovery`, `atlas_entities`, `atlas_glossary` and `atlas_types` seeds (completed between 2026-10-30 and 2026-11-02, closing the `webhdfs`, `ozone_s3`, `ranger_public` and all four Atlas packs; see `docs/BURNDOWN.md`).

## CDP Public Cloud control plane

The services behind the cdp CLI. Every call is a signed POST to api.<region>.cdp.cloudera.com.

Full tool tables: [control-plane.md](control-plane.md)

| pack | tools | beta | deprecated upstream | notes |
|---|---|---|---|---|
| [`cdp_applications`](control-plane.md#cdpapplications) | 7 | 7 |  |  |
| [`cdp_audit`](control-plane.md#cdpaudit) | 11 |  |  |  |
| [`cdp_cloudprivatelinks`](control-plane.md#cdpcloudprivatelinks) | 9 |  |  |  |
| [`cdp_compute`](control-plane.md#cdpcompute) | 25 | 10 |  |  |
| [`cdp_consumption`](control-plane.md#cdpconsumption) | 1 |  |  |  |
| [`cdp_datacatalog`](control-plane.md#cdpdatacatalog) | 21 |  |  |  |
| [`cdp_datahub`](control-plane.md#cdpdatahub) | 80 | 5 | 3 |  |
| [`cdp_datalake`](control-plane.md#cdpdatalake) | 67 | 11 | 5 |  |
| [`cdp_de`](control-plane.md#cdpde) | 25 | 1 |  |  |
| [`cdp_df`](control-plane.md#cdpdf) | 66 |  |  |  |
| [`cdp_dfworkload`](control-plane.md#cdpdfworkload) | 71 |  | 5 |  |
| [`cdp_dw`](control-plane.md#cdpdw) | 89 | 12 | 1 |  |
| [`cdp_environments`](control-plane.md#cdpenvironments) | 106 | 7 | 4 |  |
| [`cdp_iam`](control-plane.md#cdpiam) | 80 | 6 |  |  |
| [`cdp_imagecatalog`](control-plane.md#cdpimagecatalog) | 16 | 5 |  |  |
| [`cdp_lakehouseopt`](control-plane.md#cdplakehouseopt) | 30 |  |  |  |
| [`cdp_ml`](control-plane.md#cdpml) | 55 |  |  |  |
| [`cdp_notification`](control-plane.md#cdpnotification) | 18 | 18 |  |  |
| [`cdp_opdb`](control-plane.md#cdpopdb) | 31 | 12 |  |  |
| [`cdp_publicendpointmanagement`](control-plane.md#cdppublicendpointmanagement) | 3 | 3 |  |  |
| [`cdp_replicationmanager`](control-plane.md#cdpreplicationmanager) | 53 | 29 |  |  |

## Cloudera Manager

Cloudera Manager 7.13.2, API v58, split into packs by resource group.

Full tool tables: [cloudera-manager.md](cloudera-manager.md)

| pack | tools | beta | deprecated upstream | notes |
|---|---|---|---|---|
| [`cm_clusters`](cloudera-manager.md#cmclusters) | 55 |  | 1 |  |
| [`cm_services`](cloudera-manager.md#cmservices) | 41 |  | 2 |  |
| [`cm_service_hdfs_yarn_commands`](cloudera-manager.md#cmservicehdfsyarncommands) | 30 |  | 4 |  |
| [`cm_service_hbase_solr_zk_commands`](cloudera-manager.md#cmservicehbasesolrzkcommands) | 26 |  |  |  |
| [`cm_service_sql_commands`](cloudera-manager.md#cmservicesqlcommands) | 41 |  | 5 |  |
| [`cm_roles`](cloudera-manager.md#cmroles) | 55 |  | 1 |  |
| [`cm_hosts`](cloudera-manager.md#cmhosts) | 32 |  | 1 |  |
| [`cm_commands`](cloudera-manager.md#cmcommands) | 11 |  |  |  |
| [`cm_manager`](cloudera-manager.md#cmmanager) | 74 |  |  |  |
| [`cm_mgmt_service`](cloudera-manager.md#cmmgmtservice) | 41 |  |  |  |
| [`cm_auth_service`](cloudera-manager.md#cmauthservice) | 37 |  |  |  |
| [`cm_users`](cloudera-manager.md#cmusers) | 19 |  |  |  |
| [`cm_replication`](cloudera-manager.md#cmreplication) | 53 |  | 1 |  |
| [`cm_parcels`](cloudera-manager.md#cmparcels) | 11 |  |  |  |
| [`cm_external_accounts`](cloudera-manager.md#cmexternalaccounts) | 13 |  |  |  |
| [`cm_control_planes`](cloudera-manager.md#cmcontrolplanes) | 29 |  |  |  |
| [`cm_monitoring`](cloudera-manager.md#cmmonitoring) | 27 |  |  |  |

## Data in motion

NiFi, NiFi Registry, Schema Registry, Streams Messaging Manager, Streams Replication Manager, Kafka Connect, Cruise Control, SQL Stream Builder and Flink.

Full tool tables: [data-in-motion.md](data-in-motion.md)

| pack | tools | beta | deprecated upstream | notes |
|---|---|---|---|---|
| [`nifi_flow`](data-in-motion.md#nififlow) | 60 |  |  |  |
| [`nifi_process_groups`](data-in-motion.md#nifiprocessgroups) | 37 |  |  |  |
| [`nifi_versions`](data-in-motion.md#nifiversions) | 14 |  |  |  |
| [`nifi_processors`](data-in-motion.md#nifiprocessors) | 14 |  |  |  |
| [`nifi_connections`](data-in-motion.md#nificonnections) | 25 |  |  |  |
| [`nifi_remote_process_groups`](data-in-motion.md#nifiremoteprocessgroups) | 19 |  |  |  |
| [`nifi_controller_services`](data-in-motion.md#nificontrollerservices) | 13 |  |  |  |
| [`nifi_parameters`](data-in-motion.md#nifiparameters) | 29 |  |  |  |
| [`nifi_reporting_tasks`](data-in-motion.md#nifireportingtasks) | 11 |  |  |  |
| [`nifi_provenance`](data-in-motion.md#nifiprovenance) | 13 |  |  |  |
| [`nifi_security`](data-in-motion.md#nifisecurity) | 21 |  |  |  |
| [`nifi_controller`](data-in-motion.md#nificontroller) | 44 |  |  |  |
| [`nifi_registry_extensions`](data-in-motion.md#nifiregistryextensions) | 29 |  |  |  |
| [`nifi_registry_security`](data-in-motion.md#nifiregistrysecurity) | 31 |  |  |  |
| [`nifi_registry`](data-in-motion.md#nifiregistry) | 30 |  |  |  |
| [`schema_registry`](data-in-motion.md#schemaregistry) | 53 |  |  | partial source |
| [`smm_alerting`](data-in-motion.md#smmalerting) | 20 |  |  | partial source |
| [`smm_integrations`](data-in-motion.md#smmintegrations) | 48 |  |  | partial source |
| [`smm_kafka`](data-in-motion.md#smmkafka) | 46 |  |  | partial source |
| [`srm`](data-in-motion.md#srm) | 23 |  |  | partial source |
| [`kafka_connect`](data-in-motion.md#kafkaconnect) | 29 |  |  |  |
| [`cruise_control`](data-in-motion.md#cruisecontrol) | 23 |  |  |  |
| [`ssb_projects`](data-in-motion.md#ssbprojects) | 32 |  |  | partial source |
| [`ssb_jobs`](data-in-motion.md#ssbjobs) | 34 |  |  | partial source |
| [`ssb_catalog`](data-in-motion.md#ssbcatalog) | 46 |  |  | partial source |
| [`ssb_notifications`](data-in-motion.md#ssbnotifications) | 38 |  |  | partial source |
| [`ssb_flink_dashboard`](data-in-motion.md#ssbflinkdashboard) | 27 |  |  | partial source |
| [`ssb_admin`](data-in-motion.md#ssbadmin) | 25 |  |  | partial source |
| [`flink`](data-in-motion.md#flink) | 70 |  |  |  |
| [`flink_sql_gateway`](data-in-motion.md#flinksqlgateway) | 14 |  |  |  |

## Data services and Runtime components

Cloudera AI Workbench, Data Engineering, Ranger, Atlas, Knox, HDFS, Ozone, YARN, Livy, Oozie, HBase, Solr, Hue and Data Visualization.

Full tool tables: [data-services.md](data-services.md)

| pack | tools | beta | deprecated upstream | notes |
|---|---|---|---|---|
| [`cml_workbench_projects`](data-services.md#cmlworkbenchprojects) | 33 |  |  |  |
| [`cml_workbench_models`](data-services.md#cmlworkbenchmodels) | 41 |  |  |  |
| [`cml_workbench_admin`](data-services.md#cmlworkbenchadmin) | 32 |  |  |  |
| [`cde_jobs`](data-services.md#cdejobs) | 72 |  | 2 |  |
| [`ranger_public`](data-services.md#rangerpublic) | 71 |  |  |  |
| [`ranger_xusers`](data-services.md#rangerxusers) | 71 |  |  |  |
| [`ranger_permissions_audit`](data-services.md#rangerpermissionsaudit) | 43 |  |  |  |
| [`ranger_service_internal`](data-services.md#rangerserviceinternal) | 53 |  | 2 |  |
| [`ranger_tags`](data-services.md#rangertags) | 47 |  |  |  |
| [`ranger_roles_zones`](data-services.md#rangerroleszones) | 30 |  |  |  |
| [`ranger_gds`](data-services.md#rangergds) | 54 |  |  |  |
| [`ranger_admin_misc`](data-services.md#rangeradminmisc) | 51 |  |  |  |
| [`atlas_entities`](data-services.md#atlasentities) | 45 |  |  |  |
| [`atlas_types`](data-services.md#atlastypes) | 20 |  |  |  |
| [`atlas_glossary`](data-services.md#atlasglossary) | 32 |  |  |  |
| [`atlas_discovery`](data-services.md#atlasdiscovery) | 24 |  |  |  |
| [`atlas_admin`](data-services.md#atlasadmin) | 33 |  |  |  |
| [`knox`](data-services.md#knox) | 43 |  |  | partial source |
| [`webhdfs`](data-services.md#webhdfs) | 64 |  |  | 7 in built-in pack |
| [`ozone_s3`](data-services.md#ozones3) | 26 |  |  | partial source; 7 in built-in pack |
| [`ozone_recon`](data-services.md#ozonerecon) | 50 |  | 1 |  |
| [`yarn_rm`](data-services.md#yarnrm) | 48 |  |  |  |
| [`yarn_nm`](data-services.md#yarnnm) | 9 |  |  |  |
| [`yarn_history`](data-services.md#yarnhistory) | 51 |  |  |  |
| [`livy`](data-services.md#livy) | 17 |  |  |  |
| [`oozie`](data-services.md#oozie) | 45 |  |  | partial source |
| [`hbase_rest`](data-services.md#hbaserest) | 30 |  |  |  |
| [`solr`](data-services.md#solr) | 66 |  |  |  |
| [`hue`](data-services.md#hue) | 45 |  |  | partial source |
| [`cdv`](data-services.md#cdv) | 61 |  |  | partial source |

## Products with no separate REST API

- Apache Hive: HiveServer2 is Thrift (binary or HTTP transport, incl. via Knox hive service) - not REST. WebHCat/Templeton is not shipped in CDP 7 (removed with HDP->CDP; Hive 3). No REST pack.
- Apache Impala: client protocol is Thrift/HS2 (Beeswax removed). impalad/statestored/catalogd debug web UIs return JSON (?json) for /queries, /metrics etc. but are undocumented/unsupported as an API.
- Apache Kudu: no REST API (RPC/Java/C++/Python clients). Master/tserver web UIs expose /metrics, /tables etc. as JSON for monitoring only.
- Cloudera Operational Database (COD): management is CDP control plane (cdp opdb); data access via HBase REST (pack hbase_rest), Phoenix Query Server (Avatica JSON/protobuf RPC over HTTP, not REST), or HBase/Phoenix clients.
- Cloudera Data Warehouse: management via control plane (cdp dw); data via Hive/Impala JDBC/ODBC. Only Data Visualization has its own REST API (pack cdv). Hue REST covered by hue.
- Cloudera Observability / Workload XM, Replication Manager, Data Catalog: public cloud APIs are control-plane (cdp observability/cdp replicationmanager/Data Catalog has no public API beyond Atlas/Ranger); on-prem Replication Manager is the Cloudera Manager API (replications/snapshot policies). No separate packs here.
