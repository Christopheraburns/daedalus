# Cloudera Manager

Cloudera Manager 7.13.2, API v58, split into packs by resource group.

Flags: **beta** = not in the GA spec; **deprecated** = marked deprecated by the vendor spec; **in built-in pack** = the existing Daedalus `hdfs`/`s3` pack already has it.

## cm_clusters

55 tools.

- Clusters: CRUD, lifecycle/upgrade commands, cluster-wide config, templates, kerberos, hosts membership.
- Resource groups: ClustersResourceApi

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `add_hosts` | POST | `/clusters/{clusterName}/hosts` | Add hosts (no summary in spec) |  |
| `add_tags` | PUT | `/clusters/{clusterName}/tags` | Attach tags to the cluster |  |
| `auto_assign_roles` | PUT | `/clusters/{clusterName}/autoAssignRoles` | Automatically assign roles to hosts and create the roles for all the services in a cluster |  |
| `auto_configure` | PUT | `/clusters/{clusterName}/autoConfigure` | Automatically configures roles and services in a cluster |  |
| `check_ecs_prerequisites_command` | POST | `/clusters/{clusterName}/commands/checkEcsPrerequisites` | Check ecs prerequisites command (no summary in spec) |  |
| `configure_auto_tls_services_command` | POST | `/clusters/{clusterName}/commands/configureAutoTlsServices` | Configures all services in a cluster to use Auto-TLS |  |
| `configure_for_kerberos` | POST | `/clusters/{clusterName}/commands/configureForKerberos` | Command to configure the cluster to use Kerberos for authentication |  |
| `create_clusters` | POST | `/clusters` | Creates a collection of clusters |  |
| `delete_cluster` | DELETE | `/clusters/{clusterName}` | Deletes a cluster |  |
| `delete_cluster_credentials_command` | POST | `/clusters/{clusterName}/commands/deleteCredentials` | Delete existing Kerberos credentials for the cluster |  |
| `delete_tags` | DELETE | `/clusters/{clusterName}/tags` | Remove the tags associated with the cluster |  |
| `deploy_client_config` | POST | `/clusters/{clusterName}/commands/deployClientConfig` | Deploy the cluster-wide client configuration |  |
| `deploy_client_configs_and_refresh` | POST | `/clusters/{clusterName}/commands/deployClientConfigsAndRefresh` | Performs a command with the 2 steps - deploy cc - cluster refresh This orchestration is needed for the staleness wizard, so it can invoke a single command at |  |
| `deploy_cluster_client_config` | POST | `/clusters/{clusterName}/commands/deployClusterClientConfig` | Deploy the Cluster's Kerberos client configuration |  |
| `disable_tls` | POST | `/clusters/{clusterName}/commands/disableTls` | Disables TLS settings on a cluster |  |
| `ecs_download_and_distribute` | POST | `/clusters/{clusterName}/commands/ecsDownloadAndDistribute` | Ecs download and distribute (no summary in spec) |  |
| `enter_maintenance_mode` | POST | `/clusters/{clusterName}/commands/enterMaintenanceMode` | Put the cluster into maintenance mode |  |
| `exit_maintenance_mode` | POST | `/clusters/{clusterName}/commands/exitMaintenanceMode` | Take the cluster out of maintenance mode |  |
| `expire_logs` | POST | `/clusters/{clusterName}/commands/expireLogs` | Remove backup and disaster related log files in hdfs |  |
| `export` | GET | `/clusters/{clusterName}/export` | Export the cluster template for the given cluster |  |
| `first_run` | POST | `/clusters/{clusterName}/commands/firstRun` | Prepare and start services in a cluster |  |
| `get_client_config` | GET | `/clusters/{clusterName}/clientConfig` | Download a zip-compressed archive of the client configuration, of a specific cluster |  |
| `get_cluster_support_token` | GET | `/clusters/{clusterName}/clusterSupportToken` | Gets the support token for a cluster |  |
| `get_kerberos_info` | GET | `/clusters/{clusterName}/kerberosInfo` | Provides Cluster Kerberos information |  |
| `get_ozone_bucket_info` | GET | `/clusters/{clusterName}/getOzoneBucketInfo` | Returns the properties of the provided ozone bucket if the bucket exists |  |
| `get_ozone_s3_gateway_info` | POST | `/clusters/{clusterName}/getOzoneS3GatewayInfo` | Returns the REST url for the Ozone S3 Gateway, as well as the AWS credentials needed to access the S3 endpoint |  |
| `get_utilization_report` | GET | `/clusters/{clusterName}/utilization` | Provides the resource utilization of the entire cluster as well as the resource utilization per tenant |  |
| `inspect_hosts_command` | POST | `/clusters/{clusterName}/commands/inspectHosts` | Runs the host inspector on the configured hosts in the specified cluster |  |
| `is_tls_enabled` | GET | `/clusters/{clusterName}/isTlsEnabled` | Returns whether a cluster has any TLS settings enabled |  |
| `list_active_commands` | GET | `/clusters/{clusterName}/commands` | List active cluster commands |  |
| `list_dfs_services` | GET | `/clusters/{clusterName}/dfsServices` | List the services that can provide distributed file system (DFS) capabilities in this cluster |  |
| `list_hosts` | GET | `/clusters/{clusterName}/hosts` | Returns hosts in the system filtered by optional host configuration parameters, if specified |  |
| `list_service_types` | GET | `/clusters/{clusterName}/serviceTypes` | List the supported service types for a cluster |  |
| `list_upgrade_domains` | GET | `/clusters/{clusterName}/upgradeDomains` | Returns the Upgrade Domains associated with the cluster and the host names that belong to each Upgrade Domain |  |
| `perf_inspector_command` | POST | `/clusters/{clusterName}/commands/perfInspector` | Run cluster performance diagnostics test |  |
| `pools_refresh` | POST | `/clusters/{clusterName}/commands/poolsRefresh` | Updates all refreshable configuration files for services with Dynamic Resource Pools |  |
| `post_cloudera_runtime_upgrade` | POST | `/clusters/{clusterName}/commands/postClouderaRuntimeUpgrade` | Post Cloudera Runtime upgrade API |  |
| `pre_upgrade_check_command` | POST | `/clusters/{clusterName}/commands/preUpgradeCheck` | Run cluster pre-upgrade check(s) when upgrading from specified version of CDH to the other |  |
| `read_cluster` | GET | `/clusters/{clusterName}` | Reads information about a cluster |  |
| `read_clusters` | GET | `/clusters` | List all known clusters |  |
| `read_tags` | GET | `/clusters/{clusterName}/tags` | Returns the tags associated with this cluster |  |
| `refresh` | POST | `/clusters/{clusterName}/commands/refresh` | Updates all refreshable configuration files in the cluster |  |
| `remove_all_hosts` | DELETE | `/clusters/{clusterName}/hosts` | Remove all hosts (no summary in spec) |  |
| `remove_host` | DELETE | `/clusters/{clusterName}/hosts/{hostId}` | Remove host (no summary in spec) |  |
| `restart_command` | POST | `/clusters/{clusterName}/commands/restart` | Restart all services in the cluster |  |
| `rolling_restart` | POST | `/clusters/{clusterName}/commands/rollingRestart` | Command to do a \"best-effort\" rolling restart of the given cluster, i.e |  |
| `rolling_upgrade` | POST | `/clusters/{clusterName}/commands/rollingUpgrade` | Command to do a rolling upgrade of specific services in the given cluster This command does not handle any services that don't support rolling upgrades |  |
| `run_ozone_command` | POST | `/clusters/{clusterName}/runOzoneCommand` | Executes an Ozone shell command on an Ozone Role |  |
| `run_specific_host_inspections_command` | POST | `/clusters/{clusterName}/commands/runSpecificHostInspections` | Runs a specific list of host inspections |  |
| `start_command` | POST | `/clusters/{clusterName}/commands/start` | Start all services in the cluster |  |
| `stop_command` | POST | `/clusters/{clusterName}/commands/stop` | Stop all services in the cluster |  |
| `tear_down_workload_cluster` | POST | `/clusters/{clusterName}/commands/tearDownWorkload/{workloadClusterName}` | Tear Down Workload cluster |  |
| `update_cluster` | PUT | `/clusters/{clusterName}` | Update an existing cluster |  |
| `upgrade_cdh_command` | POST | `/clusters/{clusterName}/commands/upgradeCdh` | Perform CDH upgrade to the specified version |  |
| `upgrade_services_command` | POST | `/clusters/{clusterName}/commands/upgradeServices` | Upgrades the services in the cluster to the CDH5 version | deprecated |

## cm_services

41 tools.

- Services: CRUD, config, start/stop/restart, maintenance, decommission, client config, metrics, reports; HDFS nameservices; watched dirs.
- Resource groups: NameservicesResourceApi, ServicesResourceApi, WatchedDirResourceApi

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `get_metrics_nameservices` | GET | `/clusters/{clusterName}/services/{serviceName}/nameservices/{nameservice}/metrics` | Fetch metric readings for a particular nameservice | deprecated |
| `list_nameservices` | GET | `/clusters/{clusterName}/services/{serviceName}/nameservices` | List the nameservices of an HDFS service |  |
| `read_nameservice` | GET | `/clusters/{clusterName}/services/{serviceName}/nameservices/{nameservice}` | Retrieve information about a nameservice |  |
| `add_tags` | PUT | `/clusters/{clusterName}/services/{serviceName}/tags` | Attach tags to the service |  |
| `create_services` | POST | `/clusters/{clusterName}/services` | Creates a list of services |  |
| `decommission_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/decommission` | Decommission roles of a service |  |
| `delete_service` | DELETE | `/clusters/{clusterName}/services/{serviceName}` | Deletes a service from the system |  |
| `delete_tags` | DELETE | `/clusters/{clusterName}/services/{serviceName}/tags` | Remove the tags associated with the service |  |
| `deploy_client_config_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/deployClientConfig` | Deploy a service's client configuration |  |
| `ecs_upgrade_audit` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/ecsUpgradeAudit` | Ecs upgrade audit (no summary in spec) |  |
| `enter_maintenance_mode` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/enterMaintenanceMode` | Put the service into maintenance mode |  |
| `exit_maintenance_mode` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/exitMaintenanceMode` | Take the service out of maintenance mode |  |
| `first_run` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/firstRun` | Prepare and start a service |  |
| `get_client_config` | GET | `/clusters/{clusterName}/services/{serviceName}/clientConfig` | Download a zip-compressed archive of the client configuration, of a specific service |  |
| `get_hdfs_usage_report` | GET | `/clusters/{clusterName}/services/{serviceName}/reports/hdfsUsageReport` | Fetch the HDFS usage report |  |
| `get_impala_utilization` | GET | `/clusters/{clusterName}/services/{serviceName}/impalaUtilization` | Provides the resource utilization of the Impala service as well as the resource utilization per tenant |  |
| `get_metrics_services` | GET | `/clusters/{clusterName}/services/{serviceName}/metrics` | Fetch metric readings for a particular service | deprecated |
| `get_mr_usage_report` | GET | `/clusters/{clusterName}/services/{serviceName}/reports/mrUsageReport` | Fetch the MR usage report |  |
| `get_yarn_utilization` | GET | `/clusters/{clusterName}/services/{serviceName}/yarnUtilization` | Provides the resource utilization of the yarn service as well as the resource utilization per tenant |  |
| `list_active_commands` | GET | `/clusters/{clusterName}/services/{serviceName}/commands` | List active service commands |  |
| `list_role_types` | GET | `/clusters/{clusterName}/services/{serviceName}/roleTypes` | List the supported role types for a service |  |
| `list_service_commands` | GET | `/clusters/{clusterName}/services/{serviceName}/commandsByName` | Lists all the commands (for CSD based services only) that can be executed by name on the provided service |  |
| `offline_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/offline` | Offline roles of a service |  |
| `read_service` | GET | `/clusters/{clusterName}/services/{serviceName}` | Retrieves details information about a service |  |
| `read_service_config` | GET | `/clusters/{clusterName}/services/{serviceName}/config` | Retrieves the configuration of a specific service |  |
| `read_services` | GET | `/clusters/{clusterName}/services` | Lists all services registered in the cluster |  |
| `read_tags` | GET | `/clusters/{clusterName}/services/{serviceName}/tags` | Returns the tags associated with this service |  |
| `recommission_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/recommission` | Recommission roles of a service |  |
| `recommission_with_start_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/recommissionWithStart` | Start and recommission roles of a service |  |
| `restart_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/restart` | Restart the service |  |
| `rolling_restart` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/rollingRestart` | Command to run rolling restart of roles in a service |  |
| `rotate_ecs_certificates` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/rotateEcsCertificates` | Rotate ECS Internal Certificates |  |
| `service_command_by_name` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/{commandName}` | Executes a command on the service specified by name |  |
| `start_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/start` | Start the service |  |
| `stop_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/stop` | Stop the service |  |
| `update_ecs_ingress_controller_cert` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/updateEcsIngressControllerCert` | Updates the certificate used by the ECS Ingress Controller |  |
| `update_service` | PUT | `/clusters/{clusterName}/services/{serviceName}` | Updates service information |  |
| `update_service_config` | PUT | `/clusters/{clusterName}/services/{serviceName}/config` | Updates the service configuration with the given values |  |
| `add_watched_directory` | POST | `/clusters/{clusterName}/services/{serviceName}/watcheddir` | Adds a directory to the watching list |  |
| `list_watched_directories` | GET | `/clusters/{clusterName}/services/{serviceName}/watcheddir` | Lists all the watched directories |  |
| `remove_watched_directory` | DELETE | `/clusters/{clusterName}/services/{serviceName}/watcheddir/{directoryPath}` | Removes a directory from the watching list |  |

