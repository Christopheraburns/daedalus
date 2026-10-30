# CDP Public Cloud control plane

The services behind the cdp CLI. Every call is a signed POST to api.<region>.cdp.cloudera.com.

Flags: **beta** = not in the GA spec; **deprecated** = marked deprecated by the vendor spec; **in built-in pack** = the existing Daedalus `hdfs`/`s3` pack already has it.

## cdp_applications

7 tools.

- Product: CDP Applications (beta app service)
- Spec title: Cloudera Applications Service
- Description: Applications is a web service for managing application lifecycle.
- Spec source: not in GA docs, beta (https://github.com/cloudera/cdp-dev-docs/blob/5a189fcd6124f3e1b671ebee69cc229a47326865/api-docs-beta/swagger/applications.yaml) v0.9.164 (BETA)
- Service release: BETA; products: CDP
- Auth: Base URL https://api.<region>.cdp.cloudera.com (e.g. us-west-1, eu-1, ap-1; https://api.usg-1.cdp.clouderagovt.com for US Gov). All calls are POST with Content-Type: application/json and a JSON body, signed per CDP request signing V1 (headers x-altus-date and x-altus-auth = ed25519v1/rsav1 signature using the CDP access key ID + private key).
- Operations: 7 (7 beta-only, 0 deprecated)

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `create_application` | POST | `/api/v1/applications/createApplication` | Create Application | beta |
| `delete_application` | POST | `/api/v1/applications/deleteApplication` | Delete Application | beta |
| `describe_application` | POST | `/api/v1/applications/describeApplication` | Describe Application | beta |
| `get_application_metadata_configuration` | POST | `/api/v1/applications/getApplicationMetadataConfiguration` | Get Application Metadata Configuration | beta |
| `list_applications` | POST | `/api/v1/applications/listApplications` | Lists Applications | beta |
| `list_applications_metadata` | POST | `/api/v1/applications/listApplicationsMetadata` | Lists Applications Metadata | beta |
| `list_available_clusters` | POST | `/api/v1/applications/listAvailableClusters` | Lists available clusters | beta |

## cdp_audit

11 tools.

- Product: CDP Audit (account audit events / archiving)
- Spec title: Cloudera Audit Service
- Description: Cloudera CDP Auditing is a web service for interacting with the audit subsystem.
- Spec source: GA (https://github.com/cloudera/cdp-dev-docs/blob/5a189fcd6124f3e1b671ebee69cc229a47326865/api-docs/swagger/audit.yaml) v0.9.164, beta (https://github.com/cloudera/cdp-dev-docs/blob/5a189fcd6124f3e1b671ebee69cc229a47326865/api-docs-beta/swagger/audit.yaml) v0.9.164 (BETA)
- Service release: PUBLIC; products: CDP
- Auth: Base URL https://api.<region>.cdp.cloudera.com (e.g. us-west-1, eu-1, ap-1; https://api.usg-1.cdp.clouderagovt.com for US Gov). All calls are POST with Content-Type: application/json and a JSON body, signed per CDP request signing V1 (headers x-altus-date and x-altus-auth = ed25519v1/rsav1 signature using the CDP access key ID + private key).
- Operations: 11 (0 beta-only, 0 deprecated)

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `archive_audit_events` | POST | `/api/v1/audit/archiveAuditEvents` | Archive audit events. |  |
| `batch_events_for_archiving` | POST | `/api/v1/audit/batchEventsForArchiving` | Create batches of audit events to be archived. |  |
| `configure_archiving` | POST | `/api/v1/audit/configureArchiving` | Configures the audit system for archiving audit events to external cloud storage. |  |
| `get_archiving_config` | POST | `/api/v1/audit/getArchivingConfig` | Retrieve the current archiving configuration. |  |
| `get_archiving_status` | POST | `/api/v1/audit/getArchivingStatus` | Retrieve the status for an archive process. |  |
| `get_batch_events_for_archiving_status` | POST | `/api/v1/audit/getBatchEventsForArchivingStatus` | Get the status of creating batches of audit events to be archived. |  |
| `list_events` | POST | `/api/v1/audit/listEvents` | List all audit events recorded in a specified time span, and optionally with a specified request ID and/or event source. |  |
| `list_events_in_archive_batch` | POST | `/api/v1/audit/listEventsInArchiveBatch` | List events contained in a single archive batch. |  |
| `list_outstanding_archive_batches` | POST | `/api/v1/audit/listOutstandingArchiveBatches` | List outstanding (unarchived) archive batches. |  |
| `list_recent_archive_runs` | POST | `/api/v1/audit/listRecentArchiveRuns` | List recent archive runs. |  |
| `mark_archive_batches_as_successful` | POST | `/api/v1/audit/markArchiveBatchesAsSuccessful` | Mark archive batches as successful. |  |

## cdp_cloudprivatelinks

9 tools.

- Product: CDP Cloud Private Links (AWS PrivateLink / Azure Private Link to control plane)
- Spec title: Cloudera Private Links API Service
- Description: Provisions Private Link Endpoints on the cloud environments.
- Spec source: GA (https://github.com/cloudera/cdp-dev-docs/blob/5a189fcd6124f3e1b671ebee69cc229a47326865/api-docs/swagger/cloudprivatelinks.yaml) v0.9.164, beta (https://github.com/cloudera/cdp-dev-docs/blob/5a189fcd6124f3e1b671ebee69cc229a47326865/api-docs-beta/swagger/cloudprivatelinks.yaml) v0.9.164 (BETA)
- Service release: PUBLIC; products: CDP
- Auth: Base URL https://api.<region>.cdp.cloudera.com (e.g. us-west-1, eu-1, ap-1; https://api.usg-1.cdp.clouderagovt.com for US Gov). All calls are POST with Content-Type: application/json and a JSON body, signed per CDP request signing V1 (headers x-altus-date and x-altus-auth = ed25519v1/rsav1 signature using the CDP access key ID + private key).
- Operations: 9 (0 beta-only, 0 deprecated)

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `authorize_private_link_service_access` | POST | `/api/v1/cloudprivatelinks/authorizePrivateLinkServiceAccess` | Authorize Private Link services access for the cloud account id. |  |
| `create_private_link_endpoint` | POST | `/api/v1/cloudprivatelinks/createPrivateLinkEndpoint` | Creates Private Link endpoints. |  |
| `delete_private_link_endpoint` | POST | `/api/v1/cloudprivatelinks/deletePrivateLinkEndpoint` | Deletes Private Link endpoints. |  |
| `get_private_link_status` | POST | `/api/v1/cloudprivatelinks/getPrivateLinkStatus` | Get the status of a Private Link. |  |
| `list_private_link_endpoint_statuses` | POST | `/api/v1/cloudprivatelinks/listPrivateLinkEndpointStatuses` | Lists the statuses of the Private Link endpoints that are in creation/deletion status. |  |
| `list_private_link_services_for_region` | POST | `/api/v1/cloudprivatelinks/listPrivateLinkServicesForRegion` | Lists the Private Link services that are supported for the region and service group. |  |
| `migrate_private_link_endpoints` | POST | `/api/v1/cloudprivatelinks/migratePrivateLinkEndpoints` | Migrates Private Link endpoints to fallback VPCE services. |  |
| `revoke_private_link_service_access` | POST | `/api/v1/cloudprivatelinks/revokePrivateLinkServiceAccess` | Revoke Private Link services access for the cloud account ID. |  |
| `update_private_link_endpoint` | POST | `/api/v1/cloudprivatelinks/updatePrivateLinkEndpoint` | Update existing Private Link endpoint. |  |

## cdp_compute

25 tools.

- Product: CDP Compute (Kubernetes compute clusters for data services)
- Spec title: Cloudera Compute Service
- Description: Defining service of compute public API service
- Spec source: GA (https://github.com/cloudera/cdp-dev-docs/blob/5a189fcd6124f3e1b671ebee69cc229a47326865/api-docs/swagger/compute.yaml) v0.9.164, beta (https://github.com/cloudera/cdp-dev-docs/blob/5a189fcd6124f3e1b671ebee69cc229a47326865/api-docs-beta/swagger/compute.yaml) v0.9.164 (BETA)
- Service release: PUBLIC; products: CDP
- Auth: Base URL https://api.<region>.cdp.cloudera.com (e.g. us-west-1, eu-1, ap-1; https://api.usg-1.cdp.clouderagovt.com for US Gov). All calls are POST with Content-Type: application/json and a JSON body, signed per CDP request signing V1 (headers x-altus-date and x-altus-auth = ed25519v1/rsav1 signature using the CDP access key ID + private key).
- Operations: 25 (10 beta-only, 0 deprecated)

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `add_user` | POST | `/api/v1/compute/addUser` | Add User | beta |
| `create_cluster` | POST | `/api/v1/compute/createCluster` | Create compute cluster |  |
| `delete_cluster` | POST | `/api/v1/compute/deleteCluster` | Delete compute cluster |  |
| `delete_deployment` | POST | `/api/v1/compute/deleteDeployment` | Deletes a deployment | beta |
| `delete_user` | POST | `/api/v1/compute/deleteUser` | Delete User | beta |
| `describe_cluster` | POST | `/api/v1/compute/describeCluster` | Describe compute cluster |  |
| `describe_deployment` | POST | `/api/v1/compute/describeDeployment` | Describes a deployment |  |
| `describe_user` | POST | `/api/v1/compute/describeUser` | Describe User | beta |
| `get_kube_config` | POST | `/api/v1/compute/getKubeConfig` | Get kube config content | beta |
| `get_operation_details` | POST | `/api/v1/compute/getOperationDetails` | GetOperationDetails |  |
| `get_operation_status` | POST | `/api/v1/compute/getOperationStatus` | GetOperationStatus |  |
| `install_deployment` | POST | `/api/v1/compute/installDeployment` | Installs a deployment | beta |
| `list_clusters` | POST | `/api/v1/compute/listClusters` | List compute clusters |  |
| `list_deployments` | POST | `/api/v1/compute/listDeployments` | List deployments in the cluster. |  |
| `list_operations` | POST | `/api/v1/compute/listOperations` | ListOperations | beta |
| `list_users` | POST | `/api/v1/compute/listUsers` | List Users | beta |
| `resume_cluster` | POST | `/api/v1/compute/resumeCluster` | Resume Cluster |  |
| `retry_operation` | POST | `/api/v1/compute/retryOperation` | ResetOperation |  |
| `rollback_deployment` | POST | `/api/v1/compute/rollbackDeployment` | Rollbacks a deployment to a previous revision | beta |
| `suspend_cluster` | POST | `/api/v1/compute/suspendCluster` | Suspend Cluster |  |
| `update_cluster` | POST | `/api/v1/compute/updateCluster` | Update cluster |  |
| `update_instance_group` | POST | `/api/v1/compute/updateInstanceGroup` | Update instance group | beta |
| `upgrade_cluster` | POST | `/api/v1/compute/upgradeCluster` | Upgrade kubernetes version of the cluster |  |
| `upgrade_deployment` | POST | `/api/v1/compute/upgradeDeployment` | Upgrades a deployment to a different chart. |  |
| `validate_cluster` | POST | `/api/v1/compute/validateCluster` | Validate compute cluster |  |

## cdp_consumption

1 tools.

- Product: CDP Consumption (usage / compute-hours)
- Spec title: Cloudera Consumption API Service
- Description: Provides an interface to the consumption service.
- Spec source: GA (https://github.com/cloudera/cdp-dev-docs/blob/5a189fcd6124f3e1b671ebee69cc229a47326865/api-docs/swagger/consumption.yaml) v0.9.164, beta (https://github.com/cloudera/cdp-dev-docs/blob/5a189fcd6124f3e1b671ebee69cc229a47326865/api-docs-beta/swagger/consumption.yaml) v0.9.164 (BETA)
- Service release: PUBLIC; products: CDP
- Auth: Base URL https://api.<region>.cdp.cloudera.com (e.g. us-west-1, eu-1, ap-1; https://api.usg-1.cdp.clouderagovt.com for US Gov). All calls are POST with Content-Type: application/json and a JSON body, signed per CDP request signing V1 (headers x-altus-date and x-altus-auth = ed25519v1/rsav1 signature using the CDP access key ID + private key).
- Operations: 1 (0 beta-only, 0 deprecated)

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `list_compute_usage_records` | POST | `/api/v1/consumption/listComputeUsageRecords` | Lists compute usage records. |  |

## cdp_datacatalog

21 tools.

- Product: Cloudera Data Catalog
- Spec title: Cloudera DataCatalog Service
- Description: Cloudera DataCatalog Service is a web service, using this service a user can execute operations like launching profilers in DataCatalog.
- Spec source: GA (https://github.com/cloudera/cdp-dev-docs/blob/5a189fcd6124f3e1b671ebee69cc229a47326865/api-docs/swagger/datacatalog.yaml) v0.9.164, beta (https://github.com/cloudera/cdp-dev-docs/blob/5a189fcd6124f3e1b671ebee69cc229a47326865/api-docs-beta/swagger/datacatalog.yaml) v0.9.164 (BETA)
- Service release: PUBLIC; products: CDP
- Auth: Base URL https://api.<region>.cdp.cloudera.com (e.g. us-west-1, eu-1, ap-1; https://api.usg-1.cdp.clouderagovt.com for US Gov). All calls are POST with Content-Type: application/json and a JSON body, signed per CDP request signing V1 (headers x-altus-date and x-altus-auth = ed25519v1/rsav1 signature using the CDP access key ID + private key).
- Operations: 21 (0 beta-only, 0 deprecated)

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `add_assets_to_data_share` | POST | `/api/v1/datacatalog/addAssetsToDataShare` | Add assets to an existing Data Share. |  |
| `create_data_share` | POST | `/api/v1/datacatalog/createDataShare` | Create a Data Share for Data Sharing. |  |
| `create_external_users` | POST | `/api/v1/datacatalog/createExternalUsers` | Create external users for Data Sharing. |  |
| `delete_data_share` | POST | `/api/v1/datacatalog/deleteDataShare` | Delete a Data Share by its ID. |  |
| `delete_external_user` | POST | `/api/v1/datacatalog/deleteExternalUser` | Delete an external user. |  |
| `get_data_share` | POST | `/api/v1/datacatalog/getDataShare` | Get a Data Share by its ID. |  |
| `get_fgac_status_by_assets` | POST | `/api/v1/datacatalog/getFgacStatusByAssets` | get FGAC (Fine-Grained Access Control) status by assets. |  |
| `get_suggested_tags` | POST | `/api/v1/datacatalog/getSuggestedTags` | Get Suggested tags by the Data Compliance profiler. |  |
| `grant_access_to_external_users_on_data_share` | POST | `/api/v1/datacatalog/grantAccessToExternalUsersOnDataShare` | Grant access to external users on a Data Share. |  |
| `launch_profilers` | POST | `/api/v1/datacatalog/launchProfilers` | Launches DataCatalog profilers in a given datalake. |  |
| `list_data_shares` | POST | `/api/v1/datacatalog/listDataShares` | List Data Shares. |  |
| `list_external_users` | POST | `/api/v1/datacatalog/listExternalUsers` | List external users for Data Sharing. |  |
| `regenerate_external_user_credentials` | POST | `/api/v1/datacatalog/regenerateExternalUserCredentials` | Regenerate credentials for an external user. |  |
| `remove_access_of_external_users_on_data_share` | POST | `/api/v1/datacatalog/removeAccessOfExternalUsersOnDataShare` | Remove access of external users on a Data Share. |  |
| `remove_assets_from_data_share` | POST | `/api/v1/datacatalog/removeAssetsFromDataShare` | Remove assets from an existing Data Share. |  |
| `review_suggested_tags` | POST | `/api/v1/datacatalog/reviewSuggestedTags` | Review tags suggested by Data Compliance Profiler |  |
| `revoke_external_user_credentials` | POST | `/api/v1/datacatalog/revokeExternalUserCredentials` | Revoke credentials for an external user. |  |
| `share_data_share` | POST | `/api/v1/datacatalog/shareDataShare` | Share the Data Share for external users. |  |
| `unshare_data_share` | POST | `/api/v1/datacatalog/unshareDataShare` | Unshare the Data Share for external users. |  |
| `update_access_of_external_users_on_data_share` | POST | `/api/v1/datacatalog/updateAccessOfExternalUsersOnDataShare` | Update access of external users on a Data Share. |  |
| `update_data_share` | POST | `/api/v1/datacatalog/updateDataShare` | Update the Data Share. |  |

## cdp_datahub

80 tools.

- Product: Cloudera Data Hub (workload clusters)
- Spec title: Cloudera Data hub Service
- Description: Cloudera data hub is a service for launching and managing workload clusters powered by Cloudera Runtime.
- Spec source: GA (https://github.com/cloudera/cdp-dev-docs/blob/5a189fcd6124f3e1b671ebee69cc229a47326865/api-docs/swagger/datahub.yaml) v0.9.164, beta (https://github.com/cloudera/cdp-dev-docs/blob/5a189fcd6124f3e1b671ebee69cc229a47326865/api-docs-beta/swagger/datahub.yaml) v0.9.164 (BETA)
- Service release: PUBLIC; products: CDP
- Auth: Base URL https://api.<region>.cdp.cloudera.com (e.g. us-west-1, eu-1, ap-1; https://api.usg-1.cdp.clouderagovt.com for US Gov). All calls are POST with Content-Type: application/json and a JSON body, signed per CDP request signing V1 (headers x-altus-date and x-altus-auth = ed25519v1/rsav1 signature using the CDP access key ID + private key).
- Operations: 80 (5 beta-only, 3 deprecated)

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `cancel_datahub_diagnostics` | POST | `/api/v1/datahub/cancelDatahubDiagnostics` | Cancel running Datahub diagnostics collections |  |
| `check_cluster_upgrade_reinitiable` | POST | `/api/v1/datahub/checkClusterUpgradeReinitiable` | Checks if the last failed upgrade operation on a cluster can be reinitiated. | beta |
| `collect_cm_diagnostics` | POST | `/api/v1/datahub/collectCmDiagnostics` | Start Datahub Cloudera Manager based diagnostics collection |  |
| `collect_datahub_diagnostics` | POST | `/api/v1/datahub/collectDatahubDiagnostics` | Start DataHub diagnostics collection |  |
| `create_aws_cluster` | POST | `/api/v1/datahub/createAWSCluster` | Creates an AWS workload cluster. |  |
| `create_aws_gov_cloud_cluster` | POST | `/api/v1/datahub/createAWSGovCloudCluster` | Creates an AWS Data Hub cluster for GovCloud. |  |
| `create_auto_scale_rules` | POST | `/api/v1/datahub/createAutoScaleRules` | Create Auto Scaling rules for a DataHub cluster |  |
| `create_azure_cluster` | POST | `/api/v1/datahub/createAzureCluster` | Creates an Azure workload cluster. |  |
| `create_cluster_definition` | POST | `/api/v1/datahub/createClusterDefinition` | Creates a cluster definition. A cluster definition is a reusable template in JSON format that can be used for creating multiple Data Hub clusters with identical cloud provider settings. |  |
| `create_cluster_template` | POST | `/api/v1/datahub/createClusterTemplate` | Creates a cluster template. A cluster template is a reusable template in JSON format that can be used for creating multiple Data Hub clusters with identical Cloudera Runtime settings. |  |
| `create_custom_configurations` | POST | `/api/v1/datahub/createCustomConfigurations` | Creates custom configurations. Custom Configurations are sets of properties or name-value pairs that belong to any of the services present in cluster templates. These can be used to override and/or append properties to the corresponding cluster template while launching DataHub clusters. |  |
| `create_gcp_cluster` | POST | `/api/v1/datahub/createGCPCluster` | Creates a GCP workload cluster. |  |
| `create_recipe` | POST | `/api/v1/datahub/createRecipe` | Creates recipe. A recipe is a script that runs on all nodes of a specified instance group. |  |
| `delete_auto_scale_rules` | POST | `/api/v1/datahub/deleteAutoScaleRules` | Delete AutoScaling policies for a DataHub cluster |  |
| `delete_cluster` | POST | `/api/v1/datahub/deleteCluster` | Deletes a workload cluster. |  |
| `delete_cluster_definitions` | POST | `/api/v1/datahub/deleteClusterDefinitions` | Deletes cluster definitions. A cluster definition is a reusable template in JSON format that can be used for creating multiple Data Hub clusters with identical cloud provider settings. |  |
| `delete_cluster_templates` | POST | `/api/v1/datahub/deleteClusterTemplates` | Deletes cluster templates. A cluster template is a reusable template in JSON format that can be used for creating multiple Data Hub clusters with identical Cloudera Runtime settings. |  |
| `delete_custom_configurations` | POST | `/api/v1/datahub/deleteCustomConfigurations` | Deletes custom configurations. Custom Configurations are sets of properties or name-value pairs that belong to any of the services present in cluster templates. These can be used to override and/or append properties to the corresponding cluster template while launching DataHub clusters. |  |
| `delete_instances` | POST | `/api/v1/datahub/deleteInstances` | Deletes instances for the specified cluster. |  |
| `delete_recipes` | POST | `/api/v1/datahub/deleteRecipes` | Deletes recipes. A recipe is a script that runs on all nodes of a specified instance group. |  |
| `describe_auto_scale_rules` | POST | `/api/v1/datahub/describeAutoScaleRules` | Describe the AutoScaling policies for a DataHub cluster |  |
| `describe_cluster` | POST | `/api/v1/datahub/describeCluster` | Describes a workload cluster. |  |
| `describe_cluster_definition` | POST | `/api/v1/datahub/describeClusterDefinition` | Describes a cluster definition. A cluster definition is a reusable template in JSON format that can be used for creating multiple Data Hub clusters with identical cloud provider settings. |  |
| `describe_cluster_template` | POST | `/api/v1/datahub/describeClusterTemplate` | Describes a cluster template. A cluster template is a reusable template in JSON format that can be used for creating multiple Data Hub clusters with identical Cloudera Runtime settings. |  |
| `describe_custom_configurations` | POST | `/api/v1/datahub/describeCustomConfigurations` | Describes custom configurations. Custom Configurations are sets of properties or name-value pairs that belong to any of the services present in cluster templates. These can be used to override and/or append properties to the corresponding cluster template while launching DataHub clusters. |  |
| `describe_database_server` | POST | `/api/v1/datahub/describeDatabaseServer` | Gets external database server details. | beta |
| `describe_recipe` | POST | `/api/v1/datahub/describeRecipe` | Describes recipe. A recipe is a script that runs on all nodes of a specified instance group. |  |
| `describe_scaling_activity` | POST | `/api/v1/datahub/describeScalingActivity` | Describes the Scaling Activity using Cluster CRN or Cluster NAME and operation ID. |  |
| `finalize_zookeeper_to_kraft_migration` | POST | `/api/v1/datahub/finalizeZookeeperToKraftMigration` | Finalize the migration from Zookeeper to KRaft broker. |  |
| `get_cluster_host_status` | POST | `/api/v1/datahub/getClusterHostStatus` | Get cluster host status. |  |
| `get_cluster_service_status` | POST | `/api/v1/datahub/getClusterServiceStatus` | Get cluster service status. |  |
| `get_cm_roles` | POST | `/api/v1/datahub/getCmRoles` | Gather Cloudera Manager roles that can be used for filtering in CM based diagnostics collection. |  |
| `get_datahub_log_descriptors` | POST | `/api/v1/datahub/getDatahubLogDescriptors` | Gather log descriptors that are used for diagnostics collection. |  |
| `get_operation` | POST | `/api/v1/datahub/getOperation` | Get the latest (in progress or finished) operation for the datahub cluster. |  |
| `get_vm_types` | POST | `/api/v1/datahub/getVmTypes` | Creates a recommendation that advises virtual machine types for the given cluster template based on the given properties. |  |
| `list_auto_scale_history` | POST | `/api/v1/datahub/listAutoScaleHistory` | List AutoScale history activity for a DataHub cluster. |  |
| `list_cluster_definitions` | POST | `/api/v1/datahub/listClusterDefinitions` | Lists cluster definitions. A cluster definition is a reusable template in JSON format that can be used for creating multiple Data Hub clusters with identical cloud provider settings. |  |
| `list_cluster_lifecycle_events` | POST | `/api/v1/datahub/listClusterLifecycleEvents` | Lists Workload cluster lifecycle events. |  |
| `list_cluster_templates` | POST | `/api/v1/datahub/listClusterTemplates` | Lists cluster templates. A cluster template is a reusable template in JSON format that can be used for creating multiple Data Hub clusters with identical Cloudera Runtime settings. |  |
| `list_clusters` | POST | `/api/v1/datahub/listClusters` | Lists workload clusters. |  |
| `list_custom_configurations` | POST | `/api/v1/datahub/listCustomConfigurations` | Lists custom configurations. Custom Configurations are sets of properties or name-value pairs that belong to any of the services present in cluster templates. These can be used to override and/or append properties to the corresponding cluster template while launching DataHub clusters. |  |
| `list_datahub_diagnostics` | POST | `/api/v1/datahub/listDatahubDiagnostics` | List recent Datahub diagnostics collections |  |
| `list_datahub_secret_types` | POST | `/api/v1/datahub/listDatahubSecretTypes` | Lists all Datahub related secret types. |  |
| `list_recipes` | POST | `/api/v1/datahub/listRecipes` | Lists recipes. A recipe is a script that runs on all nodes of a specified instance group. |  |
| `list_scaling_activities` | POST | `/api/v1/datahub/listScalingActivities` | Lists Scaling activities for a cluster. |  |
| `migrate_skus` | POST | `/api/v1/datahub/migrateSkus` | Migrate Data Hub cluster SKUs. |  |
| `migrate_zookeeper_to_kraft` | POST | `/api/v1/datahub/migrateZookeeperToKraft` | Migrate from Zookeeper to KRaft broker. |  |
| `prepare_cluster_upgrade` | POST | `/api/v1/datahub/prepareClusterUpgrade` | Running upgrade related validations and prepares the required parcels for the upgrade. |  |
| `refresh_datalake_configurations` | POST | `/api/v1/datahub/refreshDatalakeConfigurations` | Refresh configurations from the Data Lake of a Data Hub cluster by name or CRN. | beta |
| `reinitiate_cluster_upgrade` | POST | `/api/v1/datahub/reinitiateClusterUpgrade` | Reinitiates the last failed upgrade operation on a cluster. | beta |
| `renew_certificate` | POST | `/api/v1/datahub/renewCertificate` | Renew certificate on datahub cluster by name or CRN | deprecated |
| `renew_public_certificate` | POST | `/api/v1/datahub/renewPublicCertificate` | Renews public certificate on a Datahub cluster by name or CRN. |  |
| `repair_cluster` | POST | `/api/v1/datahub/repairCluster` | Repairs a cluster. |  |
| `replace_recipes` | POST | `/api/v1/datahub/replaceRecipes` | Replaces recipes for the given instance groups. |  |
| `restart_cluster_instances` | POST | `/api/v1/datahub/restartClusterInstances` | Restarts instances of a cluster on Cloud provider. |  |
| `retry_cluster` | POST | `/api/v1/datahub/retryCluster` | Retries creation of a failed workload cluster. |  |
| `rollback_zookeeper_to_kraft_migration` | POST | `/api/v1/datahub/rollbackZookeeperToKraftMigration` | Rollback the migration from Zookeeper to KRaft broker. |  |
| `rotate_auto_tls_certificates` | POST | `/api/v1/datahub/rotateAutoTlsCertificates` | Rotate autotls certificates on the datahub's hosts | deprecated |
| `rotate_db_certificate` | POST | `/api/v1/datahub/rotateDbCertificate` | Rotates database ssl certificate for a specific Data Hub |  |
| `rotate_private_certificates` | POST | `/api/v1/datahub/rotatePrivateCertificates` | Rotates private certificates on the hosts of Datahub. |  |
| `rotate_salt_password` | POST | `/api/v1/datahub/rotateSaltPassword` | Rotate SaltStack user password on Data Hub instances. | deprecated |
| `rotate_secrets` | POST | `/api/v1/datahub/rotateSecrets` | Rotates secrets for a specific datahub |  |
| `scale_cluster` | POST | `/api/v1/datahub/scaleCluster` | Scales a cluster by adding or removing cluster nodes. |  |
| `set_catalog` | POST | `/api/v1/datahub/setCatalog` | Sets a catalog for a DataHub. |  |
| `set_default_java_version` | POST | `/api/v1/datahub/setDefaultJavaVersion` | Configures the default Java version for the Data Hub. |  |
| `start_cluster` | POST | `/api/v1/datahub/startCluster` | Starts a stopped workload cluster. |  |
| `start_cluster_vertical_scaling` | POST | `/api/v1/datahub/startClusterVerticalScaling` | Initiates the vertical scaling on Data Hub cluster. |  |
| `start_database_upgrade` | POST | `/api/v1/datahub/startDatabaseUpgrade` | Upgrades the database of the Data Hub cluster. |  |
| `start_instances` | POST | `/api/v1/datahub/startInstances` | Starts instances of a particular host group in the Data Hub cluster. |  |
| `stop_cluster` | POST | `/api/v1/datahub/stopCluster` | Stops a workload cluster. |  |
| `stop_instances` | POST | `/api/v1/datahub/stopInstances` | Stops instances of particular host group in the Data Hub cluster. |  |
| `sync_cluster` | POST | `/api/v1/datahub/syncCluster` | Synchronizes the state of a cluster with the cloud provider and Cloudera Manager. |  |
| `sync_component_versions_from_cm` | POST | `/api/v1/datahub/syncComponentVersionsFromCm` | Syncs component versions from CM after a failed upgrade. |  |
| `trigger_disk_sync` | POST | `/api/v1/datahub/triggerDiskSync` | Triggers disk sync job for a datahub either in dry run or persist mode. | beta |
| `update_auto_scale_rules` | POST | `/api/v1/datahub/updateAutoScaleRules` | Modify AutoScaling for a DataHub cluster |  |
| `update_orchestrator_state` | POST | `/api/v1/datahub/updateOrchestratorState` | Run orchestrator engine state update on the Data Hub cluster. |  |
| `update_public_dns_entries` | POST | `/api/v1/datahub/updatePublicDnsEntries` | Update public DNS entries of a Data Hub cluster by name or CRN. |  |
| `update_to_aws_imds_v1` | POST | `/api/v1/datahub/updateToAwsImdsV1` | Updates Data Hub AWS cluster to use IMDSv1. |  |
| `update_to_aws_imds_v2` | POST | `/api/v1/datahub/updateToAwsImdsV2` | Updates Data Hub AWS cluster to use IMDSv2. |  |
| `upgrade_cluster` | POST | `/api/v1/datahub/upgradeCluster` | Upgrades the OS or data platform on a datahub cluster. |  |

## cdp_datalake

67 tools.

- Product: Cloudera SDX Data Lake
- Spec title: Cloudera Datalake Service
- Description: Cloudera data lake is a service for launching and managing data lake clusters powered by Cloudera Runtime.
- Spec source: GA (https://github.com/cloudera/cdp-dev-docs/blob/5a189fcd6124f3e1b671ebee69cc229a47326865/api-docs/swagger/datalake.yaml) v0.9.164, beta (https://github.com/cloudera/cdp-dev-docs/blob/5a189fcd6124f3e1b671ebee69cc229a47326865/api-docs-beta/swagger/datalake.yaml) v0.9.164 (BETA)
- Service release: PUBLIC; products: CDP
- Auth: Base URL https://api.<region>.cdp.cloudera.com (e.g. us-west-1, eu-1, ap-1; https://api.usg-1.cdp.clouderagovt.com for US Gov). All calls are POST with Content-Type: application/json and a JSON body, signed per CDP request signing V1 (headers x-altus-date and x-altus-auth = ed25519v1/rsav1 signature using the CDP access key ID + private key).
- Operations: 67 (11 beta-only, 5 deprecated)

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `backup_datalake` | POST | `/api/v1/datalake/backupDatalake` | Create backup of datalake. |  |
| `backup_datalake_status` | POST | `/api/v1/datalake/backupDatalakeStatus` | Check the status of a datalake backup operation performed. |  |
| `cancel_backup` | POST | `/api/v1/datalake/cancelBackup` | Cancels the specified ongoing backup operation. |  |
| `cancel_datalake_diagnostics` | POST | `/api/v1/datalake/cancelDatalakeDiagnostics` | Cancel running Datalake diagnostics collections |  |
| `cancel_restore` | POST | `/api/v1/datalake/cancelRestore` | Cancels the restore that was performed. |  |
| `check_datalake_upgrade_reinitiable` | POST | `/api/v1/datalake/checkDatalakeUpgradeReinitiable` | Check if the last failed upgrade operation on a DataLake can be reinitiated. | beta |
| `collect_cm_diagnostics` | POST | `/api/v1/datalake/collectCmDiagnostics` | Start DataLake Cloudera Manager based diagnostics collection |  |
| `collect_datalake_diagnostics` | POST | `/api/v1/datalake/collectDatalakeDiagnostics` | Start DataLake diagnostics collection |  |
| `create_aws_datalake` | POST | `/api/v1/datalake/createAWSDatalake` | Creates an AWS datalake. |  |
| `create_aws_gov_cloud_datalake` | POST | `/api/v1/datalake/createAWSGovCloudDatalake` | Creates a Data Lake on AWS GovCloud. |  |
| `create_azure_datalake` | POST | `/api/v1/datalake/createAzureDatalake` | Creates an Azure datalake. |  |
| `create_gcp_datalake` | POST | `/api/v1/datalake/createGCPDatalake` | Creates an GCP Data Lake. |  |
| `delete_backup_restore_configuration` | POST | `/api/v1/datalake/deleteBackupRestoreConfiguration` | Deletes the backup and restore configuration for the datalake. | beta |
| `delete_datalake` | POST | `/api/v1/datalake/deleteDatalake` | Deletes a datalake. |  |
| `describe_database_server` | POST | `/api/v1/datalake/describeDatabaseServer` | Gets external database server details. |  |
| `describe_datalake` | POST | `/api/v1/datalake/describeDatalake` | Describes a datalake. |  |
| `enable_ranger_raz` | POST | `/api/v1/datalake/enableRangerRaz` | Sets the Ranger Raz enabled flag to true if Raz is manually installed on the datalake. | beta |
| `finalize_zookeeper_to_kraft_migration` | POST | `/api/v1/datalake/finalizeZookeeperToKraftMigration` | Finalize the migration from Zookeeper to KRaft broker. | beta |
| `get_backup_restore_configuration` | POST | `/api/v1/datalake/getBackupRestoreConfiguration` | Gets the backup and restore configuration for the datalake. | beta |
| `get_cluster_host_status` | POST | `/api/v1/datalake/getClusterHostStatus` | Get cluster host status. |  |
| `get_cluster_service_status` | POST | `/api/v1/datalake/getClusterServiceStatus` | Get cluster service status. |  |
| `get_cm_roles` | POST | `/api/v1/datalake/getCmRoles` | Gather Cloudera Manager roles that can be used for filtering in CM based diagnostics collection. |  |
| `get_datalake_log_descriptors` | POST | `/api/v1/datalake/getDatalakeLogDescriptors` | Gather log descriptors that are used for diagnostics collection. |  |
| `get_operation` | POST | `/api/v1/datalake/getOperation` | Used for retrieving operation status for the datalake cluster, defaulting to the most recent operation. Provide an operationId to view details of a specific historical operation. |  |
| `list_datalake_backups` | POST | `/api/v1/datalake/listDatalakeBackups` | List all the backup operations that were performed on the datalake. |  |
| `list_datalake_diagnostics` | POST | `/api/v1/datalake/listDatalakeDiagnostics` | List recent Datalake diagnostics collections |  |
| `list_datalake_secret_types` | POST | `/api/v1/datalake/listDatalakeSecretTypes` | Lists all Datalake related secret types. |  |
| `list_datalakes` | POST | `/api/v1/datalake/listDatalakes` | Lists datalakes. |  |
| `list_runtimes` | POST | `/api/v1/datalake/listRuntimes` | Lists the datalake versions. |  |
| `migrate_skus` | POST | `/api/v1/datalake/migrateSkus` | Migrate the Data Lake to a new SKU. |  |
| `migrate_zookeeper_to_kraft` | POST | `/api/v1/datalake/migrateZookeeperToKraft` | Migrate from Zookeeper to KRaft broker. | beta |
| `prepare_datalake_upgrade` | POST | `/api/v1/datalake/prepareDatalakeUpgrade` | Prepares the Data Lake cluster for upgrade. |  |
| `recover_datalake` | POST | `/api/v1/datalake/recoverDatalake` | Recover data lake to the original version after a failed upgrade. |  |
| `reinitiate_datalake_upgrade` | POST | `/api/v1/datalake/reinitiateDatalakeUpgrade` | Reinitiate the last failed upgrade operation on a DataLake. | beta |
| `renew_certificate` | POST | `/api/v1/datalake/renewCertificate` | Renew certificate on Datalake cluster by name or CRN | deprecated |
| `renew_public_certificate` | POST | `/api/v1/datalake/renewPublicCertificate` | Renews public certificate on Datalake cluster by name or CRN. |  |
| `repair_datalake` | POST | `/api/v1/datalake/repairDatalake` | Repairs a datalake. |  |
| `replace_recipes` | POST | `/api/v1/datalake/replaceRecipes` | Replaces recipes for the given instance groups. |  |
| `resize_datalake` | POST | `/api/v1/datalake/resizeDatalake` | Resizes the given datalake to the given target size. |  |
| `restart_datalake_instances` | POST | `/api/v1/datalake/restartDatalakeInstances` | Restarts instances of a datalake on Cloud provider. |  |
| `restore_datalake` | POST | `/api/v1/datalake/restoreDatalake` | Restore the datalake from backup taken. |  |
| `restore_datalake_status` | POST | `/api/v1/datalake/restoreDatalakeStatus` | Check the status of datalake restore operation. |  |
| `retry_datalake` | POST | `/api/v1/datalake/retryDatalake` | Retry last failed operation on a datalake. |  |
| `rollback_zookeeper_to_kraft_migration` | POST | `/api/v1/datalake/rollbackZookeeperToKraftMigration` | Rollback the migration from Zookeeper to KRaft broker. | beta |
| `rotate_auto_tls_certificates` | POST | `/api/v1/datalake/rotateAutoTlsCertificates` | Rotate autotls certificates on the datalake's hosts | deprecated |
| `rotate_db_certificate` | POST | `/api/v1/datalake/rotateDbCertificate` | Rotates database ssl certificate for a specific Data Lake |  |
| `rotate_private_certificates` | POST | `/api/v1/datalake/rotatePrivateCertificates` | Rotates private certificates on the datalake's hosts. |  |
| `rotate_salt_password` | POST | `/api/v1/datalake/rotateSaltPassword` | Rotate SaltStack user password on DataLake instances. | deprecated |
| `rotate_secrets` | POST | `/api/v1/datalake/rotateSecrets` | Rotates secrets for a specific Datalake |  |
| `scale_horizontally` | POST | `/api/v1/datalake/scaleHorizontally` | Horizontally scale the Data Lake nodes, to add additional compute nodes to the cluster. |  |
| `set_backup_restore_configuration` | POST | `/api/v1/datalake/setBackupRestoreConfiguration` | Sets the backup and restore configuration for the datalake. | beta |
| `set_catalog` | POST | `/api/v1/datalake/setCatalog` | Sets a catalog for a DataLake. |  |
| `set_default_java_version` | POST | `/api/v1/datalake/setDefaultJavaVersion` | Configures the default Java version for the Data Lake. |  |
| `start_database_upgrade` | POST | `/api/v1/datalake/startDatabaseUpgrade` | Upgrades the database of the Data Lake cluster. |  |
| `start_datalake` | POST | `/api/v1/datalake/startDatalake` | Start Datalake | deprecated |
| `start_datalake_vertical_scaling` | POST | `/api/v1/datalake/startDatalakeVerticalScaling` | Initiates the vertical scaling on Data Lake. |  |
| `stop_datalake` | POST | `/api/v1/datalake/stopDatalake` | Stop Datalake | deprecated |
| `sync_component_versions_from_cm` | POST | `/api/v1/datalake/syncComponentVersionsFromCm` | Syncs component versions from CM after a failed upgrade. |  |
| `trigger_disk_sync` | POST | `/api/v1/datalake/triggerDiskSync` | Triggers disk sync job for a datalake either in dry run or persist mode. | beta |
| `update_orchestrator_state` | POST | `/api/v1/datalake/updateOrchestratorState` | Run orchestrator engine state update on the Data Lake cluster. |  |
| `update_public_dns_entries` | POST | `/api/v1/datalake/updatePublicDnsEntries` | Update public DNS entries of a Data Lake cluster by name or CRN. |  |
| `update_to_aws_imds_v1` | POST | `/api/v1/datalake/updateToAwsImdsV1` | Updates Data Lake AWS cluster to use IMDSv1. |  |
| `update_to_aws_imds_v2` | POST | `/api/v1/datalake/updateToAwsImdsV2` | Updates Data Lake AWS cluster to use IMDSv2. |  |
| `upgrade_datalake` | POST | `/api/v1/datalake/upgradeDatalake` | OS or data platform upgrade for the SDX cluster. |  |
| `validate_aws_cloud_storage` | POST | `/api/v1/datalake/validateAwsCloudStorage` | Validates AWS cloud storage. |  |
| `validate_azure_cloud_storage` | POST | `/api/v1/datalake/validateAzureCloudStorage` | Validates Azure cloud storage. |  |
| `zookeeper_to_kraft_migration_status` | POST | `/api/v1/datalake/zookeeperToKraftMigrationStatus` | Returns the status of the Zookeeper to KRaft migration. | beta |

## cdp_de

25 tools.

- Product: Cloudera Data Engineering (CDE)
- Spec title: Cloudera Data Engineering
- Description: Create and manage Cloudera Data Engineering Services.
- Spec source: GA (https://github.com/cloudera/cdp-dev-docs/blob/5a189fcd6124f3e1b671ebee69cc229a47326865/api-docs/swagger/de.yaml) v0.9.164, beta (https://github.com/cloudera/cdp-dev-docs/blob/5a189fcd6124f3e1b671ebee69cc229a47326865/api-docs-beta/swagger/de.yaml) v0.9.164 (BETA)
- Service release: PUBLIC; products: CDP
- Auth: Base URL https://api.<region>.cdp.cloudera.com (e.g. us-west-1, eu-1, ap-1; https://api.usg-1.cdp.clouderagovt.com for US Gov). All calls are POST with Content-Type: application/json and a JSON body, signed per CDP request signing V1 (headers x-altus-date and x-altus-auth = ed25519v1/rsav1 signature using the CDP access key ID + private key).
- Operations: 25 (1 beta-only, 0 deprecated)

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `cancel_backup` | POST | `/api/v1/de/cancelBackup` | Cancel Cloudera Data Engineering(CDE) Service Backup |  |
| `create_backup` | POST | `/api/v1/de/createBackup` | Backup Cloudera Data Engineering(CDE) Service |  |
| `create_vc` | POST | `/api/v1/de/createVc` | Create Virtual Cluster |  |
| `delete_backup` | POST | `/api/v1/de/deleteBackup` | Delete Cloudera Data Engineering(CDE) Service Backup |  |
| `delete_vc` | POST | `/api/v1/de/deleteVc` | Delete Virtual Cluster |  |
| `describe_backup` | POST | `/api/v1/de/describeBackup` | Describe Cloudera Data Engineering(CDE) Service Backup |  |
| `describe_service` | POST | `/api/v1/de/describeService` | Describe Cloudera Data Engineering(CDE) Service |  |
| `describe_vc` | POST | `/api/v1/de/describeVc` | Describe Virtual Cluster |  |
| `disable_service` | POST | `/api/v1/de/disableService` | Disable Cloudera Data Engineering(CDE) Service |  |
| `enable_service` | POST | `/api/v1/de/enableService` | Enable Cloudera Data Engineering(CDE) Service |  |
| `get_backup_logs` | POST | `/api/v1/de/getBackupLogs` | Retrieve Cloudera Data Engineering(CDE) Service Backup Logs |  |
| `get_kubeconfig` | POST | `/api/v1/de/getKubeconfig` | Get Kubeconfig for the CDE service |  |
| `get_service_init_logs` | POST | `/api/v1/de/getServiceInitLogs` | Retrieve Cloudera Data Engineering(CDE) Service Initialization Logs |  |
| `get_suspend_resume_status` | POST | `/api/v1/de/getSuspendResumeStatus` | Get CDE Service Suspend Resume Status. |  |
| `get_upgrade_status` | POST | `/api/v1/de/getUpgradeStatus` | Get CDE Service Upgrade Status. |  |
| `list_backups` | POST | `/api/v1/de/listBackups` | List Cloudera Data Engineering(CDE) Service Backups |  |
| `list_services` | POST | `/api/v1/de/listServices` | List Cloudera Data Engineering(CDE) Services |  |
| `list_vcs` | POST | `/api/v1/de/listVcs` | List Virtual Clusters |  |
| `restore_service` | POST | `/api/v1/de/restoreService` | Restore Cloudera Data Engineering(CDE) Service |  |
| `resume_vc` | POST | `/api/v1/de/resumeVc` | Initiates resume on the requested VC. |  |
| `suspend_resume_service` | POST | `/api/v1/de/suspendResumeService` | Trigger a particular step of the suspend/resume process. | beta |
| `suspend_vc` | POST | `/api/v1/de/suspendVc` | Initiates suspend on the requested VC. |  |
| `update_service` | POST | `/api/v1/de/updateService` | Update Cloudera Data Engineering (CDE) Service |  |
| `update_vc` | POST | `/api/v1/de/updateVc` | Update Cloudera Data Engineering (CDE) Virtual Cluster |  |
| `upgrade_service` | POST | `/api/v1/de/upgradeService` | Trigger a particular step (prepare, backup, upgrade, resume) of the upgrade framework. |  |

## cdp_df

66 tools.

- Product: Cloudera DataFlow (control plane: services, catalog, readyflows)
- Spec title: Cloudera DataFlow Service
- Description: Manage DataFlow Services.
- Spec source: GA (https://github.com/cloudera/cdp-dev-docs/blob/5a189fcd6124f3e1b671ebee69cc229a47326865/api-docs/swagger/df.yaml) v0.9.164, beta (https://github.com/cloudera/cdp-dev-docs/blob/5a189fcd6124f3e1b671ebee69cc229a47326865/api-docs-beta/swagger/df.yaml) v0.9.164 (BETA)
- Service release: PUBLIC; products: CDP
- Auth: Base URL https://api.<region>.cdp.cloudera.com (e.g. us-west-1, eu-1, ap-1; https://api.usg-1.cdp.clouderagovt.com for US Gov). All calls are POST with Content-Type: application/json and a JSON body, signed per CDP request signing V1 (headers x-altus-date and x-altus-auth = ed25519v1/rsav1 signature using the CDP access key ID + private key).
- Operations: 66 (0 beta-only, 0 deprecated)

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `add_readyflow` | POST | `/api/v1/df/addReadyflow` | Add ready flow. |  |
| `assign_to_collection` | POST | `/api/v1/df/assignToCollection` | Assign a flow definition to collection. |  |
| `cancel_delete_project` | POST | `/api/v1/df/cancelDeleteProject` | Cancels deletion of a Project. |  |
| `create_collection` | POST | `/api/v1/df/createCollection` | Create catalog collection. |  |
| `create_flow_version_tag` | POST | `/api/v1/df/createFlowVersionTag` | Create flow version tag. |  |
| `create_project` | POST | `/api/v1/df/createProject` | Creates a Project. |  |
| `delete_added_readyflow` | POST | `/api/v1/df/deleteAddedReadyflow` | Delete added ready flow. |  |
| `delete_collection` | POST | `/api/v1/df/deleteCollection` | Delete catalog collection. |  |
| `delete_flow` | POST | `/api/v1/df/deleteFlow` | Delete flow. |  |
| `delete_flow_version_tag` | POST | `/api/v1/df/deleteFlowVersionTag` | Delete flow version tag. |  |
| `delete_project` | POST | `/api/v1/df/deleteProject` | Deletes a Project. |  |
| `describe_added_readyflow` | POST | `/api/v1/df/describeAddedReadyflow` | Describe added ready flow detail. |  |
| `describe_collection` | POST | `/api/v1/df/describeCollection` | Describe catalog collection. |  |
| `describe_deployment` | POST | `/api/v1/df/describeDeployment` | Describe deployment. |  |
| `describe_deployment_event_detail` | POST | `/api/v1/df/describeDeploymentEventDetail` | Describe event detail for deployment. |  |
| `describe_flow` | POST | `/api/v1/df/describeFlow` | Describe flow. |  |
| `describe_flow_event_detail_in_deployment` | POST | `/api/v1/df/describeFlowEventDetailInDeployment` | Describe flow event detail in a deployment. |  |
| `describe_flow_in_deployment` | POST | `/api/v1/df/describeFlowInDeployment` | Describe flow in a deployment. |  |
| `describe_project` | POST | `/api/v1/df/describeProject` | Describes a Project. |  |
| `describe_readyflow` | POST | `/api/v1/df/describeReadyflow` | Describe ready flow. |  |
| `describe_service` | POST | `/api/v1/df/describeService` | Describe service. |  |
| `describe_service_event_detail` | POST | `/api/v1/df/describeServiceEventDetail` | Describe event history detail for service. |  |
| `disable_service` | POST | `/api/v1/df/disableService` | Disable service. |  |
| `enable_service` | POST | `/api/v1/df/enableService` | Enable DataFlow service from a CDP environment. |  |
| `get_flow_version` | POST | `/api/v1/df/getFlowVersion` | Get flow version. |  |
| `get_kubeconfig` | POST | `/api/v1/df/getKubeconfig` | Get Kubeconfig. |  |
| `grant_user_kubernetes_access` | POST | `/api/v1/df/grantUserKubernetesAccess` | Grant remote user access to the service's cluster. |  |
| `import_flow_definition` | POST | `/api/v1/df/importFlowDefinition` | Import a new flow definition. |  |
| `import_flow_definition_version` | POST | `/api/v1/df/importFlowDefinitionVersion` | Import a new flow definition version to an existing flow. |  |
| `initiate_deployment` | POST | `/api/v1/df/initiateDeployment` | Initiate a deployment creation. |  |
| `initiate_flow_in_deployment` | POST | `/api/v1/df/initiateFlowInDeployment` | Initiate the flow creation process in a deployment. |  |
| `list_collections` | POST | `/api/v1/df/listCollections` | List catalog collections. |  |
| `list_deployable_services_for_new_deployments` | POST | `/api/v1/df/listDeployableServicesForNewDeployments` | List services that a DataFlow Admin can deploy to. |  |
| `list_deployment_active_alerts` | POST | `/api/v1/df/listDeploymentActiveAlerts` | List active alerts for deployment. |  |
| `list_deployment_events` | POST | `/api/v1/df/listDeploymentEvents` | List event history for deployment. |  |
| `list_deployment_kp_is` | POST | `/api/v1/df/listDeploymentKPIs` | List deployment KPIs. |  |
| `list_deployment_system_metrics` | POST | `/api/v1/df/listDeploymentSystemMetrics` | List deployment System metrics. |  |
| `list_deployments` | POST | `/api/v1/df/listDeployments` | List deployments. |  |
| `list_diagnostics` | POST | `/api/v1/df/listDiagnostics` | List diagnostics. |  |
| `list_filter_options` | POST | `/api/v1/df/listFilterOptions` | List filter options. |  |
| `list_flow_active_alerts_in_deployment` | POST | `/api/v1/df/listFlowActiveAlertsInDeployment` | List active alerts for a flow in a deployment. |  |
| `list_flow_definition_versions` | POST | `/api/v1/df/listFlowDefinitionVersions` | List flow definition versions. |  |
| `list_flow_definitions` | POST | `/api/v1/df/listFlowDefinitions` | List flow definitions. |  |
| `list_flow_events_in_deployment` | POST | `/api/v1/df/listFlowEventsInDeployment` | List event history for a flow in a deployment. |  |
| `list_flow_kpis_in_deployment` | POST | `/api/v1/df/listFlowKpisInDeployment` | List KPI metrics for a flow in a deployment. |  |
| `list_flow_version_tags` | POST | `/api/v1/df/listFlowVersionTags` | List flow version tags. |  |
| `list_flows_in_deployment` | POST | `/api/v1/df/listFlowsInDeployment` | List flows in a deployment. |  |
| `list_notifications` | POST | `/api/v1/df/listNotifications` | List notifications. |  |
| `list_project_filter_options` | POST | `/api/v1/df/listProjectFilterOptions` | List filter options. |  |
| `list_projects` | POST | `/api/v1/df/listProjects` | List Projects. |  |
| `list_readyflows` | POST | `/api/v1/df/listReadyflows` | List ready flows. |  |
| `list_service_active_alerts` | POST | `/api/v1/df/listServiceActiveAlerts` | List active alerts for service. |  |
| `list_service_events` | POST | `/api/v1/df/listServiceEvents` | List events for service. |  |
| `list_service_system_metrics` | POST | `/api/v1/df/listServiceSystemMetrics` | List service System metrics. |  |
| `list_services` | POST | `/api/v1/df/listServices` | List services. |  |
| `list_user_kubernetes_access` | POST | `/api/v1/df/listUserKubernetesAccess` | List users that have access to the service's cluster. |  |
| `renew_certificates` | POST | `/api/v1/df/renewCertificates` | Renew workload UI certificates. |  |
| `reset_service` | POST | `/api/v1/df/resetService` | Resets all references to a service. Only not-enabled services can be reset. Makes no attempt to clean-up resources. |  |
| `revoke_user_kubernetes_access` | POST | `/api/v1/df/revokeUserKubernetesAccess` | Revoke access for the remote user from the service's cluster. |  |
| `rotate_password` | POST | `/api/v1/df/rotatePassword` | Rotate password. |  |
| `start_get_diagnostics_collection` | POST | `/api/v1/df/startGetDiagnosticsCollection` | Start diagnostics collection. |  |
| `update_collection` | POST | `/api/v1/df/updateCollection` | Update a collection's details. |  |
| `update_node_images` | POST | `/api/v1/df/updateNodeImages` | Update cloud provider node images. |  |
| `update_project` | POST | `/api/v1/df/updateProject` | Updates a Project. |  |
| `update_service` | POST | `/api/v1/df/updateService` | Update service. |  |
| `upgrade_service` | POST | `/api/v1/df/upgradeService` | Upgrade service. |  |

## cdp_dfworkload

71 tools.

- Product: Cloudera DataFlow workload API (deployments, flows, parameter groups)
- Spec title: Cloudera DataFlow Workload Service
- Description: This REST API provides remote access to the DataFlow Service. Endpoints that are marked as [BETA] are subject to change in future releases of the application without backwards compatibility and without a major version change.
- Spec source: GA (https://github.com/cloudera/cdp-dev-docs/blob/5a189fcd6124f3e1b671ebee69cc229a47326865/api-docs/swagger/dfworkload.yaml) v0.9.164, beta (https://github.com/cloudera/cdp-dev-docs/blob/5a189fcd6124f3e1b671ebee69cc229a47326865/api-docs-beta/swagger/dfworkload.yaml) v0.9.164 (BETA)
- Service release: PUBLIC; products: CDP
- Auth: Workload API, not the control-plane host. Paths are /dfx/api/rpc-v1/... on the DataFlow workload endpoint of a specific environment. The CLI first calls iam generateWorkloadAuthToken (workloadName=DF, environmentCrn) on the control plane, which returns endpointUrl + token; requests then go to that endpoint with Authorization: Bearer <token> (no access-key signing). All ops are x-workload/x-client-only.
- Operations: 71 (0 beta-only, 5 deprecated)

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `abort_asset_update_request` | POST | `/dfx/api/rpc-v1/deployments/abort-asset-update-request` | Aborts asset update request. |  |
| `abort_deployment_request` | POST | `/dfx/api/rpc-v1/deployments/abort-deployment-request` | Aborts a deployment request. |  |
| `abort_flow_request_in_deployment` | POST | `/dfx/api/rpc-v1/deployed-flows/abort-flow-request-in-deployment` | Aborts a flow request in deployment. |  |
| `add_flow_to_deployment` | POST | `/dfx/api/rpc-v1/deployed-flows/add-flow-to-deployment` | Adds a flow to an existing deployment. |  |
| `cancel_change_flow_version` | POST | `/dfx/api/rpc-v1/deployments/cancel-change-flow-version` | Cancel change flow version for an existing deployment. Deprecated, use cancel-change-flow-version-in-deployment. | deprecated |
| `cancel_change_flow_version_in_deployment` | POST | `/dfx/api/rpc-v1/deployed-flows/cancel-change-flow-version-in-deployment` | Cancel change flow version for an existing flow deployment. |  |
| `cancel_nifi_version_update` | POST | `/dfx/api/rpc-v1/deployments/cancel-nifi-version-update` | Cancels a NiFi version update for a deployment. |  |
| `change_flow_version` | POST | `/dfx/api/rpc-v1/deployments/change-flow-version` | Change flow version of a running deployment. Deprecated, use change-flow-version-in-deployment. | deprecated |
| `change_flow_version_in_deployment` | POST | `/dfx/api/rpc-v1/deployed-flows/change-flow-version-in-deployment` | Change flow version of a running deployed flow. |  |
| `create_asset_update_request` | POST | `/dfx/api/rpc-v1/deployments/create-asset-update-request` | Create asset update request. |  |
| `create_custom_nar_configuration` | POST | `/dfx/api/rpc-v1/custom-nar-configurations/create-custom-nar-configuration` | Create the custom NAR configuration. |  |
| `create_custom_python_configuration` | POST | `/dfx/api/rpc-v1/custom-python-configurations/create-custom-python-configuration` | Create the custom Python configuration. |  |
| `create_deployment` | POST | `/dfx/api/rpc-v1/deployments/create-deployment` | Creates a deployment. |  |
| `create_inbound_connection_endpoint` | POST | `/dfx/api/rpc-v1/inbound-connection-endpoints/create-inbound-connection-endpoint` | Create Inbound Connection Endpoint |  |
| `create_parameter_group` | POST | `/dfx/api/rpc-v1/parameter-groups/create-parameter-group` | Creates a new parameter group. |  |
| `create_reporting_task` | POST | `/dfx/api/rpc-v1/deployments/create-reporting-task` | Creates a reporting task. |  |
| `delete_custom_nar_configuration` | POST | `/dfx/api/rpc-v1/custom-nar-configurations/delete-custom-nar-configuration` | Deletes an orphaned custom NAR configuration. |  |
| `delete_custom_python_configuration` | POST | `/dfx/api/rpc-v1/custom-python-configurations/delete-custom-python-configuration` | Deletes an orphaned custom Python configuration. |  |
| `delete_flow_draft` | POST | `/dfx/api/rpc-v1/fd-proxy/delete-flow-draft` | Deletes flow draft. |  |
| `delete_inbound_connection_endpoint` | POST | `/dfx/api/rpc-v1/inbound-connection-endpoints/delete-inbound-connection-endpoint` | Delete Inbound Connection Endpoint |  |
| `delete_parameter_group` | POST | `/dfx/api/rpc-v1/parameter-groups/delete-parameter-group` | Deletes the parameter group. |  |
| `delete_reporting_task` | POST | `/dfx/api/rpc-v1/deployments/delete-reporting-task` | Deletes a reporting task. |  |
| `describe_inbound_connection_endpoint` | POST | `/dfx/api/rpc-v1/inbound-connection-endpoints/describe-inbound-connection-endpoint` | Describe Inbound Connection Endpoint |  |
| `describe_parameter_group` | POST | `/dfx/api/rpc-v1/parameter-groups/describe-parameter-group` | Describes the parameter group with the given parameter group CRN. |  |
| `duplicate_parameter_group` | POST | `/dfx/api/rpc-v1/parameter-groups/duplicate-parameter-group` | Duplicates the parameter group with the given CRN under the given new name. |  |
| `export_deployment` | POST | `/dfx/api/rpc-v1/deployments/export-deployment` | Export deployment configuration. |  |
| `get_client_certificates_encoded` | POST | `/dfx/api/rpc-v1/inbound-connection-endpoint-certificates/download-client-certificates-encoded` | Get Inbound Connection Endpoint Client Certificates (in PEM encoding) |  |
| `get_custom_nar_configuration` | POST | `/dfx/api/rpc-v1/custom-nar-configurations/get-custom-nar-configuration` | Get a custom NAR configuration. |  |
| `get_custom_python_configuration` | POST | `/dfx/api/rpc-v1/custom-python-configurations/get-custom-python-configuration` | Get a custom Python configuration. |  |
| `get_default_custom_nar_configuration` | POST | `/dfx/api/rpc-v1/custom-nar-configurations/get-default-custom-nar-configuration` | Get the default custom NAR configuration. Deprecated, no longer supported. | deprecated |
| `get_deployment_configuration` | POST | `/dfx/api/rpc-v1/deployments/get-deployment-configuration` | Retrieves the deployment configuration. |  |
| `get_deployment_configuration_metadata` | POST | `/dfx/api/rpc-v1/deployments/get-deployment-configuration-metadata` | Retrieves the deployment configuration metadata. |  |
| `get_deployment_request_details` | POST | `/dfx/api/rpc-v1/deployments/get-deployment-request-details` | Retrieves deployment request details and registers the deployment request. |  |
| `get_flow_configuration_in_deployment` | POST | `/dfx/api/rpc-v1/deployed-flows/get-flow-configuration-in-deployment` | Retrieves the deployed flow configuration in a deployment. |  |
| `get_flow_configuration_metadata_in_deployment` | POST | `/dfx/api/rpc-v1/deployed-flows/get-flow-configuration-metadata-in-deployment` | Retrieves the deployed flow configuration metadata in a deployment. |  |
| `get_flow_request_details_in_deployment` | POST | `/dfx/api/rpc-v1/deployed-flows/get-flow-request-details-in-deployment` | Retrieves flow request details and registers the flow deployment request. |  |
| `import_deployment` | POST | `/dfx/api/rpc-v1/deployments/import-deployment` | Import deployment configuration. |  |
| `import_flow_into_deployment` | POST | `/dfx/api/rpc-v1/deployed-flows/import-flow-into-deployment` | Import flow deployment configuration. |  |
| `list_deployment_archives` | POST | `/dfx/api/rpc-v1/deployments/list-deployment-archives` | Lists the exported archive metadata of all deployments. |  |
| `list_flow_drafts` | POST | `/dfx/api/rpc-v1/fd-proxy/list-flow-drafts` | Lists flow drafts. |  |
| `list_inbound_connection_endpoints` | POST | `/dfx/api/rpc-v1/inbound-connection-endpoints/list-inbound-connection-endpoints` | List Inbound Connection Endpoints |  |
| `list_nifi_versions` | POST | `/dfx/api/rpc-v1/environments/list-nifi-versions` | Lists all supported NiFi versions. |  |
| `list_parameter_groups` | POST | `/dfx/api/rpc-v1/parameter-groups/list-parameter-groups` | Lists all known parameter groups. |  |
| `list_reporting_tasks` | POST | `/dfx/api/rpc-v1/deployments/list-reporting-tasks` | Lists all reporting tasks for a deployment. |  |
| `list_test_sessions` | POST | `/dfx/api/rpc-v1/fd-proxy/list-test-sessions` | Lists test sessions. |  |
| `reassign_resources` | POST | `/dfx/api/rpc-v1/workload-resources/reassign-resources` | Modifies the project assignment of the given workload resources. |  |
| `renew_inbound_connection_endpoint_certificates` | POST | `/dfx/api/rpc-v1/inbound-connection-endpoints/renew-certificates` | Renew Inbound Connection Endpoint certificates |  |
| `restart_deployment` | POST | `/dfx/api/rpc-v1/deployments/restart-deployment` | Restart a deployment. |  |
| `restart_test_session` | POST | `/dfx/api/rpc-v1/fd-proxy/restart-test-session` | Restarts test session. |  |
| `resume_deployment` | POST | `/dfx/api/rpc-v1/deployments/resume-deployment` | Resumes a deployment. |  |
| `start_all_flows_in_deployment` | POST | `/dfx/api/rpc-v1/deployments/start-all-flows-in-deployment` | Starts all flows in a deployment. |  |
| `start_flow` | POST | `/dfx/api/rpc-v1/deployments/start-flow` | Starts a flow. Deprecated, use start-flow-in-deployment. | deprecated |
| `start_flow_in_deployment` | POST | `/dfx/api/rpc-v1/deployed-flows/start-flow-in-deployment` | Starts a flow in a deployment. |  |
| `stop_all_flows_in_deployment` | POST | `/dfx/api/rpc-v1/deployments/stop-all-flows-in-deployment` | Stops all flows in a deployment. |  |
| `stop_flow` | POST | `/dfx/api/rpc-v1/deployments/stop-flow` | Stops a flow. Deprecated, use stop-flow-in-deployment. | deprecated |
| `stop_flow_in_deployment` | POST | `/dfx/api/rpc-v1/deployed-flows/stop-flow-in-deployment` | Stops a flow in a deployment. |  |
| `suspend_deployment` | POST | `/dfx/api/rpc-v1/deployments/suspend-deployment` | Suspends a deployment. |  |
| `suspend_test_session` | POST | `/dfx/api/rpc-v1/fd-proxy/suspend-test-session` | Suspends test session. |  |
| `terminate_deployment` | POST | `/dfx/api/rpc-v1/deployments/terminate-deployment` | Terminates a deployment. |  |
| `terminate_flow_in_deployment` | POST | `/dfx/api/rpc-v1/deployed-flows/terminate-flow-in-deployment` | Terminates a flow in a deployment. |  |
| `terminate_test_session` | POST | `/dfx/api/rpc-v1/fd-proxy/terminate-test-session` | Terminates test session. |  |
| `update_custom_nar_configuration` | POST | `/dfx/api/rpc-v1/custom-nar-configurations/update-custom-nar-configuration` | Update the custom NAR configuration. |  |
| `update_custom_python_configuration` | POST | `/dfx/api/rpc-v1/custom-python-configurations/update-custom-python-configuration` | Update the custom Python configuration. |  |
| `update_deployment` | POST | `/dfx/api/rpc-v1/deployments/update-deployment` | Updates a deployment. |  |
| `update_flow_in_deployment` | POST | `/dfx/api/rpc-v1/deployed-flows/update-flow-in-deployment` | Updates a flow deployment. |  |
| `update_nifi_version` | POST | `/dfx/api/rpc-v1/deployments/update-nifi-version` | Updates the NiFi version of a deployment. |  |
| `update_parameter_group` | POST | `/dfx/api/rpc-v1/parameter-groups/update-parameter-group` | Updates the parameter group for the given parameter group CRN. |  |
| `upload_asset` | POST | `/dfx/api/rpc-v1/deployments/upload-asset` | Upload an asset. |  |
| `upload_parameter_asset` | POST | `/dfx/api/rpc-v1/parameter-groups/upload-parameter-asset` | Uploads a parameter asset. |  |
| `validate_custom_nar_configuration` | POST | `/dfx/api/rpc-v1/custom-nar-configurations/validate-custom-nar-configuration` | Validates the custom NAR configuration. |  |
| `validate_custom_python_configuration` | POST | `/dfx/api/rpc-v1/custom-python-configurations/validate-custom-python-configuration` | Validates the custom Python configuration. |  |

## cdp_dw

89 tools.

- Product: Cloudera Data Warehouse (CDW)
- Spec title: Cloudera Data Warehouse [EXPERIMENTAL]
- Description: Install and manage Cloudera Data Warehouse clusters.
- Spec source: GA (https://github.com/cloudera/cdp-dev-docs/blob/5a189fcd6124f3e1b671ebee69cc229a47326865/api-docs/swagger/dw.yaml) v0.9.164, beta (https://github.com/cloudera/cdp-dev-docs/blob/5a189fcd6124f3e1b671ebee69cc229a47326865/api-docs-beta/swagger/dw.yaml) v0.9.164 (BETA)
- Service release: PUBLIC; products: CDP
- Auth: Base URL https://api.<region>.cdp.cloudera.com (e.g. us-west-1, eu-1, ap-1; https://api.usg-1.cdp.clouderagovt.com for US Gov). All calls are POST with Content-Type: application/json and a JSON body, signed per CDP request signing V1 (headers x-altus-date and x-altus-auth = ed25519v1/rsav1 signature using the CDP access key ID + private key).
- Operations: 89 (12 beta-only, 1 deprecated)

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `add_user` | POST | `/api/v1/dw/addUser` | Adds the given user to the cluster. |  |
| `backup_cluster` | POST | `/api/v1/dw/backupCluster` | Creates a backup from the cluster configuration and settings. |  |
| `create_aws_cluster` | POST | `/api/v1/dw/createAwsCluster` | Create an AWS cluster in the Cloudera Data Warehouse. |  |
| `create_azure_cluster` | POST | `/api/v1/dw/createAzureCluster` | Create an Azure cluster in the Cloudera Data Warehouse. |  |
| `create_cluster` | POST | `/api/v1/dw/createCluster` | Create a Cloudera Data Warehouse cluster. |  |
| `create_cluster_diagnostic_data_job` | POST | `/api/v1/dw/createClusterDiagnosticDataJob` | Create a diagnostic job for the given cluster. |  |
| `create_connector` | POST | `/api/v1/dw/createConnector` | Creates a Connector |  |
| `create_connector_test_job` | POST | `/api/v1/dw/createConnectorTestJob` | Test Trino Connector in a CDW cluster. |  |
| `create_data_visualization` | POST | `/api/v1/dw/createDataVisualization` | Creates a Cloudera Data Visualization. |  |
| `create_dbc` | POST | `/api/v1/dw/createDbc` | Create a Database Catalog. | deprecated |
| `create_dbc_diagnostic_data_job` | POST | `/api/v1/dw/createDbcDiagnosticDataJob` | Create a diagnostic job for the given database catalog. |  |
| `create_hue` | POST | `/api/v1/dw/createHue` | Create Hue Query Editor in a CDW cluster. | beta |
| `create_vw` | POST | `/api/v1/dw/createVw` | Create a Virtual Warehouse. |  |
| `create_vw_diagnostic_data_job` | POST | `/api/v1/dw/createVwDiagnosticDataJob` | Create a diagnostic job for the given Virtual Warehouse. |  |
| `delete_cluster` | POST | `/api/v1/dw/deleteCluster` | Delete a Cloudera Data Warehouse cluster. |  |
| `delete_cluster_diagnostic_data_job` | POST | `/api/v1/dw/deleteClusterDiagnosticDataJob` | Deletes a diagnostic job for the given cluster. |  |
| `delete_connector` | POST | `/api/v1/dw/deleteConnector` | Deletes a Database connector. |  |
| `delete_data_visualization` | POST | `/api/v1/dw/deleteDataVisualization` | Asynchronous operation that deletes a Cloudera Data Visualization. When the DV is in deleting state, we can still use describe-data-visualization to check the status. Once it is deleted, the describe-data-visualization would return a not found error. |  |
| `delete_dbc` | POST | `/api/v1/dw/deleteDbc` | Delete a Database Catalog. |  |
| `delete_dbc_diagnostic_data_job` | POST | `/api/v1/dw/deleteDbcDiagnosticDataJob` | Deletes a diagnostic job for the given Database Catalog. |  |
| `delete_hue` | POST | `/api/v1/dw/deleteHue` | Asynchronous operation that deletes a Hue Query Editor. When the Hue is in deleting state, we can still use describe-hue to check the status. Once it is deleted, the describe-hue would return a not found error. | beta |
| `delete_secret` | POST | `/api/v1/dw/deleteSecret` | Deletes a secret. |  |
| `delete_user` | POST | `/api/v1/dw/deleteUser` | Deletes the given user from the cluster. |  |
| `delete_vw` | POST | `/api/v1/dw/deleteVw` | Delete a Virtual Warehouse. |  |
| `delete_vw_diagnostic_data_job` | POST | `/api/v1/dw/deleteVwDiagnosticDataJob` | Delete a diagnostic job for the given Virtual Warehouse. |  |
| `describe_allowed_instance_types` | POST | `/api/v1/dw/describeAllowedInstanceTypes` | Get allowed compute instance types for both AWS and Azure cluster types and their default values. |  |
| `describe_cluster` | POST | `/api/v1/dw/describeCluster` | Describe a Cloudera Data Warehouse cluster. |  |
| `describe_cluster_diagnostic_data_job` | POST | `/api/v1/dw/describeClusterDiagnosticDataJob` | Describes a diagnostic job for the given Cluster. |  |
| `describe_config` | POST | `/api/v1/dw/describeConfig` | Describe a service configuration. |  |
| `describe_config_diff` | POST | `/api/v1/dw/describeConfigDiff` | Get differences between two service configurations. |  |
| `describe_data_visualization` | POST | `/api/v1/dw/describeDataVisualization` | Describes a Cloudera Data Visualization. |  |
| `describe_dbc` | POST | `/api/v1/dw/describeDbc` | Describe a Database Catalog. |  |
| `describe_dbc_config` | POST | `/api/v1/dw/describeDbcConfig` | Describes the Database Catalog current configuration. |  |
| `describe_dbc_diagnostic_data_job` | POST | `/api/v1/dw/describeDbcDiagnosticDataJob` | Describes a diagnostic job for the given Database Catalog. |  |
| `describe_hue` | POST | `/api/v1/dw/describeHue` | Describes a Hue Query Editor. | beta |
| `describe_kubeconfig` | POST | `/api/v1/dw/describeKubeconfig` | Get Kubeconfig for a Cloudera Data Warehouse cluster. |  |
| `describe_vw` | POST | `/api/v1/dw/describeVw` | Describe a Virtual Warehouse. |  |
| `describe_vw_config` | POST | `/api/v1/dw/describeVwConfig` | Describes the current configuration of a Hive or Impala Virtual Warehouse. |  |
| `describe_vw_diagnostic_data_job` | POST | `/api/v1/dw/describeVwDiagnosticDataJob` | Describe a diagnostic jobs for the given Virtual Warehouse. |  |
| `get_data_visualization_upgrade_version` | POST | `/api/v1/dw/getDataVisualizationUpgradeVersion` | Gets latest version and latest compatible version for Cloudera Data Visualization. |  |
| `get_hue_upgrade_version` | POST | `/api/v1/dw/getHueUpgradeVersion` | Gets latest version and latest compatible version for Hue Query Editor. | beta |
| `get_upgrade_dbc_versions` | POST | `/api/v1/dw/getUpgradeDbcVersions` | Gets the latest version and latest compatible version for Database Catalog. |  |
| `get_upgrade_vw_versions` | POST | `/api/v1/dw/getUpgradeVwVersions` | Gets the latest version and latest compatible version for Virtual Warehouse. |  |
| `health_check` | POST | `/api/v1/dw/healthCheck` | Check the health of the API. |  |
| `list_cluster_diagnostic_data_jobs` | POST | `/api/v1/dw/listClusterDiagnosticDataJobs` | Get a list of diagnostic jobs for the given cluster. |  |
| `list_clusters` | POST | `/api/v1/dw/listClusters` | List Cloudera Data Warehouse clusters. |  |
| `list_connector_test_jobs` | POST | `/api/v1/dw/listConnectorTestJobs` | List test connector jobs. |  |
| `list_connectors` | POST | `/api/v1/dw/listConnectors` | Lists Database Connectors. |  |
| `list_data_visualizations` | POST | `/api/v1/dw/listDataVisualizations` | Lists Cloudera Data Visualization in the provided CDW cluster. |  |
| `list_dbc_configs` | POST | `/api/v1/dw/listDbcConfigs` | Get the configuration history of a Database Catalog. |  |
| `list_dbc_diagnostic_data_jobs` | POST | `/api/v1/dw/listDbcDiagnosticDataJobs` | Get a list of diagnostic jobs for the given Database Catalog. |  |
| `list_dbc_events` | POST | `/api/v1/dw/listDbcEvents` | Get the list of events for the given Database Catalog. |  |
| `list_dbcs` | POST | `/api/v1/dw/listDbcs` | List Database Catalogs. |  |
| `list_events` | POST | `/api/v1/dw/listEvents` | Get the list of events. |  |
| `list_hues` | POST | `/api/v1/dw/listHues` | List Hue Query Editors in the provided CDW cluster. | beta |
| `list_latest_versions` | POST | `/api/v1/dw/listLatestVersions` | Lists the latest version of the product (if available) for all catalogs in the environment. |  |
| `list_secrets` | POST | `/api/v1/dw/listSecrets` | Lists all secrets. |  |
| `list_users` | POST | `/api/v1/dw/listUsers` | Lists the users who have access to the cluster. |  |
| `list_vw_configs` | POST | `/api/v1/dw/listVwConfigs` | Get the configuration history of a Virtual Warehouse. |  |
| `list_vw_diagnostic_data_jobs` | POST | `/api/v1/dw/listVwDiagnosticDataJobs` | Get a list of diagnostic jobs for the given Virtual Warehouse. |  |
| `list_vw_events` | POST | `/api/v1/dw/listVwEvents` | Get the list of events for the given Virtual Warehouse. |  |
| `list_vws` | POST | `/api/v1/dw/listVws` | List Virtual Warehouses. |  |
| `rebuild_dbc` | POST | `/api/v1/dw/rebuildDbc` | Rebuild a Database Catalog. |  |
| `rebuild_hue` | POST | `/api/v1/dw/rebuildHue` | Asynchronous operation that rebuilds a Hue Query Editor keeping the same version. | beta |
| `rebuild_vw` | POST | `/api/v1/dw/rebuildVw` | Rebuild a Virtual Warehouse. |  |
| `register_secret` | POST | `/api/v1/dw/registerSecret` | Registers a reference to a secret stored in the vault of the cloud provider. |  |
| `renew_certificates` | POST | `/api/v1/dw/renewCertificates` | Renew certificates for a Cloudera Data Warehouse public cloud cluster. |  |
| `restore_cluster` | POST | `/api/v1/dw/restoreCluster` | Restores the cluster from a backup data made by "backup-cluster" command. |  |
| `resume_cluster` | POST | `/api/v1/dw/resumeCluster` | Resume Cloudera Data Warehouse cluster. | beta |
| `start_dbc` | POST | `/api/v1/dw/startDbc` | Start a Database Catalog. |  |
| `start_vw` | POST | `/api/v1/dw/startVw` | Starts a suspended Virtual Warehouse. |  |
| `suspend_cluster` | POST | `/api/v1/dw/suspendCluster` | Suspend Cloudera Data Warehouse cluster. | beta |
| `suspend_dbc` | POST | `/api/v1/dw/suspendDbc` | Suspends a running Database Catalog. |  |
| `suspend_vw` | POST | `/api/v1/dw/suspendVw` | Suspends a running Virtual Warehouse. |  |
| `update_aws_cluster` | POST | `/api/v1/dw/updateAwsCluster` | Updates an AWS cluster in the Cloudera Data Warehouse. | beta |
| `update_azure_cluster` | POST | `/api/v1/dw/updateAzureCluster` | Updates an Azure cluster in the Cloudera Data Warehouse. | beta |
| `update_cluster` | POST | `/api/v1/dw/updateCluster` | Updates the Cloudera Data Warehouse cluster. |  |
| `update_connector` | POST | `/api/v1/dw/updateConnector` | Updates the Cloudera Data Warehouse connector. |  |
| `update_data_visualization` | POST | `/api/v1/dw/updateDataVisualization` | Asynchronous operation that updates the configuration of a Cloudera Data Visualization. The describe-data-visualization can be used at any time to get the latest status of a Data Visualization. |  |
| `update_dbc` | POST | `/api/v1/dw/updateDbc` | Update the configuration of a Database Catalog. |  |
| `update_dbc_config` | POST | `/api/v1/dw/updateDbcConfig` | Update a Database Catalog configuration. |  |
| `update_hue` | POST | `/api/v1/dw/updateHue` | Asynchronous operation that updates the configuration of a Hue Query Editor. The describe-hue can be used at any time to get the latest status of a Hue Query Editor. | beta |
| `update_ssh_key` | POST | `/api/v1/dw/updateSshKey` | Update the SSH Key for a Cloudera Data Warehouse cluster |  |
| `update_vw` | POST | `/api/v1/dw/updateVw` | Update the configuration of a Virtual Warehouse. |  |
| `update_vw_config` | POST | `/api/v1/dw/updateVwConfig` | Update a Virtual Warehouse configuration. |  |
| `upgrade_data_visualization` | POST | `/api/v1/dw/upgradeDataVisualization` | Asynchronous operation that upgrades a Cloudera Data Visualization to a compatible version. The describe-data-visualization can be used at any time to get the latest status of a Data Visualization. |  |
| `upgrade_dbc` | POST | `/api/v1/dw/upgradeDbc` | Upgrades the Database Catalog to a compatible version. |  |
| `upgrade_hue` | POST | `/api/v1/dw/upgradeHue` | Asynchronous operation that upgrades a Hue Query Editor to a compatible version. The describe-hue can be used at any time to get the latest status of a Hue Query Editor. | beta |
| `upgrade_vw` | POST | `/api/v1/dw/upgradeVw` | Upgrades the Virtual Warehouse to a compatible version. |  |

## cdp_environments

106 tools.

- Product: CDP Environments, credentials, FreeIPA, proxy configs
- Spec title: Cloudera Environments Service
- Description: Cloudera Environments Service is a web service that manages cloud provider access.
- Spec source: GA (https://github.com/cloudera/cdp-dev-docs/blob/5a189fcd6124f3e1b671ebee69cc229a47326865/api-docs/swagger/environments.yaml) v0.9.164, beta (https://github.com/cloudera/cdp-dev-docs/blob/5a189fcd6124f3e1b671ebee69cc229a47326865/api-docs-beta/swagger/environments.yaml) v0.9.164 (BETA)
- Service release: PUBLIC; products: CDP
- Auth: Base URL https://api.<region>.cdp.cloudera.com (e.g. us-west-1, eu-1, ap-1; https://api.usg-1.cdp.clouderagovt.com for US Gov). All calls are POST with Content-Type: application/json and a JSON body, signed per CDP request signing V1 (headers x-altus-date and x-altus-auth = ed25519v1/rsav1 signature using the CDP access key ID + private key).
- Operations: 106 (7 beta-only, 4 deprecated)

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `add_trust` | POST | `/api/v1/environments2/addTrust` | Add cross-realm trust between an on-premise Active Directory and an environment. | beta |
| `attach_free_ipa_recipes` | POST | `/api/v1/environments2/attachFreeIpaRecipes` | Attach recipes to FreeIPA. |  |
| `cancel_freeipa_diagnostics` | POST | `/api/v1/environments2/cancelFreeipaDiagnostics` | Cancel running FreeIPA diagnostics collections |  |
| `cancel_trust` | POST | `/api/v1/environments2/cancelTrust` | Cancel cross-realm trust for FreeIPA. |  |
| `change_environment_credential` | POST | `/api/v1/environments2/changeEnvironmentCredential` | Changes the credential for an environment. |  |
| `collect_freeipa_diagnostics` | POST | `/api/v1/environments2/collectFreeipaDiagnostics` | Start FreeIPA diagnostics collection |  |
| `create_aws_credential` | POST | `/api/v1/environments2/createAWSCredential` | Creates a new AWS credential that can be attatched to an environment. The credential is used for authorization to provision resources such as compute instances within your cloud provider account. |  |
| `create_aws_environment` | POST | `/api/v1/environments2/createAWSEnvironment` | Creates a new AWS environment by providing the cloud provider access and network information. A FreeIPA server will be automatically provisioned when an environment is created. |  |
| `create_aws_gov_cloud_credential` | POST | `/api/v1/environments2/createAWSGovCloudCredential` | Creates a new AWS credential for GovCloud that can be attatched to an environment. The credential is used for authorization to provision resources such as compute instances within your cloud provider account. |  |
| `create_aws_gov_cloud_environment` | POST | `/api/v1/environments2/createAWSGovCloudEnvironment` | Creates a new AWS GovCloud environment by providing the cloud provider access and network information. A FreeIPA server will be automatically provisioned when an environment is created. |  |
| `create_azure_credential` | POST | `/api/v1/environments2/createAzureCredential` | Creates a new Azure credential that can be attached to an environment. The credential is used for authorization to provision resources such as compute instances within your cloud provider account. |  |
| `create_azure_environment` | POST | `/api/v1/environments2/createAzureEnvironment` | Creates a new Azure environment by providing the cloud provider access and network information. A FreeIPA server will be automatically provisioned when an environment is created. |  |
| `create_gcp_credential` | POST | `/api/v1/environments2/createGCPCredential` | Creates a new GCP credential that can be attatched to an environment. The credential is used for authorization to provision resources such as compute instances within your cloud provider account. |  |
| `create_gcp_environment` | POST | `/api/v1/environments2/createGCPEnvironment` | Creates a new GCP environment by providing the cloud provider access and network information. A FreeIPA server will be automatically provisioned when an environment is created. |  |
| `create_proxy_config` | POST | `/api/v1/environments2/createProxyConfig` | Creates a new proxy config that can be attatched to an environment. |  |
| `delete_audit_credential` | POST | `/api/v1/environments2/deleteAuditCredential` | Deletes an audit credential. |  |
| `delete_credential` | POST | `/api/v1/environments2/deleteCredential` | Deletes a credential. |  |
| `delete_environment` | POST | `/api/v1/environments2/deleteEnvironment` | Deletes an environment. |  |
| `delete_proxy_config` | POST | `/api/v1/environments2/deleteProxyConfig` | Deletes a proxy config. |  |
| `describe_environment` | POST | `/api/v1/environments2/describeEnvironment` | Describes an environment. |  |
| `detach_free_ipa_recipes` | POST | `/api/v1/environments2/detachFreeIpaRecipes` | Detach recipes from FreeIPA. |  |
| `disable_s3_guard` | POST | `/api/v1/environments2/disableS3Guard` | Disable the S3Guard for an environment. | deprecated, beta |
| `downscale_freeipa` | POST | `/api/v1/environments2/downscaleFreeipa` | Downscales FreeIPA instances. |  |
| `finish_setup_trust` | POST | `/api/v1/environments2/finishSetupTrust` | Complete cross-realm trust setup for FreeIPA. |  |
| `get_account_telemetry` | POST | `/api/v1/environments2/getAccountTelemetry` | Get account level telemetry settings. (telemetry features and anonymization rules) |  |
| `get_account_telemetry_default` | POST | `/api/v1/environments2/getAccountTelemetryDefault` | Get default account level telemetry settings. Helps to set back the default values. |  |
| `get_audit_credential_prerequisites` | POST | `/api/v1/environments2/getAuditCredentialPrerequisites` | This API provides the audit credential prerequisites for the given cloud provider. |  |
| `get_automated_sync_environment_status` | POST | `/api/v1/environments2/getAutomatedSyncEnvironmentStatus` | Gets the the automated sync status for the environment. |  |
| `get_azure_image_terms_policy` | POST | `/api/v1/environments2/getAzureImageTermsPolicy` | Gets account level Azure Marketplace image policy. CDP is capable to automatically accept Azure Marketplace image terms during cluster deployment. You can use this setting in your account to opt in or opt out this behaviour. |  |
| `get_credential_prerequisites` | POST | `/api/v1/environments2/getCredentialPrerequisites` | This API provides the credential prerequisites for the given cloud provider. |  |
| `get_environment_user_sync_state` | POST | `/api/v1/environments2/getEnvironmentUserSyncState` | Returns the user synchronization state for an environment. |  |
| `get_freeipa_log_descriptors` | POST | `/api/v1/environments2/getFreeipaLogDescriptors` | Gather log descriptors that are used for diagnostics collection. |  |
| `get_freeipa_status` | POST | `/api/v1/environments2/getFreeipaStatus` | Get the status of the FreeIPA services |  |
| `get_freeipa_upgrade_options` | POST | `/api/v1/environments2/getFreeipaUpgradeOptions` | Get available images for FreeIPA upgrade. |  |
| `get_gov_cloud_audit_credential_prerequisites` | POST | `/api/v1/environments2/getGovCloudAuditCredentialPrerequisites` | This API provides the audit credential prerequisites for GovCloud for the enabled providers. |  |
| `get_gov_cloud_credential_prerequisites` | POST | `/api/v1/environments2/getGovCloudCredentialPrerequisites` | This API provides the credential prerequisites for GovCloud for the enabled providers. |  |
| `get_id_broker_mappings` | POST | `/api/v1/environments2/getIdBrokerMappings` | Gets all ID Broker mappings for an environment. |  |
| `get_id_broker_mappings_sync_status` | POST | `/api/v1/environments2/getIdBrokerMappingsSyncStatus` | Gets ID Broker mappings sync status. |  |
| `get_keytab` | POST | `/api/v1/environments2/getKeytab` | Retrieves a keytab for a user or machine user. |  |
| `get_operation` | POST | `/api/v1/environments2/getOperation` | Get the latest (in progress or finished) operation for the environment resource. |  |
| `get_repair_freeipa_status` | POST | `/api/v1/environments2/getRepairFreeipaStatus` | Returns status of the repair operation for the operation id. |  |
| `get_root_certificate` | POST | `/api/v1/environments2/getRootCertificate` | This API provides contents of public certificate for an environment. |  |
| `get_trust_cleanup_commands` | POST | `/api/v1/environments2/getTrustCleanupCommands` | Gets the commands to be run for cross-realm trust clean up. |  |
| `get_trust_setup_commands` | POST | `/api/v1/environments2/getTrustSetupCommands` | Lists the commands to be executed for cross-realm trust setup. |  |
| `initialize_aws_compute_cluster` | POST | `/api/v1/environments2/initializeAWSComputeCluster` | Initialize compute cluster for AWS environment. |  |
| `initialize_azure_compute_cluster` | POST | `/api/v1/environments2/initializeAzureComputeCluster` | Initialize compute cluster for Azure environment. |  |
| `last_sync_status` | POST | `/api/v1/environments2/lastSyncStatus` | Returns status of the sync operation for the environment crn. |  |
| `list_audit_credentials` | POST | `/api/v1/environments2/listAuditCredentials` | Lists audit credentials. |  |
| `list_connected_data_services` | POST | `/api/v1/environments2/listConnectedDataServices` | Returns the list of Data Services and their cluster names that are attached the given environment. |  |
| `list_credentials` | POST | `/api/v1/environments2/listCredentials` | Lists credentials. |  |
| `list_environments` | POST | `/api/v1/environments2/listEnvironments` | Lists environments. |  |
| `list_freeipa_diagnostics` | POST | `/api/v1/environments2/listFreeipaDiagnostics` | List recent FreeIPA diagnostics collections |  |
| `list_freeipa_secret_types` | POST | `/api/v1/environments2/listFreeipaSecretTypes` | Lists all FreeIPA related secret types. |  |
| `list_proxy_configs` | POST | `/api/v1/environments2/listProxyConfigs` | Lists proxy configs. |  |
| `prepare_freeipa_upgrade` | POST | `/api/v1/environments2/prepareFreeipaUpgrade` | Prepares and validates an environment for FreeIPA upgrade. |  |
| `rebuild_freeipa` | POST | `/api/v1/environments2/rebuildFreeipa` | Recreate FreeIPA in case of disaster. | beta |
| `repair_freeipa` | POST | `/api/v1/environments2/repairFreeipa` | Repairs the FreeIPA nodes. |  |
| `repair_trust` | POST | `/api/v1/environments2/repairTrust` | Repair cross-realm trust of FreeIPA with an Active Directory Server. |  |
| `retry_freeipa` | POST | `/api/v1/environments2/retryFreeipa` | Retries the last failed operation on a FreeIPA. |  |
| `rotate_freeipa_secrets` | POST | `/api/v1/environments2/rotateFreeipaSecrets` | Rotate FreeIPA related secret for FreeIPA instances. |  |
| `rotate_salt_password` | POST | `/api/v1/environments2/rotateSaltPassword` | Rotate SaltStack user password on FreeIPA instances. | deprecated |
| `set_aws_audit_credential` | POST | `/api/v1/environments2/setAWSAuditCredential` | Creates or updates the AWS audit credential for the account. The credential is used for authorization to archive audit events to your cloud storage. |  |
| `set_aws_gov_cloud_audit_credential` | POST | `/api/v1/environments2/setAWSGovCloudAuditCredential` | Creates or updates the AWS GovCloud audit credential for the account. The credential is used for authorization to archive audit events to your cloud storage. |  |
| `set_account_telemetry` | POST | `/api/v1/environments2/setAccountTelemetry` | Set account level telemetry settings. (telemetry features and anonymization rules) |  |
| `set_azure_audit_credential` | POST | `/api/v1/environments2/setAzureAuditCredential` | Creates or updates the Azure audit credential for the account. The credential is used for authorization to archive audit events to your cloud storage. |  |
| `set_catalog` | POST | `/api/v1/environments2/setCatalog` | Sets a catalog for a FreeIPA installation. |  |
| `set_endpoint_access_gateway` | POST | `/api/v1/environments2/setEndpointAccessGateway` | Sets endpoint access gateway settings for the environment. |  |
| `set_gcp_audit_credential` | POST | `/api/v1/environments2/setGCPAuditCredential` | Creates or updates the GCP audit credential for the account. The credential is used for authorization to archive audit events to your cloud storage. |  |
| `set_id_broker_mappings` | POST | `/api/v1/environments2/setIdBrokerMappings` | Sets all ID Broker mappings for an environment. |  |
| `set_password` | POST | `/api/v1/environments2/setPassword` | Sets workload user's password and updates into all environments. | deprecated |
| `set_telemetry_features` | POST | `/api/v1/environments2/setTelemetryFeatures` | Configure environment level telemetry feature setting. |  |
| `setup_active_directory_trust` | POST | `/api/v1/environments2/setupActiveDirectoryTrust` | Setup cross-realm trust between FreeIPA and Active Directory. |  |
| `setup_mit_trust` | POST | `/api/v1/environments2/setupMitTrust` | Setup cross-realm trust between FreeIPA and MIT Kerberos. | beta |
| `start_environment` | POST | `/api/v1/environments2/startEnvironment` | Start an environment. |  |
| `start_free_ipa_vertical_scaling` | POST | `/api/v1/environments2/startFreeIpaVerticalScaling` | Initiates the vertical scaling on FreeIPA. |  |
| `stop_environment` | POST | `/api/v1/environments2/stopEnvironment` | Stop an environment. |  |
| `sync_all_users` | POST | `/api/v1/environments2/syncAllUsers` | Synchronizes environments with all users and groups state with CDP. |  |
| `sync_id_broker_mappings` | POST | `/api/v1/environments2/syncIdBrokerMappings` | Syncs all ID Broker mappings for an environment. |  |
| `sync_status` | POST | `/api/v1/environments2/syncStatus` | Returns status of the sync operation for the operation id. |  |
| `sync_user` | POST | `/api/v1/environments2/syncUser` | Synchronizes environments with single user to the FreeIPA servers. |  |
| `synchronize_all_environments` | POST | `/api/v1/environments2/synchronizeAllEnvironments` | Synchronizes all environments in the calling account. | deprecated, beta |
| `test_account_telemetry_rules` | POST | `/api/v1/environments2/testAccountTelemetryRules` | Test anonymization rules (for account telemetry) against text input. |  |
| `update_aws_credential` | POST | `/api/v1/environments2/updateAwsCredential` | Updates an AWS credential that can be attached to an environment. The credential is used for authorization to provision resources such as compute instances within your cloud provider account. |  |
| `update_aws_disk_encryption_parameters` | POST | `/api/v1/environments2/updateAwsDiskEncryptionParameters` | Update the AWS encryption key ARN for the environment. |  |
| `update_azure_availability_zones` | POST | `/api/v1/environments2/updateAzureAvailabilityZones` | Update the Availability Zones for the Azure environment. |  |
| `update_azure_credential` | POST | `/api/v1/environments2/updateAzureCredential` | Updates a new certificate based Azure credential that can be attached to an environment. The credential is used for authorization to provision resources such as compute instances within your cloud provider account. |  |
| `update_azure_database_resources` | POST | `/api/v1/environments2/updateAzureDatabaseResources` | Update the Azure database resources for the environment. |  |
| `update_azure_encryption_resources` | POST | `/api/v1/environments2/updateAzureEncryptionResources` | Update the Azure encryption resources for the environment. |  |
| `update_azure_image_terms_policy` | POST | `/api/v1/environments2/updateAzureImageTermsPolicy` | Updates account level Azure Marketplace image policy. CDP is capable to automatically accept Azure Marketplace image terms during cluster deployment. You can use this setting in your account to opt in or opt out this behaviour. |  |
| `update_custom_docker_registry` | POST | `/api/v1/environments2/updateCustomDockerRegistry` | Updates custom docker registry CRN of an environment. |  |
| `update_data_service_resources` | POST | `/api/v1/environments2/updateDataServiceResources` | Updates Data Service resources of an environment. |  |
| `update_freeipa_to_aws_imds_v1` | POST | `/api/v1/environments2/updateFreeipaToAwsImdsV1` | Updates FreeIPA AWS cluster to use IMDSv1. |  |
| `update_freeipa_to_aws_imds_v2` | POST | `/api/v1/environments2/updateFreeipaToAwsImdsV2` | Updates FreeIPA AWS cluster to use IMDSv2. |  |
| `update_gcp_availability_zones` | POST | `/api/v1/environments2/updateGcpAvailabilityZones` | Update the Availability Zones for the GCP environment. | beta |
| `update_orchestrator_state` | POST | `/api/v1/environments2/updateOrchestratorState` | Run orchestrator engine state update on the FreeIPA cluster. |  |
| `update_proxy_config` | POST | `/api/v1/environments2/updateProxyConfig` | Updates the proxy config of the given environment. The newly added proxy configs will only be used for the Cloudera Data Hub clusters created within the environment after the new proxy configs were added. All the existing environment resources such as the Data Lake, FreeIPA, and any existing Cloudera Data Hub clusters will remain with the proxy configs originally defined during environment creation. |  |
| `update_root_volume_freeipa` | POST | `/api/v1/environments2/updateRootVolumeFreeipa` | Update root volume size and type in FreeIPA instances. | beta |
| `update_security_access` | POST | `/api/v1/environments2/updateSecurityAccess` | Updates the security access settings of the given environment. The newly added security groups will only be used for the Cloudera Data Hub clusters created within the environment after the new security groups were added. All the existing environment resources such as the Data Lake, FreeIPA, and any existing Cloudera Data Hub clusters will remain within the security groups originally defined during environment creation. |  |
| `update_ssh_key` | POST | `/api/v1/environments2/updateSshKey` | Updates the designated SSH key for the given environment. The newly added SSH key will only be used for the Cloudera Data Hub clusters created within the environment after the new SSH key were added. All the existing environment resources such as the Data Lake, FreeIPA, and any existing Cloudera Data Hub clusters will remain within the SSH key originally defined during environment creation. |  |
| `update_subnet` | POST | `/api/v1/environments2/updateSubnet` | Updates the subnet(s) of the given environment. The newly added subnets will only be used for the Cloudera Data Hub clusters created within the environment after the new subnets were added. All the existing environment resources such as the Data Lake, FreeIPA, and any existing Cloudera Data Hub clusters will remain within the subnets originally defined during environment creation. |  |
| `update_tags` | POST | `/api/v1/environments2/updateTags` | Updates the user defined tags of the given environment. The newly added tags will only be used for the Cloudera Data Hub clusters created within the environment after the new tags were added. All the existing environment resources such as the Data Lake, FreeIPA, and any existing Cloudera Data Hub clusters will remain with the tags originally defined during environment creation. |  |
| `upgrade_ccm` | POST | `/api/v1/environments2/upgradeCcm` | Upgrades Cluster Connectivity Manager on the environment to the latest available version. |  |
| `upgrade_freeipa` | POST | `/api/v1/environments2/upgradeFreeipa` | Upgrades FreeIPA to the latest or defined image. |  |
| `upscale_freeipa` | POST | `/api/v1/environments2/upscaleFreeipa` | Upscales FreeIPA instances. |  |
| `validate_aws_cloud_storage` | POST | `/api/v1/environments2/validateAwsCloudStorage` | Validates AWS cloud storage settings of the given environment. |  |
| `validate_azure_cloud_storage` | POST | `/api/v1/environments2/validateAzureCloudStorage` | Validates Azure cloud storage settings of the given environment. |  |

## cdp_iam

80 tools.

- Product: CDP Identity and Access Management
- Spec title: Cloudera IAM Service
- Description: Cloudera CDP IAM is a web service that you can use to manage users and user permissions under your CDP account.
- Spec source: GA (https://github.com/cloudera/cdp-dev-docs/blob/5a189fcd6124f3e1b671ebee69cc229a47326865/api-docs/swagger/iam.yaml) v0.9.164, beta (https://github.com/cloudera/cdp-dev-docs/blob/5a189fcd6124f3e1b671ebee69cc229a47326865/api-docs-beta/swagger/iam.yaml) v0.9.164 (BETA)
- Service release: PUBLIC; products: ALTUS,CDP
- Auth: Base URL https://api.<region>.cdp.cloudera.com (e.g. us-west-1, eu-1, ap-1; https://api.usg-1.cdp.clouderagovt.com for US Gov). All calls are POST with Content-Type: application/json and a JSON body, signed per CDP request signing V1 (headers x-altus-date and x-altus-auth = ed25519v1/rsav1 signature using the CDP access key ID + private key). IAM is an ALTUS,CDP service: its paths have no /api/v1 prefix (/iam/<op>). In us-west-1 the CLI defaults to https://iamapi.us-west-1.altus.cloudera.com; other regions use https://api.<region>.cdp.cloudera.com/iam/<op>.
- Operations: 80 (6 beta-only, 0 deprecated)

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `add_machine_user_to_group` | POST | `/iam/addMachineUserToGroup` | Add a machine user to group. |  |
| `add_ssh_public_key` | POST | `/iam/addSshPublicKey` | Adds an SSH public key for an actor. |  |
| `add_user_to_group` | POST | `/iam/addUserToGroup` | Add a user to a group. |  |
| `assign_azure_cloud_identity` | POST | `/iam/assignAzureCloudIdentity` | Assign an Azure cloud identity to an actor or group. | beta |
| `assign_group_resource_role` | POST | `/iam/assignGroupResourceRole` | Assign a resource role to a group. |  |
| `assign_group_role` | POST | `/iam/assignGroupRole` | Assign a role to a group. |  |
| `assign_machine_user_resource_role` | POST | `/iam/assignMachineUserResourceRole` | Assign a resource role to a machine user. |  |
| `assign_machine_user_role` | POST | `/iam/assignMachineUserRole` | Assign a role to a machine user. |  |
| `assign_service_principal_azure_cloud_identity` | POST | `/iam/assignServicePrincipalAzureCloudIdentity` | Assign an Azure cloud identity to a service principal. | beta |
| `assign_user_resource_role` | POST | `/iam/assignUserResourceRole` | Assign a resource role to a user. |  |
| `assign_user_role` | POST | `/iam/assignUserRole` | Assign a role to a user. |  |
| `create_group` | POST | `/iam/createGroup` | Create a group. |  |
| `create_machine_user` | POST | `/iam/createMachineUser` | Create a machine user. |  |
| `create_machine_user_access_key` | POST | `/iam/createMachineUserAccessKey` | Creates a new access key for a machine user. |  |
| `create_saml_provider` | POST | `/iam/createSamlProvider` | Creates a SAML provider in CDP. |  |
| `create_scim_access_token` | POST | `/iam/createScimAccessToken` | Creates a SCIM access token for a SCIM enabled identity provider. |  |
| `create_user` | POST | `/iam/createUser` | Creates a user in CDP. |  |
| `create_user_access_key` | POST | `/iam/createUserAccessKey` | Creates a new access key for a user. |  |
| `delete_access_key` | POST | `/iam/deleteAccessKey` | Deletes an access key. |  |
| `delete_group` | POST | `/iam/deleteGroup` | Delete a group. |  |
| `delete_machine_user` | POST | `/iam/deleteMachineUser` | Delete a machine user. |  |
| `delete_saml_provider` | POST | `/iam/deleteSamlProvider` | Deletes a SAML provider in CDP account. |  |
| `delete_scim_access_token` | POST | `/iam/deleteScimAccessToken` | Deletes a SCIM access token. |  |
| `delete_ssh_public_key` | POST | `/iam/deleteSshPublicKey` | Deletes an SSH public key for an actor. |  |
| `delete_user` | POST | `/iam/deleteUser` | Deletes a user and all associated resources. |  |
| `describe_saml_provider` | POST | `/iam/describeSamlProvider` | Describes one SAML provider. |  |
| `describe_ssh_public_key` | POST | `/iam/describeSshPublicKey` | Describes an SSH public key for an actor. |  |
| `disable_cloudera_sso_login` | POST | `/iam/disableClouderaSSOLogin` | Disables interactive login using Cloudera SSO for this account. |  |
| `disable_user_workload_password_changed_notifications` | POST | `/iam/disableUserWorkloadPasswordChangedNotifications` | Disables sending user workload password changed email notifications for the account. |  |
| `enable_cloudera_sso_login` | POST | `/iam/enableClouderaSSOLogin` | Enables interactive login using Cloudera SSO for this account. |  |
| `enable_user_workload_password_changed_notifications` | POST | `/iam/enableUserWorkloadPasswordChangedNotifications` | Enables sending user workload password changed email notifications for the account. |  |
| `generate_workload_auth_token` | POST | `/iam/generateWorkloadAuthToken` | Generates an authentication token for workload APIs. |  |
| `get_access_key` | POST | `/iam/getAccessKey` | Gets information on an access key. |  |
| `get_account` | POST | `/iam/getAccount` | Retrieves information about the CDP account. |  |
| `get_account_messages` | POST | `/iam/getAccountMessages` | Get account messages. |  |
| `get_default_identity_provider` | POST | `/iam/getDefaultIdentityProvider` | Retrieves the CRN of the default identity provider. |  |
| `get_user` | POST | `/iam/getUser` | Gets information on a user. |  |
| `list_access_keys` | POST | `/iam/listAccessKeys` | Lists access keys. |  |
| `list_group_assigned_resource_roles` | POST | `/iam/listGroupAssignedResourceRoles` | Lists a group's assigned resource roles. |  |
| `list_group_assigned_roles` | POST | `/iam/listGroupAssignedRoles` | Lists the group's assigned roles. |  |
| `list_group_members` | POST | `/iam/listGroupMembers` | List the members of a group. |  |
| `list_groups` | POST | `/iam/listGroups` | Lists groups. |  |
| `list_groups_for_machine_user` | POST | `/iam/listGroupsForMachineUser` | List the groups that the machine user belongs to. |  |
| `list_groups_for_user` | POST | `/iam/listGroupsForUser` | List the groups that the user belongs to. |  |
| `list_machine_user_assigned_resource_roles` | POST | `/iam/listMachineUserAssignedResourceRoles` | Lists a machine user's assigned resource roles. |  |
| `list_machine_user_assigned_roles` | POST | `/iam/listMachineUserAssignedRoles` | Lists the machine user's assigned roles. |  |
| `list_machine_users` | POST | `/iam/listMachineUsers` | Lists machine users. |  |
| `list_resource_assignees` | POST | `/iam/listResourceAssignees` | List the resource assignees and their respective resource roles for the resource. |  |
| `list_resource_roles` | POST | `/iam/listResourceRoles` | Lists all the available resource roles. |  |
| `list_roles` | POST | `/iam/listRoles` | Lists all the available roles. |  |
| `list_saml_providers` | POST | `/iam/listSamlProviders` | Lists SAML providers in CDP account. |  |
| `list_scim_access_tokens` | POST | `/iam/listScimAccessTokens` | Lists SCIM access tokens for a SCIM enabled identity provider. |  |
| `list_service_principal_cloud_identities` | POST | `/iam/listServicePrincipalCloudIdentities` | List cloud identity mappings for service principals. | beta |
| `list_ssh_public_keys` | POST | `/iam/listSshPublicKeys` | Lists SSH public keys for an actor. |  |
| `list_user_assigned_resource_roles` | POST | `/iam/listUserAssignedResourceRoles` | Lists a user's assigned resource roles. |  |
| `list_user_assigned_roles` | POST | `/iam/listUserAssignedRoles` | Lists the user's assigned roles. |  |
| `list_users` | POST | `/iam/listUsers` | Lists users. |  |
| `remove_machine_user_from_group` | POST | `/iam/removeMachineUserFromGroup` | Remove a machine user from a group. |  |
| `remove_user_from_group` | POST | `/iam/removeUserFromGroup` | Remove a user from a group. |  |
| `set_account_messages` | POST | `/iam/setAccountMessages` | Set messages for an account. |  |
| `set_authentication_policy` | POST | `/iam/setAuthenticationPolicy` | Set the authentication policy for the account. | beta |
| `set_default_identity_provider` | POST | `/iam/setDefaultIdentityProvider` | Sets the default identity provider. |  |
| `set_workload_password` | POST | `/iam/setWorkloadPassword` | Set the workload password for an actor. |  |
| `set_workload_password_policy` | POST | `/iam/setWorkloadPasswordPolicy` | Set the workload password policy for the account. |  |
| `unassign_azure_cloud_identity` | POST | `/iam/unassignAzureCloudIdentity` | Unassign an Azure cloud identity from an actor or group. | beta |
| `unassign_group_resource_role` | POST | `/iam/unassignGroupResourceRole` | Unassign a resource role from a group. |  |
| `unassign_group_role` | POST | `/iam/unassignGroupRole` | Unassign a role from a group. |  |
| `unassign_machine_user_resource_role` | POST | `/iam/unassignMachineUserResourceRole` | Unassign a resource role from a machine user. |  |
| `unassign_machine_user_role` | POST | `/iam/unassignMachineUserRole` | Unassign a role from a machine user. |  |
| `unassign_service_principal_azure_cloud_identity` | POST | `/iam/unassignServicePrincipalAzureCloudIdentity` | Unassign an Azure cloud identity from a service principal. | beta |
| `unassign_user_resource_role` | POST | `/iam/unassignUserResourceRole` | Unassign a resource role from a user. |  |
| `unassign_user_role` | POST | `/iam/unassignUserRole` | Unassign a role from a user. |  |
| `unlock_machine_user_in_control_plane` | POST | `/iam/unlockMachineUserInControlPlane` | Unlocks machine user in the CDP control plane. |  |
| `unlock_user_in_control_plane` | POST | `/iam/unlockUserInControlPlane` | Unlocks user in the CDP control plane. |  |
| `unset_workload_password_min_lifetime` | POST | `/iam/unsetWorkloadPasswordMinLifetime` | Removes workload password minimum lifetime date for an actor. |  |
| `unset_workload_password_policy` | POST | `/iam/unsetWorkloadPasswordPolicy` | Unset workload password policy for the account. |  |
| `update_access_key` | POST | `/iam/updateAccessKey` | Updates an access key. |  |
| `update_group` | POST | `/iam/updateGroup` | Update a group. |  |
| `update_saml_provider` | POST | `/iam/updateSamlProvider` | Updates a SAML provider in CDP. |  |
| `update_user` | POST | `/iam/updateUser` | Updates a user. |  |

## cdp_imagecatalog

16 tools.

- Product: CDP Image Catalog
- Spec title: Image catalog service
- Description: Service for managing custom image catalogs and their associated Cloudera Runtime and FreeIPA images.
- Spec source: GA (https://github.com/cloudera/cdp-dev-docs/blob/5a189fcd6124f3e1b671ebee69cc229a47326865/api-docs/swagger/imagecatalog.yaml) v0.9.164, beta (https://github.com/cloudera/cdp-dev-docs/blob/5a189fcd6124f3e1b671ebee69cc229a47326865/api-docs-beta/swagger/imagecatalog.yaml) v0.9.164 (BETA)
- Service release: PUBLIC; products: CDP
- Auth: Base URL https://api.<region>.cdp.cloudera.com (e.g. us-west-1, eu-1, ap-1; https://api.usg-1.cdp.clouderagovt.com for US Gov). All calls are POST with Content-Type: application/json and a JSON body, signed per CDP request signing V1 (headers x-altus-date and x-altus-auth = ed25519v1/rsav1 signature using the CDP access key ID + private key).
- Operations: 16 (5 beta-only, 0 deprecated)

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `create_custom_catalog` | POST | `/api/v1/imagecatalog/createCustomCatalog` | Create custom image catalog |  |
| `create_kubernetes_catalog` | POST | `/api/v1/imagecatalog/createKubernetesCatalog` | Creates a Kubernetes catalog | beta |
| `delete_custom_catalog` | POST | `/api/v1/imagecatalog/deleteCustomCatalog` | Delete custom image catalog |  |
| `delete_freeipa_image` | POST | `/api/v1/imagecatalog/deleteFreeipaImage` | Delete FreeIPA image |  |
| `delete_runtime_image` | POST | `/api/v1/imagecatalog/deleteRuntimeImage` | Delete Cloudera Runtime image |  |
| `describe_custom_catalog` | POST | `/api/v1/imagecatalog/describeCustomCatalog` | Describe custom image catalog |  |
| `describe_custom_image` | POST | `/api/v1/imagecatalog/describeCustomImage` | Describe custom image |  |
| `describe_default_image` | POST | `/api/v1/imagecatalog/describeDefaultImage` | Describe default image |  |
| `describe_kubernetes_catalog` | POST | `/api/v1/imagecatalog/describeKubernetesCatalog` | Describes a Kubernetes catalog | beta |
| `find_default_image` | POST | `/api/v1/imagecatalog/findDefaultImage` | Find default image |  |
| `list_custom_catalogs` | POST | `/api/v1/imagecatalog/listCustomCatalogs` | List custom image catalogs |  |
| `list_images` | POST | `/api/v1/imagecatalog/listImages` | List images from a catalog | beta |
| `list_kubernetes_catalogs` | POST | `/api/v1/imagecatalog/listKubernetesCatalogs` | List Kubernetes catalogs | beta |
| `set_freeipa_image` | POST | `/api/v1/imagecatalog/setFreeipaImage` | Add or update FreeIPA image |  |
| `set_runtime_image` | POST | `/api/v1/imagecatalog/setRuntimeImage` | Add or update Cloudera Runtime image |  |
| `update_kubernetes_catalog` | POST | `/api/v1/imagecatalog/updateKubernetesCatalog` | Updates a Kubernetes catalog | beta |

## cdp_lakehouseopt

30 tools.

- Product: Cloudera Lakehouse Optimizer
- Spec title: Cloudera Lakehouse Optimizer Service
- Description: CDP Cloudera Lakehouse Optimizer Service does the iceberg table maintenance, it allows users to define policies to schedule iceberg spark actions to perform regular maintenance.
- Spec source: GA (https://github.com/cloudera/cdp-dev-docs/blob/5a189fcd6124f3e1b671ebee69cc229a47326865/api-docs/swagger/lakehouseopt.yaml) v0.9.164, beta (https://github.com/cloudera/cdp-dev-docs/blob/5a189fcd6124f3e1b671ebee69cc229a47326865/api-docs-beta/swagger/lakehouseopt.yaml) v0.9.164 (BETA)
- Service release: PUBLIC; products: CDP
- Auth: Base URL https://api.<region>.cdp.cloudera.com (e.g. us-west-1, eu-1, ap-1; https://api.usg-1.cdp.clouderagovt.com for US Gov). All calls are POST with Content-Type: application/json and a JSON body, signed per CDP request signing V1 (headers x-altus-date and x-altus-auth = ed25519v1/rsav1 signature using the CDP access key ID + private key).
- Operations: 30 (0 beta-only, 0 deprecated)

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `change_table_policy` | POST | `/api/v1/lakehouseopt/changeTablePolicy` | Perform policy change operations on a table. |  |
| `create_associations` | POST | `/api/v1/lakehouseopt/createAssociations` | Create policy to table associations. |  |
| `create_policy` | POST | `/api/v1/lakehouseopt/createPolicy` | Create a new policy. |  |
| `create_table_policies_associations` | POST | `/api/v1/lakehouseopt/createTablePoliciesAssociations` | create associations of a table and policies. |  |
| `delete_policy` | POST | `/api/v1/lakehouseopt/deletePolicy` | Delete a policy definition for a resource. |  |
| `download_policy` | POST | `/api/v1/lakehouseopt/downloadPolicy` | Downloads the policy definition for a particular policy version. |  |
| `execute_policy` | POST | `/api/v1/lakehouseopt/executePolicy` | Execute a policy on a table. |  |
| `get_associated_namespaces` | POST | `/api/v1/lakehouseopt/getAssociatedNamespaces` | Get all associated namespaces for a policy. |  |
| `get_associated_tables` | POST | `/api/v1/lakehouseopt/getAssociatedTables` | Get all associated tables for a policy |  |
| `get_association_details` | POST | `/api/v1/lakehouseopt/getAssociationDetails` | Get policy association details. |  |
| `get_associations` | POST | `/api/v1/lakehouseopt/getAssociations` | Get policy to table associations. |  |
| `get_clo_datahub` | POST | `/api/v1/lakehouseopt/getCloDatahub` | Fetches CLO Data Hub for an environment. |  |
| `get_datahub_crn` | POST | `/api/v1/lakehouseopt/getDatahubCrn` | Fetches Data Hub CRN for an environment. |  |
| `get_health` | POST | `/api/v1/lakehouseopt/getHealth` | Performs health check on CLO components. |  |
| `get_namespaces` | POST | `/api/v1/lakehouseopt/getNamespaces` | Get all namespaces. |  |
| `get_policy` | POST | `/api/v1/lakehouseopt/getPolicy` | Fetches the policy details. |  |
| `get_policy_names` | POST | `/api/v1/lakehouseopt/getPolicyNames` | get all policy names associated with a namespace. |  |
| `get_scripts` | POST | `/api/v1/lakehouseopt/getScripts` | Get scripts. |  |
| `get_table_names` | POST | `/api/v1/lakehouseopt/getTableNames` | Get table names in a namespace. |  |
| `get_table_policies` | POST | `/api/v1/lakehouseopt/getTablePolicies` | get policies of a table in a namespace. |  |
| `get_table_status_details` | POST | `/api/v1/lakehouseopt/getTableStatusDetails` | Get table status details. |  |
| `get_timezones` | POST | `/api/v1/lakehouseopt/getTimezones` | Get all supported timezones. |  |
| `list_environments` | POST | `/api/v1/lakehouseopt/listEnvironments` | List environments. |  |
| `list_policies` | POST | `/api/v1/lakehouseopt/listPolicies` | Lists policies. |  |
| `list_tables` | POST | `/api/v1/lakehouseopt/listTables` | List tables in a namespace. |  |
| `list_tasks` | POST | `/api/v1/lakehouseopt/listTasks` | Retrieves CLO maintenance tasks. |  |
| `pause_table` | POST | `/api/v1/lakehouseopt/pauseTable` | Pause a table. |  |
| `unpause_table` | POST | `/api/v1/lakehouseopt/unpauseTable` | Unpause a table. |  |
| `unsubscribe_policy` | POST | `/api/v1/lakehouseopt/unsubscribePolicy` | Unsubscribe a policy from the table. |  |
| `update_policy` | POST | `/api/v1/lakehouseopt/updatePolicy` | Update an existing policy. |  |

## cdp_ml

55 tools.

- Product: Cloudera AI / Machine Learning (workspaces, registries, inference)
- Spec title: Cloudera AI
- Description: Install and manage Cloudera AI applications.
- Spec source: GA (https://github.com/cloudera/cdp-dev-docs/blob/5a189fcd6124f3e1b671ebee69cc229a47326865/api-docs/swagger/ml.yaml) v0.9.164, beta (https://github.com/cloudera/cdp-dev-docs/blob/5a189fcd6124f3e1b671ebee69cc229a47326865/api-docs-beta/swagger/ml.yaml) v0.9.164 (BETA)
- Service release: PUBLIC; products: CDP
- Auth: Base URL https://api.<region>.cdp.cloudera.com (e.g. us-west-1, eu-1, ap-1; https://api.usg-1.cdp.clouderagovt.com for US Gov). All calls are POST with Content-Type: application/json and a JSON body, signed per CDP request signing V1 (headers x-altus-date and x-altus-auth = ed25519v1/rsav1 signature using the CDP access key ID + private key).
- Operations: 55 (0 beta-only, 0 deprecated)

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `add_instance_groups` | POST | `/api/v1/ml/addInstanceGroups` | Add new Cloudera AI workbench cluster instance groups. |  |
| `add_instance_groups_ml_serving_app` | POST | `/api/v1/ml/addInstanceGroupsMlServingApp` | Add instance group to an existing Cloudera AI Inference Service instance. |  |
| `backup_workspace` | POST | `/api/v1/ml/backupWorkspace` | Backup a Cloudera AI workbench. |  |
| `create_file_replica` | POST | `/api/v1/ml/createFileReplica` | Create file system replica. |  |
| `create_ml_serving_app` | POST | `/api/v1/ml/createMlServingApp` | Deploys Cloudera AI Inference Service into an existing Kubernetes cluster. |  |
| `create_model_registry` | POST | `/api/v1/ml/createModelRegistry` | Creates a new model registry. |  |
| `create_workspace` | POST | `/api/v1/ml/createWorkspace` | Create a Cloudera AI workbench. |  |
| `delete_backup` | POST | `/api/v1/ml/deleteBackup` | Deletes a backup snapshot. |  |
| `delete_file_replica` | POST | `/api/v1/ml/deleteFileReplica` | Delete existing replication for project files. |  |
| `delete_instance_group` | POST | `/api/v1/ml/deleteInstanceGroup` | Deletes an instance group from the cluster. |  |
| `delete_instance_group_ml_serving_app` | POST | `/api/v1/ml/deleteInstanceGroupMlServingApp` | Deletes an instance group from a Cloudera AI Inference Service instance. |  |
| `delete_ml_serving_app` | POST | `/api/v1/ml/deleteMlServingApp` | Deletes Cloudera AI Inference Service instance. |  |
| `delete_model_registry` | POST | `/api/v1/ml/deleteModelRegistry` | Deletes a model registry. |  |
| `delete_workspace` | POST | `/api/v1/ml/deleteWorkspace` | Delete Cloudera AI workbench. |  |
| `describe_ml_serving_app` | POST | `/api/v1/ml/describeMlServingApp` | Describe Cloudera AI Inference Service instance. |  |
| `describe_model_registry` | POST | `/api/v1/ml/describeModelRegistry` | Deprecated: Cloudera AI Model Registry is now deprecated. |  |
| `describe_workspace` | POST | `/api/v1/ml/describeWorkspace` | Describe Cloudera AI workbench. |  |
| `describe_workspace_backup` | POST | `/api/v1/ml/describeWorkspaceBackup` | Describe backup snapshot of a workbench. |  |
| `fail_over_file_system` | POST | `/api/v1/ml/failOverFileSystem` | Failover to replica file system |  |
| `get_audit_events` | POST | `/api/v1/ml/getAuditEvents` | Gets all the events belong to a workbench crn. |  |
| `get_kubeconfig` | POST | `/api/v1/ml/getKubeconfig` | ListWorkspaceAccess Cloudera AI workbench. |  |
| `get_latest_model_registry_version` | POST | `/api/v1/ml/getLatestModelRegistryVersion` | GetLatestModelRegistryVersion Cloudera AI Registry. |  |
| `get_latest_workspace_version` | POST | `/api/v1/ml/getLatestWorkspaceVersion` | GetLatestWorkspaceVersion Cloudera AI workbench. |  |
| `get_logs` | POST | `/api/v1/ml/getLogs` | Gets all the logs belong to a request id. |  |
| `get_ml_serving_app_kubeconfig` | POST | `/api/v1/ml/getMlServingAppKubeconfig` | Return kubeconfig for a Cloudera AI Inference Service Kubernetes cluster. |  |
| `get_model_registry_kubeconfig` | POST | `/api/v1/ml/getModelRegistryKubeconfig` | GetModelRegistryKubeconfig returns kube config for model registry. |  |
| `grant_ml_serving_app_access` | POST | `/api/v1/ml/grantMlServingAppAccess` | Grants admin access to a Cloudera AI Inference Service cluster. |  |
| `grant_model_registry_access` | POST | `/api/v1/ml/grantModelRegistryAccess` | GrantModelRegistryAccess Cloudera AI Model Registry. |  |
| `grant_workspace_access` | POST | `/api/v1/ml/grantWorkspaceAccess` | GrantWorkspaceAccess Cloudera AI workbench. |  |
| `list_instance_type_configuration` | POST | `/api/v1/ml/listInstanceTypeConfiguration` | List the instance configuration for a given instance type. |  |
| `list_ml_serving_app_access` | POST | `/api/v1/ml/listMlServingAppAccess` | List members that have Kubernetes access to a Cloudera AI Inference Service cluster. |  |
| `list_ml_serving_apps` | POST | `/api/v1/ml/listMlServingApps` | List all Cloudera AI Inference Service instances. |  |
| `list_model_registries` | POST | `/api/v1/ml/listModelRegistries` | Lists all model registries. |  |
| `list_model_registry_access` | POST | `/api/v1/ml/listModelRegistryAccess` | ListWorkspaceAccess Cloudera AI Model Registry. |  |
| `list_relevant_instances` | POST | `/api/v1/ml/listRelevantInstances` | List the instance types for Cloudera AI workbench creation that have the requested resource. |  |
| `list_workspace_access` | POST | `/api/v1/ml/listWorkspaceAccess` | ListWorkspaceAccess Cloudera AI workbench. |  |
| `list_workspace_backups` | POST | `/api/v1/ml/listWorkspaceBackups` | List backup snapshots of a workbench. |  |
| `list_workspaces` | POST | `/api/v1/ml/listWorkspaces` | List Cloudera AI workbenches. |  |
| `modify_cluster_instance_group` | POST | `/api/v1/ml/modifyClusterInstanceGroup` | Modify Cloudera AI workbench cluster instance group. |  |
| `modify_cluster_security` | POST | `/api/v1/ml/modifyClusterSecurity` | Modify Cloudera AI workbench cluster security. |  |
| `modify_ml_serving_app` | POST | `/api/v1/ml/modifyMlServingApp` | Modify instance groups for a Cloudera AI Inference Service cluster. |  |
| `modify_workspace_load_balancer` | POST | `/api/v1/ml/modifyWorkspaceLoadBalancer` | Modify Cloudera AI workbench loadbalancer. |  |
| `refresh_model_registry_configmap` | POST | `/api/v1/ml/refreshModelRegistryConfigmap` | Refreshes the model registry configmap of the workbench. |  |
| `request_workflow_cancellation` | POST | `/api/v1/ml/requestWorkflowCancellation` | Request a workflow cancellation. |  |
| `request_workflow_rollback` | POST | `/api/v1/ml/requestWorkflowRollback` | Request a workflow rollback |  |
| `restore_workspace` | POST | `/api/v1/ml/restoreWorkspace` | Restore a Cloudera AI workbench. |  |
| `resume_workspace` | POST | `/api/v1/ml/resumeWorkspace` | Resume Cloudera AI workbench. |  |
| `revoke_ml_serving_app_access` | POST | `/api/v1/ml/revokeMlServingAppAccess` | Revokes access to a Cloudera AI Inference Service cluster. |  |
| `revoke_model_registry_access` | POST | `/api/v1/ml/revokeModelRegistryAccess` | RevokeModelRegistryAccess Cloudera AI Model Registry. |  |
| `revoke_workspace_access` | POST | `/api/v1/ml/revokeWorkspaceAccess` | RevokeWorkspaceAccess Cloudera AI workbench. |  |
| `rollback_model_registry_upgrade` | POST | `/api/v1/ml/rollbackModelRegistryUpgrade` | Rollback a model registry upgrade. Restore prior model registry. |  |
| `suspend_workspace` | POST | `/api/v1/ml/suspendWorkspace` | Suspend Cloudera AI workbench. |  |
| `upgrade_ml_serving_app` | POST | `/api/v1/ml/upgradeMlServingApp` | Upgrade a Cloudera AI Inference Service instance. |  |
| `upgrade_model_registry` | POST | `/api/v1/ml/upgradeModelRegistry` | Upgrade a model registry. |  |
| `upgrade_workspace` | POST | `/api/v1/ml/upgradeWorkspace` | Upgrade Cloudera AI workbench. |  |

## cdp_notification

18 tools.

- Product: CDP Notifications (beta)
- Spec title: Notification API Service
- Description: Provides an interface to the notification service.
- Spec source: not in GA docs, beta (https://github.com/cloudera/cdp-dev-docs/blob/5a189fcd6124f3e1b671ebee69cc229a47326865/api-docs-beta/swagger/notification.yaml) v0.9.164 (BETA)
- Service release: BETA; products: CDP
- Auth: Base URL https://api.<region>.cdp.cloudera.com (e.g. us-west-1, eu-1, ap-1; https://api.usg-1.cdp.clouderagovt.com for US Gov). All calls are POST with Content-Type: application/json and a JSON body, signed per CDP request signing V1 (headers x-altus-date and x-altus-auth = ed25519v1/rsav1 signature using the CDP access key ID + private key).
- Operations: 18 (18 beta-only, 0 deprecated)

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `create_or_update_account_metadata` | POST | `/api/v1/notification/createOrUpdateAccountMetadata` | CreateOrUpdateAccountMetadata | beta |
| `create_or_update_distribution_list` | POST | `/api/v1/notification/createOrUpdateDistributionList` | CreateOrUpdateDistributionList | beta |
| `create_or_update_resource_subscription` | POST | `/api/v1/notification/createOrUpdateResourceSubscription` | CreateOrUpdateResourceSubscription | beta |
| `delete_all_subscriptions_for_resource` | POST | `/api/v1/notification/deleteAllSubscriptionsForResource` | DeleteAllSubscriptionsForResource | beta |
| `delete_app_registration` | POST | `/api/v1/notification/deleteAppRegistration` | API endpoint used to delete app registration | beta |
| `delete_distribution_list` | POST | `/api/v1/notification/deleteDistributionList` | DeleteDistributionList | beta |
| `delete_distribution_lists_for_resource` | POST | `/api/v1/notification/deleteDistributionListsForResource` | DeleteDistributionListsForResource | beta |
| `delete_resource_subscription` | POST | `/api/v1/notification/deleteResourceSubscription` | DeleteResourceSubscription | beta |
| `delete_resource_subscriptions_for_resource` | POST | `/api/v1/notification/deleteResourceSubscriptionsForResource` | DeleteResourceSubscriptionsForResource | beta |
| `get_account_metadata` | POST | `/api/v1/notification/getAccountMetadata` | GetAccountMetadata | beta |
| `get_app_registration_status` | POST | `/api/v1/notification/getAppRegistrationStatus` | API endpoint to get AppRegistrationStatus | beta |
| `get_distribution_list` | POST | `/api/v1/notification/getDistributionList` | GetDistributionList | beta |
| `get_o_auth_url` | POST | `/api/v1/notification/getOAuthUrl` | GetOAuthURL | beta |
| `get_resource_subscription` | POST | `/api/v1/notification/getResourceSubscription` | GetResourceSubscription | beta |
| `list_distribution_lists` | POST | `/api/v1/notification/listDistributionLists` | ListDistributionLists | beta |
| `list_resource_event_catalog` | POST | `/api/v1/notification/listResourceEventCatalog` | Lists all the types of resource events available in the catalog. | beta |
| `list_resource_subscriptions` | POST | `/api/v1/notification/listResourceSubscriptions` | ListResourceSubscriptions | beta |
| `update_app_authorization_code` | POST | `/api/v1/notification/updateAppAuthorizationCode` | API endpoint to get UpdateAppAuthorizationCode | beta |

## cdp_opdb

31 tools.

- Product: Cloudera Operational Database (COD)
- Spec title: Operational Database service
- Description: Interact with the Cloudera Operational Database service
- Spec source: GA (https://github.com/cloudera/cdp-dev-docs/blob/5a189fcd6124f3e1b671ebee69cc229a47326865/api-docs/swagger/opdb.yaml) v0.9.164, beta (https://github.com/cloudera/cdp-dev-docs/blob/5a189fcd6124f3e1b671ebee69cc229a47326865/api-docs-beta/swagger/opdb.yaml) v0.9.164 (BETA)
- Service release: PUBLIC; products: CDP
- Auth: Base URL https://api.<region>.cdp.cloudera.com (e.g. us-west-1, eu-1, ap-1; https://api.usg-1.cdp.clouderagovt.com for US Gov). All calls are POST with Content-Type: application/json and a JSON body, signed per CDP request signing V1 (headers x-altus-date and x-altus-auth = ed25519v1/rsav1 signature using the CDP access key ID + private key).
- Operations: 31 (12 beta-only, 0 deprecated)

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `add_coprocessor` | POST | `/api/v1/opdb/addCoprocessor` | Add a coprocessor for a specific table | beta |
| `collect_diagnostics` | POST | `/api/v1/opdb/collectDiagnostics` | Collect diagnostic data bundles from the database |  |
| `create_database` | POST | `/api/v1/opdb/createDatabase` | Create opDb |  |
| `create_snapshot` | POST | `/api/v1/opdb/createSnapshot` | Creates a snapshot for a specific table. |  |
| `delete_snapshot` | POST | `/api/v1/opdb/deleteSnapshot` | Deletes a snapshot. |  |
| `describe_client_connectivity` | POST | `/api/v1/opdb/describeClientConnectivity` | Returns client connectivity details |  |
| `describe_database` | POST | `/api/v1/opdb/describeDatabase` | Describe a opDb |  |
| `describe_hbase_configuration` | POST | `/api/v1/opdb/describeHbaseConfiguration` | Describes the configuration of HBase. | beta |
| `describe_upgrade_database` | POST | `/api/v1/opdb/describeUpgradeDatabase` | Describes the upgrade availability. |  |
| `drop_database` | POST | `/api/v1/opdb/dropDatabase` | drop a opDb |  |
| `list_certificates` | POST | `/api/v1/opdb/listCertificates` | List certificates | beta |
| `list_coprocessors` | POST | `/api/v1/opdb/listCoprocessors` | Lists coprocessors in a database | beta |
| `list_databases` | POST | `/api/v1/opdb/listDatabases` | List all opDbs in an environment |  |
| `list_diagnostics` | POST | `/api/v1/opdb/listDiagnostics` | List all diagnostics associated to the database |  |
| `list_edge_nodes` | POST | `/api/v1/opdb/listEdgeNodes` | Lists edge nodes in a database | beta |
| `list_events` | POST | `/api/v1/opdb/listEvents` | Lists events | beta |
| `list_restore_snapshots` | POST | `/api/v1/opdb/listRestoreSnapshots` | Lists instances when a snapshot was restored to a database. |  |
| `list_scaling_events` | POST | `/api/v1/opdb/listScalingEvents` | Lists scaling events | beta |
| `list_snapshots` | POST | `/api/v1/opdb/listSnapshots` | Shows snapshot for a table name in a specific location. |  |
| `list_supported_environments` | POST | `/api/v1/opdb/listSupportedEnvironments` | List of environments available for the database creation |  |
| `list_supported_instance_types` | POST | `/api/v1/opdb/listSupportedInstanceTypes` | Lists instance types supported by COD | beta |
| `prepare_upgrade_database` | POST | `/api/v1/opdb/prepareUpgradeDatabase` | Prepare database upgrade. |  |
| `remove_coprocessor` | POST | `/api/v1/opdb/removeCoprocessor` | Removes a coprocessor for a specific table | beta |
| `restore_snapshot` | POST | `/api/v1/opdb/restoreSnapshot` | Restores a snapshot. |  |
| `start_database` | POST | `/api/v1/opdb/startDatabase` | Starts the database |  |
| `stop_database` | POST | `/api/v1/opdb/stopDatabase` | Stops the database |  |
| `update_database` | POST | `/api/v1/opdb/updateDatabase` | Updates the database |  |
| `update_edge_nodes` | POST | `/api/v1/opdb/updateEdgeNodes` | Update edge nodes in a database | beta |
| `update_hbase_configuration` | POST | `/api/v1/opdb/updateHbaseConfiguration` | Updates the configuration of HBase. | beta |
| `upgrade_database` | POST | `/api/v1/opdb/upgradeDatabase` | Upgrades the database. |  |
| `upload_certificate` | POST | `/api/v1/opdb/uploadCertificate` | Upload custom certificate | beta |

## cdp_publicendpointmanagement

3 tools.

- Product: CDP Public Endpoint Management (beta)
- Spec title: PublicEndpointManagement Public Service
- Description: PublicEndpointManagement Public Service is a web service for CDP applications to manage public DNS entries and TLS certificates.
- Spec source: not in GA docs, beta (https://github.com/cloudera/cdp-dev-docs/blob/5a189fcd6124f3e1b671ebee69cc229a47326865/api-docs-beta/swagger/publicendpointmanagement.yaml) v0.9.164 (BETA)
- Service release: BETA; products: CDP
- Auth: Base URL https://api.<region>.cdp.cloudera.com (e.g. us-west-1, eu-1, ap-1; https://api.usg-1.cdp.clouderagovt.com for US Gov). All calls are POST with Content-Type: application/json and a JSON body, signed per CDP request signing V1 (headers x-altus-date and x-altus-auth = ed25519v1/rsav1 signature using the CDP access key ID + private key).
- Operations: 3 (3 beta-only, 0 deprecated)

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `create_dns_entry` | POST | `/api/v1/publicendpointmanagement/createDnsEntry` | Create or update a DNS entry. | beta |
| `delete_dns_entry` | POST | `/api/v1/publicendpointmanagement/deleteDnsEntry` | Delete a DNS entry. | beta |
| `list_dns_entries` | POST | `/api/v1/publicendpointmanagement/listDnsEntries` | List all DNS entries. | beta |

## cdp_replicationmanager

53 tools.

- Product: Cloudera Replication Manager
- Spec title: Cloudera Replication Manager Service
- Description: Create and manage replication policies using Cloudera Replication Manager.
- Spec source: GA (https://github.com/cloudera/cdp-dev-docs/blob/5a189fcd6124f3e1b671ebee69cc229a47326865/api-docs/swagger/replicationmanager.yaml) v0.9.164, beta (https://github.com/cloudera/cdp-dev-docs/blob/5a189fcd6124f3e1b671ebee69cc229a47326865/api-docs-beta/swagger/replicationmanager.yaml) v0.9.164 (BETA)
- Service release: PUBLIC; products: CDP
- Auth: Base URL https://api.<region>.cdp.cloudera.com (e.g. us-west-1, eu-1, ap-1; https://api.usg-1.cdp.clouderagovt.com for US Gov). All calls are POST with Content-Type: application/json and a JSON body, signed per CDP request signing V1 (headers x-altus-date and x-altus-auth = ed25519v1/rsav1 signature using the CDP access key ID + private key).
- Operations: 53 (29 beta-only, 0 deprecated)

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `abort_policy` | POST | `/api/v1/replicationmanager/abortPolicy` | Abort replication policy. | beta |
| `activate_hbase_policy` | POST | `/api/v1/replicationmanager/activateHbasePolicy` | Resume a suspended HBase replication policy. |  |
| `activate_policy` | POST | `/api/v1/replicationmanager/activatePolicy` | Resume all replication tasks defined by the policy. |  |
| `activate_snapshot_policy` | POST | `/api/v1/replicationmanager/activateSnapshotPolicy` | Resume snapshot policy. | beta |
| `collect_diagnostic_bundle` | POST | `/api/v1/replicationmanager/collectDiagnosticBundle` | Collect diagnostic bundle for a policy. |  |
| `continue_hbase_setup` | POST | `/api/v1/replicationmanager/continueHbaseSetup` | Continue the setup of an HBase policy. |  |
| `create_abfs_access_key_credential` | POST | `/api/v1/replicationmanager/createAbfsAccessKeyCredential` | Create an ABFS Access Key based account in DLM Engine. | beta |
| `create_abfs_client_key_credential` | POST | `/api/v1/replicationmanager/createAbfsClientKeyCredential` | Create an Azure Active Directory Service Principal account in Cloudera Manager. | beta |
| `create_abfs_credential` | POST | `/api/v1/replicationmanager/createAbfsCredential` | Create an ABFS Cloud Credential. |  |
| `create_aws_access_key_credential` | POST | `/api/v1/replicationmanager/createAwsAccessKeyCredential` | Create an AWS Access Key cloud credential. | beta |
| `create_aws_credential` | POST | `/api/v1/replicationmanager/createAwsCredential` | Create an AWS Cloud Credential. |  |
| `create_aws_iam_credential` | POST | `/api/v1/replicationmanager/createAwsIamCredential` | Create an AWS IAM Role based cloud credential. | beta |
| `create_aws_idbroker_credential` | POST | `/api/v1/replicationmanager/createAwsIdbrokerCredential` | Create an AWS IDBroker cloud credential. | beta |
| `create_gcs_private_key_credential` | POST | `/api/v1/replicationmanager/createGcsPrivateKeyCredential` | Create a GCS Private Key cloud credential. | beta |
| `create_hbase_policy` | POST | `/api/v1/replicationmanager/createHbasePolicy` | Create an HBase Replication Policy. |  |
| `create_policy` | POST | `/api/v1/replicationmanager/createPolicy` | Create a Replication Policy. |  |
| `create_snapshot_policy` | POST | `/api/v1/replicationmanager/createSnapshotPolicy` | Create snapshot policy. | beta |
| `delete_credential` | POST | `/api/v1/replicationmanager/deleteCredential` | Delete Cloud Credential. |  |
| `delete_hbase_policy` | POST | `/api/v1/replicationmanager/deleteHbasePolicy` | Delete an HBase Replication Policy. |  |
| `delete_policy` | POST | `/api/v1/replicationmanager/deletePolicy` | Delete Replication Policy. |  |
| `delete_snapshot_policy` | POST | `/api/v1/replicationmanager/deleteSnapshotPolicy` | Delete snapshot policy. | beta |
| `download_diagnostic_bundle` | POST | `/api/v1/replicationmanager/downloadDiagnosticBundle` | Download diagnostic bundle for a policy. |  |
| `get_cluster_config` | POST | `/api/v1/replicationmanager/getClusterConfig` | Get configuration of a cluster. |  |
| `get_command_status` | POST | `/api/v1/replicationmanager/getCommandStatus` | Get the status of the given CM command. |  |
| `get_credentials` | POST | `/api/v1/replicationmanager/getCredentials` | Get Cloud Credentials from a Cluster. |  |
| `get_hbase_time_series` | POST | `/api/v1/replicationmanager/getHbaseTimeSeries` | Retrieve time series data for an HBase replication peer. | beta |
| `get_snapshot_policy` | POST | `/api/v1/replicationmanager/getSnapshotPolicy` | Get Snapshot Policy. | beta |
| `list_all_credentials` | POST | `/api/v1/replicationmanager/listAllCredentials` | Lists Cloud Credentials. |  |
| `list_cluster_service_statuses` | POST | `/api/v1/replicationmanager/listClusterServiceStatuses` | Lists Cluster Service Statuses. |  |
| `list_clusters` | POST | `/api/v1/replicationmanager/listClusters` | Lists all clusters. |  |
| `list_paired_hbase_clusters` | POST | `/api/v1/replicationmanager/listPairedHbaseClusters` | List cluster CRNs which have an active HBase policy. |  |
| `list_policies` | POST | `/api/v1/replicationmanager/listPolicies` | Get All Replication Policies. |  |
| `list_policy_jobs` | POST | `/api/v1/replicationmanager/listPolicyJobs` | List policy jobs. | beta |
| `list_snapshot_policies` | POST | `/api/v1/replicationmanager/listSnapshotPolicies` | Get All Snapshot Policies. | beta |
| `list_snapshot_policy_jobs` | POST | `/api/v1/replicationmanager/listSnapshotPolicyJobs` | List snapshot policy jobs. | beta |
| `repair_hbase_policy` | POST | `/api/v1/replicationmanager/repairHbasePolicy` | Repair a failed HBase policy. | beta |
| `rerun_policy` | POST | `/api/v1/replicationmanager/rerunPolicy` | Rerun policy job. | beta |
| `restore_snapshot` | POST | `/api/v1/replicationmanager/restoreSnapshot` | Restore snapshot. | beta |
| `retry_failed_hbase_first_time_setup` | POST | `/api/v1/replicationmanager/retryFailedHbaseFirstTimeSetup` | Retry failed first time setup for an HBase policy. | beta |
| `retry_failed_hbase_snapshots` | POST | `/api/v1/replicationmanager/retryFailedHbaseSnapshots` | Retry failed snapshots for an HBase policy. | beta |
| `suspend_hbase_policy` | POST | `/api/v1/replicationmanager/suspendHbasePolicy` | Suspend an HBase replication policy. |  |
| `suspend_policy` | POST | `/api/v1/replicationmanager/suspendPolicy` | Stop all replication tasks defined by the policy. |  |
| `suspend_snapshot_policy` | POST | `/api/v1/replicationmanager/suspendSnapshotPolicy` | Suspend snapshot policy. | beta |
| `update_abfs_access_key_credential` | POST | `/api/v1/replicationmanager/updateAbfsAccessKeyCredential` | Update an ABFS Access Key based account in DLM Engine. | beta |
| `update_abfs_client_key_credential` | POST | `/api/v1/replicationmanager/updateAbfsClientKeyCredential` | Update an Azure Active Directory Service Principal account in Cloudera Manager. | beta |
| `update_aws_access_key_credential` | POST | `/api/v1/replicationmanager/updateAwsAccessKeyCredential` | Update an AWS Access Key cloud credential. | beta |
| `update_aws_iam_credential` | POST | `/api/v1/replicationmanager/updateAwsIamCredential` | Update an AWS IAM Role based cloud credential. | beta |
| `update_aws_idbroker_credential` | POST | `/api/v1/replicationmanager/updateAwsIdbrokerCredential` | Update an AWS IDBroker cloud credential. | beta |
| `update_gcs_private_key_credential` | POST | `/api/v1/replicationmanager/updateGcsPrivateKeyCredential` | Update a GCS Private Key cloud credential. | beta |
| `update_hbase_policy` | POST | `/api/v1/replicationmanager/updateHbasePolicy` | Update an HBase Replication Policy. |  |
| `update_policy` | POST | `/api/v1/replicationmanager/updatePolicy` | Update a Replication Policy. | beta |
| `update_snapshot_policy` | POST | `/api/v1/replicationmanager/updateSnapshotPolicy` | Update snapshot policy. | beta |
| `verify_hbase_cluster_pair` | POST | `/api/v1/replicationmanager/verifyHbaseClusterPair` | Verify a source-destination cluster pair for HBase policy creation. |  |