## cm_service_hdfs_yarn_commands

30 tools.

- Service-type commands for HDFS, YARN, MapReduce (HA, failover, dirs, upgrades).
- Resource groups: ServicesResourceApi

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `collect_yarn_application_diagnostics` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/yarnApplicationDiagnosticsCollection` | Collect the Diagnostics data for Yarn applications Available since API v8 |  |
| `copy_hdfs_file` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/copyHdfsFile` | Copies source HDFS file to destination cluster HDFS |  |
| `create_hdfs_file` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/createHdfsFile` | Create hdfs file (no summary in spec) |  |
| `create_yarn_cm_container_usage_input_dir_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/yarnCreateCmContainerUsageInputDirCommand` | Creates the HDFS directory where YARN container usage metrics are stored by NodeManagers for CM to read and aggregate into app usage metrics |  |
| `create_yarn_job_history_dir_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/yarnCreateJobHistoryDirCommand` | Create the Yarn job history directory Available since API v6 |  |
| `create_yarn_node_manager_remote_app_log_dir_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/yarnNodeManagerRemoteAppLogDirCommand` | Create the Yarn NodeManager remote application log directory Available since API v6 |  |
| `delete_hdfs_path` | DELETE | `/clusters/{clusterName}/services/{serviceName}/commands/deleteHdfsPath` | Deletes the file or directory, specified by the given path, on the given HDFS service |  |
| `disable_jt_ha_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/disableJtHa` | Disable high availability (HA) for JobTracker |  |
| `disable_rm_ha_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/disableRmHa` | Disable high availability (HA) for ResourceManager |  |
| `enable_jt_ha_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/enableJtHa` | Enable high availability (HA) for a JobTracker |  |
| `enable_rm_ha_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/enableRmHa` | Enable high availability (HA) for a YARN ResourceManager |  |
| `get_policies_from_ranger` | GET | `/clusters/{clusterName}/services/{serviceName}/commands/getPoliciesFromRanger` | Collects information about the policies defined in the local Ranger service |  |
| `get_services_from_ranger` | GET | `/clusters/{clusterName}/services/{serviceName}/commands/getServicesFromRanger` | Collects information about the services defined in the local Ranger service |  |
| `get_users_from_ranger` | GET | `/clusters/{clusterName}/services/{serviceName}/commands/getUsersFromRanger` | Collects information about the users defined in the local Ranger service |  |
| `hdfs_add_sbnn_to_ns_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/hdfsAddSBNNToNS` | Hdfs add s b n n to n s command (no summary in spec) |  |
| `hdfs_create_tmp_dir` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/hdfsCreateTmpDir` | Creates a tmp directory on the HDFS filesystem |  |
| `hdfs_disable_auto_failover_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/hdfsDisableAutoFailover` | Disable auto-failover for a highly available HDFS nameservice | deprecated |
| `hdfs_disable_ha_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/hdfsDisableHa` | Disable high availability (HA) for an HDFS NameNode | deprecated |
| `hdfs_disable_nn_ha_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/hdfsDisableNnHa` | Disable High Availability (HA) with Automatic Failover for an HDFS NameNode |  |
| `hdfs_enable_auto_failover_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/hdfsEnableAutoFailover` | Enable auto-failover for an HDFS nameservice | deprecated |
| `hdfs_enable_ha_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/hdfsEnableHa` | Enable high availability (HA) for an HDFS NameNode | deprecated |
| `hdfs_enable_nn_ha_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/hdfsEnableNnHa` | Enable High Availability (HA) with Automatic Failover for an HDFS NameNode |  |
| `hdfs_failover_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/hdfsFailover` | Initiate a failover in an HDFS HA NameNode pair |  |
| `hdfs_finalize_rolling_upgrade` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/hdfsFinalizeRollingUpgrade` | Finalizes the rolling upgrade for HDFS by updating the NameNode metadata permanently to the next version |  |
| `hdfs_roll_edits_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/hdfsRollEdits` | Roll the edits of an HDFS NameNode or Nameservice |  |
| `hdfs_upgrade_metadata_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/hdfsUpgradeMetadata` | Upgrade HDFS Metadata as part of a major version upgrade |  |
| `import_mr_configs_into_yarn` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/importMrConfigsIntoYarn` | Import MapReduce configuration into Yarn, overwriting Yarn configuration |  |
| `install_mr_framework_jars` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/installMrFrameworkJars` | Creates an HDFS directory to hold the MapReduce2 framework JARs (if necessary), and uploads the framework JARs to it |  |
| `switch_to_mr2` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/switchToMr2` | Change the cluster to use MR2 instead of MR1 |  |
| `yarn_format_state_store` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/yarnFormatStateStore` | Formats the state store in ZooKeeper used for Resource Manager High Availability |  |

## cm_service_hbase_solr_zk_commands

26 tools.

- Service-type commands for HBase (incl. replication setup), Solr, ZooKeeper.
- Resource groups: ServicesResourceApi

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `create_h_base_root_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/hbaseCreateRoot` | Creates the root directory of an HBase service |  |
| `create_solr_hdfs_home_dir_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/createSolrHdfsHomeDir` | Creates the home directory of a Solr service in HDFS |  |
| `hbase_replication_create_user_directory` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/hbaseCreateUserDirectory` | Create the HBase user directory (usually /user/hbase) |  |
| `hbase_replication_first_time_setup_automatic` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/hbaseReplicationFirstTimeSetupAutomatic` | Starts an automatic HBase replication first time setup |  |
| `hbase_replication_first_time_setup_clean_and_reset` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/hbaseReplicationFirstTimeSetupCleanAndReset` | Cleans and resets the HBase replication first time setup on the given source and target: clears the HBase replication auxiliary info and deletes the JCEKS fi |  |
| `hbase_replication_first_time_setup_for_already_paired_clusters` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/hbaseReplicationFirstTimeSetupForAlreadyPairedClusters` | Starts an HBase replication first time setup for the source and target |  |
| `hbase_replication_first_time_setup_for_source_only` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/hbaseReplicationFirstTimeSetupForSourceOnly` | Starts an HBase replication first time setup for the source only |  |
| `hbase_replication_first_time_setup_for_target_only` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/hbaseReplicationFirstTimeSetupForTargetOnly` | Starts an HBase replication first time setup for the target only |  |
| `hbase_replication_first_time_setup_force_ready` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/hbaseReplicationFirstTimeSetupForceReady` | Force sets the HBase replication first time setup status to be READY for the given source and target |  |
| `hbase_replication_first_time_setup_manual` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/hbaseReplicationFirstTimeSetupManual` | Starts a manual HBase replication first time setup |  |
| `hbase_replication_first_time_setup_manual_continue` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/hbaseReplicationFirstTimeSetupManualContinue` | Should be called after #hbaseReplicationFirstTimeSetupManual(String, ApiHBaseReplicationSetupCommandArgs) to finish the manual HBase replication first time s |  |
| `hbase_replication_first_time_setup_reset` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/hbaseReplicationFirstTimeSetupReset` | Resets/removes the HBase replication first time setup status for the given source and target |  |
| `hbase_replication_first_time_setup_status` | GET | `/clusters/{clusterName}/services/{serviceName}/commands/hbaseReplicationFirstTimeSetupStatus` | Hbase replication first time setup status (no summary in spec) |  |
| `hbase_replication_setup` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/hbaseReplicationSetup` | Perform one time setup for HBase replication |  |
| `hbase_replication_setup_admin` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/hbaseReplicationSetupAdmin` | Hbase replication setup admin (no summary in spec) |  |
| `hbase_shell_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/hbaseShellCommand` | Execute a hbase shell command |  |
| `hbase_upgrade_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/hbaseUpgrade` | Upgrade HBase data in HDFS and ZooKeeper as part of upgrade from CDH4 to CDH5 |  |
| `init_solr_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/initSolr` | Initializes the Solr service in Zookeeper |  |
| `solr_bootstrap_collections_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/solrBootstrapCollections` | Bootstraps Solr Collections after the CDH upgrade |  |
| `solr_bootstrap_config_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/solrBootstrapConfig` | Bootstraps Solr config during the CDH upgrade |  |
| `solr_config_backup_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/solrConfigBackup` | Backs up Solr configuration metadata before CDH upgrade |  |
| `solr_migrate_sentry_privileges_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/solrMigrateSentryPrivilegesCommand` | Migrates Sentry privileges to new model compatible to support more granular permissions if Solr is configured with a Sentry service |  |
| `solr_reinitialize_state_for_upgrade_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/solrReinitializeStateForUpgrade` | Reinitializes the Solr state by clearing the Solr HDFS data directory, the Solr data directory, and the Zookeeper state |  |
| `solr_validate_metadata_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/solrValidateMetadata` | Validates Solr metadata and configurations |  |
| `zoo_keeper_cleanup_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/zooKeeperCleanup` | Clean up all running server instances of a ZooKeeper service |  |
| `zoo_keeper_init_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/zooKeeperInit` | Initializes all the server instances of a ZooKeeper service |  |

## cm_service_sql_commands

41 tools.

- Service-type commands for Hive, Impala, Hue, Oozie, Sentry, Sqoop, Ranger, Atlas, Iceberg.
- Resource groups: ServicesResourceApi

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `create_beeswax_warehouse_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/hueCreateHiveWarehouse` | Create the Beeswax role's Hive warehouse directory, on Hue services | deprecated |
| `create_hive_user_dir_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/hiveCreateHiveUserDir` | Create the Hive user directory Available since API v4 |  |
| `create_hive_warehouse_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/hiveCreateHiveWarehouse` | Create the Hive warehouse directory, on Hive services |  |
| `create_hive_warehouse_external_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/hiveCreateHiveWarehouseExternal` | Create the Hive warehouse external directory for Private Cloud |  |
| `create_impala_user_dir_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/impalaCreateUserDir` | Create the Impala user directory Available since API v6 |  |
| `create_oozie_db` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/createOozieDb` | Creates the Oozie Database Schema in the configured database |  |
| `create_sqoop_user_dir_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/createSqoopUserDir` | Creates the user directory of a Sqoop service in HDFS |  |
| `disable_catalog_statestore_ha_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/disableCatalogStatestoreHa` | Disable high availability (HA) for Catalog and Statestore service |  |
| `disable_llama_ha_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/impalaDisableLlamaHa` | Not Supported | deprecated |
| `disable_llama_rm_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/impalaDisableLlamaRm` | Not Supported | deprecated |
| `disable_oozie_ha_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/oozieDisableHa` | Disable high availability (HA) for Oozie |  |
| `disable_sentry_ha_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/disableSentryHa` | Disable high availability (HA) for Sentry service |  |
| `enable_catalog_statestore_ha_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/enableCatalogStatestoreHa` | Enable high availability (HA) for Catalog and Statestore service |  |
| `enable_llama_ha_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/impalaEnableLlamaHa` | Not Supported | deprecated |
| `enable_llama_rm_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/impalaEnableLlamaRm` | Not Supported | deprecated |
| `enable_oozie_ha_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/oozieEnableHa` | Enable high availability (HA) for Oozie service |  |
| `enable_sentry_ha_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/enableSentryHa` | Enable high availability (HA) for Sentry service |  |
| `export_sentry_permissions_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/exportSentryPermissions` | Export Sentry Permissions |  |
| `get_entity_types_from_atlas` | GET | `/clusters/{clusterName}/services/{serviceName}/commands/getEntityTypesFromAtlas` | Retrieves the atlas entities from a cluster |  |
| `hive_create_metastore_database_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/hiveCreateMetastoreDatabase` | Create the Hive Metastore Database |  |
| `hive_create_metastore_database_tables_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/hiveCreateMetastoreDatabaseTables` | Create the Hive Metastore Database tables |  |
| `hive_update_metastore_namenodes_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/hiveUpdateMetastoreNamenodes` | Update Hive Metastore to point to a NameNode's Nameservice name instead of hostname |  |
| `hive_upgrade_metastore_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/hiveUpgradeMetastore` | Upgrade Hive Metastore as part of a major version upgrade |  |
| `hive_validate_metastore_schema_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/hiveValidateMetastoreSchema` | Validate the Hive Metastore Schema |  |
| `hue_dump_db_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/hueDumpDb` | Runs Hue's dumpdata command |  |
| `hue_load_db_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/hueLoadDb` | Runs Hue's loaddata command |  |
| `hue_sync_db_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/hueSyncDb` | Runs Hue's syncdb command |  |
| `iceberg_replication_test_access` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/icebergReplicationTestAccess` | Executes IcebergReplicationTestAccess command for the given path |  |
| `impala_create_catalog_database_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/impalaCreateCatalogDatabase` | Not needed in CM 5.0.0 Release, since Impala Catalog Database is not yet available in CDH as of this release |  |
| `impala_create_catalog_database_tables_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/impalaCreateCatalogDatabaseTables` | Not needed in CM 5.0.0 Release, since Impala Catalog Database is not yet available in CDH as of this release |  |
| `install_oozie_share_lib` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/installOozieShareLib` | Creates directory for Oozie user in HDFS and installs the ShareLib in it |  |
| `ks_migrate_to_sentry` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/migrateToSentry` | Migrates the HBase Indexer policy-based permissions to Sentry, by invoking the SentryConfigToolIndexer |  |
| `oozie_create_embedded_database_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/oozieCreateEmbeddedDatabase` | Create the Oozie Server Database |  |
| `oozie_dump_database_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/oozieDumpDatabase` | Dump the Oozie Server Database |  |
| `oozie_load_database_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/oozieLoadDatabase` | Load the Oozie Server Database from dump |  |
| `oozie_upgrade_db_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/oozieUpgradeDb` | Upgrade Oozie Database schema as part of a major version upgrade |  |
| `sentry_create_database_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/sentryCreateDatabase` | Create the Sentry Server Database |  |
| `sentry_create_database_tables_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/sentryCreateDatabaseTables` | Create the Sentry Server Database tables |  |
| `sentry_upgrade_database_tables_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/sentryUpgradeDatabaseTables` | Upgrade the Sentry Server Database tables |  |
| `sqoop_create_database_tables_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/sqoopCreateDatabaseTables` | Create the Sqoop2 Server Database tables |  |
| `sqoop_upgrade_db_command` | POST | `/clusters/{clusterName}/services/{serviceName}/commands/sqoopUpgradeDb` | Upgrade Sqoop Database schema as part of a major version upgrade |  |

## cm_roles

55 tools.

- Roles, role commands, role config groups, role processes.
- Resource groups: ProcessResourceApi, RoleCommandsResourceApi, RoleConfigGroupsResourceApi, RolesResourceApi

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `get_config_file` | GET | `/clusters/{clusterName}/services/{serviceName}/roles/{roleName}/process/configFiles/{configFileName}` | Returns the contents of the specified config file |  |
| `get_process` | GET | `/clusters/{clusterName}/services/{serviceName}/roles/{roleName}/process` | Get process (no summary in spec) |  |
| `format_command` | POST | `/clusters/{clusterName}/services/{serviceName}/roleCommands/hdfsFormat` | Format HDFS NameNodes |  |
| `hdfs_bootstrap_stand_by_command` | POST | `/clusters/{clusterName}/services/{serviceName}/roleCommands/hdfsBootstrapStandBy` | Bootstrap HDFS stand-by NameNodes |  |
| `hdfs_enter_safemode` | POST | `/clusters/{clusterName}/services/{serviceName}/roleCommands/hdfsEnterSafemode` | Enter safemode for namenodes Available since API v4 |  |
| `hdfs_finalize_metadata_upgrade` | POST | `/clusters/{clusterName}/services/{serviceName}/roleCommands/hdfsFinalizeMetadataUpgrade` | Finalize HDFS NameNode metadata upgrade |  |
| `hdfs_initialize_auto_failover_command` | POST | `/clusters/{clusterName}/services/{serviceName}/roleCommands/hdfsInitializeAutoFailover` | Initialize HDFS HA failover controller metadata |  |
| `hdfs_initialize_shared_dir_command` | POST | `/clusters/{clusterName}/services/{serviceName}/roleCommands/hdfsInitializeSharedDir` | Initialize HDFS NameNodes' shared edit directory |  |
| `hdfs_leave_safemode` | POST | `/clusters/{clusterName}/services/{serviceName}/roleCommands/hdfsLeaveSafemode` | Leave safemode for namenodes Available since API v4 |  |
| `hdfs_save_namespace` | POST | `/clusters/{clusterName}/services/{serviceName}/roleCommands/hdfsSaveNamespace` | Save namespace for namenodes Available since API v4 |  |
| `jmap_dump` | POST | `/clusters/{clusterName}/services/{serviceName}/roleCommands/jmapDump` | Run the jmapDump diagnostic command |  |
| `jmap_histo` | POST | `/clusters/{clusterName}/services/{serviceName}/roleCommands/jmapHisto` | Run the jmapHisto diagnostic command |  |
| `jstack` | POST | `/clusters/{clusterName}/services/{serviceName}/roleCommands/jstack` | Run the jstack diagnostic command |  |
| `lsof` | POST | `/clusters/{clusterName}/services/{serviceName}/roleCommands/lsof` | Run the lsof diagnostic command |  |
| `refresh_command` | POST | `/clusters/{clusterName}/services/{serviceName}/roleCommands/refresh` | Refresh a role's data |  |
| `restart_command` | POST | `/clusters/{clusterName}/services/{serviceName}/roleCommands/restart` | Restart a set of role instances Bulk command operations are not atomic, and may contain partial failures |  |
| `role_command_by_name` | POST | `/clusters/{clusterName}/services/{serviceName}/roleCommands/{commandName}` | Execute a role command by name |  |
| `start_command` | POST | `/clusters/{clusterName}/services/{serviceName}/roleCommands/start` | Start a set of role instances |  |
| `stop_command` | POST | `/clusters/{clusterName}/services/{serviceName}/roleCommands/stop` | Stop a set of role instances |  |
| `sync_hue_db_command` | POST | `/clusters/{clusterName}/services/{serviceName}/roleCommands/hueSyncDb` | Create / update the Hue database schema |  |
| `zoo_keeper_cleanup_command` | POST | `/clusters/{clusterName}/services/{serviceName}/roleCommands/zooKeeperCleanup` | Cleanup a list of ZooKeeper server roles |  |
| `zoo_keeper_init_command` | POST | `/clusters/{clusterName}/services/{serviceName}/roleCommands/zooKeeperInit` | Initialize a list of ZooKeeper server roles |  |
| `create_role_config_groups` | POST | `/clusters/{clusterName}/services/{serviceName}/roleConfigGroups` | Creates new role config groups |  |
| `delete_role_config_group` | DELETE | `/clusters/{clusterName}/services/{serviceName}/roleConfigGroups/{roleConfigGroupName}` | Deletes a role config group |  |
| `move_roles` | PUT | `/clusters/{clusterName}/services/{serviceName}/roleConfigGroups/{roleConfigGroupName}/roles` | Moves roles to the specified role config group |  |
| `move_roles_to_base_group` | PUT | `/clusters/{clusterName}/services/{serviceName}/roleConfigGroups/roles` | Moves roles to the base role config group |  |
| `read_config` | GET | `/clusters/{clusterName}/services/{serviceName}/roleConfigGroups/{roleConfigGroupName}/config` | Returns the current revision of the config for the specified role config group |  |
| `read_role_config_group` | GET | `/clusters/{clusterName}/services/{serviceName}/roleConfigGroups/{roleConfigGroupName}` | Returns the information for a role config group |  |
| `read_role_config_groups` | GET | `/clusters/{clusterName}/services/{serviceName}/roleConfigGroups` | Returns the information for all role config groups for a given cluster and service |  |
| `read_roles_role_config_groups` | GET | `/clusters/{clusterName}/services/{serviceName}/roleConfigGroups/{roleConfigGroupName}/roles` | Returns all roles in the given role config group |  |
| `update_config` | PUT | `/clusters/{clusterName}/services/{serviceName}/roleConfigGroups/{roleConfigGroupName}/config` | Updates the config for the given role config group |  |
| `update_role_config_group` | PUT | `/clusters/{clusterName}/services/{serviceName}/roleConfigGroups/{roleConfigGroupName}` | Updates an existing role config group Available since API v3 |  |
| `add_tags` | PUT | `/clusters/{clusterName}/services/{serviceName}/roles/{roleName}/tags` | Attach tags to the role |  |
| `bulk_delete_roles` | POST | `/clusters/{clusterName}/services/{serviceName}/roles/bulkDelete` | Bulk delete roles in a particular service by name |  |
| `create_roles` | POST | `/clusters/{clusterName}/services/{serviceName}/roles` | Create new roles in a given service |  |
| `delete_force_role` | DELETE | `/clusters/{clusterName}/services/{serviceName}/roles/{roleName}/forceDelete` | Force deletes a role from a given service |  |
| `delete_role` | DELETE | `/clusters/{clusterName}/services/{serviceName}/roles/{roleName}` | Deletes a role from a given service |  |
| `delete_tags` | DELETE | `/clusters/{clusterName}/services/{serviceName}/roles/{roleName}/tags` | Remove the tags associated with the role |  |
| `enter_maintenance_mode` | POST | `/clusters/{clusterName}/services/{serviceName}/roles/{roleName}/commands/enterMaintenanceMode` | Put the role into maintenance mode |  |
| `exit_maintenance_mode` | POST | `/clusters/{clusterName}/services/{serviceName}/roles/{roleName}/commands/exitMaintenanceMode` | Take the role out of maintenance mode |  |
| `get_full_log` | GET | `/clusters/{clusterName}/services/{serviceName}/roles/{roleName}/logs/full` | Retrieves the log file for the role's main process |  |
| `get_metrics` | GET | `/clusters/{clusterName}/services/{serviceName}/roles/{roleName}/metrics` | Fetch metric readings for a particular role | deprecated |
| `get_stacks_log` | GET | `/clusters/{clusterName}/services/{serviceName}/roles/{roleName}/logs/stacks` | Retrieves the stacks log file, if any, for the role's main process |  |
| `get_stacks_logs_bundle` | GET | `/clusters/{clusterName}/services/{serviceName}/roles/{roleName}/logs/stacksBundle` | Download a zip-compressed archive of role stacks logs |  |
| `get_standard_error` | GET | `/clusters/{clusterName}/services/{serviceName}/roles/{roleName}/logs/stderr` | Retrieves the role's standard error output |  |
| `get_standard_output` | GET | `/clusters/{clusterName}/services/{serviceName}/roles/{roleName}/logs/stdout` | Retrieves the role's standard output |  |
| `impala_diagnostics` | POST | `/clusters/{clusterName}/services/{serviceName}/roles/{roleName}/commands/impalaDiagnostics` | Collects diagnostics data for an Impala role |  |
| `list_active_commands` | GET | `/clusters/{clusterName}/services/{serviceName}/roles/{roleName}/commands` | List active role commands |  |
| `list_commands` | GET | `/clusters/{clusterName}/services/{serviceName}/roles/{roleName}/commandsByName` | Lists all the commands that can be executed by name on the provided role |  |
| `read_role` | GET | `/clusters/{clusterName}/services/{serviceName}/roles/{roleName}` | Retrieves detailed information about a role |  |
| `read_role_config` | GET | `/clusters/{clusterName}/services/{serviceName}/roles/{roleName}/config` | Retrieves the configuration of a specific role |  |
| `read_roles_config` | GET | `/clusters/{clusterName}/services/{serviceName}/roles/configs` | Retrieves all the roles in the service, including all the configurations for each role |  |
| `read_tags` | GET | `/clusters/{clusterName}/services/{serviceName}/roles/{roleName}/tags` | Returns the tags associated with this role |  |
| `roles_read_roles` | GET | `/clusters/{clusterName}/services/{serviceName}/roles` | Lists all roles of a given service |  |
| `update_role_config` | PUT | `/clusters/{clusterName}/services/{serviceName}/roles/{roleName}/config` | Updates the role configuration with the given values |  |

## cm_hosts

32 tools.

- Hosts, all-hosts config, host templates.
- Resource groups: AllHostsResourceApi, HostTemplatesResourceApi, HostsResourceApi

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `read_config` | GET | `/cm/allHosts/config` | Retrieve the default configuration for all hosts |  |
| `update_config` | PUT | `/cm/allHosts/config` | Update the default configuration values for all hosts |  |
| `apply_host_template` | POST | `/clusters/{clusterName}/hostTemplates/{hostTemplateName}/commands/applyHostTemplate` | Applies a host template to a collection of hosts |  |
| `create_host_templates` | POST | `/clusters/{clusterName}/hostTemplates` | Creates new host templates |  |
| `delete_host_template` | DELETE | `/clusters/{clusterName}/hostTemplates/{hostTemplateName}` | Deletes a host template |  |
| `read_host_template` | GET | `/clusters/{clusterName}/hostTemplates/{hostTemplateName}` | Retrieves information about a host template |  |
| `read_host_templates` | GET | `/clusters/{clusterName}/hostTemplates` | Lists all host templates in a cluster |  |
| `reapply_host_template_on_hosts` | POST | `/clusters/{clusterName}/hostTemplates/{hostTemplateName}/commands/reapplyHostTemplateOnHosts` | Reapplies a host template on all the hosts associated with the host template |  |
| `update_host_template` | PUT | `/clusters/{clusterName}/hostTemplates/{hostTemplateName}` | Updates an existing host template |  |
| `add_tags` | PUT | `/hosts/{hostname}/tags` | Attach tags to the host |  |
| `create_hosts` | POST | `/hosts` | Create one or more hosts |  |
| `delete_all_hosts` | DELETE | `/hosts` | Delete all hosts in the system |  |
| `delete_host` | DELETE | `/hosts/{hostId}` | Delete a host from the system |  |
| `delete_tags` | DELETE | `/hosts/{hostname}/tags` | Remove the tags associated with the host |  |
| `enter_maintenance_mode` | POST | `/hosts/{hostId}/commands/enterMaintenanceMode` | Put the host into maintenance mode |  |
| `exit_maintenance_mode` | POST | `/hosts/{hostId}/commands/exitMaintenanceMode` | Take the host out of maintenance mode |  |
| `generate_host_certs` | POST | `/hosts/{hostId}/commands/generateHostCerts` | Generates (or regenerates) a key and certificate for this host if Auto-TLS is enabled |  |
| `get_host_components` | GET | `/hosts/{hostId}/components` | Returns the list of Component details on the requested host |  |
| `get_metrics` | GET | `/hosts/{hostId}/metrics` | Fetch metric readings for a host | deprecated |
| `hosts_enter_maintenance_mode` | POST | `/hosts/enterMaintenanceMode` | Puts a set of hosts into Maintenance mode Available since API v49 |  |
| `migrate_roles` | POST | `/hosts/{hostId}/commands/migrateRoles` | Migrate roles to a different host |  |
| `read_host` | GET | `/hosts/{hostId}` | Returns a specific Host in the system |  |
| `read_host_config` | GET | `/hosts/{hostId}/config` | Retrieves the configuration of a specific host |  |
| `read_hosts` | GET | `/hosts` | Returns hosts in the system filtered by optional host configuration parameters, if specified |  |
| `read_tags` | GET | `/hosts/{hostname}/tags` | Returns the tags associated with this host |  |
| `reallocate_memory` | POST | `/hosts/reallocateMemory` | Performs recalculation of memory params for roles present on the specified set of hosts, and applies the configuration changes |  |
| `reallocate_memory_diff` | POST | `/hosts/reallocateMemory/diff` | Performs recalculation of memory params for roles present on the specified set of hosts |  |
| `remove_hosts_from_cluster` | POST | `/hosts/removeHostsFromCluster` | Decommissions and deletes all non management roles from the list of hosts and removes the hosts from the cluster |  |
| `reset_host_id` | POST | `/hosts/{hostId}/commands/resetHostId` | Forces agent on specified host to switch to reporting a different host id |  |
| `stop_all_roles_on_node_gracefully` | POST | `/hosts/{hostname}/commands/stopAllRolesGracefully` | Gracefully stops all roles that support it; otherwise, performs a simple stop on the provided host |  |
| `update_host` | PUT | `/hosts/{hostId}` | Update an existing host in the system |  |
| `update_host_config` | PUT | `/hosts/{hostId}/config` | Updates the host configuration with the given values |  |

## cm_commands

11 tools.

- Command status/abort/retry and batch requests.
- Resource groups: BatchResourceApi, CommandsResourceApi

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `execute` | POST | `/batch` | Executes a batch of API requests in one database transaction |  |
| `abort_command` | POST | `/commands/{commandId}/abort` | Abort a running command |  |
| `find_command_by_correlation_id` | GET | `/commands/commandByCorrelationId/{correlationId}` | Retrieve command by the correlation ID that was provided at command creation |  |
| `get_command_result_data` | GET | `/commands/{commandId}/download` | Download the end result of a command |  |
| `get_command_with_steps` | GET | `/commands/{commandId}/steps` | Retrieve detailed information of an asynchronous command including the command steps |  |
| `get_standard_error` | GET | `/commands/{commandId}/logs/stderr` | Download a zip-compressed archive of standard error outputs for the command's one-off processes |  |
| `get_standard_output` | GET | `/commands/{commandId}/logs/stdout` | Download a zip-compressed archive of standard outputs for the command's one-off processes |  |
| `read_command` | GET | `/commands/{commandId}` | Retrieve detailed information on an asynchronous command |  |
| `read_commands` | GET | `/commands/commands` | Retrieve detailed information on all recent commands |  |
| `replication_report` | GET | `/commands/{commandId}/replicationReport` | Get the replication report CSV files |  |
| `retry` | POST | `/commands/{commandId}/retry` | Try to rerun a command |  |

## cm_manager

74 tools.

- Cloudera Manager server: config, license, deployment, Kerberos/TLS, diagnostics, peers-level commands, certificates, tools.
- Resource groups: CertManagerResourceApi, ClouderaManagerResourceApi, CspResourceApi, ToolsResourceApi

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `generate_certificate` | POST | `/certs/generateCertificate` | Exchange a cert request token for a certificate |  |
| `get_truststore` | GET | `/certs/truststore` | Gets the Auto-TLS truststore contents |  |
| `get_truststore_password` | GET | `/certs/truststorePassword` | Gets the configured CM truststore password |  |
| `add_config_policy` | POST | `/cm/configPolicies` | Add config policy (no summary in spec) |  |
| `add_custom_certs` | POST | `/cm/commands/addCustomCerts` | Add custom certificates to the Auto-TLS certificate database |  |
| `begin_trial` | POST | `/cm/trial/begin` | Begin trial license |  |
| `clusters_perf_inspector_command` | POST | `/cm/commands/clustersPerfInspector` | Run performance diagnostics test against specified clusters in ApiClustersPerfInspectorArgs User must be Full Administrator or Global Cluster Administrator |  |
| `collect_diagnostic_data_command` | POST | `/cm/commands/collectDiagnosticData` | Collect diagnostic data from hosts managed by Cloudera Manager |  |
| `delete_config_policy` | DELETE | `/cm/configPolicies` | Delete config policy (no summary in spec) |  |
| `delete_credentials_command` | POST | `/cm/commands/deleteCredentials` | Delete existing Kerberos credentials |  |
| `delete_instances` | POST | `/cm/deleteInstances` | Remove a list of cm servers from ha cluster |  |
| `deregister_clusters` | POST | `/cm/deregisterClusters` | Cloudera Manager connects to the Cloudera License Service and uploads the deregistration information for all deleted but still registered clusters if there i |  |
| `deregister_clusters_by_uuid` | POST | `/cm/deregisterClustersByUuid` | Cloudera Manager connects to the Cloudera License Service and uploads the deregistration information for the list of clusters provided |  |
| `disable_csp` | POST | `/cm/commands/disableCsp` | Disables the CSP by setting csp type to \"none\", only when currently the csp type is either \"embedded\" or \"vault\". This will decrypt the encrypted confi |  |
| `enable_csp` | POST | `/cm/commands/enableCsp` | Enables the CSP by setting csp type to \"vault\" or \"embedded\" as chosen by the user |  |
| `end_trial` | POST | `/cm/trial/end` | End trial license |  |
| `generate_cmca` | POST | `/cm/commands/generateCmca` | Generate a CMCA |  |
| `generate_credentials_adhoc` | POST | `/cm/commands/generateCredentialsAdhoc` | Generate missing Kerberos credentials, optionally accepting a list of ad-hoc credentials to generate as well |  |
| `generate_credentials_command` | POST | `/cm/commands/generateCredentials` | Generate missing Kerberos credentials |  |
| `generate_usage_report` | POST | `/cm/generateUsageReport` | Generate Usage reports for clusters |  |
| `get_cluster_support_token_list` | GET | `/cm/clusterSupportTokens` | Gets the support tokens for all the clusters |  |
| `get_config` | GET | `/cm/config` | Retrieve the Cloudera Manager settings |  |
| `get_config_policies` | GET | `/cm/configPolicies` | Get config policies (no summary in spec) |  |
| `get_deployment2` | GET | `/cm/deployment` | Retrieve full description of the entire Cloudera Manager deployment including all hosts, clusters, services, roles, users, settings, etc |  |
| `get_kerberos_info` | GET | `/cm/kerberosInfo` | Provides Cloudera Manager Kerberos information |  |
| `get_kerberos_principals` | GET | `/cm/kerberosPrincipals` | Returns the Kerberos principals needed by the services being managed by Cloudera Manager |  |
| `get_krb5_conf` | GET | `/cm/krb5conf` | Retrieves krb5.conf of the CM server host Available since API v41 |  |
| `get_licensed_feature_usage` | GET | `/cm/licensedFeatureUsage` | Retrieve a summary of licensed feature usage |  |
| `get_log` | GET | `/cm/log` | Returns the entire contents of the Cloudera Manager log file |  |
| `get_scm_db_info` | GET | `/cm/scmDbInfo` | Provides Cloudera Manager server's database information |  |
| `get_shutdown_readiness` | GET | `/cm/shutdownReadiness` | Retrieve Cloudera Manager's readiness for shutdown and destroy |  |
| `get_usage_report` | GET | `/cm/getUsageReport` | Retrieve the latest generated Usage reports for all clusters |  |
| `get_version` | GET | `/cm/version` | Provides version information of Cloudera Manager itself |  |
| `host_install_command` | POST | `/cm/commands/hostInstall` | Perform installation on a set of hosts |  |
| `hosts_decommission_command` | POST | `/cm/commands/hostsDecommission` | Decommission the given hosts |  |
| `hosts_offline_or_decommission_command` | POST | `/cm/commands/hostsOfflineOrDecommission` | Decommission the given hosts |  |
| `hosts_perf_inspector_command` | POST | `/cm/commands/hostsPerfInspector` | Run performance diagnostics test against specified hosts in ApiHostsPerfInspectorArgs User must be Full Administrator or Global Cluster Administrator |  |
| `hosts_recommission_and_exit_maintenance_mode_command` | POST | `/cm/commands/hostsRecommissionAndExitMaintenanceMode` | Recommission and exit maintenance on the given hosts |  |
| `hosts_recommission_command` | POST | `/cm/commands/hostsRecommission` | Recommission the given hosts |  |
| `hosts_recommission_with_start_command` | POST | `/cm/commands/hostsRecommissionWithStart` | Recommission the given hosts |  |
| `hosts_repair_roles_command` | POST | `/cm/commands/hostsRepairRoles` | Execute repair command on the given hosts |  |
| `hosts_start_roles_command` | POST | `/cm/commands/hostsStartRoles` | Start all the roles on the given hosts |  |
| `hosts_stop_roles_command` | POST | `/cm/commands/hostsStopRoles` | Stop all the roles on the given hosts |  |
| `import_admin_credentials` | POST | `/cm/commands/importAdminCredentials` | Imports the KDC Account Manager credentials needed by Cloudera Manager to create kerberos principals needed by CDH services |  |
| `import_cluster_template` | POST | `/cm/importClusterTemplate` | Create cluster as per the given cluster template |  |
| `import_kerberos_principal` | POST | `/cm/commands/importKerberosPrincipal` | Imports the Kerberos credentials for the specified principal which can then be used to add to a role's keytab by running Generate Credentials command |  |
| `inspect_hosts_command` | POST | `/cm/commands/inspectHosts` | Runs the host inspector on the configured hosts |  |
| `list_active_commands` | GET | `/cm/commands` | List active global commands |  |
| `list_all_generated_usage_reports` | GET | `/cm/listAllGeneratedUsageReports` | retrieve all generated cluster usage reports currently on disk |  |
| `manual_deregistration_request` | GET | `/cm/manualDeregistrationRequest` | API call to retrieve a manual deregistration payload to help manual “Deregister Cluster” process in Cloudera Admin Console (CAC) |  |
| `manual_deregistration_request_all_deleted` | GET | `/cm/manualDeregistrationRequestAllDeleted` | API call to retrieve a manual deregistration payload to help manual “Deregister Cluster” process in Cloudera Admin Console (CAC) |  |
| `manual_registration_request` | GET | `/cm/manualRegistrationRequest` | API call to retrieve a manual registration payload to help manual “Register Cluster” process in Cloudera Admin Console (CAC) |  |
| `migrate_cmca_to_db` | POST | `/cm/commands/migrateCmcaToDb` | Migrate CMCA to the DB |  |
| `process_manual_registration_response` | POST | `/cm/processManualRegistrationResponse` | API call to process the signed result of the manual registration or deregistration in Cloudera Admin Console (CAC) |  |
| `process_manual_registration_response_zip` | POST | `/cm/processManualRegistrationResponseZip` | API call to process the signed result of the manual registration or deregistration in Cloudera Admin Console (CAC) |  |
| `read_instance` | GET | `/cm/instances/{cmServerId}` | Retrieves the CM server information |  |
| `read_instances` | GET | `/cm/instances` | Retrieves all CM server information |  |
| `read_license` | GET | `/cm/license` | Retrieve information about the Cloudera Manager license |  |
| `read_registration_status` | GET | `/cm/registrationStatus` | Retrieve information about the Cloudera Manager registration statuses in the Cloudera Manager Database |  |
| `refresh_parcel_repos` | POST | `/cm/commands/refreshParcelRepos` | Submit a command to refresh parcels information |  |
| `register_clusters` | POST | `/cm/registerClusters` | Cloudera Manager connects to the Cloudera License Service and uploads the registration information for the list of clusters provided |  |
| `retrieve_keytab` | POST | `/cm/retrieveKeytab` | Retrieves a keytab for a list of principals |  |
| `rotate_csp_keys` | POST | `/cm/commands/rotateCspKeys` | Perform rotation of the CSP key |  |
| `rotate_license_registration_encryption_key` | POST | `/cm/rotateLicenseRegistrationEncryptionKey` | Rotate Cloudera License Server registration encryption key for this Cloudera Manager and re-register with the Cloudera License Server |  |
| `send_usage_report` | POST | `/cm/sendUsageReport` | Send Usage reports for clusters to cloudera ops |  |
| `test_external_authentication` | POST | `/cm/commands/testExternalAuthentication` | Launches a command to test the currently configured external authentication |  |
| `update_config` | PUT | `/cm/config` | Update the Cloudera Manager settings |  |
| `update_csp_type` | POST | `/cm/commands/updateCspType` | Updates the CSP type from previous csp type to new csp type, by copying the key_id (used for encryption of configs) from previous csp type to new csp type or |  |
| `update_deployment2` | PUT | `/cm/deployment` | Apply the supplied deployment description to the system |  |
| `update_global_truststore` | POST | `/cm/commands/updateGlobalTruststore` | Add/remove certificates to the Auto-TLS certificate truststore |  |
| `update_license` | POST | `/cm/license` | Updates the Cloudera Manager license |  |
| `upload_csp_cert` | PUT | `/csp/uploadCspCert` | Upload CA certificates, client certificates and client key for Credential Storage Provider |  |
| `echo` | GET | `/tools/echo` | Echoes the provided message back to the caller |  |
| `echo_error` | GET | `/tools/echoError` | Throws an error containing the given input message |  |

## cm_mgmt_service

41 tools.

- Cloudera Management Service and its roles, role commands, role config groups.
- Resource groups: MgmtRoleCommandsResourceApi, MgmtRoleConfigGroupsResourceApi, MgmtRolesResourceApi, MgmtServiceResourceApi

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `jmap_dump` | POST | `/cm/service/roleCommands/jmapDump` | Run the jmapDump diagnostic command |  |
| `jmap_histo` | POST | `/cm/service/roleCommands/jmapHisto` | Run the jmapHisto diagnostic command |  |
| `jstack` | POST | `/cm/service/roleCommands/jstack` | Run the jstack diagnostic command |  |
| `lsof` | POST | `/cm/service/roleCommands/lsof` | Run the lsof diagnostic command |  |
| `restart_command_mgmt_role_commands` | POST | `/cm/service/roleCommands/restart` | Restart a set of Cloudera Management Services roles |  |
| `start_command_mgmt_role_commands` | POST | `/cm/service/roleCommands/start` | Start a set of Cloudera Management Services roles |  |
| `stop_command_mgmt_role_commands` | POST | `/cm/service/roleCommands/stop` | Stop a set of Cloudera Management Services roles |  |
| `read_config` | GET | `/cm/service/roleConfigGroups/{roleConfigGroupName}/config` | Returns the current revision of the config for the specified role config group in the Cloudera Management Services |  |
| `read_role_config_group` | GET | `/cm/service/roleConfigGroups/{roleConfigGroupName}` | Returns the information for a given role config group in the Cloudera Management Services |  |
| `read_role_config_groups` | GET | `/cm/service/roleConfigGroups` | Returns the information for all role config groups in the Cloudera Management Services |  |
| `read_roles_mgmt_role_config_groups` | GET | `/cm/service/roleConfigGroups/{roleConfigGroupName}/roles` | Returns all roles in the given role config group in the Cloudera Management Services |  |
| `update_config` | PUT | `/cm/service/roleConfigGroups/{roleConfigGroupName}/config` | Updates the config for the given role config group in the Cloudera Management Services |  |
| `update_role_config_group` | PUT | `/cm/service/roleConfigGroups/{roleConfigGroupName}` | Updates an existing role config group in the Cloudera Management Services |  |
| `create_roles` | POST | `/cm/service/roles` | Create new roles in the Cloudera Management Services |  |
| `delete_role` | DELETE | `/cm/service/roles/{roleName}` | Delete a role from the Cloudera Management Services |  |
| `enter_maintenance_mode_mgmt_roles` | POST | `/cm/service/roles/{roleName}/commands/enterMaintenanceMode` | Put the Cloudera Management Service role into maintenance mode.This is a synchronous command |  |
| `exit_maintenance_mode_mgmt_roles` | POST | `/cm/service/roles/{roleName}/commands/exitMaintenanceMode` | Take the Cloudera Management Service role out of maintenance mode |  |
| `get_full_log` | GET | `/cm/service/roles/{roleName}/logs/full` | Retrieves the log file for the role's main process |  |
| `get_stacks_log` | GET | `/cm/service/roles/{roleName}/logs/stacks` | Retrieves the stacks log file, if any, for the role's main process |  |
| `get_stacks_logs_bundle` | GET | `/cm/service/roles/{roleName}/logs/stacksBundle` | Download a zip-compressed archive of role stacks logs |  |
| `get_standard_error` | GET | `/cm/service/roles/{roleName}/logs/stderr` | Retrieves the role's standard error output |  |
| `get_standard_output` | GET | `/cm/service/roles/{roleName}/logs/stdout` | Retrieves the role's standard output |  |
| `list_active_commands_mgmt_roles` | GET | `/cm/service/roles/{roleName}/commands` | List active role commands |  |
| `read_role` | GET | `/cm/service/roles/{roleName}` | Retrieve detailed information about a Cloudera Management Services role |  |
| `read_role_config` | GET | `/cm/service/roles/{roleName}/config` | Retrieve the configuration of a specific Cloudera Management Services role |  |
| `read_roles_mgmt_roles` | GET | `/cm/service/roles` | List all roles of the Cloudera Management Services |  |
| `update_role_config` | PUT | `/cm/service/roles/{roleName}/config` | Update the configuration of a Cloudera Management Services role |  |
| `auto_assign_roles` | PUT | `/cm/service/autoAssignRoles` | Automatically assign roles to hosts and create the roles for the Cloudera Management Service |  |
| `auto_configure` | PUT | `/cm/service/autoConfigure` | Automatically configures roles of the Cloudera Management Service |  |
| `delete_cms` | DELETE | `/cm/service` | Delete the Cloudera Management Services |  |
| `enter_maintenance_mode_mgmt_service` | POST | `/cm/service/commands/enterMaintenanceMode` | Put Cloudera Management Service into maintenance mode |  |
| `exit_maintenance_mode_mgmt_service` | POST | `/cm/service/commands/exitMaintenanceMode` | Take Cloudera Management Service out of maintenance mode |  |
| `list_active_commands_mgmt_service` | GET | `/cm/service/commands` | List active Cloudera Management Services commands |  |
| `list_role_types` | GET | `/cm/service/roleTypes` | List the supported role types for the Cloudera Management Services |  |
| `read_service` | GET | `/cm/service` | Retrieve information about the Cloudera Management Services |  |
| `read_service_config` | GET | `/cm/service/config` | Retrieve the configuration of the Cloudera Management Services |  |
| `restart_command_mgmt_service` | POST | `/cm/service/commands/restart` | Restart the Cloudera Management Services |  |
| `setup_cms` | PUT | `/cm/service` | Setup the Cloudera Management Services |  |
| `start_command_mgmt_service` | POST | `/cm/service/commands/start` | Start the Cloudera Management Services |  |
| `stop_command_mgmt_service` | POST | `/cm/service/commands/stop` | Stop the Cloudera Management Services |  |
| `update_service_config` | PUT | `/cm/service/config` | Update the Cloudera Management Services configuration |  |

## cm_auth_service

37 tools.

- Authentication Service and its roles, role commands, role config groups.
- Resource groups: AuthServiceResourceApi, AuthServiceRoleCommandsResourceApi, AuthServiceRoleConfigGroupsResourceApi, AuthServiceRolesResourceApi

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `auto_assign_roles` | PUT | `/cm/authService/autoAssignRoles` | Automatically assign roles to hosts and create the roles for the Authentication Service |  |
| `auto_configure` | PUT | `/cm/authService/autoConfigure` | Automatically configures roles of the Authentication Service |  |
| `delete` | DELETE | `/cm/authService` | Delete the Authentication Service |  |
| `enter_maintenance_mode_auth_service` | POST | `/cm/authService/commands/enterMaintenanceMode` | Put the Authentication Service into maintenance mode |  |
| `exit_maintenance_mode_auth_service` | POST | `/cm/authService/commands/exitMaintenanceMode` | Take the Authentication Service out of maintenance mode |  |
| `list_active_commands_auth_service` | GET | `/cm/authService/commands` | List active Authentication Service commands |  |
| `list_role_types` | GET | `/cm/authService/roleTypes` | List the supported role types for the Authentication Service |  |
| `read_service` | GET | `/cm/authService` | Retrieve information about the Authentication Services |  |
| `read_service_config` | GET | `/cm/authService/config` | Read service config (no summary in spec) |  |
| `restart_command_auth_service` | POST | `/cm/authService/commands/restart` | Restart the Authentication Service |  |
| `setup` | PUT | `/cm/authService` | Setup the Authentication Service |  |
| `start_command_auth_service` | POST | `/cm/authService/commands/start` | Start the Authentication Service |  |
| `stop_command_auth_service` | POST | `/cm/authService/commands/stop` | Stop the Authentication Service |  |
| `update_service_config` | PUT | `/cm/authService/config` | Update service config (no summary in spec) |  |
| `restart_command_auth_service_role_commands` | POST | `/cm/authService/roleCommands/restart` | Restart a set of Authentication Service roles |  |
| `start_command_auth_service_role_commands` | POST | `/cm/authService/roleCommands/start` | Start a set of Authentication Service roles |  |
| `stop_command_auth_service_role_commands` | POST | `/cm/authService/roleCommands/stop` | Stop a set of Authentication Service roles |  |
| `read_config` | GET | `/cm/authService/roleConfigGroups/{roleConfigGroupName}/config` | Returns the current revision of the config for the specified role config group in the Authentication Service |  |
| `read_role_config_group` | GET | `/cm/authService/roleConfigGroups/{roleConfigGroupName}` | Returns the information for a given role config group in the Authentication Service |  |
| `read_role_config_groups` | GET | `/cm/authService/roleConfigGroups` | Returns the information for all role config groups in the Authentication Service |  |
| `read_roles_auth_service_role_config_groups` | GET | `/cm/authService/roleConfigGroups/{roleConfigGroupName}/roles` | Returns all roles in the given role config group in the Authentication Service |  |
| `update_config` | PUT | `/cm/authService/roleConfigGroups/{roleConfigGroupName}/config` | Updates the config for the given role config group in the Authentication Service |  |
| `update_role_config_group` | PUT | `/cm/authService/roleConfigGroups/{roleConfigGroupName}` | Updates an existing role config group in the Authentication Service |  |
| `create_roles` | POST | `/cm/authService/roles` | Create new roles in the Authentication Services |  |
| `delete_role` | DELETE | `/cm/authService/roles/{roleName}` | Delete a role from the Authentication Services |  |
| `enter_maintenance_mode_auth_service_roles` | POST | `/cm/authService/roles/{roleName}/commands/enterMaintenanceMode` | Put the Authentication Service role into maintenance mode.This is a synchronous command |  |
| `exit_maintenance_mode_auth_service_roles` | POST | `/cm/authService/roles/{roleName}/commands/exitMaintenanceMode` | Take the Authentication Service role out of maintenance mode |  |
| `get_full_log` | GET | `/cm/authService/roles/{roleName}/logs/full` | Retrieves the log file for the role's main process |  |
| `get_stacks_log` | GET | `/cm/authService/roles/{roleName}/logs/stacks` | Retrieves the stacks log file, if any, for the role's main process |  |
| `get_stacks_logs_bundle` | GET | `/cm/authService/roles/{roleName}/logs/stacksBundle` | Download a zip-compressed archive of role stacks logs |  |
| `get_standard_error` | GET | `/cm/authService/roles/{roleName}/logs/stderr` | Retrieves the role's standard error output |  |
| `get_standard_output` | GET | `/cm/authService/roles/{roleName}/logs/stdout` | Retrieves the role's standard output |  |
| `list_active_commands_auth_service_roles` | GET | `/cm/authService/roles/{roleName}/commands` | List active role commands |  |
| `read_role` | GET | `/cm/authService/roles/{roleName}` | Retrieve detailed information about a Authentication Services role |  |
| `read_role_config` | GET | `/cm/authService/roles/{roleName}/config` | Retrieve the configuration of a specific Authentication Services role |  |
| `read_roles_auth_service_roles` | GET | `/cm/authService/roles` | List all roles of the Authentication Services |  |
| `update_role_config` | PUT | `/cm/authService/roles/{roleName}/config` | Update the configuration of a Authentication Services role |  |

## cm_users

19 tools.

- Users, auth roles, auth role metadata, external user mappings.
- Resource groups: AuthRoleMetadatasResourceApi, AuthRolesResourceApi, ExternalUserMappingsResourceApi, UsersResourceApi

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `read_auth_roles_metadata_auth_role_metadatas` | GET | `/authRoleMetadatas` | Returns a list of the auth roles' metadata for the built-in roles |  |
| `create_auth_roles` | POST | `/authRoles` | Creates a list of auth roles |  |
| `delete_auth_role` | DELETE | `/authRoles/{uuid}` | Deletes an auth role from the system |  |
| `read_auth_role` | GET | `/authRoles/{uuid}` | Returns detailed information about an auth role |  |
| `read_auth_roles` | GET | `/authRoles` | Returns a list of the auth roles configured in the system |  |
| `read_auth_roles_metadata_auth_roles` | GET | `/authRoles/metadata` | Returns a list of the auth roles' metadata for the built-in roles |  |
| `update_auth_role` | PUT | `/authRoles/{uuid}` | Updates the given auth role's information |  |
| `create_external_user_mappings` | POST | `/externalUserMappings` | Creates a list of external user mappings |  |
| `delete_external_user_mapping` | DELETE | `/externalUserMappings/{uuid}` | Deletes an external user mapping from the system |  |
| `read_external_user_mapping` | GET | `/externalUserMappings/{uuid}` | Returns detailed information about an external user mapping |  |
| `read_external_user_mappings` | GET | `/externalUserMappings` | Returns a list of the external user mappings configured in the system |  |
| `update_external_user_mapping` | PUT | `/externalUserMappings/{uuid}` | Updates the given external user mapping's information |  |
| `create_users2` | POST | `/users` | Creates a list of users |  |
| `delete_user2` | DELETE | `/users/{userName}` | Deletes a user from the system |  |
| `expire_sessions` | POST | `/users/expireSessions/{userName}` | Expires the sessions associated with interactive authenticated user in Cloudera Manager |  |
| `get_sessions` | GET | `/users/sessions` | Return a list of the sessions associated with interactive authenticated users in Cloudera Manager |  |
| `read_user2` | GET | `/users/{userName}` | Returns detailed information about a user |  |
| `read_users2` | GET | `/users` | Returns a list of the user names configured in the system |  |
| `update_user2` | PUT | `/users/{userName}` | Updates the given user's information |  |

## cm_replication

53 tools.

- Replication schedules, snapshot policies, CM peers.
- Resource groups: CmPeersResourceApi, ReplicationsResourceApi, SnapshotsResourceApi

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `create_peer` | POST | `/cm/peers` | Create a new Cloudera Manager peer |  |
| `delete_peer` | DELETE | `/cm/peers/{peerName}` | Delete Cloudera Manager peer |  |
| `list_peers` | GET | `/cm/peers` | Retrieves all configured Cloudera Manager peers |  |
| `read_peer` | GET | `/cm/peers/{peerName}` | Fetch information about an existing Cloudera Manager peer |  |
| `test_peer` | POST | `/cm/peers/{peerName}/commands/test` | Test the connectivity of a peer |  |
| `update_peer` | PUT | `/cm/peers/{peerName}` | Update information for a Cloudera Manager peer |  |
| `add_h_base_replication_peer` | POST | `/clusters/{clusterName}/services/{serviceName}/replications/operations/addReplicationPeer` | Starts a command that adds a new replication peer to HBase |  |
| `add_tables_to_h_base_peer` | POST | `/clusters/{clusterName}/services/{serviceName}/replications/operations/addTablesToHBasePeer` | Starts a command that adds tables and column families to an existing HBase replication peer |  |
| `check_h_base_tables_exist` | POST | `/clusters/{clusterName}/services/{serviceName}/replications/operations/checkTables` | Starts a command that checks if the specified tables exist in HBase |  |
| `collect_diagnostic_data` | POST | `/clusters/{clusterName}/services/{serviceName}/replications/{scheduleId}/collectDiagnosticData` | Collect diagnostic data for a schedule, optionally for a subset of commands on that schedule, matched by schedule ID |  |
| `create_cloud_credstore_on_hdfs` | POST | `/clusters/{clusterName}/services/{serviceName}/replications/createCloudCredstoreOnHdfs` | Creates a credstore provider jceks file on HDFS for the given service |  |
| `create_credstore` | POST | `/clusters/{clusterName}/services/{serviceName}/replications/createCredstore` | Use the following API endpoint instead: com.cloudera.api.v50.ReplicationsResourceV50#createCloudCredstoreOnHdfs(String, boolean) | deprecated |
| `create_schedules` | POST | `/clusters/{clusterName}/services/{serviceName}/replications` | Creates one or more replication schedules |  |
| `delete_all_schedules` | DELETE | `/clusters/{clusterName}/services/{serviceName}/replications` | Deletes all existing replication schedules |  |
| `delete_schedule` | DELETE | `/clusters/{clusterName}/services/{serviceName}/replications/{scheduleId}` | Deletes an existing replication schedule |  |
| `export_atlas_entites` | POST | `/clusters/{clusterName}/services/{serviceName}/replications/exportAtlasEntities` | Exports the given Atlas Entities (defined in the API body) to a zipped file in hdfs |  |
| `export_ranger_services` | POST | `/clusters/{clusterName}/services/{serviceName}/replications/exportRangerServices` | Exports the given Ranger services and policies (defined in the API body) to a zipped file |  |
| `fetch_h_base_column_families` | POST | `/clusters/{clusterName}/services/{serviceName}/replications/operations/fetchColumnFamilies` | Starts a command that fetches column families for the desired tables |  |
| `fetch_h_base_peer_info` | POST | `/clusters/{clusterName}/services/{serviceName}/replications/operations/fetchHBasePeerInfo` | Starts a command that fetches information about an HBase peer by its ID |  |
| `force_delete_schedule` | DELETE | `/clusters/{clusterName}/services/{serviceName}/replications/{scheduleId}/forcedDelete` | Deletes an existing replication schedule only from the DB |  |
| `generate_cloud_repl_credstore_password` | POST | `/clusters/{clusterName}/services/{serviceName}/replications/generateCloudReplCredstorePassword` | (Re)generates the cloud credential provider password, used by the given service, for replicating to the cloud |  |
| `get_replication_state` | GET | `/clusters/{clusterName}/services/{serviceName}/replications/replicationState` | returns the replication state |  |
| `is_hive3_reverse_direction_enabled` | GET | `/clusters/{clusterName}/services/{serviceName}/replications/isHive3ReverseDirectionEnabled` | This API endpoint checks if there is an ENABLED Hive3 replication policy on this server that replicates for the reverse direction |  |
| `list_h_base_namespaces` | GET | `/clusters/{clusterName}/services/{serviceName}/replications/operations/listNamespaces` | Starts a command that lists all namespaces in HBase |  |
| `list_h_base_peers` | GET | `/clusters/{clusterName}/services/{serviceName}/replications/operations/listPeers` | Starts a command that retrieves all peers registered in the HBase service |  |
| `list_h_base_tables` | GET | `/clusters/{clusterName}/services/{serviceName}/replications/operations/listTables` | Starts a command that lists tables from the HBase service |  |
| `post_copy_reconciliation` | POST | `/clusters/{clusterName}/services/{serviceName}/replications/{scheduleId}/postCopyReconciliation` | Starts a command that executes PostCopyReconciliation steps on a schedule |  |
| `read_history_replications` | GET | `/clusters/{clusterName}/services/{serviceName}/replications/{scheduleId}/history` | Returns a list of commands triggered by a schedule |  |
| `read_schedule` | GET | `/clusters/{clusterName}/services/{serviceName}/replications/{scheduleId}` | Returns information for a specific replication schedule |  |
| `read_schedules` | GET | `/clusters/{clusterName}/services/{serviceName}/replications` | Retrieves information about replication schedules |  |
| `recreate_cloud_credstores_on_hdfs` | POST | `/clusters/{clusterName}/services/{serviceName}/replications/recreateCloudCredstoresOnHdfs` | Recreates the existing credential provider jceks files on HDFS, that are used by the given service, for replicating to the cloud |  |
| `remove_h_base_peer` | POST | `/clusters/{clusterName}/services/{serviceName}/replications/operations/removeHBasePeer` | Starts a command that removes the specified HBase replication peer from the local HBase service |  |
| `remove_tables_from_h_base_peer` | POST | `/clusters/{clusterName}/services/{serviceName}/replications/operations/removeTablesFromHBasePeer` | Starts a command that removes tables and column families from an existing HBase replication peer |  |
| `reschedule_hive3_replication_metrics_getter` | POST | `/clusters/{clusterName}/services/{serviceName}/replications/rescheduleHive3ReplicationMetricsGetter` | Set the Hive3 Replication Metrics Getter next start time |  |
| `retry_schedule` | POST | `/clusters/{clusterName}/services/{serviceName}/replications/{scheduleId}/retry` | Retry the last command of a failed replication schedule |  |
| `run_copy_listing` | POST | `/clusters/{clusterName}/services/{serviceName}/replications/hdfsCopyListing` | Run the hdfs copy listing command The copy listing command will be triggered with the provided arguments Available since API v18 |  |
| `run_h_base_replication_retry_failed_snapshots` | POST | `/clusters/{clusterName}/services/{serviceName}/replications/{scheduleId}/runHBaseReplicationRetryFailedSnapshots` | Executes a command to run a HBase replication retry on failed snapshots for the given schedule ID |  |
| `run_h_base_replication_security_tool` | POST | `/clusters/{clusterName}/services/{serviceName}/replications/hbaseReplicationSecurityTool` | Run the hbase replication security tool The replication security tool is invoked against the provided arguments |  |
| `run_h_base_replication_validation_tool` | POST | `/clusters/{clusterName}/services/{serviceName}/replications/hbaseReplicationValidationTool` | Executes a command, which validates if HBase replication works properly for the given hbasePeerId |  |
| `run_hive_replication_query` | POST | `/clusters/{clusterName}/services/{serviceName}/replications/hiveReplicationQuery` | Execute a hive replication query on local HS2 service instance The command executes hive replication query on local HS2 instance with the provided arguments |  |
| `run_schedule` | POST | `/clusters/{clusterName}/services/{serviceName}/replications/{scheduleId}/run` | Run the schedule immediately |  |
| `set_c_fs_replication_scope` | POST | `/clusters/{clusterName}/services/{serviceName}/replications/operations/setCFsReplicationScope` | Starts a command that set the replication scope of the provided column families to the desired value |  |
| `update_h_base_peer_state` | PUT | `/clusters/{clusterName}/services/{serviceName}/replications/updateHBasePeerState` | Update HBase peer state ('DISABLE' or 'ENABLE'), and set the related HBase replication schedules ApiHBaseReplicationArguments.peerState for the given peer na |  |
| `update_h_base_replication_peer_state` | POST | `/clusters/{clusterName}/services/{serviceName}/replications/operations/updateReplicationPeerState` | Starts a command that updates the state of an existing HBase replication peer |  |
| `update_schedule` | PUT | `/clusters/{clusterName}/services/{serviceName}/replications/{scheduleId}` | Updates an existing replication schedule |  |
| `create_h_base_snapshot_from_remote` | POST | `/clusters/{clusterName}/services/{serviceName}/snapshots` | Create h base snapshot from remote (no summary in spec) |  |
| `create_policies` | POST | `/clusters/{clusterName}/services/{serviceName}/snapshots/policies` | Creates one or more snapshot policies |  |
| `delete_policy` | DELETE | `/clusters/{clusterName}/services/{serviceName}/snapshots/policies/{policyName}` | Deletes an existing snapshot policy |  |
| `list_h_base_snapshots_command` | POST | `/clusters/{clusterName}/services/{serviceName}/snapshots/listHBaseSnapshotsCommand` | Starts a command that lists the available HBase snapshots from S3 or local HBase service |  |
| `read_history_snapshots` | GET | `/clusters/{clusterName}/services/{serviceName}/snapshots/policies/{policyName}/history` | Returns a list of commands triggered by a snapshot policy |  |
| `read_policies` | GET | `/clusters/{clusterName}/services/{serviceName}/snapshots/policies` | Returns information for all snapshot policies |  |
| `read_policy` | GET | `/clusters/{clusterName}/services/{serviceName}/snapshots/policies/{policyName}` | Returns information for a specific snapshot policy |  |
| `update_policy` | PUT | `/clusters/{clusterName}/services/{serviceName}/snapshots/policies/{policyName}` | Updates an existing snapshot policy |  |

## cm_parcels

11 tools.

- Parcels per cluster.
- Resource groups: ParcelResourceApi, ParcelsResourceApi

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `activate_command` | POST | `/clusters/{clusterName}/parcels/products/{product}/versions/{version}/commands/activate` | A synchronous command that activates the parcel on the cluster |  |
| `cancel_distribution_command` | POST | `/clusters/{clusterName}/parcels/products/{product}/versions/{version}/commands/cancelDistribution` | A synchronous command that cancels the parcel distribution |  |
| `cancel_download_command` | POST | `/clusters/{clusterName}/parcels/products/{product}/versions/{version}/commands/cancelDownload` | A synchronous command that cancels the parcel download |  |
| `deactivate_command` | POST | `/clusters/{clusterName}/parcels/products/{product}/versions/{version}/commands/deactivate` | A synchronous command that deactivates the parcel on the cluster |  |
| `read_parcel` | GET | `/clusters/{clusterName}/parcels/products/{product}/versions/{version}` | Retrieves detailed information about a parcel |  |
| `remove_download_command` | POST | `/clusters/{clusterName}/parcels/products/{product}/versions/{version}/commands/removeDownload` | A synchronous command that removes the downloaded parcel |  |
| `start_distribution_command` | POST | `/clusters/{clusterName}/parcels/products/{product}/versions/{version}/commands/startDistribution` | A synchronous command that starts the distribution of the parcel to the cluster |  |
| `start_download_command` | POST | `/clusters/{clusterName}/parcels/products/{product}/versions/{version}/commands/startDownload` | A synchronous command that starts the parcel download |  |
| `start_removal_of_distribution_command` | POST | `/clusters/{clusterName}/parcels/products/{product}/versions/{version}/commands/startRemovalOfDistribution` | A synchronous command that removes the distribution from the hosts in the cluster |  |
| `get_parcel_usage` | GET | `/clusters/{clusterName}/parcels/usage` | Retrieve details parcel usage information for the cluster |  |
| `read_parcels` | GET | `/clusters/{clusterName}/parcels` | Lists all parcels that the cluster has access to |  |

## cm_external_accounts

13 tools.

- External accounts (AWS, Azure, etc.).
- Resource groups: ExternalAccountsResourceApi

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `create_account` | POST | `/externalAccounts/create` | Create a new external account |  |
| `delete_account` | DELETE | `/externalAccounts/delete/{name}` | Delete an external account, specifying its name |  |
| `external_account_command_by_name` | POST | `/externalAccounts/account/{name}/commands/{commandName}` | Executes a command on the external account specified by name |  |
| `get_supported_categories` | GET | `/externalAccounts/supportedCategories` | List of external account categories supported by this Cloudera Manager |  |
| `get_supported_types` | GET | `/externalAccounts/supportedTypes/{categoryName}` | List of external account types supported by this Cloudera Manager by category |  |
| `list_external_account_commands` | GET | `/externalAccounts/typeInfo/{typeName}/commandsByName` | Lists all the commands that can be executed by name on the provided external account type |  |
| `read_account` | GET | `/externalAccounts/account/{name}` | Get a single external account by account name |  |
| `read_account_by_display_name` | GET | `/externalAccounts/accountByDisplayName/{displayName}` | Get a single external account by display name |  |
| `read_account_credentials` | GET | `/externalAccounts/account/{name}/credentials` | Get un-redacted credentials of an external account for the given account name, currently supported only for ALTUS accounts |  |
| `read_accounts` | GET | `/externalAccounts/type/{typeName}` | Get a list of external accounts for a specific account type |  |
| `read_config` | GET | `/externalAccounts/account/{name}/config` | Get configs of external account for the given account name |  |
| `update_account` | PUT | `/externalAccounts/update` | Update an external account |  |
| `update_config` | PUT | `/externalAccounts/account/{name}/config` | Upadate configs of external account for the given account name |  |

## cm_control_planes

29 tools.

- Control planes (Data Services / ECS), data contexts, CDP remote contexts.
- Resource groups: CdpResourceApi, ControlPlanesResourceApi, DataContextsResourceApi

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `create_environment_command` | POST | `/cdp/createEnvironment` | Create an environment in ECS |  |
| `get_remote_context` | GET | `/cdp/remoteContext/byContext/{dataContextName}` | Get a JSON for creating a remote data context in a Workload cluster |  |
| `get_remote_context_by_cluster` | GET | `/cdp/remoteContext/byCluster/{clusterName}` | Get a JSON for creating a remote data context in a Workload cluster |  |
| `post_remote_context` | POST | `/cdp/remoteContext` | Create or update the remote data context in the Workload cluster |  |
| `add_tags` | PUT | `/controlPlanes/{controlPlaneUuid}/tags` | Attach tags to the control plane |  |
| `copy_images_in_features` | POST | `/controlPlanes/{controlPlaneUuid}/commands/copyImagesInFeatures` | Launches the command to copy images for one or more features (a comma separated list) |  |
| `delete_tags` | DELETE | `/controlPlanes/{controlPlaneUuid}/tags` | Remove the tags associated with the control plane |  |
| `generate_cleanup_docker` | POST | `/controlPlanes/commands/generateCleanupDocker` | Launches the Generate Docker Cleanup Script Command |  |
| `generate_copy_docker` | POST | `/controlPlanes/commands/generateCopyDocker` | Launches the Generate Copy Docker Script Command |  |
| `generate_external_vault_setup` | POST | `/controlPlanes/commands/generateExternalVaultSetup` | Launches the Generate Vault Setup Command command |  |
| `get_control_planes` | GET | `/controlPlanes` | Current Control Planes |  |
| `get_experience_cluster` | GET | `/controlPlanes/{controlPlaneUuid}/getTaggedCluster` | The cluster with tags matching this control plane's UUID, if any |  |
| `get_log_content` | POST | `/controlPlanes/fetchResources/{commandId}/logContent` | Fetches the log content for the specific command |  |
| `get_manifest_json` | POST | `/controlPlanes/fetchResources/manifest.json` | Fetches the manifest.json under the specified remote repo |  |
| `install_control_plane` | POST | `/controlPlanes/commands/installControlPlane` | Launches the install control plane command |  |
| `install_embedded_control_plane` | POST | `/controlPlanes/commands/installEmbeddedControlPlane` | Brings up a control plane on embedded kubernetes |  |
| `read_control_plane_by_uuid` | GET | `/controlPlanes/{controlPlaneUuid}` | The control plane with the given id |  |
| `read_tags` | GET | `/controlPlanes/{controlPlaneUuid}/tags` | Returns the tags associated with this control plane |  |
| `resolve_longhorn_upgrade_path` | POST | `/controlPlanes/commands/resolveLonghornUpgradePath` | Resolves the Longhorn multi-hop upgrade path for the embedded ECS upgrade wizard |  |
| `start_longhorn_multihop_upgrade` | POST | `/controlPlanes/commands/startLonghornMultihopUpgrade` | Starts the deferred Longhorn multihop upgrade from the control-plane upgrade wizard |  |
| `uninstall_control_plane` | POST | `/controlPlanes/{controlPlaneUuid}/commands/uninstallControlPlane` | Launches Uninstall Command on the control plane with the given uuid |  |
| `update_values_yaml` | POST | `/controlPlanes/{controlPlaneUuid}/commands/updateControlPlaneValuesYaml` | Launches update the values.yaml from the control plane with the given uuid This updates the content of values.yaml.merged in the CM database |  |
| `upgrade_control_plane` | POST | `/controlPlanes/{controlPlaneUuid}/commands/upgradeControlPlane` | Launches the Upgrade Command on the control plane with the given uuid |  |
| `upgrade_embedded_control_plane` | POST | `/controlPlanes/commands/upgradeEmbeddedControlPlane` | Upgrade a Containerized Cluster, including upgrading the control plane running on embedded kubernetes |  |
| `create_data_context` | POST | `/dataContexts` | Create a datacontext |  |
| `delete_data_context` | DELETE | `/dataContexts/{dataContextName}` | Delete a datacontext |  |
| `read_data_context` | GET | `/dataContexts/{dataContextName}` | Reads information about a datacontext |  |
| `read_data_contexts` | GET | `/dataContexts` | Get all the datacontexts |  |
| `update_data_context` | PUT | `/dataContexts` | Update a datacontext |  |

## cm_monitoring

27 tools.

- Time series, events, audits, dashboards, activities, Impala queries, YARN applications, tags.
- Resource groups: ActivitiesResourceApi, AuditsResourceApi, DashboardsResourceApi, EventsResourceApi, ImpalaQueriesResourceApi, TagsResourceApi, TimeSeriesResourceApi, YarnApplicationsResourceApi

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `get_metrics` | GET | `/clusters/{clusterName}/services/{serviceName}/activities/{activityId}/metrics` | Fetch metric readings for a particular activity |  |
| `read_activities` | GET | `/clusters/{clusterName}/services/{serviceName}/activities` | Read all activities in the system |  |
| `read_activity` | GET | `/clusters/{clusterName}/services/{serviceName}/activities/{activityId}` | Returns a specific activity in the system |  |
| `read_child_activities` | GET | `/clusters/{clusterName}/services/{serviceName}/activities/{activityId}/children` | Returns the child activities |  |
| `read_similar_activities` | GET | `/clusters/{clusterName}/services/{serviceName}/activities/{activityId}/similar` | Returns a list of similar activities |  |
| `read_audits` | GET | `/audits` | Fetch audit events from Cloudera Manager (CM) and CM managed services like HDFS, HBase, Impala, Hive, and Sentry |  |
| `stream_audits` | GET | `/audits/stream` | Stream audits (no summary in spec) |  |
| `create_dashboards` | POST | `/timeseries/dashboards` | Creates the list of dashboards |  |
| `delete_dashboard` | DELETE | `/timeseries/dashboards/{dashboardName}` | Deletes a dashboard |  |
| `get_dashboard` | GET | `/timeseries/dashboards/{dashboardName}` | Returns a dashboard definition for the specified name |  |
| `get_dashboards` | GET | `/timeseries/dashboards` | Returns the list of all user-customized dashboards |  |
| `read_event` | GET | `/events/{eventId}` | Returns a specific event in the system |  |
| `read_events` | GET | `/events` | Allows you to query events in the system |  |
| `cancel_impala_query` | POST | `/clusters/{clusterName}/services/{serviceName}/impalaQueries/{queryId}/cancel` | Cancels an Impala Query |  |
| `get_impala_queries` | GET | `/clusters/{clusterName}/services/{serviceName}/impalaQueries` | Returns a list of queries that satisfy the filter Available since API v4 |  |
| `get_impala_query_attributes` | GET | `/clusters/{clusterName}/services/{serviceName}/impalaQueries/attributes` | Returns the list of all attributes that the Service Monitor can associate with Impala queries |  |
| `get_query_details` | GET | `/clusters/{clusterName}/services/{serviceName}/impalaQueries/{queryId}` | Returns details about the query |  |
| `get_tags` | GET | `/tags` | Current CM entities and their tags |  |
| `read_tags_by_name` | GET | `/tags/{tagName}` | Get Entities given the Tag name, grouped by entity type |  |
| `get_entity_type_attributes` | GET | `/timeseries/entityTypeAttributes` | Retrieve all metric entity type attributes monitored by Cloudera Manager |  |
| `get_entity_types` | GET | `/timeseries/entityTypes` | Retrieve all metric entity types monitored by Cloudera Manager |  |
| `get_metric_schema` | GET | `/timeseries/schema` | Retrieve schema for all metrics The schema is fixed for a product version |  |
| `query_time_series` | GET | `/timeseries` | Retrieve time-series data from the Cloudera Manager (CM) time-series data store using a tsquery |  |
| `query_time_series_0` | POST | `/timeseries` | Retrieve time-series data from the Cloudera Manager (CM) time-series data store accepting HTTP POST request |  |
| `get_yarn_application_attributes` | GET | `/clusters/{clusterName}/services/{serviceName}/yarnApplications/attributes` | Returns the list of all attributes that the Service Monitor can associate with YARN applications |  |
| `get_yarn_applications` | GET | `/clusters/{clusterName}/services/{serviceName}/yarnApplications` | Returns a list of applications that satisfy the filter Available since API v6 |  |
| `kill_yarn_application` | POST | `/clusters/{clusterName}/services/{serviceName}/yarnApplications/{applicationId}/kill` | Kills an YARN Application Available since API v6 |  |
