# Data in motion

NiFi, NiFi Registry, Schema Registry, Streams Messaging Manager, Streams Replication Manager, Kafka Connect, Cruise Control, SQL Stream Builder and Flink.

Flags: **beta** = not in the GA spec; **deprecated** = marked deprecated by the vendor spec; **in built-in pack** = the existing Daedalus `hdfs`/`s3` pack already has it.

## nifi_flow

60 tools.

- Product/version: Apache NiFi REST API 2.6.0 (Cloudera Flow Management 4.12 ships NiFi 2.6.0.4.12.x)
- Spec source: https://repo1.maven.org/maven2/org/apache/nifi/nifi-web-api/2.6.0/nifi-web-api-2.6.0.war (docs/rest-api/swagger.json, OpenAPI 3.0.1)
- Tags included: Flow
- Auth: Base path /nifi-api. JWT bearer (HTTPBearerJWT / __Secure-Request-Token cookie) obtained via POST /access/token (LDAP/Kerberos login identity provider) or POST /access/kerberos (SPNEGO); mutual-TLS client certs; OIDC/SAML/Knox SSO. Via Knox: https://<knox>/gateway/cdp-proxy-api/nifi-app/nifi-api with Knox basic/JWT. Mutating requests on components need a revision object (version + clientId).
- Operation count: 60

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `get_about_info` | GET | `/nifi-api/flow/about` | Retrieves details about this NiFi to put in the About dialog |  |
| `get_additional_details` | GET | `/nifi-api/flow/additional-details/{group}/{artifact}/{version}/{type}` | Retrieves the additional details for the specified component type. |  |
| `get_banners` | GET | `/nifi-api/flow/banners` | Retrieves the banners for this NiFi |  |
| `get_bulletin_board` | GET | `/nifi-api/flow/bulletin-board` | Gets current bulletins |  |
| `generate_client_id` | GET | `/nifi-api/flow/client-id` | Generates a client id. |  |
| `search_cluster` | GET | `/nifi-api/flow/cluster/search-results` | Searches the cluster for a node with the specified address |  |
| `get_cluster_summary` | GET | `/nifi-api/flow/cluster/summary` | The cluster summary for this NiFi |  |
| `get_flow_config` | GET | `/nifi-api/flow/config` | Retrieves the configuration for this NiFi flow |  |
| `get_connection_statistics` | GET | `/nifi-api/flow/connections/{id}/statistics` | Gets statistics for a connection |  |
| `get_connection_status` | GET | `/nifi-api/flow/connections/{id}/status` | Gets status for a connection |  |
| `get_connection_status_history` | GET | `/nifi-api/flow/connections/{id}/status/history` | Gets the status history for a connection |  |
| `get_content_viewers` | GET | `/nifi-api/flow/content-viewers` | Retrieves the registered content viewers |  |
| `get_controller_service_definition` | GET | `/nifi-api/flow/controller-service-definition/{group}/{artifact}/{version}/{type}` | Retrieves the Controller Service Definition for the specified component type. |  |
| `get_controller_service_types` | GET | `/nifi-api/flow/controller-service-types` | Retrieves the types of controller services that this NiFi supports |  |
| `get_bulletins` | GET | `/nifi-api/flow/controller/bulletins` | Retrieves Controller level bulletins |  |
| `get_controller_services_from_controller` | GET | `/nifi-api/flow/controller/controller-services` | Gets controller services for reporting tasks |  |
| `get_current_user` | GET | `/nifi-api/flow/current-user` | Retrieves the user identity of the user making the request |  |
| `get_flow_analysis_rule_definition` | GET | `/nifi-api/flow/flow-analysis-rule-definition/{group}/{artifact}/{version}/{type}` | Retrieves the Flow Analysis Rule Definition for the specified component type. |  |
| `get_flow_analysis_rule_types` | GET | `/nifi-api/flow/flow-analysis-rule-types` | Retrieves the types of available Flow Analysis Rules |  |
| `get_all_flow_analysis_results` | GET | `/nifi-api/flow/flow-analysis/results` | Returns all flow analysis results currently in effect |  |
| `get_flow_analysis_results` | GET | `/nifi-api/flow/flow-analysis/results/{processGroupId}` | Returns flow analysis results produced by the analysis of a given process group |  |
| `query_history` | GET | `/nifi-api/flow/history` | Gets configuration history |  |
| `get_component_history` | GET | `/nifi-api/flow/history/components/{componentId}` | Gets configuration history for a component |  |
| `get_action` | GET | `/nifi-api/flow/history/{id}` | Gets an action |  |
| `get_input_port_status` | GET | `/nifi-api/flow/input-ports/{id}/status` | Gets status for an input port |  |
| `get_flow_metrics` | GET | `/nifi-api/flow/metrics/{producer}` | Gets all metrics for the flow from a particular node |  |
| `get_output_port_status` | GET | `/nifi-api/flow/output-ports/{id}/status` | Gets status for an output port |  |
| `get_parameter_contexts` | GET | `/nifi-api/flow/parameter-contexts` | Gets all Parameter Contexts |  |
| `get_parameter_provider_definition` | GET | `/nifi-api/flow/parameter-provider-definition/{group}/{artifact}/{version}/{type}` | Retrieves the Parameter Provider Definition for the specified component type. |  |
| `get_parameter_provider_types` | GET | `/nifi-api/flow/parameter-provider-types` | Retrieves the types of parameter providers that this NiFi supports |  |
| `get_parameter_providers` | GET | `/nifi-api/flow/parameter-providers` | Gets all parameter providers |  |
| `get_prioritizers` | GET | `/nifi-api/flow/prioritizers` | Retrieves the types of prioritizers that this NiFi supports |  |
| `get_flow` | GET | `/nifi-api/flow/process-groups/{id}` | Gets a process group |  |
| `schedule_components` | PUT | `/nifi-api/flow/process-groups/{id}` | Schedule or unschedule components in the specified Process Group. |  |
| `get_breadcrumbs` | GET | `/nifi-api/flow/process-groups/{id}/breadcrumbs` | Gets the breadcrumbs for a process group |  |
| `get_controller_services_from_group` | GET | `/nifi-api/flow/process-groups/{id}/controller-services` | Gets all controller services |  |
| `activate_controller_services` | PUT | `/nifi-api/flow/process-groups/{id}/controller-services` | Enable or disable Controller Services in the specified Process Group. |  |
| `get_process_group_status` | GET | `/nifi-api/flow/process-groups/{id}/status` | Gets the status for a process group |  |
| `get_process_group_status_history` | GET | `/nifi-api/flow/process-groups/{id}/status/history` | Gets status history for a remote process group |  |
| `get_processor_definition` | GET | `/nifi-api/flow/processor-definition/{group}/{artifact}/{version}/{type}` | Retrieves the Processor Definition for the specified component type. |  |
| `get_processor_types` | GET | `/nifi-api/flow/processor-types` | Retrieves the types of processors that this NiFi supports |  |
| `get_processor_status` | GET | `/nifi-api/flow/processors/{id}/status` | Gets status for a processor |  |
| `get_processor_status_history` | GET | `/nifi-api/flow/processors/{id}/status/history` | Gets status history for a processor |  |
| `get_registry_clients` | GET | `/nifi-api/flow/registries` | Gets the listing of available flow registry clients |  |
| `get_branches` | GET | `/nifi-api/flow/registries/{id}/branches` | Gets the branches from the specified registry for the current user |  |
| `get_buckets` | GET | `/nifi-api/flow/registries/{id}/buckets` | Gets the buckets from the specified registry for the current user |  |
| `get_version_differences` | GET | `/nifi-api/flow/registries/{registry-id}/branches/{branch-id-a}/buckets/{bucket-id-a}/flows/{flow-id-a}/{version-a}/diff/branches/{branch-id-b}/buckets/{bucket-id-b}/flows/{flow-id-b}/{version-b}` | Gets the differences between two versions of the same versioned flow, the basis of the comparison will be the first version |  |
| `get_flows` | GET | `/nifi-api/flow/registries/{registry-id}/buckets/{bucket-id}/flows` | Gets the flows from the specified registry and bucket for the current user |  |
| `get_details` | GET | `/nifi-api/flow/registries/{registry-id}/buckets/{bucket-id}/flows/{flow-id}/details` | Gets the details of a flow from the specified registry and bucket for the specified flow for the current user |  |
| `get_versions` | GET | `/nifi-api/flow/registries/{registry-id}/buckets/{bucket-id}/flows/{flow-id}/versions` | Gets the flow versions from the specified registry and bucket for the specified flow for the current user |  |
| `get_remote_process_group_status` | GET | `/nifi-api/flow/remote-process-groups/{id}/status` | Gets status for a remote process group |  |
| `get_remote_process_group_status_history` | GET | `/nifi-api/flow/remote-process-groups/{id}/status/history` | Gets the status history |  |
| `get_reporting_task_definition` | GET | `/nifi-api/flow/reporting-task-definition/{group}/{artifact}/{version}/{type}` | Retrieves the Reporting Task Definition for the specified component type. |  |
| `get_reporting_task_types` | GET | `/nifi-api/flow/reporting-task-types` | Retrieves the types of reporting tasks that this NiFi supports |  |
| `get_reporting_tasks` | GET | `/nifi-api/flow/reporting-tasks` | Gets all reporting tasks |  |
| `download_reporting_task_snapshot` | GET | `/nifi-api/flow/reporting-tasks/download` | Download a snapshot of the given reporting tasks and any controller services they use |  |
| `get_reporting_task_snapshot` | GET | `/nifi-api/flow/reporting-tasks/snapshot` | Get a snapshot of the given reporting tasks and any controller services they use |  |
| `get_runtime_manifest` | GET | `/nifi-api/flow/runtime-manifest` | Retrieves the runtime manifest for this NiFi instance. |  |
| `search_flow` | GET | `/nifi-api/flow/search-results` | Performs a search against this NiFi using the specified search term |  |
| `get_controller_status` | GET | `/nifi-api/flow/status` | Gets the current status of this NiFi |  |

## nifi_process_groups

37 tools.

- Product/version: Apache NiFi REST API 2.6.0 (Cloudera Flow Management 4.12 ships NiFi 2.6.0.4.12.x)
- Spec source: https://repo1.maven.org/maven2/org/apache/nifi/nifi-web-api/2.6.0/nifi-web-api-2.6.0.war (docs/rest-api/swagger.json, OpenAPI 3.0.1)
- Tags included: ProcessGroups, Snippets
- Auth: Base path /nifi-api. JWT bearer (HTTPBearerJWT / __Secure-Request-Token cookie) obtained via POST /access/token (LDAP/Kerberos login identity provider) or POST /access/kerberos (SPNEGO); mutual-TLS client certs; OIDC/SAML/Knox SSO. Via Knox: https://<knox>/gateway/cdp-proxy-api/nifi-app/nifi-api with Knox basic/JWT. Mutating requests on components need a revision object (version + clientId).
- Operation count: 37

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `delete_replace_process_group_request` | DELETE | `/nifi-api/process-groups/replace-requests/{id}` | Deletes the Replace Request with the given ID |  |
| `get_replace_process_group_request` | GET | `/nifi-api/process-groups/replace-requests/{id}` | Returns the Replace Request with the given ID |  |
| `remove_process_group` | DELETE | `/nifi-api/process-groups/{id}` | Deletes a process group |  |
| `get_process_group` | GET | `/nifi-api/process-groups/{id}` | Gets a process group |  |
| `update_process_group` | PUT | `/nifi-api/process-groups/{id}` | Updates a process group |  |
| `get_connections` | GET | `/nifi-api/process-groups/{id}/connections` | Gets all connections |  |
| `create_connection` | POST | `/nifi-api/process-groups/{id}/connections` | Creates a connection |  |
| `create_controller_service_1` | POST | `/nifi-api/process-groups/{id}/controller-services` | Creates a new controller service |  |
| `copy` | POST | `/nifi-api/process-groups/{id}/copy` | Generates a copy response for the given copy request |  |
| `export_process_group` | GET | `/nifi-api/process-groups/{id}/download` | Gets a process group for download |  |
| `create_empty_all_connections_request` | POST | `/nifi-api/process-groups/{id}/empty-all-connections-requests` | Creates a request to drop all flowfiles of all connection queues in this process group. |  |
| `remove_drop_request_1` | DELETE | `/nifi-api/process-groups/{id}/empty-all-connections-requests/{drop-request-id}` | Cancels and/or removes a request to drop all flowfiles. |  |
| `get_drop_all_flowfiles_request` | GET | `/nifi-api/process-groups/{id}/empty-all-connections-requests/{drop-request-id}` | Gets the current status of a drop all flowfiles request. |  |
| `replace_process_group` | PUT | `/nifi-api/process-groups/{id}/flow-contents` | Replace Process Group contents with the given ID with the specified Process Group contents |  |
| `get_funnels` | GET | `/nifi-api/process-groups/{id}/funnels` | Gets all funnels |  |
| `create_funnel` | POST | `/nifi-api/process-groups/{id}/funnels` | Creates a funnel |  |
| `get_input_ports` | GET | `/nifi-api/process-groups/{id}/input-ports` | Gets all input ports |  |
| `create_input_port` | POST | `/nifi-api/process-groups/{id}/input-ports` | Creates an input port |  |
| `get_labels` | GET | `/nifi-api/process-groups/{id}/labels` | Gets all labels |  |
| `create_label` | POST | `/nifi-api/process-groups/{id}/labels` | Creates a label |  |
| `get_local_modifications` | GET | `/nifi-api/process-groups/{id}/local-modifications` | Gets a list of local modifications to the Process Group since it was last synchronized with the Flow Registry |  |
| `get_output_ports` | GET | `/nifi-api/process-groups/{id}/output-ports` | Gets all output ports |  |
| `create_output_port` | POST | `/nifi-api/process-groups/{id}/output-ports` | Creates an output port |  |
| `paste` | PUT | `/nifi-api/process-groups/{id}/paste` | Pastes into the specified process group |  |
| `get_process_groups` | GET | `/nifi-api/process-groups/{id}/process-groups` | Gets all process groups |  |
| `create_process_group` | POST | `/nifi-api/process-groups/{id}/process-groups` | Creates a process group |  |
| `import_process_group` | POST | `/nifi-api/process-groups/{id}/process-groups/import` | Imports a specified process group |  |
| `upload_process_group` | POST | `/nifi-api/process-groups/{id}/process-groups/upload` | Uploads a versioned flow definition and creates a process group |  |
| `get_processors` | GET | `/nifi-api/process-groups/{id}/processors` | Gets all processors |  |
| `create_processor` | POST | `/nifi-api/process-groups/{id}/processors` | Creates a new processor |  |
| `get_remote_process_groups` | GET | `/nifi-api/process-groups/{id}/remote-process-groups` | Gets all remote process groups |  |
| `create_remote_process_group` | POST | `/nifi-api/process-groups/{id}/remote-process-groups` | Creates a new process group |  |
| `initiate_replace_process_group` | POST | `/nifi-api/process-groups/{id}/replace-requests` | Initiate the Replace Request of a Process Group with the given ID |  |
| `copy_snippet` | POST | `/nifi-api/process-groups/{id}/snippet-instance` | Copies a snippet and discards it. |  |
| `create_snippet` | POST | `/nifi-api/snippets` | Creates a snippet. |  |
| `delete_snippet` | DELETE | `/nifi-api/snippets/{id}` | Deletes the components in a snippet and discards the snippet |  |
| `update_snippet` | PUT | `/nifi-api/snippets/{id}` | Move's the components in this Snippet into a new Process Group and discards the snippet |  |

## nifi_versions

14 tools.

- Product/version: Apache NiFi REST API 2.6.0 (Cloudera Flow Management 4.12 ships NiFi 2.6.0.4.12.x)
- Spec source: https://repo1.maven.org/maven2/org/apache/nifi/nifi-web-api/2.6.0/nifi-web-api-2.6.0.war (docs/rest-api/swagger.json, OpenAPI 3.0.1)
- Tags included: Versions
- Auth: Base path /nifi-api. JWT bearer (HTTPBearerJWT / __Secure-Request-Token cookie) obtained via POST /access/token (LDAP/Kerberos login identity provider) or POST /access/kerberos (SPNEGO); mutual-TLS client certs; OIDC/SAML/Knox SSO. Via Knox: https://<knox>/gateway/cdp-proxy-api/nifi-app/nifi-api with Knox basic/JWT. Mutating requests on components need a revision object (version + clientId).
- Operation count: 14

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `create_version_control_request` | POST | `/nifi-api/versions/active-requests` | Create a version control request |  |
| `delete_version_control_request` | DELETE | `/nifi-api/versions/active-requests/{id}` | Deletes the version control request with the given ID |  |
| `update_version_control_request` | PUT | `/nifi-api/versions/active-requests/{id}` | Updates the request with the given ID |  |
| `stop_version_control` | DELETE | `/nifi-api/versions/process-groups/{id}` | Stops version controlling the Process Group with the given ID |  |
| `get_version_information` | GET | `/nifi-api/versions/process-groups/{id}` | Gets the Version Control information for a process group |  |
| `save_to_flow_registry` | POST | `/nifi-api/versions/process-groups/{id}` | Save the Process Group with the given ID |  |
| `update_flow_version` | PUT | `/nifi-api/versions/process-groups/{id}` | Update the version of a Process Group with the given ID |  |
| `export_flow_version` | GET | `/nifi-api/versions/process-groups/{id}/download` | Gets the latest version of a Process Group for download |  |
| `initiate_revert_flow_version` | POST | `/nifi-api/versions/revert-requests/process-groups/{id}` | Initiate the Revert Request of a Process Group with the given ID |  |
| `delete_revert_request` | DELETE | `/nifi-api/versions/revert-requests/{id}` | Deletes the Revert Request with the given ID |  |
| `get_revert_request` | GET | `/nifi-api/versions/revert-requests/{id}` | Returns the Revert Request with the given ID |  |
| `initiate_version_control_update` | POST | `/nifi-api/versions/update-requests/process-groups/{id}` | Initiate the Update Request of a Process Group with the given ID |  |
| `delete_update_request_1` | DELETE | `/nifi-api/versions/update-requests/{id}` | Deletes the Update Request with the given ID |  |
| `get_update_request` | GET | `/nifi-api/versions/update-requests/{id}` | Returns the Update Request with the given ID |  |

## nifi_processors

14 tools.

- Product/version: Apache NiFi REST API 2.6.0 (Cloudera Flow Management 4.12 ships NiFi 2.6.0.4.12.x)
- Spec source: https://repo1.maven.org/maven2/org/apache/nifi/nifi-web-api/2.6.0/nifi-web-api-2.6.0.war (docs/rest-api/swagger.json, OpenAPI 3.0.1)
- Tags included: Processors
- Auth: Base path /nifi-api. JWT bearer (HTTPBearerJWT / __Secure-Request-Token cookie) obtained via POST /access/token (LDAP/Kerberos login identity provider) or POST /access/kerberos (SPNEGO); mutual-TLS client certs; OIDC/SAML/Knox SSO. Via Knox: https://<knox>/gateway/cdp-proxy-api/nifi-app/nifi-api with Knox basic/JWT. Mutating requests on components need a revision object (version + clientId).
- Operation count: 14

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `get_processor_run_status_details` | POST | `/nifi-api/processors/run-status-details/queries` | Submits a query to retrieve the run status details of all processors that are in the given list of Processor IDs |  |
| `delete_processor` | DELETE | `/nifi-api/processors/{id}` | Deletes a processor |  |
| `get_processor` | GET | `/nifi-api/processors/{id}` | Gets a processor |  |
| `update_processor` | PUT | `/nifi-api/processors/{id}` | Updates a processor |  |
| `analyze_configuration_2` | POST | `/nifi-api/processors/{id}/config/analysis` | Performs analysis of the component's configuration, providing information about which attributes are referenced. |  |
| `submit_processor_verification_request` | POST | `/nifi-api/processors/{id}/config/verification-requests` | Performs verification of the Processor's configuration |  |
| `delete_verification_request_2` | DELETE | `/nifi-api/processors/{id}/config/verification-requests/{requestId}` | Deletes the Verification Request with the given ID |  |
| `get_verification_request_2` | GET | `/nifi-api/processors/{id}/config/verification-requests/{requestId}` | Returns the Verification Request with the given ID |  |
| `get_property_descriptor_3` | GET | `/nifi-api/processors/{id}/descriptors` | Gets the descriptor for a processor property |  |
| `get_processor_diagnostics` | GET | `/nifi-api/processors/{id}/diagnostics` | Gets diagnostics information about a processor |  |
| `update_run_status_4` | PUT | `/nifi-api/processors/{id}/run-status` | Updates run status of a processor |  |
| `get_state_2` | GET | `/nifi-api/processors/{id}/state` | Gets the state for a processor |  |
| `clear_state_3` | POST | `/nifi-api/processors/{id}/state/clear-requests` | Clears the state for a processor |  |
| `terminate_processor` | DELETE | `/nifi-api/processors/{id}/threads` | Terminates a processor, essentially "deleting" its threads and any active tasks |  |

## nifi_connections

25 tools.

- Product/version: Apache NiFi REST API 2.6.0 (Cloudera Flow Management 4.12 ships NiFi 2.6.0.4.12.x)
- Spec source: https://repo1.maven.org/maven2/org/apache/nifi/nifi-web-api/2.6.0/nifi-web-api-2.6.0.war (docs/rest-api/swagger.json, OpenAPI 3.0.1)
- Tags included: Connections, FlowFileQueues, Funnels, InputPorts, Labels, OutputPorts
- Auth: Base path /nifi-api. JWT bearer (HTTPBearerJWT / __Secure-Request-Token cookie) obtained via POST /access/token (LDAP/Kerberos login identity provider) or POST /access/kerberos (SPNEGO); mutual-TLS client certs; OIDC/SAML/Knox SSO. Via Knox: https://<knox>/gateway/cdp-proxy-api/nifi-app/nifi-api with Knox basic/JWT. Mutating requests on components need a revision object (version + clientId).
- Operation count: 25

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `delete_connection` | DELETE | `/nifi-api/connections/{id}` | Deletes a connection |  |
| `get_connection` | GET | `/nifi-api/connections/{id}` | Gets a connection |  |
| `update_connection` | PUT | `/nifi-api/connections/{id}` | Updates a connection |  |
| `create_drop_request` | POST | `/nifi-api/flowfile-queues/{id}/drop-requests` | Creates a request to drop the contents of the queue in this connection. |  |
| `remove_drop_request` | DELETE | `/nifi-api/flowfile-queues/{id}/drop-requests/{drop-request-id}` | Cancels and/or removes a request to drop the contents of this connection. |  |
| `get_drop_request` | GET | `/nifi-api/flowfile-queues/{id}/drop-requests/{drop-request-id}` | Gets the current status of a drop request for the specified connection. |  |
| `get_flow_file` | GET | `/nifi-api/flowfile-queues/{id}/flowfiles/{flowfile-uuid}` | Gets a FlowFile from a Connection. |  |
| `download_flow_file_content` | GET | `/nifi-api/flowfile-queues/{id}/flowfiles/{flowfile-uuid}/content` | Gets the content for a FlowFile in a Connection. |  |
| `create_flow_file_listing` | POST | `/nifi-api/flowfile-queues/{id}/listing-requests` | Lists the contents of the queue in this connection. |  |
| `delete_listing_request` | DELETE | `/nifi-api/flowfile-queues/{id}/listing-requests/{listing-request-id}` | Cancels and/or removes a request to list the contents of this connection. |  |
| `get_listing_request` | GET | `/nifi-api/flowfile-queues/{id}/listing-requests/{listing-request-id}` | Gets the current status of a listing request for the specified connection. |  |
| `remove_funnel` | DELETE | `/nifi-api/funnels/{id}` | Deletes a funnel |  |
| `get_funnel` | GET | `/nifi-api/funnels/{id}` | Gets a funnel |  |
| `update_funnel` | PUT | `/nifi-api/funnels/{id}` | Updates a funnel |  |
| `remove_input_port` | DELETE | `/nifi-api/input-ports/{id}` | Deletes an input port |  |
| `get_input_port` | GET | `/nifi-api/input-ports/{id}` | Gets an input port |  |
| `update_input_port` | PUT | `/nifi-api/input-ports/{id}` | Updates an input port |  |
| `update_run_status_2` | PUT | `/nifi-api/input-ports/{id}/run-status` | Updates run status of an input-port |  |
| `remove_label` | DELETE | `/nifi-api/labels/{id}` | Deletes a label |  |
| `get_label` | GET | `/nifi-api/labels/{id}` | Gets a label |  |
| `update_label` | PUT | `/nifi-api/labels/{id}` | Updates a label |  |
| `remove_output_port` | DELETE | `/nifi-api/output-ports/{id}` | Deletes an output port |  |
| `get_output_port` | GET | `/nifi-api/output-ports/{id}` | Gets an output port |  |
| `update_output_port` | PUT | `/nifi-api/output-ports/{id}` | Updates an output port |  |
| `update_run_status_3` | PUT | `/nifi-api/output-ports/{id}/run-status` | Updates run status of an output-port |  |

## nifi_remote_process_groups

19 tools.

- Product/version: Apache NiFi REST API 2.6.0 (Cloudera Flow Management 4.12 ships NiFi 2.6.0.4.12.x)
- Spec source: https://repo1.maven.org/maven2/org/apache/nifi/nifi-web-api/2.6.0/nifi-web-api-2.6.0.war (docs/rest-api/swagger.json, OpenAPI 3.0.1)
- Tags included: DataTransfer, RemoteProcessGroups, SiteToSite
- Auth: Base path /nifi-api. JWT bearer (HTTPBearerJWT / __Secure-Request-Token cookie) obtained via POST /access/token (LDAP/Kerberos login identity provider) or POST /access/kerberos (SPNEGO); mutual-TLS client certs; OIDC/SAML/Knox SSO. Via Knox: https://<knox>/gateway/cdp-proxy-api/nifi-app/nifi-api with Knox basic/JWT. Mutating requests on components need a revision object (version + clientId).
- Operation count: 19

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `commit_input_port_transaction` | DELETE | `/nifi-api/data-transfer/input-ports/{portId}/transactions/{transactionId}` | Commit or cancel the specified transaction |  |
| `extend_input_port_transaction_ttl` | PUT | `/nifi-api/data-transfer/input-ports/{portId}/transactions/{transactionId}` | Extend transaction TTL |  |
| `receive_flow_files` | POST | `/nifi-api/data-transfer/input-ports/{portId}/transactions/{transactionId}/flow-files` | Transfer flow files to the input port |  |
| `commit_output_port_transaction` | DELETE | `/nifi-api/data-transfer/output-ports/{portId}/transactions/{transactionId}` | Commit or cancel the specified transaction |  |
| `extend_output_port_transaction_ttl` | PUT | `/nifi-api/data-transfer/output-ports/{portId}/transactions/{transactionId}` | Extend transaction TTL |  |
| `transfer_flow_files` | GET | `/nifi-api/data-transfer/output-ports/{portId}/transactions/{transactionId}/flow-files` | Transfer flow files from the output port |  |
| `create_port_transaction` | POST | `/nifi-api/data-transfer/{portType}/{portId}/transactions` | Create a transaction to the specified output port or input port |  |
| `update_remote_process_group_run_statuses` | PUT | `/nifi-api/remote-process-groups/process-group/{id}/run-status` | Updates run status of all remote process groups in a process group (recursively) |  |
| `remove_remote_process_group` | DELETE | `/nifi-api/remote-process-groups/{id}` | Deletes a remote process group |  |
| `get_remote_process_group` | GET | `/nifi-api/remote-process-groups/{id}` | Gets a remote process group |  |
| `update_remote_process_group` | PUT | `/nifi-api/remote-process-groups/{id}` | Updates a remote process group |  |
| `update_remote_process_group_input_port` | PUT | `/nifi-api/remote-process-groups/{id}/input-ports/{port-id}` | Updates a remote port |  |
| `update_remote_process_group_input_port_run_status` | PUT | `/nifi-api/remote-process-groups/{id}/input-ports/{port-id}/run-status` | Updates run status of a remote port |  |
| `update_remote_process_group_output_port` | PUT | `/nifi-api/remote-process-groups/{id}/output-ports/{port-id}` | Updates a remote port |  |
| `update_remote_process_group_output_port_run_status` | PUT | `/nifi-api/remote-process-groups/{id}/output-ports/{port-id}/run-status` | Updates run status of a remote port |  |
| `update_remote_process_group_run_status` | PUT | `/nifi-api/remote-process-groups/{id}/run-status` | Updates run status of a remote process group |  |
| `get_state_3` | GET | `/nifi-api/remote-process-groups/{id}/state` | Gets the state for a RemoteProcessGroup |  |
| `get_site_to_site_details` | GET | `/nifi-api/site-to-site` | Returns the details about this NiFi necessary to communicate via site to site |  |
| `get_peers` | GET | `/nifi-api/site-to-site/peers` | Returns the available Peers and its status of this NiFi |  |

## nifi_controller_services

13 tools.

- Product/version: Apache NiFi REST API 2.6.0 (Cloudera Flow Management 4.12 ships NiFi 2.6.0.4.12.x)
- Spec source: https://repo1.maven.org/maven2/org/apache/nifi/nifi-web-api/2.6.0/nifi-web-api-2.6.0.war (docs/rest-api/swagger.json, OpenAPI 3.0.1)
- Tags included: Controller Services
- Auth: Base path /nifi-api. JWT bearer (HTTPBearerJWT / __Secure-Request-Token cookie) obtained via POST /access/token (LDAP/Kerberos login identity provider) or POST /access/kerberos (SPNEGO); mutual-TLS client certs; OIDC/SAML/Knox SSO. Via Knox: https://<knox>/gateway/cdp-proxy-api/nifi-app/nifi-api with Knox basic/JWT. Mutating requests on components need a revision object (version + clientId).
- Operation count: 13

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `remove_controller_service` | DELETE | `/nifi-api/controller-services/{id}` | Deletes a controller service |  |
| `get_controller_service` | GET | `/nifi-api/controller-services/{id}` | Gets a controller service |  |
| `update_controller_service` | PUT | `/nifi-api/controller-services/{id}` | Updates a controller service |  |
| `analyze_configuration` | POST | `/nifi-api/controller-services/{id}/config/analysis` | Performs analysis of the component's configuration, providing information about which attributes are referenced. |  |
| `submit_config_verification_request` | POST | `/nifi-api/controller-services/{id}/config/verification-requests` | Performs verification of the Controller Service's configuration |  |
| `delete_verification_request` | DELETE | `/nifi-api/controller-services/{id}/config/verification-requests/{requestId}` | Deletes the Verification Request with the given ID |  |
| `get_verification_request` | GET | `/nifi-api/controller-services/{id}/config/verification-requests/{requestId}` | Returns the Verification Request with the given ID |  |
| `get_property_descriptor_1` | GET | `/nifi-api/controller-services/{id}/descriptors` | Gets a controller service property descriptor |  |
| `get_controller_service_references` | GET | `/nifi-api/controller-services/{id}/references` | Gets a controller service |  |
| `update_controller_service_references` | PUT | `/nifi-api/controller-services/{id}/references` | Updates a controller services references |  |
| `update_run_status_1` | PUT | `/nifi-api/controller-services/{id}/run-status` | Updates run status of a controller service |  |
| `get_state` | GET | `/nifi-api/controller-services/{id}/state` | Gets the state for a controller service |  |
| `clear_state_1` | POST | `/nifi-api/controller-services/{id}/state/clear-requests` | Clears the state for a controller service |  |

## nifi_parameters

29 tools.

- Product/version: Apache NiFi REST API 2.6.0 (Cloudera Flow Management 4.12 ships NiFi 2.6.0.4.12.x)
- Spec source: https://repo1.maven.org/maven2/org/apache/nifi/nifi-web-api/2.6.0/nifi-web-api-2.6.0.war (docs/rest-api/swagger.json, OpenAPI 3.0.1)
- Tags included: ParameterContexts, ParameterProviders
- Auth: Base path /nifi-api. JWT bearer (HTTPBearerJWT / __Secure-Request-Token cookie) obtained via POST /access/token (LDAP/Kerberos login identity provider) or POST /access/kerberos (SPNEGO); mutual-TLS client certs; OIDC/SAML/Knox SSO. Via Knox: https://<knox>/gateway/cdp-proxy-api/nifi-app/nifi-api with Knox basic/JWT. Mutating requests on components need a revision object (version + clientId).
- Operation count: 29

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `create_parameter_context` | POST | `/nifi-api/parameter-contexts` | Create a Parameter Context |  |
| `get_assets` | GET | `/nifi-api/parameter-contexts/{contextId}/assets` | Lists the assets that belong to the Parameter Context with the given ID |  |
| `create_asset` | POST | `/nifi-api/parameter-contexts/{contextId}/assets` | Creates a new Asset in the given Parameter Context |  |
| `delete_asset` | DELETE | `/nifi-api/parameter-contexts/{contextId}/assets/{assetId}` | Deletes an Asset from the given Parameter Context |  |
| `get_asset_content` | GET | `/nifi-api/parameter-contexts/{contextId}/assets/{assetId}` | Retrieves the content of the asset with the given id |  |
| `submit_parameter_context_update` | POST | `/nifi-api/parameter-contexts/{contextId}/update-requests` | Initiate the Update Request of a Parameter Context |  |
| `delete_update_request` | DELETE | `/nifi-api/parameter-contexts/{contextId}/update-requests/{requestId}` | Deletes the Update Request with the given ID |  |
| `get_parameter_context_update` | GET | `/nifi-api/parameter-contexts/{contextId}/update-requests/{requestId}` | Returns the Update Request with the given ID |  |
| `submit_validation_request` | POST | `/nifi-api/parameter-contexts/{contextId}/validation-requests` | Initiate a Validation Request to determine how the validity of components will change if a Parameter Context were to be updated |  |
| `delete_validation_request` | DELETE | `/nifi-api/parameter-contexts/{contextId}/validation-requests/{id}` | Deletes the Validation Request with the given ID |  |
| `get_validation_request` | GET | `/nifi-api/parameter-contexts/{contextId}/validation-requests/{id}` | Returns the Validation Request with the given ID |  |
| `delete_parameter_context` | DELETE | `/nifi-api/parameter-contexts/{id}` | Deletes the Parameter Context with the given ID |  |
| `get_parameter_context` | GET | `/nifi-api/parameter-contexts/{id}` | Returns the Parameter Context with the given ID |  |
| `update_parameter_context` | PUT | `/nifi-api/parameter-contexts/{id}` | Modifies a Parameter Context |  |
| `remove_parameter_provider` | DELETE | `/nifi-api/parameter-providers/{id}` | Deletes a parameter provider |  |
| `get_parameter_provider` | GET | `/nifi-api/parameter-providers/{id}` | Gets a parameter provider |  |
| `update_parameter_provider` | PUT | `/nifi-api/parameter-providers/{id}` | Updates a parameter provider |  |
| `analyze_configuration_1` | POST | `/nifi-api/parameter-providers/{id}/config/analysis` | Performs analysis of the component's configuration, providing information about which attributes are referenced. |  |
| `submit_config_verification_request_1` | POST | `/nifi-api/parameter-providers/{id}/config/verification-requests` | Performs verification of the Parameter Provider's configuration |  |
| `delete_verification_request_1` | DELETE | `/nifi-api/parameter-providers/{id}/config/verification-requests/{requestId}` | Deletes the Verification Request with the given ID |  |
| `get_verification_request_1` | GET | `/nifi-api/parameter-providers/{id}/config/verification-requests/{requestId}` | Returns the Verification Request with the given ID |  |
| `get_property_descriptor_2` | GET | `/nifi-api/parameter-providers/{id}/descriptors` | Gets a parameter provider property descriptor |  |
| `fetch_parameters` | POST | `/nifi-api/parameter-providers/{id}/parameters/fetch-requests` | Fetches and temporarily caches the parameters for a provider |  |
| `get_parameter_provider_references` | GET | `/nifi-api/parameter-providers/{id}/references` | Gets all references to a parameter provider |  |
| `get_state_1` | GET | `/nifi-api/parameter-providers/{id}/state` | Gets the state for a parameter provider |  |
| `clear_state_2` | POST | `/nifi-api/parameter-providers/{id}/state/clear-requests` | Clears the state for a parameter provider |  |
| `submit_apply_parameters` | POST | `/nifi-api/parameter-providers/{providerId}/apply-parameters-requests` | Initiate a request to apply the fetched parameters of a Parameter Provider |  |
| `delete_apply_parameters_request` | DELETE | `/nifi-api/parameter-providers/{providerId}/apply-parameters-requests/{requestId}` | Deletes the Apply Parameters Request with the given ID |  |
| `get_parameter_provider_apply_parameters_request` | GET | `/nifi-api/parameter-providers/{providerId}/apply-parameters-requests/{requestId}` | Returns the Apply Parameters Request with the given ID |  |

## nifi_reporting_tasks

11 tools.

- Product/version: Apache NiFi REST API 2.6.0 (Cloudera Flow Management 4.12 ships NiFi 2.6.0.4.12.x)
- Spec source: https://repo1.maven.org/maven2/org/apache/nifi/nifi-web-api/2.6.0/nifi-web-api-2.6.0.war (docs/rest-api/swagger.json, OpenAPI 3.0.1)
- Tags included: ReportingTasks
- Auth: Base path /nifi-api. JWT bearer (HTTPBearerJWT / __Secure-Request-Token cookie) obtained via POST /access/token (LDAP/Kerberos login identity provider) or POST /access/kerberos (SPNEGO); mutual-TLS client certs; OIDC/SAML/Knox SSO. Via Knox: https://<knox>/gateway/cdp-proxy-api/nifi-app/nifi-api with Knox basic/JWT. Mutating requests on components need a revision object (version + clientId).
- Operation count: 11

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `remove_reporting_task` | DELETE | `/nifi-api/reporting-tasks/{id}` | Deletes a reporting task |  |
| `get_reporting_task` | GET | `/nifi-api/reporting-tasks/{id}` | Gets a reporting task |  |
| `update_reporting_task` | PUT | `/nifi-api/reporting-tasks/{id}` | Updates a reporting task |  |
| `analyze_configuration_3` | POST | `/nifi-api/reporting-tasks/{id}/config/analysis` | Performs analysis of the component's configuration, providing information about which attributes are referenced. |  |
| `submit_config_verification_request_2` | POST | `/nifi-api/reporting-tasks/{id}/config/verification-requests` | Performs verification of the Reporting Task's configuration |  |
| `delete_verification_request_3` | DELETE | `/nifi-api/reporting-tasks/{id}/config/verification-requests/{requestId}` | Deletes the Verification Request with the given ID |  |
| `get_verification_request_3` | GET | `/nifi-api/reporting-tasks/{id}/config/verification-requests/{requestId}` | Returns the Verification Request with the given ID |  |
| `get_property_descriptor_4` | GET | `/nifi-api/reporting-tasks/{id}/descriptors` | Gets a reporting task property descriptor |  |
| `update_run_status_5` | PUT | `/nifi-api/reporting-tasks/{id}/run-status` | Updates run status of a reporting task |  |
| `get_state_4` | GET | `/nifi-api/reporting-tasks/{id}/state` | Gets the state for a reporting task |  |
| `clear_state_4` | POST | `/nifi-api/reporting-tasks/{id}/state/clear-requests` | Clears the state for a reporting task |  |

## nifi_provenance

13 tools.

- Product/version: Apache NiFi REST API 2.6.0 (Cloudera Flow Management 4.12 ships NiFi 2.6.0.4.12.x)
- Spec source: https://repo1.maven.org/maven2/org/apache/nifi/nifi-web-api/2.6.0/nifi-web-api-2.6.0.war (docs/rest-api/swagger.json, OpenAPI 3.0.1)
- Tags included: Provenance, ProvenanceEvents
- Auth: Base path /nifi-api. JWT bearer (HTTPBearerJWT / __Secure-Request-Token cookie) obtained via POST /access/token (LDAP/Kerberos login identity provider) or POST /access/kerberos (SPNEGO); mutual-TLS client certs; OIDC/SAML/Knox SSO. Via Knox: https://<knox>/gateway/cdp-proxy-api/nifi-app/nifi-api with Knox basic/JWT. Mutating requests on components need a revision object (version + clientId).
- Operation count: 13

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `submit_provenance_request` | POST | `/nifi-api/provenance` | Submits a provenance query |  |
| `submit_replay_latest_event` | POST | `/nifi-api/provenance-events/latest/replays` | Replays content from a provenance event |  |
| `get_latest_provenance_events` | GET | `/nifi-api/provenance-events/latest/{componentId}` | Retrieves the latest cached Provenance Events for the specified component |  |
| `submit_replay` | POST | `/nifi-api/provenance-events/replays` | Replays content from a provenance event |  |
| `get_provenance_event` | GET | `/nifi-api/provenance-events/{id}` | Gets a provenance event |  |
| `get_input_content` | GET | `/nifi-api/provenance-events/{id}/content/input` | Gets the input content for a provenance event |  |
| `get_output_content` | GET | `/nifi-api/provenance-events/{id}/content/output` | Gets the output content for a provenance event |  |
| `submit_lineage_request` | POST | `/nifi-api/provenance/lineage` | Submits a lineage query |  |
| `delete_lineage` | DELETE | `/nifi-api/provenance/lineage/{id}` | Deletes a lineage query |  |
| `get_lineage` | GET | `/nifi-api/provenance/lineage/{id}` | Gets a lineage query |  |
| `get_search_options` | GET | `/nifi-api/provenance/search-options` | Gets the searchable attributes for provenance events |  |
| `delete_provenance` | DELETE | `/nifi-api/provenance/{id}` | Deletes a provenance query |  |
| `get_provenance` | GET | `/nifi-api/provenance/{id}` | Gets a provenance query |  |

## nifi_security

21 tools.

- Product/version: Apache NiFi REST API 2.6.0 (Cloudera Flow Management 4.12 ships NiFi 2.6.0.4.12.x)
- Spec source: https://repo1.maven.org/maven2/org/apache/nifi/nifi-web-api/2.6.0/nifi-web-api-2.6.0.war (docs/rest-api/swagger.json, OpenAPI 3.0.1)
- Tags included: Access, Authentication, Policies, Resources, Tenants
- Auth: Base path /nifi-api. JWT bearer (HTTPBearerJWT / __Secure-Request-Token cookie) obtained via POST /access/token (LDAP/Kerberos login identity provider) or POST /access/kerberos (SPNEGO); mutual-TLS client certs; OIDC/SAML/Knox SSO. Via Knox: https://<knox>/gateway/cdp-proxy-api/nifi-app/nifi-api with Knox basic/JWT. Mutating requests on components need a revision object (version + clientId).
- Operation count: 21

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `log_out` | DELETE | `/nifi-api/access/logout` | Performs a logout for other providers that have been issued a JWT. |  |
| `log_out_complete` | GET | `/nifi-api/access/logout/complete` | Completes the logout sequence by removing the cached Logout Request and Cookie if they existed and redirects to /nifi/login. |  |
| `create_access_token` | POST | `/nifi-api/access/token` | Creates a token for accessing the REST API via username/password |  |
| `get_authentication_configuration` | GET | `/nifi-api/authentication/configuration` | Retrieves the authentication configuration endpoint and status information |  |
| `create_access_policy` | POST | `/nifi-api/policies` | Creates an access policy |  |
| `get_access_policy_for_resource` | GET | `/nifi-api/policies/{action}/{resource}` | Gets an access policy for the specified action and resource |  |
| `remove_access_policy` | DELETE | `/nifi-api/policies/{id}` | Deletes an access policy |  |
| `get_access_policy` | GET | `/nifi-api/policies/{id}` | Gets an access policy |  |
| `update_access_policy` | PUT | `/nifi-api/policies/{id}` | Updates a access policy |  |
| `get_resources` | GET | `/nifi-api/resources` | Gets the available resources that support access/authorization policies |  |
| `search_tenants` | GET | `/nifi-api/tenants/search-results` | Searches for a tenant with the specified identity |  |
| `get_user_groups` | GET | `/nifi-api/tenants/user-groups` | Gets all user groups |  |
| `create_user_group` | POST | `/nifi-api/tenants/user-groups` | Creates a user group |  |
| `remove_user_group` | DELETE | `/nifi-api/tenants/user-groups/{id}` | Deletes a user group |  |
| `get_user_group` | GET | `/nifi-api/tenants/user-groups/{id}` | Gets a user group |  |
| `update_user_group` | PUT | `/nifi-api/tenants/user-groups/{id}` | Updates a user group |  |
| `get_users` | GET | `/nifi-api/tenants/users` | Gets all users |  |
| `create_user` | POST | `/nifi-api/tenants/users` | Creates a user |  |
| `remove_user` | DELETE | `/nifi-api/tenants/users/{id}` | Deletes a user |  |
| `get_user` | GET | `/nifi-api/tenants/users/{id}` | Gets a user |  |
| `update_user` | PUT | `/nifi-api/tenants/users/{id}` | Updates a user |  |

## nifi_controller

44 tools.

- Product/version: Apache NiFi REST API 2.6.0 (Cloudera Flow Management 4.12 ships NiFi 2.6.0.4.12.x)
- Spec source: https://repo1.maven.org/maven2/org/apache/nifi/nifi-web-api/2.6.0/nifi-web-api-2.6.0.war (docs/rest-api/swagger.json, OpenAPI 3.0.1)
- Tags included: Controller, Counters, SystemDiagnostics
- Auth: Base path /nifi-api. JWT bearer (HTTPBearerJWT / __Secure-Request-Token cookie) obtained via POST /access/token (LDAP/Kerberos login identity provider) or POST /access/kerberos (SPNEGO); mutual-TLS client certs; OIDC/SAML/Knox SSO. Via Knox: https://<knox>/gateway/cdp-proxy-api/nifi-app/nifi-api with Knox basic/JWT. Mutating requests on components need a revision object (version + clientId).
- Operation count: 44

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `create_bulletin` | POST | `/nifi-api/controller/bulletin` | Creates a new bulletin |  |
| `get_cluster` | GET | `/nifi-api/controller/cluster` | Gets the contents of the cluster |  |
| `delete_node` | DELETE | `/nifi-api/controller/cluster/nodes/{id}` | Removes a node from the cluster |  |
| `get_node` | GET | `/nifi-api/controller/cluster/nodes/{id}` | Gets a node in the cluster |  |
| `update_node` | PUT | `/nifi-api/controller/cluster/nodes/{id}` | Updates a node in the cluster |  |
| `get_controller_config` | GET | `/nifi-api/controller/config` | Retrieves the configuration for this NiFi Controller |  |
| `update_controller_config` | PUT | `/nifi-api/controller/config` | Retrieves the configuration for this NiFi |  |
| `create_controller_service` | POST | `/nifi-api/controller/controller-services` | Creates a new controller service |  |
| `get_flow_analysis_rules` | GET | `/nifi-api/controller/flow-analysis-rules` | Gets all flow analysis rules |  |
| `create_flow_analysis_rule` | POST | `/nifi-api/controller/flow-analysis-rules` | Creates a new flow analysis rule |  |
| `remove_flow_analysis_rule` | DELETE | `/nifi-api/controller/flow-analysis-rules/{id}` | Deletes a flow analysis rule |  |
| `get_flow_analysis_rule` | GET | `/nifi-api/controller/flow-analysis-rules/{id}` | Gets a flow analysis rule |  |
| `update_flow_analysis_rule` | PUT | `/nifi-api/controller/flow-analysis-rules/{id}` | Updates a flow analysis rule |  |
| `analyze_flow_analysis_rule_configuration` | POST | `/nifi-api/controller/flow-analysis-rules/{id}/config/analysis` | Performs analysis of the component's configuration, providing information about which attributes are referenced. |  |
| `submit_flow_analysis_rule_config_verification_request` | POST | `/nifi-api/controller/flow-analysis-rules/{id}/config/verification-requests` | Performs verification of the Flow Analysis Rule's configuration |  |
| `delete_flow_analysis_rule_verification_request` | DELETE | `/nifi-api/controller/flow-analysis-rules/{id}/config/verification-requests/{requestId}` | Deletes the Verification Request with the given ID |  |
| `get_flow_analysis_rule_verification_request` | GET | `/nifi-api/controller/flow-analysis-rules/{id}/config/verification-requests/{requestId}` | Returns the Verification Request with the given ID |  |
| `get_flow_analysis_rule_property_descriptor` | GET | `/nifi-api/controller/flow-analysis-rules/{id}/descriptors` | Gets a flow analysis rule property descriptor |  |
| `update_run_status` | PUT | `/nifi-api/controller/flow-analysis-rules/{id}/run-status` | Updates run status of a flow analysis rule |  |
| `get_flow_analysis_rule_state` | GET | `/nifi-api/controller/flow-analysis-rules/{id}/state` | Gets the state for a flow analysis rule |  |
| `clear_state` | POST | `/nifi-api/controller/flow-analysis-rules/{id}/state/clear-requests` | Clears the state for a flow analysis rule |  |
| `delete_history` | DELETE | `/nifi-api/controller/history` | Purges history |  |
| `get_nar_summaries` | GET | `/nifi-api/controller/nar-manager/nars` | Retrieves summary information for installed NARs |  |
| `upload_nar` | POST | `/nifi-api/controller/nar-manager/nars/content` | Uploads a NAR and requests for it to be installed |  |
| `delete_nar` | DELETE | `/nifi-api/controller/nar-manager/nars/{id}` | Deletes an installed NAR |  |
| `get_nar_summary` | GET | `/nifi-api/controller/nar-manager/nars/{id}` | Retrieves the summary information for the NAR with the given identifier |  |
| `download_nar` | GET | `/nifi-api/controller/nar-manager/nars/{id}/content` | Retrieves the content of the NAR with the given id |  |
| `get_nar_details` | GET | `/nifi-api/controller/nar-manager/nars/{id}/details` | Retrieves the component types available from the installed NARs |  |
| `create_parameter_provider` | POST | `/nifi-api/controller/parameter-providers` | Creates a new parameter provider |  |
| `get_flow_registry_clients` | GET | `/nifi-api/controller/registry-clients` | Gets the listing of available flow registry clients |  |
| `create_flow_registry_client` | POST | `/nifi-api/controller/registry-clients` | Creates a new flow registry client |  |
| `delete_flow_registry_client` | DELETE | `/nifi-api/controller/registry-clients/{id}` | Deletes a flow registry client |  |
| `get_flow_registry_client` | GET | `/nifi-api/controller/registry-clients/{id}` | Gets a flow registry client |  |
| `update_flow_registry_client` | PUT | `/nifi-api/controller/registry-clients/{id}` | Updates a flow registry client |  |
| `get_property_descriptor` | GET | `/nifi-api/controller/registry-clients/{id}/descriptors` | Gets a flow registry client property descriptor |  |
| `get_registry_client_types` | GET | `/nifi-api/controller/registry-types` | Retrieves the types of flow that this NiFi supports |  |
| `create_reporting_task` | POST | `/nifi-api/controller/reporting-tasks` | Creates a new reporting task |  |
| `import_reporting_task_snapshot` | POST | `/nifi-api/controller/reporting-tasks/import` | Imports a reporting task snapshot |  |
| `get_node_status_history` | GET | `/nifi-api/controller/status/history` | Gets status history for the node |  |
| `get_counters` | GET | `/nifi-api/counters` | Gets the current counters for this NiFi |  |
| `update_all_counters` | PUT | `/nifi-api/counters` | Updates all counters. |  |
| `update_counter` | PUT | `/nifi-api/counters/{id}` | Updates the specified counter. |  |
| `get_system_diagnostics` | GET | `/nifi-api/system-diagnostics` | Gets the diagnostics for the system NiFi is running on |  |
| `get_jmx_metrics` | GET | `/nifi-api/system-diagnostics/jmx-metrics` | Retrieve available JMX metrics |  |

## nifi_registry_extensions

29 tools.

- Product/version: Apache NiFi Registry REST API 2.6.0 (CFM 4.12 ships NiFi Registry 2.6.0.4.12.x)
- Spec source: https://repo1.maven.org/maven2/org/apache/nifi/registry/nifi-registry-web-api/2.6.0/nifi-registry-web-api-2.6.0.war (docs/rest-api/swagger.json, OpenAPI 3.0.1)
- Tags included: BucketBundles, Bundles, ExtensionRepository, Extensions
- Auth: Base path /nifi-registry-api. Bearer JWT from POST /access/token/login (basic creds via LDAP/Kerberos identity provider), POST /access/token/kerberos (SPNEGO); mutual TLS; Knox: /gateway/cdp-proxy-api/nifi-registry-app/nifi-registry-api.
- Operation count: 29

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `get_extension_bundles` | GET | `/nifi-registry-api/buckets/{bucketId}/bundles` | Get extension bundles by bucket |  |
| `create_extension_bundle_version` | POST | `/nifi-registry-api/buckets/{bucketId}/bundles/{bundleType}` | Create extension bundle version |  |
| `get_bundles` | GET | `/nifi-registry-api/bundles` | Get all bundles |  |
| `get_bundle_versions_1` | GET | `/nifi-registry-api/bundles/versions` | Get all bundle versions |  |
| `delete_bundle` | DELETE | `/nifi-registry-api/bundles/{bundleId}` | Delete bundle |  |
| `get_bundle` | GET | `/nifi-registry-api/bundles/{bundleId}` | Get bundle |  |
| `get_bundle_versions` | GET | `/nifi-registry-api/bundles/{bundleId}/versions` | Get bundle versions |  |
| `delete_bundle_version` | DELETE | `/nifi-registry-api/bundles/{bundleId}/versions/{version}` | Delete bundle version |  |
| `get_bundle_version` | GET | `/nifi-registry-api/bundles/{bundleId}/versions/{version}` | Get bundle version |  |
| `get_bundle_version_content` | GET | `/nifi-registry-api/bundles/{bundleId}/versions/{version}/content` | Get bundle version content |  |
| `get_bundle_version_extensions` | GET | `/nifi-registry-api/bundles/{bundleId}/versions/{version}/extensions` | Get bundle version extensions |  |
| `get_bundle_version_extension` | GET | `/nifi-registry-api/bundles/{bundleId}/versions/{version}/extensions/{name}` | Get bundle version extension |  |
| `get_bundle_version_extension_docs` | GET | `/nifi-registry-api/bundles/{bundleId}/versions/{version}/extensions/{name}/docs` | Get bundle version extension docs |  |
| `get_bundle_version_extension_additional_details_docs` | GET | `/nifi-registry-api/bundles/{bundleId}/versions/{version}/extensions/{name}/docs/additional-details` | Get bundle version extension docs details |  |
| `get_extension_repo_buckets` | GET | `/nifi-registry-api/extension-repository` | Get extension repo buckets |  |
| `get_extension_repo_groups` | GET | `/nifi-registry-api/extension-repository/{bucketName}` | Get extension repo groups |  |
| `get_extension_repo_artifacts` | GET | `/nifi-registry-api/extension-repository/{bucketName}/{groupId}` | Get extension repo artifacts |  |
| `get_extension_repo_versions` | GET | `/nifi-registry-api/extension-repository/{bucketName}/{groupId}/{artifactId}` | Get extension repo versions |  |
| `get_extension_repo_version` | GET | `/nifi-registry-api/extension-repository/{bucketName}/{groupId}/{artifactId}/{version}` | Get extension repo version |  |
| `get_extension_repo_version_content` | GET | `/nifi-registry-api/extension-repository/{bucketName}/{groupId}/{artifactId}/{version}/content` | Get extension repo version content |  |
| `get_extension_repo_version_extensions` | GET | `/nifi-registry-api/extension-repository/{bucketName}/{groupId}/{artifactId}/{version}/extensions` | Get extension repo extensions |  |
| `get_extension_repo_version_extension` | GET | `/nifi-registry-api/extension-repository/{bucketName}/{groupId}/{artifactId}/{version}/extensions/{name}` | Get extension repo extension |  |
| `get_extension_repo_version_extension_docs` | GET | `/nifi-registry-api/extension-repository/{bucketName}/{groupId}/{artifactId}/{version}/extensions/{name}/docs` | Get extension repo extension docs |  |
| `get_extension_repo_version_extension_additional_details_docs` | GET | `/nifi-registry-api/extension-repository/{bucketName}/{groupId}/{artifactId}/{version}/extensions/{name}/docs/additional-details` | Get extension repo extension details |  |
| `get_extension_repo_version_sha256` | GET | `/nifi-registry-api/extension-repository/{bucketName}/{groupId}/{artifactId}/{version}/sha256` | Get extension repo version checksum |  |
| `get_global_extension_repo_version_sha256` | GET | `/nifi-registry-api/extension-repository/{groupId}/{artifactId}/{version}/sha256` | Get global extension repo version checksum |  |
| `get_extensions` | GET | `/nifi-registry-api/extensions` | Get all extensions |  |
| `get_extensions_providing_service_api` | GET | `/nifi-registry-api/extensions/provided-service-api` | Get extensions providing service API |  |
| `get_tags` | GET | `/nifi-registry-api/extensions/tags` | Get extension tags |  |

## nifi_registry_security

31 tools.

- Product/version: Apache NiFi Registry REST API 2.6.0 (CFM 4.12 ships NiFi Registry 2.6.0.4.12.x)
- Spec source: https://repo1.maven.org/maven2/org/apache/nifi/registry/nifi-registry-web-api/2.6.0/nifi-registry-web-api-2.6.0.war (docs/rest-api/swagger.json, OpenAPI 3.0.1)
- Tags included: Access, Policies, Tenants
- Auth: Base path /nifi-registry-api. Bearer JWT from POST /access/token/login (basic creds via LDAP/Kerberos identity provider), POST /access/token/kerberos (SPNEGO); mutual TLS; Knox: /gateway/cdp-proxy-api/nifi-registry-app/nifi-registry-api.
- Operation count: 31

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `get_access_status` | GET | `/nifi-registry-api/access` | Get access status |  |
| `logout` | DELETE | `/nifi-registry-api/access/logout` | Performs a logout for other providers that have been issued a JWT. |  |
| `logout_complete` | GET | `/nifi-registry-api/access/logout/complete` | Completes the logout sequence. |  |
| `oidc_callback` | GET | `/nifi-registry-api/access/oidc/callback` | Redirect/callback URI for processing the result of the OpenId Connect login sequence. |  |
| `oidc_exchange` | POST | `/nifi-registry-api/access/oidc/exchange` | Retrieves a JWT following a successful login sequence using the configured OpenId Connect provider. |  |
| `oidc_logout` | GET | `/nifi-registry-api/access/oidc/logout` | Performs a logout in the OpenId Provider. |  |
| `oidc_logout_callback` | GET | `/nifi-registry-api/access/oidc/logout/callback` | Redirect/callback URI for processing the result of the OpenId Connect logout sequence. |  |
| `oidc_request` | GET | `/nifi-registry-api/access/oidc/request` | Initiates a request to authenticate through the configured OpenId Connect provider. |  |
| `create_access_token_by_trying_all_providers` | POST | `/nifi-registry-api/access/token` | Create token trying all providers |  |
| `create_access_token_using_identity_provider_credentials` | POST | `/nifi-registry-api/access/token/identity-provider` | Create token using identity provider |  |
| `test_identity_provider_recognizes_credentials_format` | POST | `/nifi-registry-api/access/token/identity-provider/test` | Test identity provider |  |
| `get_identity_provider_usage_instructions` | GET | `/nifi-registry-api/access/token/identity-provider/usage` | Get identity provider usage |  |
| `create_access_token_using_kerberos_ticket` | POST | `/nifi-registry-api/access/token/kerberos` | Create token using kerberos |  |
| `create_access_token_using_basic_auth_credentials` | POST | `/nifi-registry-api/access/token/login` | Create token using basic auth |  |
| `get_access_policies` | GET | `/nifi-registry-api/policies` | Get all access policies |  |
| `create_access_policy` | POST | `/nifi-registry-api/policies` | Create access policy |  |
| `get_resources` | GET | `/nifi-registry-api/policies/resources` | Get available resources |  |
| `get_access_policy_for_resource` | GET | `/nifi-registry-api/policies/{action}/{resource}` | Get access policy for resource |  |
| `remove_access_policy` | DELETE | `/nifi-registry-api/policies/{id}` | Delete access policy |  |
| `get_access_policy` | GET | `/nifi-registry-api/policies/{id}` | Get access policy |  |
| `update_access_policy` | PUT | `/nifi-registry-api/policies/{id}` | Update access policy |  |
| `get_user_groups` | GET | `/nifi-registry-api/tenants/user-groups` | Get user groups |  |
| `create_user_group` | POST | `/nifi-registry-api/tenants/user-groups` | Create user group |  |
| `remove_user_group` | DELETE | `/nifi-registry-api/tenants/user-groups/{id}` | Delete user group |  |
| `get_user_group` | GET | `/nifi-registry-api/tenants/user-groups/{id}` | Get user group |  |
| `update_user_group` | PUT | `/nifi-registry-api/tenants/user-groups/{id}` | Update user group |  |
| `get_users` | GET | `/nifi-registry-api/tenants/users` | Get all users |  |
| `create_user` | POST | `/nifi-registry-api/tenants/users` | Create user |  |
| `remove_user` | DELETE | `/nifi-registry-api/tenants/users/{id}` | Delete user |  |
| `get_user` | GET | `/nifi-registry-api/tenants/users/{id}` | Get user |  |
| `update_user` | PUT | `/nifi-registry-api/tenants/users/{id}` | Update user |  |

## nifi_registry

30 tools.

- Product/version: Apache NiFi Registry REST API 2.6.0 (CFM 4.12 ships NiFi Registry 2.6.0.4.12.x)
- Spec source: https://repo1.maven.org/maven2/org/apache/nifi/registry/nifi-registry-web-api/2.6.0/nifi-registry-web-api-2.6.0.war (docs/rest-api/swagger.json, OpenAPI 3.0.1)
- Tags included: About, BucketFlows, Buckets, Config, Flows, Items
- Auth: Base path /nifi-registry-api. Bearer JWT from POST /access/token/login (basic creds via LDAP/Kerberos identity provider), POST /access/token/kerberos (SPNEGO); mutual TLS; Knox: /gateway/cdp-proxy-api/nifi-registry-app/nifi-registry-api.
- Operation count: 30

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `get_version` | GET | `/nifi-registry-api/about` | Get version |  |
| `get_buckets` | GET | `/nifi-registry-api/buckets` | Get all buckets |  |
| `create_bucket` | POST | `/nifi-registry-api/buckets` | Create bucket |  |
| `get_available_bucket_fields` | GET | `/nifi-registry-api/buckets/fields` | Get bucket fields |  |
| `delete_bucket` | DELETE | `/nifi-registry-api/buckets/{bucketId}` | Delete bucket |  |
| `get_bucket` | GET | `/nifi-registry-api/buckets/{bucketId}` | Get bucket |  |
| `update_bucket` | PUT | `/nifi-registry-api/buckets/{bucketId}` | Update bucket |  |
| `get_flows` | GET | `/nifi-registry-api/buckets/{bucketId}/flows` | Get bucket flows |  |
| `create_flow` | POST | `/nifi-registry-api/buckets/{bucketId}/flows` | Create flow |  |
| `delete_flow` | DELETE | `/nifi-registry-api/buckets/{bucketId}/flows/{flowId}` | Delete bucket flow |  |
| `get_flow` | GET | `/nifi-registry-api/buckets/{bucketId}/flows/{flowId}` | Get bucket flow |  |
| `update_flow` | PUT | `/nifi-registry-api/buckets/{bucketId}/flows/{flowId}` | Update bucket flow |  |
| `get_flow_diff` | GET | `/nifi-registry-api/buckets/{bucketId}/flows/{flowId}/diff/{versionA}/{versionB}` | Get bucket flow diff |  |
| `get_flow_versions` | GET | `/nifi-registry-api/buckets/{bucketId}/flows/{flowId}/versions` | Get bucket flow versions |  |
| `create_flow_version` | POST | `/nifi-registry-api/buckets/{bucketId}/flows/{flowId}/versions` | Create flow version |  |
| `import_versioned_flow` | POST | `/nifi-registry-api/buckets/{bucketId}/flows/{flowId}/versions/import` | Import flow version |  |
| `get_latest_flow_version` | GET | `/nifi-registry-api/buckets/{bucketId}/flows/{flowId}/versions/latest` | Get latest bucket flow version content |  |
| `get_latest_flow_version_metadata` | GET | `/nifi-registry-api/buckets/{bucketId}/flows/{flowId}/versions/latest/metadata` | Get latest bucket flow version metadata |  |
| `get_flow_version` | GET | `/nifi-registry-api/buckets/{bucketId}/flows/{flowId}/versions/{versionNumber}` | Get bucket flow version |  |
| `export_versioned_flow` | GET | `/nifi-registry-api/buckets/{bucketId}/flows/{flowId}/versions/{versionNumber}/export` | Exports specified bucket flow version content |  |
| `get_configuration` | GET | `/nifi-registry-api/config` | Get configration |  |
| `get_available_flow_fields` | GET | `/nifi-registry-api/flows/fields` | Get flow fields |  |
| `get_flow_1` | GET | `/nifi-registry-api/flows/{flowId}` | Get flow |  |
| `get_flow_versions_1` | GET | `/nifi-registry-api/flows/{flowId}/versions` | Get flow versions |  |
| `get_latest_flow_version_1` | GET | `/nifi-registry-api/flows/{flowId}/versions/latest` | Get latest flow version |  |
| `get_latest_flow_version_metadata_1` | GET | `/nifi-registry-api/flows/{flowId}/versions/latest/metadata` | Get latest flow version metadata |  |
| `get_flow_version_1` | GET | `/nifi-registry-api/flows/{flowId}/versions/{versionNumber}` | Get flow version |  |
| `get_items` | GET | `/nifi-registry-api/items` | Get all items |  |
| `get_available_bucket_item_fields` | GET | `/nifi-registry-api/items/fields` | Get item fields |  |
| `get_items_1` | GET | `/nifi-registry-api/items/{bucketId}` | Get bucket items |  |

## schema_registry

53 tools. **Partial source:** from HTML reference pages; may be incomplete.

- Product/version: Cloudera Schema Registry REST API (Cloudera Runtime 7.3.2)
- Spec source: https://docs.cloudera.com/cdp-private-cloud-base/7.3.2/sr-rest-api-reference/index.html - from HTML docs (swagger-codegen html2 page generated from the service swagger; complete for that doc build, but no raw spec was published; may be partial vs. newer service builds). Live spec: http(s)://<host>:7788/swagger.json (7790 TLS).
- Tags included: Apiv1schemaregistry, Class1Schema, Class2SerializerDeserializer, Class3ExportImport, Class4Other, Class5ConfluentSchemaRegistryCompatibleAPI, Class6Atlas
- Auth: Base path /api/v1. Kerberos SPNEGO (curl --negotiate) or Knox (/gateway/cdp-proxy-api/schema-registry/api/v1, basic or JWT). Ranger authorization. Confluent-compatible endpoints under /api/v1/confluent.
- Operation count: 53

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `invalidate_cache` | POST | `/api/v1/schemaregistry/cache/{cacheType}/invalidate` | Address HA requirements with cache synchronization. |  |
| `options` | OPTIONS | `/api/v1/schemaregistry` | (no summary in source) options |  |
| `add_schema_info` | POST | `/api/v1/schemaregistry/schemas` | Create a schema metadata if it does not already exist |  |
| `add_schema_version` | POST | `/api/v1/schemaregistry/schemas/{name}/versions` | Register a new version of the schema |  |
| `archive_schema` | POST | `/api/v1/schemaregistry/schemas/versions/{id}/state/archive` | Archives version of the schema identified by the given version id |  |
| `check_compatibility_with_schema1` | POST | `/api/v1/schemaregistry/schemas/{name}/compatibility` | Checks if the given schema text is compatible with all the versions of the schema identified by the name |  |
| `create_schema_branch` | POST | `/api/v1/schemaregistry/schemas/versionsById/{versionId}/branch` | Fork a new schema branch given its schema name and version id |  |
| `delete_schema` | POST | `/api/v1/schemaregistry/schemas/versions/{id}/state/delete` | Deletes version of the schema identified by the given version id |  |
| `delete_schema_branch` | DELETE | `/api/v1/schemaregistry/schemas/branch/{branchId}` | Delete a branch given its branch id |  |
| `delete_schema_metadata` | DELETE | `/api/v1/schemaregistry/schemas/{name}` | Delete a schema metadata and all related data |  |
| `delete_schema_version` | DELETE | `/api/v1/schemaregistry/schemas/{name}/versions/{version}` | Delete a schema version given its schema name and version id |  |
| `disable_schema` | POST | `/api/v1/schemaregistry/schemas/versions/{id}/state/disable` | Disables version of the schema identified by the given version id |  |
| `enable_schema` | POST | `/api/v1/schemaregistry/schemas/versions/{id}/state/enable` | Enables version of the schema identified by the given version id |  |
| `execute_state` | POST | `/api/v1/schemaregistry/schemas/versions/{id}/state/{stateId}` | Runs the state execution for schema version identified by the given version id and executes action associated with target state id |  |
| `find_aggregated_schemas` | GET | `/api/v1/schemaregistry/search/schemas/aggregated` | Search for schemas containing the given name and description |  |
| `find_schemas` | GET | `/api/v1/schemaregistry/search/schemas` | Search for schema metadata containing the given name and description |  |
| `find_schemas_by_fields` | GET | `/api/v1/schemaregistry/search/schemas/fields` | Search for schemas containing the given field names |  |
| `get_aggregated_schema_info` | GET | `/api/v1/schemaregistry/schemas/{name}/aggregated` | Get aggregated schema information for the given schema name |  |
| `get_all_schema_versions` | GET | `/api/v1/schemaregistry/schemas/{name}/versions` | Get all the versions of the schema for the given schema name) |  |
| `get_latest_schema_version` | GET | `/api/v1/schemaregistry/schemas/{name}/versions/latest` | Get the latest version of the schema for the given schema name |  |
| `get_latest_schema_version_text` | GET | `/api/v1/schemaregistry/schemas/{name}/versions/latest/schemaText` | Get the schema text property of the latest version of the given schema name |  |
| `get_schema_info` | GET | `/api/v1/schemaregistry/schemasById/{schemaId}` | Get schema information for a given schema identifier |  |
| `get_schema_info1` | GET | `/api/v1/schemaregistry/schemas/{name}` | Get schema information for the given schema name |  |
| `get_schema_text_version_by_id` | GET | `/api/v1/schemaregistry/schemas/versionsById/{id}/schemaText` | Get the schema text property of the schema identified by the given version id |  |
| `get_schema_version1` | GET | `/api/v1/schemaregistry/schemas/{name}/versions/{version}` | Get a version of the schema identified by the schema name |  |
| `get_schema_version_by_fingerprint` | GET | `/api/v1/schemaregistry/schemas/versionsByFingerprint/{fingerprint}` | Get a version of the schema with the given fingerprint |  |
| `get_schema_version_by_id` | GET | `/api/v1/schemaregistry/schemas/versionsById/{id}` | Get a version of the schema identified by the given version id |  |
| `get_schema_version_life_cycle_states` | GET | `/api/v1/schemaregistry/schemas/versions/statemachine` | Get schema version life cycle states |  |
| `get_schema_version_text` | GET | `/api/v1/schemaregistry/schemas/{name}/versions/{version}/schemaText` | Get the schema text property of the schema identified by name and version |  |
| `list_aggregated_schemas` | GET | `/api/v1/schemaregistry/schemas/aggregated` | Get list of schemas by filtering with the given query parameters |  |
| `list_schemas` | GET | `/api/v1/schemaregistry/schemas` | Get list of schema metadata by filtering with the given query parameters |  |
| `merge_schema_version` | POST | `/api/v1/schemaregistry/schemas/{versionId}/merge` | Merge a schema version to master given its version id |  |
| `start_review_schema` | POST | `/api/v1/schemaregistry/schemas/versions/{id}/state/startReview` | Starts review version of the schema identified by the given version id |  |
| `update_schema_info` | POST | `/api/v1/schemaregistry/schemas/{name}` | Updates schema information for the given schema name |  |
| `upload_schema_version1` | POST | `/api/v1/schemaregistry/schemas/{name}/versions/upload` | Register a new version of an existing schema by uploading schema version text |  |
| `add_ser_des` | POST | `/api/v1/schemaregistry/serdes` | Add a Serializer/Deserializer into the Schema Registry |  |
| `get_ser_des` | GET | `/api/v1/schemaregistry/serdes/{id}` | Get a Serializer for the given serializer id |  |
| `get_serializers` | GET | `/api/v1/schemaregistry/schemas/{name}/serdes` | Get list of Serializers registered for the given schema name |  |
| `map_schema_with_ser_des` | POST | `/api/v1/schemaregistry/schemas/{name}/mapping/{serDesId}` | Bind the given Serializer/Deserializer to the schema identified by the schema name |  |
| `upload_schema_version` | POST | `/api/v1/schemaregistry/import` | Bulk import schemas from a file |  |
| `download_file` | GET | `/api/v1/schemaregistry/files/download/{fileId}` | Downloads the respective for the given fileId if it exists |  |
| `get_all_branches` | GET | `/api/v1/schemaregistry/schemas/{name}/branches` | Get list of registered schema branches |  |
| `get_registered_schema_provider_infos` | GET | `/api/v1/schemaregistry/schemaproviders` | Get list of registered Schema Providers |  |
| `get_version` | GET | `/api/v1/schemaregistry/version` | Get the version information of this Schema Registry instance |  |
| `upload_file` | POST | `/api/v1/schemaregistry/files` | Upload the given file and returns respective identifier. |  |
| `check_compatibility_with_schema` | POST | `/api/v1/confluent/compatibility/subjects/{schema}/versions/{version}` | Checks if the given schema text is compatible with the specified ("latest" or versionID) version of the schema identified by the name |  |
| `get_all_versions` | GET | `/api/v1/confluent/subjects/{subject}/versions` | Get the number of all schema versions of given subject |  |
| `get_schema_by_id` | GET | `/api/v1/confluent/schemas/ids/{id}` | Get schema version by id |  |
| `get_schema_version` | GET | `/api/v1/confluent/subjects/{subject}/versions/{versionId}` | Get the schema information for given subject and versionId |  |
| `get_subjects` | GET | `/api/v1/confluent/subjects` | Get all registered subjects |  |
| `lookup_subject_version` | POST | `/api/v1/confluent/subjects/{subject}` | Get schema information for the given schema subject and schema text |  |
| `register_schema_version` | POST | `/api/v1/confluent/subjects/{subject}/versions` | Register a new version of the schema |  |
| `setup_atlas_model` | POST | `/api/v1/schemaregistry/setupAtlasModel` | Setup SchemaRegistry model in Atlas |  |

## smm_alerting

20 tools. **Partial source:** from HTML reference pages; may be incomplete.

- Product/version: Cloudera Streams Messaging Manager REST API (Cloudera Runtime 7.3.2)
- Spec source: https://docs.cloudera.com/cdp-private-cloud-base/7.3.2/smm-rest-api-reference/index.html - from HTML docs (swagger-codegen html2 page generated from the service swagger; complete for that doc build, but no raw spec was published; may be partial vs. newer service builds). Live spec: http(s)://<smm-host>:8585/swagger.json.
- Tags included: AlertNotifications, AlertPolicyOperations, AlertingConfigOperations, NotifierRelatedOperations
- Auth: Base path /api/v1 and /api/v2 on the SMM REST server (8585/8587 TLS). Kerberos SPNEGO, basic auth (when enabled), or Knox (/gateway/cdp-proxy-api/smm-api/...). POST /api/v1/admin/auth/login etc. under Authentication. Ranger authorization of Kafka resources applies.
- Operation count: 20

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `get_alert_notifications` | GET | `/api/v1/admin/alert/notifications` | Get the Alert notifications from the given `offset`, up to the given `limit`. |  |
| `get_alert_notifications_by_entity_type` | GET | `/api/v1/admin/alert/notifications/entity/{entityType}` | Get all the Alert notifications for a given entity type |  |
| `get_alert_notifications_by_entity_type_and_name` | GET | `/api/v1/admin/alert/notifications/entity/{entityType}/{entityName}` | Get the Alert notifications for the given entity type and resource name |  |
| `mark_alert_notifications` | PUT | `/api/v1/admin/alert/notifications/read` | Mark the Alert notifications as read |  |
| `unmark_alert_notifications` | PUT | `/api/v1/admin/alert/notifications/unread` | Mark the alert notifications as unread |  |
| `add_alert_policy` | POST | `/api/v1/admin/alertPolicy` | Add an alert policy. |  |
| `delete_alert_policy` | DELETE | `/api/v1/admin/alertPolicy/{id}` | Delete an existing alert policy. |  |
| `disable_alert_policy` | PUT | `/api/v1/admin/alertPolicy/{id}/disable` | Disable an existing alert policy. |  |
| `enable_alert_policy` | PUT | `/api/v1/admin/alertPolicy/{id}/enable` | Enable an existing alert policy. |  |
| `get_alert_policy` | GET | `/api/v1/admin/alertPolicy/{id}` | Get the alert policy for a given id. |  |
| `get_all_alert_policies` | GET | `/api/v1/admin/alertPolicy` | Get all the alert policies register. |  |
| `get_auto_complete_automata` | GET | `/api/v1/admin/alertPolicy/automata/{version}` | Returns Autocomplete automata for alert policy. |  |
| `update_alert_policy` | PUT | `/api/v1/admin/alertPolicy/{id}` | Update an existing alert policy. |  |
| `is_streams_replication_manager_configured` | GET | `/api/v1/admin/alert/is-configured` | Check if alerting is configured |  |
| `create_notifier` | POST | `/api/v1/admin/notifiers` | Creates Notifier for the given NotifierConfiguration |  |
| `delete_notifier` | DELETE | `/api/v1/admin/notifiers/{notifierId}` | Deletes Notifier for the given notifierId |  |
| `get_notifier` | GET | `/api/v1/admin/notifiers/{notifierId}` | Notifier configuration for the given notifierId |  |
| `get_notifier_provider_configs` | GET | `/api/v1/admin/notifiers/providerConfigs` | This API return map of notifier provider id with respective configuration fields. |  |
| `list_notifiers` | GET | `/api/v1/admin/notifiers` | List of added notifiers |  |
| `update_notifier` | PUT | `/api/v1/admin/notifiers/{notifierId}` | Updates Notifier for the given NotifierConfiguration with notifierId |  |

## smm_integrations

48 tools. **Partial source:** from HTML reference pages; may be incomplete.

- Product/version: Cloudera Streams Messaging Manager REST API (Cloudera Runtime 7.3.2)
- Spec source: https://docs.cloudera.com/cdp-private-cloud-base/7.3.2/smm-rest-api-reference/index.html - from HTML docs (swagger-codegen html2 page generated from the service swagger; complete for that doc build, but no raw spec was published; may be partial vs. newer service builds). Live spec: http(s)://<smm-host>:8585/swagger.json.
- Tags included: ApplicationContextRelatedOperations, Authentication, CMKafkaInfo, KafkaConnectConfigOperations, KafkaConnectMetricsOperations, KafkaConnectOperations, ResourceConfigurationOperations, SMMDebugOperations, SchemaRegistryConfigOperations, SchemaRegistryOperations, SerdesRelatedOperations, StreamsReplicationManagerConfigOperations, StreamsReplicationManagerMonitoringOperations, StreamsReplicationManagerMonitoringOperationsUsingV2SRMAPI
- Auth: Base path /api/v1 and /api/v2 on the SMM REST server (8585/8587 TLS). Kerberos SPNEGO, basic auth (when enabled), or Knox (/gateway/cdp-proxy-api/smm-api/...). POST /api/v1/admin/auth/login etc. under Authentication. Ranger authorization of Kafka resources applies.
- Operation count: 48

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `get_smm_version` | GET | `/api/v1/admin/version` | Returns version of SMM service |  |
| `get_access` | GET | `/api/v1/admin/auth/access` | Get the Authentication status. |  |
| `login` | POST | `/api/v1/admin/auth/login` | Get the login response |  |
| `logout` | GET | `/api/v1/admin/auth/logout` | Get the logout success |  |
| `get_kafka_role_info` | GET | `/api/v1/admin/cluster/cmKafkaClusterRolesInfo` | Fetch Kafka cluster Role information from the Cloudera Manager environment |  |
| `is_kafka_connect_configured` | GET | `/api/v1/admin/kafka-connect/is-configured` | Check if Kafka Connect is configured |  |
| `get_connect_worker_metrics` | GET | `/api/v1/admin/metrics/connect/workers` | Get worker level metrics for the given connector. |  |
| `get_sink_connector_task_metrics` | GET | `/api/v1/admin/metrics/connect/sink/{connectorName}/{taskId}` | Get task level metrics for the given connector. |  |
| `get_source_connector_task_metrics` | GET | `/api/v1/admin/metrics/connect/source/{connectorName}/{taskId}` | Get task level metrics for the given connector. |  |
| `configure_connector` | PUT | `/api/v1/admin/kafka-connect/connectors/{connector}` | Create or reconfigure a Connector |  |
| `connector` | GET | `/api/v1/admin/kafka-connect/connectors/{connector}` | Get info for a single configured Connector or null if it does not exist |  |
| `connector_operation` | POST | `/api/v1/admin/kafka-connect/connectors/{connector}/{operation}` | Pause, resume, or restart a Connector |  |
| `connector_templates` | GET | `/api/v1/admin/kafka-connect/connector-templates` | Returns a list of connector templates that can be used for creating connectors |  |
| `connectors` | GET | `/api/v1/admin/kafka-connect/connectors` | Get info for all configured Connectors |  |
| `delete_connector` | DELETE | `/api/v1/admin/kafka-connect/connectors/{connector}` | Delete a Connector |  |
| `get_connector_config_def` | GET | `/api/v1/admin/kafka-connect/connector-templates/config/definitions` | Get Configuration Definitions |  |
| `get_connector_permissions` | GET | `/api/v1/admin/kafka-connect/connector-permissions` | Connector Permissions |  |
| `handle_enhance_config` | POST | `/api/v1/admin/kafka-connect/connector-templates/config/enhance` | Enhance Provided Configuration |  |
| `handle_get_sample_config_for_template` | GET | `/api/v1/admin/kafka-connect/connector-templates/config/sample` | Template Configuration |  |
| `plugin_config_sample` | GET | `/api/v1/admin/kafka-connect/connector-plugins/{connector}/config/sample` | Return a sample configuration of a connector plugin |  |
| `plugin_connectors` | GET | `/api/v1/admin/kafka-connect/connector-plugins` | Return a list of connector plugins installed in the Kafka Connect cluster |  |
| `task_operation` | POST | `/api/v1/admin/kafka-connect/connectors/{connector}/tasks/{task}/{operation}` | Restart a Task |  |
| `validate_config` | PUT | `/api/v1/admin/kafka-connect/connector-plugins/{connector}/config/validate` | Validate Connector Configuration |  |
| `validate_template_config` | PUT | `/api/v1/admin/kafka-connect/connector-templates/config/validate` | Validate Template Configuration |  |
| `validate_template_config_detailed` | PUT | `/api/v1/admin/kafka-connect/connector-templates/config/validate-detailed` | Validate Template Configuration |  |
| `alter_topic_configs` | PUT | `/api/v1/admin/configs/topics/{topicName}` | Alter Topic configurations for the given topicName. |  |
| `get_all_broker_details` | GET | `/api/v1/admin/configs/brokers` | Get kafka configurations for the given brokerIds. |  |
| `get_all_topic_configs` | GET | `/api/v1/admin/configs/topics` | Get kafka configurations for all topics. |  |
| `get_broker_details` | GET | `/api/v1/admin/configs/brokers/{brokerId}` | Get kafka configurations for the given brokerId. |  |
| `get_default_topic_configs` | GET | `/api/v1/admin/configs/default/topics` | Get default kafka topic configuration |  |
| `get_topic_configs` | GET | `/api/v1/admin/configs/topics/{topicName}` | Get kafka configurations for a topic with given topicName. |  |
| `get_attribute_value` | GET | `/api/v1/admin/debug/alert/attributeValue` | Get alert resource attribute value |  |
| `is_schema_registry_configured` | GET | `/api/v1/admin/schemas/is-configured` | Check if schema registry is configured |  |
| `get_key_schema_version_infos` | GET | `/api/v1/admin/schemas/topics/{topicName}/keySchema/versions` | Get schema versions for the given kafka topic name |  |
| `get_schema_meta_for_topic` | GET | `/api/v1/admin/schemas/topics/{topicName}/schema/mapping` | Schema mapping for a given kafka topic name |  |
| `get_schema_registry_info` | GET | `/api/v1/admin/schemas/registryInfo` | Get the information about schema registry |  |
| `get_value_schema_version_infos` | GET | `/api/v1/admin/schemas/topics/{topicName}/valueSchema/versions` | Get schema versions for the given kafka topic name |  |
| `register_topic_schema_meta` | POST | `/api/v1/admin/schemas/topics/{topicName}/schema/mapping` | Register a schema name for a kafka topic name |  |
| `get_supported_serdes` | GET | `/api/v1/admin/serdes` | List of supported serdes |  |
| `is_streams_replication_manager_configured1` | GET | `/api/v1/admin/replication-stats/is-configured` | Check if streams replication manager is configured |  |
| `is_streams_replication_manager_configured2` | GET | `/api/v2/admin/replication-stats/is-configured` | Check if streams replication manager is configured |  |
| `cluster_replication_stats` | GET | `/api/v1/admin/replication-stats` | Get replication stats for all the streams that are being replicated |  |
| `topic_replication_stats` | GET | `/api/v1/admin/replication-stats/{source}/topics` | Get all the topic replication stats for a given source cluster |  |
| `topic_timeline_metrics` | GET | `/api/v1/admin/replication-stats/topics/{topic}` | Get all the timeline metrics for a given topic |  |
| `cluster_replication_stats1` | GET | `/api/v2/admin/replication-stats` | Get replication stats for all the streams that are being replicated |  |
| `downstream_topic_metrics_for_colocated_cluster` | GET | `/api/v2/admin/replication-stats/topics/{downstreamTopic}` | Get topic metrics from colocated SRM Service for a specific (downstream) topic |  |
| `topic_replication_stats1` | GET | `/api/v2/admin/replication-stats/topics/{source}/{target}` | Get all the topic replication stats for a given source cluster |  |
| `topic_timeline_metrics1` | GET | `/api/v2/admin/replication-stats/topics/{source}/{target}/{upstreamtopic}` | Get all the timeline metrics for a given topic |  |

## smm_kafka

46 tools. **Partial source:** from HTML reference pages; may be incomplete.

- Product/version: Cloudera Streams Messaging Manager REST API (Cloudera Runtime 7.3.2)
- Spec source: https://docs.cloudera.com/cdp-private-cloud-base/7.3.2/smm-rest-api-reference/index.html - from HTML docs (swagger-codegen html2 page generated from the service swagger; complete for that doc build, but no raw spec was published; may be partial vs. newer service builds). Live spec: http(s)://<smm-host>:8585/swagger.json.
- Tags included: AggregatedMetricOperations, BrokerMetricsOperations, BrokersMetadataOperations, ClusterMetadataOperations, ConsumerGroupRelatedDetails_, ConsumerMetricOperations, EndToEndLatencyMetrics, LineageOperations, ProducerMetricsOperations, SearchRelatedOperations, TopicConsumptionOperations, TopicMetadataRelatedOperations, TopicMetricsOperations
- Auth: Base path /api/v1 and /api/v2 on the SMM REST server (8585/8587 TLS). Kerberos SPNEGO, basic auth (when enabled), or Knox (/gateway/cdp-proxy-api/smm-api/...). POST /api/v1/admin/auth/login etc. under Authentication. Ranger authorization of Kafka resources applies.
- Operation count: 46

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `get_all_consumer_group_metrics` | GET | `/api/v2/admin/metrics/aggregated/groups` | Get all consumer group details. |  |
| `get_all_producer_metrics` | GET | `/api/v2/admin/metrics/aggregated/producers` | Get producer metrics for all the alive producers |  |
| `get_broker_details1` | GET | `/api/v2/admin/metrics/aggregated/brokers/{brokerId}` | Get broker details with metrics for a given brokerId |  |
| `get_cluster_with_broker_metrics` | GET | `/api/v2/admin/metrics/aggregated/brokers` | Get cluster with broker metrics |  |
| `get_cluster_with_topic_metrics` | GET | `/api/v2/admin/metrics/aggregated/topics` | Get cluster with topic metrics |  |
| `get_consumer_group_metrics` | GET | `/api/v2/admin/metrics/aggregated/groups/{groupName}` | Get consumer group details for the given groupName. |  |
| `get_producer_metrics` | GET | `/api/v2/admin/metrics/aggregated/producers/{producerClientId}` | Get producer metrics for the given producerClientId |  |
| `get_topic_metrics` | GET | `/api/v2/admin/metrics/aggregated/topics/{topicName}` | Get topic metrics for the given topic |  |
| `get_broker_metrics` | GET | `/api/v1/admin/metrics/brokers/{brokerId}` | Get broker metrics for given brokerId. |  |
| `get_broker` | GET | `/api/v1/admin/brokers/{brokerId}` | Returns broker node in the cluster with the given broker Id. |  |
| `get_brokers` | GET | `/api/v1/admin/brokers` | Returns all broker nodes in the cluster with the given brokerIds if they exist. |  |
| `get_cluster_details` | GET | `/api/v1/admin/cluster` | Get the kafka cluster details to which this service is connected to. |  |
| `get_all_consumer_info` | GET | `/api/v1/admin/consumers/clients` | Get consumer group details for all clients. |  |
| `get_consumer_group_info` | GET | `/api/v1/admin/consumers/groups/{groupName}` | Get consumer group details for the given groupName `groupName`. |  |
| `get_consumer_group_names` | GET | `/api/v1/admin/consumers/groupNames` | Get all consumer group names. |  |
| `get_consumer_groups` | GET | `/api/v1/admin/consumers/groups` | Get all consumer group details. |  |
| `get_consumer_info` | GET | `/api/v1/admin/consumers/clients/{clientId}` | Get consumer group details for a given clientId. |  |
| `reset_offset` | POST | `/api/v1/admin/consumers/groups/{groupName}/resetOffsets` | Reset consumer offsets |  |
| `get_consumer_group_metrics1` | GET | `/api/v2/admin/metrics/consumers/group/{groupId}` | Get timeline metrics for a consumer group. |  |
| `get_consumer_metrics` | GET | `/api/v1/admin/etelatency/{topicName}` | Get the end to end latency metrics for the given topic across all intercepted consumer groups. |  |
| `get_consumer_metrics_by_client_id` | GET | `/api/v1/admin/etelatency/{topicName}/groups/{groupId}/clients/{clientId}` | Get the end to end latency metrics under a given consumer group for the given clientId and topic. |  |
| `get_consumer_metrics_by_client_partition` | GET | `/api/v1/admin/etelatency/{topicName}/partitions/{partitionNum}/groups/{groupId}/clients/{clientId}` | Get the end to end latency metrics of a client under a given consumer group for the given partition and topic. |  |
| `get_consumer_metrics_by_group` | GET | `/api/v1/admin/etelatency/{topicName}/groups/{groupId}` | Get the end to end latency metrics under the given consumer group Id for the given topic. |  |
| `get_consumer_metrics_by_partition` | GET | `/api/v1/admin/etelatency/{topicName}/partitions/{partitionNum}/groups/{groupId}` | Get the end to end latency metrics under a given consumer group for the given partition and topic. |  |
| `get_consumer_group_lineage` | GET | `/api/v2/admin/lineage/consumerGroups/{consumerGroupId}` | Get lineage for Consumer Group |  |
| `get_producer_lineage` | GET | `/api/v2/admin/lineage/producers/{producerId}` | Get lineage for Producer |  |
| `get_topic_lineage` | GET | `/api/v2/admin/lineage/partitions/{topic}` | Get lineage for Producer |  |
| `get_topic_partition_lineage` | GET | `/api/v2/admin/lineage/partitions/{topic}/{partition}` | Get lineage for Topic Partition |  |
| `get_all_producer_metrics1` | GET | `/api/v1/admin/metrics/producers` | Get producer metrics for all the alive producers |  |
| `get_producer_metrics1` | GET | `/api/v1/admin/metrics/producers/{producerClientId}` | Get producer metrics for the given producerClientId |  |
| `get_broker_configs` | GET | `/api/v1/admin/search/configs/brokers` | Get kafka configurations for the given brokerIds. |  |
| `get_brokers1` | GET | `/api/v1/admin/search/brokers` | Returns broker nodes in the cluster with the given brokerIds if they exist. |  |
| `get_topic_configs1` | GET | `/api/v1/admin/search/configs/topics` | Get kafka configurations at topic level for given topicNames |  |
| `get_topic_details` | GET | `/api/v1/admin/search/topics` | Get respective details for given topicNames. |  |
| `get_topic_partition_infos` | GET | `/api/v1/admin/search/topicPartitions` | Get a list of topic partitions with respective details for the given collection of topicPartitions which exist in target Kafka cluster. |  |
| `get_topic_content` | GET | `/api/v1/admin/topics/{topicName}/partition/{partitionId}/payloads` | Get topic content for a given topic, its partition and the offset range with in the partition |  |
| `get_topic_offsets` | GET | `/api/v1/admin/topics/{topicName}/offsets` | Get offsets for all the partition for a given kafka topic name |  |
| `all_topic_infos` | GET | `/api/v1/admin/topics` | Get respective details for all the topics. |  |
| `create_partitions` | PUT | `/api/v1/admin/topics` | Alter topic partitions |  |
| `create_topics` | POST | `/api/v1/admin/topics` | Create topics |  |
| `delete_topics` | DELETE | `/api/v1/admin/topics` | Delete topics |  |
| `get_topic_description` | GET | `/api/v1/admin/topics/{topicName}/description` | Get respective description about topic with the given `topicName`. |  |
| `get_topic_info` | GET | `/api/v1/admin/topics/{topicName}` | Get respective details about topic with the given `topicName` |  |
| `get_topic_partitions` | GET | `/api/v1/admin/topics/{topicName}/partitions` | Get respective partitions for the given topic with topicName |  |
| `get_topic_metrics1` | GET | `/api/v1/admin/metrics/topics/{topicName}` | Get topic metrics for the given topic. |  |
| `get_topic_partition_metrics` | GET | `/api/v1/admin/metrics/topics/{topicName}/{partitionNum}` | Get topic-partition metrics for the given topic-partition. |  |

## srm

23 tools. **Partial source:** from HTML reference pages; may be incomplete.

- Product/version: Cloudera Streams Replication Manager Service REST API (Cloudera Runtime 7.3.2)
- Spec source: https://docs.cloudera.com/cdp-private-cloud-base/7.3.2/srm-rest-api-reference/index.html - from HTML docs (swagger-codegen html2 page generated from the service swagger; complete for that doc build, but no raw spec was published; may be partial vs. newer service builds). Live: Cloudera Manager > SRM > Web UI > SRM Service Swagger UI.
- Tags included: Class1SRMServiceAPIV2, Class2SRMServiceAPIV1, Class3SRMServiceAPIV2Internal, Class4SRMServiceAPIV1Internal, Default
- Auth: SRM Service REST server (default 6670, 6671 TLS). Kerberos SPNEGO and/or basic auth (srm.service.rest.basic.auth), TLS; Knox (/gateway/cdp-proxy-api/srm-api). Cloudera recommends V2 endpoints; "Internal" tags are used by SMM.
- Operation count: 23

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `cluster_info` | GET | `/v2/cluster-info/{kafkaClusterId}` | Get cluster info for the specified Kafka cluster ID. |  |
| `cluster_metrics1` | GET | `/v2/cluster-metrics/{source}/{target}/{metric}` | Get cluster-level metric data of the specified replication. |  |
| `remote_topics1` | GET | `/v2/remote-topics/{source}/{target}` | Get topic info about topics replicated from the specified source to the specified target. |  |
| `replications` | GET | `/v2/replications` | Get replication info about the replications with the specified sources and targets. |  |
| `topic_metrics_with_downstream_topic_name` | GET | `/v2/topic-metrics/{target}/{downstreamTopic}/{metric}` | Get metric data about the specified topic replicated to the specified target. |  |
| `topic_metrics_with_downstream_topic_name1` | GET | `/v2/topic-metrics/{source}/{target}/{upstreamTopic}/{metric}` | Get metric data about the specified topic replicated from the specified source to the specified target. |  |
| `cluster_metrics` | GET | `/cluster-metrics/{cluster}/{metric}` | Get cluster-level metric data about the replication with the specified source cluster and the default target cluster. |  |
| `remote_topics` | GET | `/remote-topics/{source}` | Get topic info about topics replicated from the specified source cluster to the default target cluster. |  |
| `replication_info` | GET | `/replications` | Get replication info about the replications targeting the default target cluster. |  |
| `topic_metrics` | GET | `/topic-metrics/{topic}/{metric}` | Get metric data about the specified remote (replicated) topic. |  |
| `cluster_info1` | GET | `/v2/inter-cluster/cluster-info/{kafkaClusterId}` | (no summary in source) cluster info1 |  |
| `cluster_metrics2` | GET | `/v2/inter-cluster/cluster-metrics/{source}/{target}/{metric}` | (no summary in source) cluster metrics2 |  |
| `cluster_metrics3` | GET | `/v2/intra-cluster/cluster-metrics/{source}/{target}/{metric}` | (no summary in source) cluster metrics3 |  |
| `connector_metrics` | GET | `/v2/intra-cluster/connector-metrics/{source}/{target}/{connector}/{metric}` | (no summary in source) connector metrics |  |
| `health_check` | HEAD | `/v2/health-check` | Health check. |  |
| `remote_topics2` | GET | `/v2/inter-cluster/remote-topics/{source}/{target}` | (no summary in source) remote topics2 |  |
| `replications1` | GET | `/v2/inter-cluster/replications` | (no summary in source) replications1 |  |
| `topic_metrics1` | GET | `/v2/intra-cluster/topic-metrics/{source}/{target}/{upstreamTopic}/{metric}` | (no summary in source) topic metrics1 |  |
| `topic_metrics_with_downstream_topic_name2` | GET | `/v2/inter-cluster/topic-metrics/{target}/{downstreamTopic}/{metric}` | (no summary in source) topic metrics with downstream topic name2 |  |
| `topic_metrics_with_downstream_topic_name3` | GET | `/v2/inter-cluster/topic-metrics/{source}/{target}/{upstreamTopic}/{metric}` | (no summary in source) topic metrics with downstream topic name3 |  |
| `cluster_metrics_local` | GET | `/cluster-metrics-local/{cluster}/{metric}` | (no summary in source) cluster metrics local |  |
| `topic_metrics_local` | GET | `/topic-metrics-local/{topic}/{metric}` | (no summary in source) topic metrics local |  |
| `api_metadata` | GET | `/` | (no summary in source) api metadata |  |

## kafka_connect

29 tools.

- Product/version: Kafka Connect REST API (Apache Kafka 3.9 branch source; cross-checked with Cloudera Runtime 7.3.2 "Kafka Connect REST API" reference, which was generated from 3.4.1.7.1.9 and lacks offsets/stop/PATCH-config/health)
- Spec source: https://github.com/apache/kafka/tree/3.9/connect/runtime/src/main/java/org/apache/kafka/connect/runtime/rest/resources (JAX-RS annotations, script-extracted) + https://docs.cloudera.com/cdp-private-cloud-base/7.3.2/kafka-rest-api-reference/index.html
- Tags included: Root, Connectors, ConnectorPlugins, Logging
- Auth: Connect worker REST (Cloudera default 28083 TLS / 28085). Kerberos SPNEGO (Cloudera enables SPNEGO auth via JAAS) and/or basic auth extension; Knox via SMM proxy. Cloudera connector extensions (Stateless NiFi, HDFS/S3 sinks etc.) are configured through these same endpoints; Cloudera documents no extra REST operations. Internal endpoints (/connectors/{c}/tasks POST, fence-zombies) and GET /health may not exist on older Cloudera builds.
- Operation count: 29

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `server_info` | GET | `/` | Get details about this Connect worker and the ID of the Kafka cluster it is connected to |  |
| `health_check` | GET | `/health` | Health check endpoint to verify worker readiness and liveness |  |
| `list_connectors` | GET | `/connectors` | List all active connectors |  |
| `create_connector` | POST | `/connectors` | Create a new connector |  |
| `get_connector` | GET | `/connectors/{connector}` | Get the details for the specified connector |  |
| `get_connector_config` | GET | `/connectors/{connector}/config` | Get the configuration for the specified connector |  |
| `get_tasks_config` | GET | `/connectors/{connector}/tasks-config` | Get the configuration of all tasks for the specified connector |  |
| `get_connector_status` | GET | `/connectors/{connector}/status` | Get the status for the specified connector |  |
| `get_connector_active_topics` | GET | `/connectors/{connector}/topics` | Get the list of topics actively used by the specified connector |  |
| `reset_connector_active_topics` | PUT | `/connectors/{connector}/topics/reset` | Reset the list of topics actively used by the specified connector |  |
| `put_connector_config` | PUT | `/connectors/{connector}/config` | Create or reconfigure the specified connector |  |
| `patch_connector_config` | PATCH | `/connectors/{connector}/config` | Patch (merge) the configuration of the specified connector |  |
| `restart_connector` | POST | `/connectors/{connector}/restart` | Restart the specified connector |  |
| `stop_connector` | PUT | `/connectors/{connector}/stop` | Stop the specified connector |  |
| `pause_connector` | PUT | `/connectors/{connector}/pause` | Pause the specified connector |  |
| `resume_connector` | PUT | `/connectors/{connector}/resume` | Resume the specified connector |  |
| `get_task_configs` | GET | `/connectors/{connector}/tasks` | List all tasks and their configurations for the specified connector |  |
| `get_task_status` | GET | `/connectors/{connector}/tasks/{task}/status` | Get the state of the specified task for the specified connector |  |
| `restart_task` | POST | `/connectors/{connector}/tasks/{task}/restart` | Restart the specified task for the specified connector |  |
| `destroy_connector` | DELETE | `/connectors/{connector}` | Delete the specified connector |  |
| `get_offsets` | GET | `/connectors/{connector}/offsets` | Get the current offsets for the specified connector |  |
| `alter_connector_offsets` | PATCH | `/connectors/{connector}/offsets` | Alter the offsets for the specified connector |  |
| `reset_connector_offsets` | DELETE | `/connectors/{connector}/offsets` | Reset the offsets for the specified connector |  |
| `validate_configs` | PUT | `/connector-plugins/{pluginName}/config/validate` | Validate the provided configuration against the configuration definition for the specified pluginName |  |
| `list_connector_plugins` | GET | `/connector-plugins` | List all connector plugins installed |  |
| `get_connector_config_def` | GET | `/connector-plugins/{pluginName}/config` | Get the configuration definition for the specified pluginName |  |
| `list_loggers` | GET | `/admin/loggers` | List the current loggers that have their levels explicitly set and their log levels |  |
| `get_logger` | GET | `/admin/loggers/{logger}` | Get the log level for the specified logger |  |
| `set_level` | PUT | `/admin/loggers/{logger}` | Set the log level for the specified logger |  |

## cruise_control

23 tools.

- Product/version: Cruise Control REST API (linkedin/cruise-control main, OpenAPI 3.0; Cloudera Runtime 7.3.2 ships Cruise Control 2.5.x)
- Spec source: https://github.com/linkedin/cruise-control/tree/main/cruise-control/src/main/resources/yaml (base.yaml + endpoints/*.yaml); cross-checked with https://docs.cloudera.com/cdp-private-cloud-base/7.3.2/cctrl-rest-api-reference/index.html
- Tags included: (single tag)
- Auth: Base /kafkacruisecontrol (webserver.api.urlprefix), port 8899. Basic auth or JWT bearer when webserver.security.enable=true; Cloudera supports SPNEGO/Kerberos and Knox (/gateway/cdp-proxy-api/cruisecontrol). Most POSTs default dryrun=true; long ops are async via User-Task-ID header.
- Operation count: 23

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `add_broker` | POST | `/kafkacruisecontrol/add_broker` | Move partitions to the specified brokers, according to the specified goals. |  |
| `admin` | POST | `/kafkacruisecontrol/admin` | Dynamically change some configs of Cruise Control. |  |
| `bootstrap` | GET | `/kafkacruisecontrol/bootstrap` | Bootstrap Cruise Control. |  |
| `demote_broker` | POST | `/kafkacruisecontrol/demote_broker` | Demote specified brokers. |  |
| `fix_offline_replicas` | POST | `/kafkacruisecontrol/fix_offline_replicas` | Fix offline replicas by moving currently offline replicas to healthy brokers. |  |
| `kafka_cluster_state` | GET | `/kafkacruisecontrol/kafka_cluster_state` | Retrive the current Kafka cluster state. |  |
| `load` | GET | `/kafkacruisecontrol/load` | Get the cluster load once Cruise Control Load Monitor is running. |  |
| `partitionload` | GET | `/kafkacruisecontrol/partition_load` | Get the resource load for each partition. |  |
| `pause_sampling` | POST | `/kafkacruisecontrol/pause_sampling` | Pause metric sampling. |  |
| `proposals` | GET | `/kafkacruisecontrol/proposals` | Get current proposals. |  |
| `permissions` | GET | `/kafkacruisecontrol/permissions` | Get the permissions of a user specified as a query parameter |  |
| `rebalance` | POST | `/kafkacruisecontrol/rebalance` | Rebalance a Kafka cluster based on goals. |  |
| `remove_broker` | POST | `/kafkacruisecontrol/remove_broker` | Remove/decomission specified brokers. |  |
| `rightsize` | POST | `/kafkacruisecontrol/rightsize` | Manually invoke provisioner rightsizing of the cluster. |  |
| `resume_sampling` | POST | `/kafkacruisecontrol/resume_sampling` | Resume metric sampling. |  |
| `review` | POST | `/kafkacruisecontrol/review` | Reivew pending Cruise Control requests. |  |
| `review_board` | GET | `/kafkacruisecontrol/review_board` | Check review status of Cruise Control requests. |  |
| `state` | GET | `/kafkacruisecontrol/state` | Get the state of cruise control. |  |
| `stop_proposal_execution` | POST | `/kafkacruisecontrol/stop_proposal_execution` | Stop ongoing execution in Cruise Control. |  |
| `topic_configuration` | POST | `/kafkacruisecontrol/topic_configuration` | Change the configuration of a topic |  |
| `train` | GET | `/kafkacruisecontrol/train` | Train Cruise Control to better model broker cpu usage. |  |
| `user_tasks` | GET | `/kafkacruisecontrol/user_tasks` | Get the recent user tasks from cruise control. |  |
| `remove_disks` | POST | `/kafkacruisecontrol/remove_disks` | [not in Cloudera 7.3.2 reference] Move all replicas from the specified disk to other disks of the same broker. |  |

## ssb_projects

32 tools. **Partial source:** from HTML reference pages; may be incomplete.

- Product/version: Cloudera SQL Stream Builder (Streaming SQL Engine) REST API, Cloudera Streaming Analytics 1.18.0
- Spec source: https://docs.cloudera.com/csa/1.18.0/sql-stream-builder-rest-api-reference/index.html - from HTML docs (swagger-codegen html2 page generated from the service swagger; complete for that doc build, but no raw spec was published; may be partial vs. newer service builds). Live spec: http(s)://<host>:<ssb-port>/swagger/api-docs/public.
- Tags included: APIKeyOperations, ProjectEnvironmentOperations, ProjectInvitationOperations, ProjectOperations, ProjectPermissionOperations, SynchronizingAnExistingProject
- Auth: Base /api/v2 (older CSA: /api/v1/ssb). Kerberos SPNEGO (curl --negotiate), Knox (/gateway/cdp-proxy-api/ssb-sse-api/...) with basic/JWT, project API keys (APIKeyOperations), or Username header on unsecured clusters.
- Operation count: 32

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `create_api_key` | POST | `/api/v2/projects/{projectId}/api-keys` | Creates a new api key in the specified project. |  |
| `delete_api_key_by_id` | DELETE | `/api/v2/projects/{projectId}/api-keys/{id}` | Deletes an api key from the specified project. |  |
| `get_all_api_keys_in_project` | GET | `/api/v2/projects/{projectId}/api-keys` | Retrieves all api keys in the specified project. |  |
| `get_api_key_by_id` | GET | `/api/v2/projects/{projectId}/api-keys/{id}` | Retrieves an api key from the specified project by its id. |  |
| `activate_v2` | POST | `/api/v2/projects/{projectId}/environments/{id}/activate` | Activates an environment in the specified project. |  |
| `create_environment_v2` | POST | `/api/v2/projects/{projectId}/environments` | Create a new environment in the specified project. |  |
| `deactivate_v2` | POST | `/api/v2/projects/{projectId}/environments/deactivate` | Deactivates the active environment in the specified project. |  |
| `delete_environment_v2` | DELETE | `/api/v2/projects/{projectId}/environments/{id}` | Delete an environment from the specified project. |  |
| `export_environment_file_v2` | GET | `/api/v2/projects/{projectId}/environments/file/{id}` | Export an environment to a JSON file. |  |
| `get_all_environments_by_project_v2` | GET | `/api/v2/projects/{projectId}/environments` | Get all environments of the specified project |  |
| `get_environment_by_id_v2` | GET | `/api/v2/projects/{projectId}/environments/{id}` | Get an environment in the specified project |  |
| `import_environment_file_v2` | POST | `/api/v2/projects/{projectId}/environments/file` | Import an environment from a JSON file. |  |
| `update_environment_v2` | PUT | `/api/v2/projects/{projectId}/environments/{id}` | Update an environment in the specified project. |  |
| `accept_project_invitation_v2` | POST | `/api/v2/project-invitations/accept/{projectId}` | Accepts Project Invitation for the provided project id. |  |
| `create_project_invitation_v2` | POST | `/api/v2/project-invitations` | Creates a new Project Invitation. |  |
| `delete_project_invitation_v2` | DELETE | `/api/v2/project-invitations` | Deletes a Project Invitation by user id and project id. |  |
| `get_project_invitations_v2` | GET | `/api/v2/project-invitations` | Retrieves Project Invitations by user id and / or project id. |  |
| `create_project_v2` | POST | `/api/v2/projects` | Creates a new project. |  |
| `delete_project_v2` | DELETE | `/api/v2/projects/{projectId}` | Deletes a project by its id. |  |
| `find_project_by_id_v2` | GET | `/api/v2/projects/{projectId}` | Retrieves a project by its id. |  |
| `get_all_projects_with_access_v2` | GET | `/api/v2/projects` | Retrieves all projects the user has access to. |  |
| `import_project_v21` | POST | `/api/v2/projects/import` | Import a new project to SSB from a specified sync source. |  |
| `delete_project_permission` | DELETE | `/api/v2/project-permissions` | Deletes a Project Permission by user id and project id. |  |
| `get_project_permissions` | GET | `/api/v2/project-permissions` | Retrieves project Permissions by user id and project id. |  |
| `update_project_permission` | PUT | `/api/v2/project-permissions` | Updates a Project Permission. |  |
| `delete_sync_source_v2` | DELETE | `/api/v2/projects/{projectId}/sync/config` | Delete the specified project's sync source configuration. |  |
| `export_project_v2` | POST | `/api/v2/projects/{projectId}/sync/export` | Commit the specified project's changes and push it to a specified sync source. |  |
| `get_sync_source_v2` | GET | `/api/v2/projects/{projectId}/sync/config` | Get the specified project's sync source configuration. |  |
| `git_diff` | GET | `/api/v2/projects/{projectId}/sync/gitdiff` | Preview the diff between the current SSB project state (database) and the last committed state in the remote git repository. |  |
| `import_project_v2` | POST | `/api/v2/projects/{projectId}/sync/import` | Import (update) an existing project from a specified sync source. |  |
| `set_sync_source_v2` | POST | `/api/v2/projects/{projectId}/sync/config` | Update the specified project's sync source configuration. |  |
| `validate_sync_source_v2` | POST | `/api/v2/projects/{projectId}/sync/config/validate` | Validate a sync source configuration for a given project. |  |

## ssb_jobs

34 tools. **Partial source:** from HTML reference pages; may be incomplete.

- Product/version: Cloudera SQL Stream Builder (Streaming SQL Engine) REST API, Cloudera Streaming Analytics 1.18.0
- Spec source: https://docs.cloudera.com/csa/1.18.0/sql-stream-builder-rest-api-reference/index.html - from HTML docs (swagger-codegen html2 page generated from the service swagger; complete for that doc build, but no raw spec was published; may be partial vs. newer service builds). Live spec: http(s)://<host>:<ssb-port>/swagger/api-docs/public.
- Tags included: FlinkController, FlinkJobOperations, FlinkSessionClusterOperations, HistoryController, JobOperations, SQLHistoryOperations, SQLOperations, SSBSessionOperations, SamplingOperations, UIJobOperations
- Auth: Base /api/v2 (older CSA: /api/v1/ssb). Kerberos SPNEGO (curl --negotiate), Knox (/gateway/cdp-proxy-api/ssb-sse-api/...) with basic/JWT, project API keys (APIKeyOperations), or Username header on unsecured clusters.
- Operation count: 34

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `get_catalog_connectors` | GET | `/internal/flink/catalogs` | Retrieves all available Flink catalog connectors on the class path |  |
| `run` | POST | `/api/v2/projects/{projectId}/flink/run` | Run a Flink job from an uploaded artifact. |  |
| `get_flink_session_by_user_v2` | GET | `/api/v2/flink/session-cluster` | Returns Flink session properties. |  |
| `provide_flink_session_v2` | POST | `/api/v2/flink/session-cluster` | Ensures the Flink session exists and returns session properties. |  |
| `stop_session_cluster` | POST | `/api/v2/flink/session-cluster/stop` | Stops the running Flink Session Cluster of the user. |  |
| `delete_history_all_by_project_id` | DELETE | `/internal/history` | (no summary in source) delete history all by project id |  |
| `delete_history_by_id` | DELETE | `/internal/history/{id}` | (no summary in source) delete history by id |  |
| `get_items_for_project` | GET | `/internal/history` | (no summary in source) get items for project |  |
| `copy_ssb_job_v2` | POST | `/api/v2/projects/{projectId}/jobs/{id}/copy` | Creates a copy of a given SSB job. |  |
| `create_ssb_job_v2` | POST | `/api/v2/projects/{projectId}/jobs` | Creates a new SSB job. |  |
| `delete_mv_api_endpoint_v2` | DELETE | `/api/v2/projects/{projectId}/jobs/{id}/mv` | Removes a Materialized View of a given SSB job. |  |
| `delete_ssb_job_v2` | DELETE | `/api/v2/projects/{projectId}/jobs/{id}` | Removes the given job. |  |
| `execute_v2` | POST | `/api/v2/projects/{projectId}/jobs/{id}/execute` | Executes the given SSB job. |  |
| `get_job_log_items_v2` | GET | `/api/v2/projects/{projectId}/jobs/{id}/events` | Retrieves the events of a given SSB job. |  |
| `get_job_state_v2` | GET | `/api/v2/projects/{projectId}/jobs/{id}/state` | Retrieves the state of a given SSB job. |  |
| `get_ssb_job_v2` | GET | `/api/v2/projects/{projectId}/jobs/{id}` | Retrieves the given SSB job. |  |
| `get_ssb_jobs_v2` | GET | `/api/v2/projects/{projectId}/jobs` | Retrieves SSB jobs. |  |
| `stop_job_v2` | POST | `/api/v2/projects/{projectId}/jobs/{id}/stop` | Stops the given SSB job. |  |
| `update_ssb_job_v2` | PUT | `/api/v2/projects/{projectId}/jobs/{id}` | Updates the given SSB job. |  |
| `upsert_mv_api_endpoint_v2` | POST | `/api/v2/projects/{projectId}/jobs/{id}/mv` | Creates or updates a Materialized View of a given job. |  |
| `delete_all_by_project_id_and_user_id_v2` | DELETE | `/api/v2/projects/{projectId}/history/user/{userId}` | Deletes all history items of the given user in the specified project. |  |
| `delete_all_by_project_id_v2` | DELETE | `/api/v2/projects/{projectId}/history` | Deletes all history items of the current user in the specified project. |  |
| `delete_by_id_and_project_v2` | DELETE | `/api/v2/projects/{projectId}/history/{id}` | Deletes a given history item from the specified project. |  |
| `get_all_by_current_user_v2` | GET | `/api/v2/projects/{projectId}/history/user` | Retrieves all history items of the current user from the specified project. |  |
| `get_all_by_other_user_v2` | GET | `/api/v2/projects/{projectId}/history/user/{userId}` | Retrieves all history items of the given user from the specified project. |  |
| `get_all_by_project_v2` | GET | `/api/v2/projects/{projectId}/history` | Retrieves all history items in the specified project. |  |
| `analyze_sql_v2` | POST | `/api/v2/projects/{projectId}/sql/analyze` | Execute SQL analyze query. |  |
| `execute_sql_v2` | POST | `/api/v2/projects/{projectId}/sql/execute` | Execute SQL query. |  |
| `ensure_session` | POST | `/internal/session` | Ensures the session exists and returns session properties. |  |
| `reset_session` | POST | `/internal/session/reset` | Resets the session and returns the newly created session properties. |  |
| `configure` | POST | `/api/v2/samples/{sampleId}/configure` | Configures sampling. |  |
| `poll_result` | GET | `/api/v2/samples/{sampleId}` | Polls sample results. |  |
| `execute_in_session` | POST | `/internal/job/{jobId}/execute` | Can execute the given SSB job in both session and per_job execution mode. |  |
| `execute_sql_in_session` | POST | `/internal/job/execute` | Can execute the given SQL query in both session and per_job execution mode. |  |

## ssb_catalog

46 tools. **Partial source:** from HTML reference pages; may be incomplete.

- Product/version: Cloudera SQL Stream Builder (Streaming SQL Engine) REST API, Cloudera Streaming Analytics 1.18.0
- Spec source: https://docs.cloudera.com/csa/1.18.0/sql-stream-builder-rest-api-reference/index.html - from HTML docs (swagger-codegen html2 page generated from the service swagger; complete for that doc build, but no raw spec was published; may be partial vs. newer service builds). Live spec: http(s)://<host>:<ssb-port>/swagger/api-docs/public.
- Tags included: ArtifactOperations, ConnectorOperations, DDLTemplates, DataFormatOperations, DataSourceOperations, DatabaseInfo, EventStreamTypeOperations, KafkaController, ServiceDiscoveryController, TableOperations, UDFArtifactOperations, UDFOperations
- Auth: Base /api/v2 (older CSA: /api/v1/ssb). Kerberos SPNEGO (curl --negotiate), Knox (/gateway/cdp-proxy-api/ssb-sse-api/...) with basic/JWT, project API keys (APIKeyOperations), or Username header on unsecured clusters.
- Operation count: 46

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `delete_artifact_v2` | DELETE | `/api/v2/artifacts` | Delete an artifact that is available to the user. |  |
| `get_artifact_v2` | GET | `/api/v2/artifacts` | Lists artifacts available to the user. |  |
| `upload_artifact_v2` | POST | `/api/v2/artifacts` | Upload an artifact file. |  |
| `create_connector` | POST | `/api/v2/ddl/connectors` | Creates a Connector. |  |
| `delete_connector_by_id` | DELETE | `/api/v2/ddl/connectors/{id}` | Deletes a Connector by ID. |  |
| `delete_connector_by_type` | DELETE | `/api/v2/ddl/connectors/type/{type}` | Deletes a Connector by type. |  |
| `get_connector_by_id` | GET | `/api/v2/ddl/connectors/{id}` | Retrieves a Connector by ID. |  |
| `get_connector_by_type` | GET | `/api/v2/ddl/connectors/type/{type}` | Retrieves a Connector by type. |  |
| `get_connector_jar_file` | GET | `/api/v2/ddl/connectors/jar/{type}` | Retrieves a Connector JAR file. |  |
| `get_connectors` | GET | `/api/v2/ddl/connectors` | Retrieves all connectors. |  |
| `create_table` | POST | `/internal/ddl/create-table` | (no summary in source) create table |  |
| `create_data_format` | POST | `/api/v2/ddl/data-formats` | Creates a Data Format. |  |
| `delete_data_format_by_id` | DELETE | `/api/v2/ddl/data-formats/{id}` | Deletes a Data Format by ID. |  |
| `delete_data_format_by_type` | DELETE | `/api/v2/ddl/data-formats/type/{type}` | Deletes a Data Format by type. |  |
| `get_data_format_by_id` | GET | `/api/v2/ddl/data-formats/{id}` | Retrieves a Data Format by ID. |  |
| `get_data_format_by_type` | GET | `/api/v2/ddl/data-formats/type/{type}` | Retrieves a Connector by type. |  |
| `get_data_formats` | GET | `/api/v2/ddl/data-formats` | Retrieves all Data Formats. |  |
| `copy_data_source_v2` | POST | `/api/v2/projects/{projectId}/data-sources/{id}/copy` | Creates a copy of a data source in the specified project. |  |
| `create_data_source_v2` | POST | `/api/v2/projects/{projectId}/data-sources` | Creates a data source in the specified project. |  |
| `delete_data_source_v2` | DELETE | `/api/v2/projects/{projectId}/data-sources/{id}` | Deletes a data source from the specified project. |  |
| `get_data_source_in_project_by_id_v2` | GET | `/api/v2/projects/{projectId}/data-sources/{id}` | Retrieves a data source in the specified project by its id. |  |
| `get_data_sources_in_project_v2` | GET | `/api/v2/projects/{projectId}/data-sources` | Retrieves all data sources in the specified project. |  |
| `get_kafka_sources_in_project_v2` | GET | `/api/v2/projects/{projectId}/data-sources/kafka` | Retrieves Kafka data sources in the specified project. |  |
| `update_data_source_v2` | PUT | `/api/v2/projects/{projectId}/data-sources/{id}` | Updates an existing data source in the specified project. |  |
| `validate_data_source_v2` | POST | `/api/v2/projects/{projectId}/data-sources/validate` | Validates a data source as a Flink catalog in the active project. |  |
| `connect_string` | GET | `/internal/database/connect-string` | (no summary in source) connect string |  |
| `info` | GET | `/internal/database/info` | (no summary in source) info |  |
| `version` | GET | `/internal/database/version` | (no summary in source) version |  |
| `emit_sample_stream` | GET | `/api/v2/event-stream/samples/{sampleId}` | Polls job sample results in a streaming manner. |  |
| `get_dependent_catalogs` | GET | `/internal/kafka/{providerId}/dependent-catalogs` | (no summary in source) get dependent catalogs |  |
| `get_schema` | GET | `/internal/kafka/{providerId}/schema` | (no summary in source) get schema |  |
| `get_topics` | GET | `/internal/kafka/{providerId}/topics` | (no summary in source) get topics |  |
| `register_available_providers` | POST | `/internal/service-discovery` | (no summary in source) register available providers |  |
| `delete_table_by_project_id_and_id_v2` | DELETE | `/api/v2/projects/{projectId}/tables/{id}` | Delete a table in the specified project by its id. |  |
| `get_table_by_id_v2` | GET | `/api/v2/projects/{projectId}/tables/{id}` | Retrieve a table in the specified project by its id. |  |
| `get_tables_in_project_v2` | GET | `/api/v2/projects/{projectId}/tables` | Retrieve all tables in the specified project. |  |
| `get_tables_tree` | GET | `/api/v2/projects/{projectId}/tables/tree` | Retrieves a list of tables in hierarchical form organized by catalog. |  |
| `upsert_table` | POST | `/api/v2/projects/{projectId}/tables` | Create or update a table in the specified project. |  |
| `delete_jar_with_udfs_v2` | DELETE | `/api/v2/projects/{projectId}/udfs/artifact/{id}` | Deletes and Artifact along with all of its associated UDFs. |  |
| `get_jar_based_udfs_in_project_v2` | GET | `/api/v2/projects/{projectId}/udfs/artifact` | List all JAR-based UDFs in the specified project. |  |
| `upload_udf_jar_v2` | POST | `/api/v2/projects/{projectId}/udfs/artifact` | Upload a JAR and create UDFs from the contained classes. |  |
| `create_udf_v2` | POST | `/api/v2/projects/{projectId}/udfs` | Creates a UDF. |  |
| `delete_udf_v2` | DELETE | `/api/v2/projects/{projectId}/udfs/{id}` | Deletes a UDF by its id. |  |
| `get_all_udfs_in_project_v2` | GET | `/api/v2/projects/{projectId}/udfs` | Retrieves all UDFs in the specified project. |  |
| `get_udf_by_id_v2` | GET | `/api/v2/projects/{projectId}/udfs/{id}` | Retrieves a UDF by its id. |  |
| `update_udf_v2` | PUT | `/api/v2/projects/{projectId}/udfs` | Updates a UDF. |  |

## ssb_notifications

38 tools. **Partial source:** from HTML reference pages; may be incomplete.

- Product/version: Cloudera SQL Stream Builder (Streaming SQL Engine) REST API, Cloudera Streaming Analytics 1.18.0
- Spec source: https://docs.cloudera.com/csa/1.18.0/sql-stream-builder-rest-api-reference/index.html - from HTML docs (swagger-codegen html2 page generated from the service swagger; complete for that doc build, but no raw spec was published; may be partial vs. newer service builds). Live spec: http(s)://<host>:<ssb-port>/swagger/api-docs/public.
- Tags included: JobNotificationActionOperations, JobNotificationRuleController, JobNotificationRuleOperations, NotificationActionController
- Auth: Base /api/v2 (older CSA: /api/v1/ssb). Kerberos SPNEGO (curl --negotiate), Knox (/gateway/cdp-proxy-api/ssb-sse-api/...) with basic/JWT, project API keys (APIKeyOperations), or Username header on unsecured clusters.
- Operation count: 38

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `add_to_job_notification_group_v2` | POST | `/api/v2/projects/{projectId}/notification-actions/groups/{groupId}/child/{childId}` | Adds a Notification Action or Group to a Notification Group |  |
| `create_job_notification_group_v2` | POST | `/api/v2/projects/{projectId}/notification-actions/groups` | Creates a new Job Notification Group. |  |
| `create_job_notification_v2` | POST | `/api/v2/projects/{projectId}/notification-actions` | Creates a new Job Notification Action. |  |
| `delete_job_notification_v2` | DELETE | `/api/v2/projects/{projectId}/notification-actions/{id}` | Removes the given Job Notification Action. |  |
| `find_all_job_notification_by_job_id_v2` | GET | `/api/v2/projects/{projectId}/notification-actions/job/{jobId}` | Retrieves Job Notification Actions for the given job |  |
| `get_job_notification_group_children_v2` | GET | `/api/v2/projects/{projectId}/notification-actions/groups/{id}/children` | Retrieves the Notification Actions and Groups in a group. |  |
| `get_job_notification_group_v2` | GET | `/api/v2/projects/{projectId}/notification-actions/groups/{id}` | Retrieves the given Job Notification Group. |  |
| `get_job_notification_v2` | GET | `/api/v2/projects/{projectId}/notification-actions/{id}` | Retrieves the given Job Notification Action. |  |
| `get_notification_template_variables_v2` | GET | `/api/v2/projects/{projectId}/notification-actions/template-variables` | Retrieves the available template variables that are usable in notification templates |  |
| `list_all_job_notification_actions_v2` | GET | `/api/v2/projects/{projectId}/notification-actions` | Retrieves Job Notification Actions. |  |
| `remove_from_job_notification_group_v2` | DELETE | `/api/v2/projects/{projectId}/notification-actions/groups/{groupId}/child/{childId}` | Deletes a Notification Action or Group from a Notification Group |  |
| `resolve_job_notification_group_actions_v2` | GET | `/api/v2/projects/{projectId}/notification-actions/groups/{id}/resolve-actions` | Retrieves all the Notification Actions in a group, including every children the inner groups |  |
| `update_job_notification_group_v2` | PUT | `/api/v2/projects/{projectId}/notification-actions/groups/{id}` | Updates the given Job Notification Group. |  |
| `update_job_notification_v2` | PUT | `/api/v2/projects/{projectId}/notification-actions/{id}` | Updates the given Job Notification Action. |  |
| `validate_webhook_body_v2` | POST | `/api/v2/projects/{projectId}/notification-actions/validate` | Validates the Webhook body |  |
| `create_job_notification_rule` | POST | `/internal/job-notification-rules` | (no summary in source) create job notification rule |  |
| `delete_job_notification_rule` | DELETE | `/internal/job-notification-rules/{notificationRuleId}` | (no summary in source) delete job notification rule |  |
| `delete_job_notification_rule_by_job_id_and_notification_action_i` | DELETE | `/internal/job-notification-rules/job/{jobId}/notification-action/{notificationActionId}` | (no summary in source) delete job notification rule by job id and notification action id |  |
| `find_all_job_notifications_by_job_id` | GET | `/internal/job-notification-rules/{jobId}` | (no summary in source) find all job notifications by job id |  |
| `create_job_notification_rule_v2` | POST | `/api/v2/projects/{projectId}/job-notification-rules` | Links a Job Notification Action to a Group. |  |
| `delete_job_notification_rule_by_job_id_and_notification_action_2` | DELETE | `/api/v2/projects/{projectId}/job-notification-rules/job/{jobId}/notification-action/{notificationActionId}` | Removes the given Job Notification Action from the job. |  |
| `delete_job_notification_rule_v2` | DELETE | `/api/v2/projects/{projectId}/job-notification-rules/{notificationRuleId}` | Removes the given Job Notification Rule. |  |
| `find_all_job_notifications_by_job_id_v2` | GET | `/api/v2/projects/{projectId}/job-notification-rules/{jobId}` | Retrieves Job Notification Actions for the given job. |  |
| `add_to_job_notification_group` | POST | `/internal/notification-actions/groups/{groupId}/child/{childId}` | (no summary in source) add to job notification group |  |
| `create_job_notification` | POST | `/internal/notification-actions` | (no summary in source) create job notification |  |
| `create_job_notification_group` | POST | `/internal/notification-actions/groups` | (no summary in source) create job notification group |  |
| `delete_job_notification` | DELETE | `/internal/notification-actions/{id}` | (no summary in source) delete job notification |  |
| `find_all_job_notification_by_job_id` | GET | `/internal/notification-actions/job/{jobId}` | (no summary in source) find all job notification by job id |  |
| `get_job_notification` | GET | `/internal/notification-actions/{id}` | (no summary in source) get job notification |  |
| `get_job_notification_group` | GET | `/internal/notification-actions/groups/{id}` | (no summary in source) get job notification group |  |
| `get_job_notification_group_children` | GET | `/internal/notification-actions/groups/{id}/children` | (no summary in source) get job notification group children |  |
| `get_notification_template_variables` | GET | `/internal/notification-actions/template-variables` | (no summary in source) get notification template variables |  |
| `list_all_job_notification_actions` | GET | `/internal/notification-actions` | (no summary in source) list all job notification actions |  |
| `remove_from_job_notification_group` | DELETE | `/internal/notification-actions/groups/{groupId}/child/{childId}` | (no summary in source) remove from job notification group |  |
| `resolve_job_notification_group_actions` | GET | `/internal/notification-actions/groups/{id}/resolve-actions` | (no summary in source) resolve job notification group actions |  |
| `update_job_notification` | PUT | `/internal/notification-actions/{id}` | (no summary in source) update job notification |  |
| `update_job_notification_group` | PUT | `/internal/notification-actions/groups/{id}` | (no summary in source) update job notification group |  |
| `validate_webhook_body` | POST | `/internal/notification-actions/validate` | (no summary in source) validate webhook body |  |

## ssb_flink_dashboard

27 tools. **Partial source:** from HTML reference pages; may be incomplete.

- Product/version: Cloudera SQL Stream Builder (Streaming SQL Engine) REST API, Cloudera Streaming Analytics 1.18.0
- Spec source: https://docs.cloudera.com/csa/1.18.0/sql-stream-builder-rest-api-reference/index.html - from HTML docs (swagger-codegen html2 page generated from the service swagger; complete for that doc build, but no raw spec was published; may be partial vs. newer service builds). Live spec: http(s)://<host>:<ssb-port>/swagger/api-docs/public.
- Tags included: FlinkDashboard, KubernetesCustomResourceOperations, KubernetesFlinkDashboardProxyControllerV2
- Auth: Base /api/v2 (older CSA: /api/v1/ssb). Kerberos SPNEGO (curl --negotiate), Knox (/gateway/cdp-proxy-api/ssb-sse-api/...) with basic/JWT, project API keys (APIKeyOperations), or Username header on unsecured clusters.
- Operation count: 27

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `get_all_jobs_overview` | GET | `/ui/flink/jobs/overview` | (no summary in source) get all jobs overview |  |
| `get_all_overview` | GET | `/ui/flink/overview` | (no summary in source) get all overview |  |
| `get_config` | GET | `/ui/flink/config` | (no summary in source) get config |  |
| `redirect_to_index` | GET | `/ui/flink` | (no summary in source) redirect to index |  |
| `redirect_to_index1` | GET | `/ui/flink/` | (no summary in source) redirect to index1 |  |
| `route_job_request` | GET | `/ui/flink/jobs/{jobId}/**` | (no summary in source) route job request |  |
| `route_job_request1` | POST | `/ui/flink/jobs/{jobId}/**` | (no summary in source) route job request1 |  |
| `route_job_request2` | PUT | `/ui/flink/jobs/{jobId}/**` | (no summary in source) route job request2 |  |
| `route_job_request3` | DELETE | `/ui/flink/jobs/{jobId}/**` | (no summary in source) route job request3 |  |
| `route_job_request4` | PATCH | `/ui/flink/jobs/{jobId}/**` | (no summary in source) route job request4 |  |
| `route_job_request5` | HEAD | `/ui/flink/jobs/{jobId}/**` | (no summary in source) route job request5 |  |
| `route_job_request6` | OPTIONS | `/ui/flink/jobs/{jobId}/**` | (no summary in source) route job request6 |  |
| `route_task_request` | GET | `/ui/flink/taskmanagers/{tmId}/**` | (no summary in source) route task request |  |
| `route_task_request1` | POST | `/ui/flink/taskmanagers/{tmId}/**` | (no summary in source) route task request1 |  |
| `route_task_request2` | PUT | `/ui/flink/taskmanagers/{tmId}/**` | (no summary in source) route task request2 |  |
| `route_task_request3` | DELETE | `/ui/flink/taskmanagers/{tmId}/**` | (no summary in source) route task request3 |  |
| `route_task_request4` | PATCH | `/ui/flink/taskmanagers/{tmId}/**` | (no summary in source) route task request4 |  |
| `route_task_request5` | HEAD | `/ui/flink/taskmanagers/{tmId}/**` | (no summary in source) route task request5 |  |
| `route_task_request6` | OPTIONS | `/ui/flink/taskmanagers/{tmId}/**` | (no summary in source) route task request6 |  |
| `delete_job_resource` | DELETE | `/api/v2/kubernetes/resources/jobs/{id}` | Removes the kubernetes custom resource associated with the given job. |  |
| `proxy_flink_dashboard` | GET | `/flink-dashboard/{jobId}/**` | (no summary in source) proxy flink dashboard |  |
| `proxy_flink_dashboard1` | POST | `/flink-dashboard/{jobId}/**` | (no summary in source) proxy flink dashboard1 |  |
| `proxy_flink_dashboard2` | PUT | `/flink-dashboard/{jobId}/**` | (no summary in source) proxy flink dashboard2 |  |
| `proxy_flink_dashboard3` | DELETE | `/flink-dashboard/{jobId}/**` | (no summary in source) proxy flink dashboard3 |  |
| `proxy_flink_dashboard4` | PATCH | `/flink-dashboard/{jobId}/**` | (no summary in source) proxy flink dashboard4 |  |
| `proxy_flink_dashboard5` | HEAD | `/flink-dashboard/{jobId}/**` | (no summary in source) proxy flink dashboard5 |  |
| `proxy_flink_dashboard6` | OPTIONS | `/flink-dashboard/{jobId}/**` | (no summary in source) proxy flink dashboard6 |  |

## ssb_admin

25 tools. **Partial source:** from HTML reference pages; may be incomplete.

- Product/version: Cloudera SQL Stream Builder (Streaming SQL Engine) REST API, Cloudera Streaming Analytics 1.18.0
- Spec source: https://docs.cloudera.com/csa/1.18.0/sql-stream-builder-rest-api-reference/index.html - from HTML docs (swagger-codegen html2 page generated from the service swagger; complete for that doc build, but no raw spec was published; may be partial vs. newer service builds). Live spec: http(s)://<host>:<ssb-port>/swagger/api-docs/public.
- Tags included: AdminOperations, GlobalConfigurationOperations, Heartbeat, RegisterOperations, UiConfigController, UserKeytabOperations, UserOperations
- Auth: Base /api/v2 (older CSA: /api/v1/ssb). Kerberos SPNEGO (curl --negotiate), Knox (/gateway/cdp-proxy-api/ssb-sse-api/...) with basic/JWT, project API keys (APIKeyOperations), or Username header on unsecured clusters.
- Operation count: 25

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `generate_keytab1` | POST | `/api/v2/admin/users/{userId}/keytab/generate` | Generates a keytab for the user with the given credentials. |  |
| `get_diagnostics` | GET | `/api/v2/admin/diag` | (no summary in source) get diagnostics |  |
| `update_user_password1` | PATCH | `/api/v2/admin/users/{userId}/password` | Updates the password for the user. |  |
| `upload_keytab1` | POST | `/api/v2/admin/users/{userId}/keytab/upload` | Uploads a keytab file for the user with the given credentials. |  |
| `bulk_update_global_config` | PUT | `/api/v1/global-configs/bulk-update` | Bulk updates global configurations. |  |
| `bulk_update_global_config1` | PUT | `/api/v2/global-configs/bulk-update` | Bulk updates global configurations. |  |
| `get_all_global_config` | GET | `/api/v2/global-configs` | Retrieves all global configurations. |  |
| `get_all_global_config1` | GET | `/api/v1/global-configs` | Retrieves all global configurations. |  |
| `get_global_config_value` | GET | `/api/v1/global-configs/{key}` | Retrieves the global configuration of the given config key. |  |
| `get_global_config_value1` | GET | `/api/v2/global-configs/{key}` | Retrieves the global configuration of the given config key. |  |
| `update_global_config` | PUT | `/api/v2/global-configs` | Updates a global configuration. |  |
| `update_global_config1` | PUT | `/api/v1/global-configs` | Updates a global configuration. |  |
| `validate_sampling_global_config` | POST | `/api/v2/global-configs/validate-sampling` | Validates sampling Kafka global configurations. |  |
| `validate_sampling_global_config1` | POST | `/api/v1/global-configs/validate-sampling` | Validates sampling Kafka global configurations. |  |
| `heartbeat` | GET | `/api/v2/heartbeat` | (no summary in source) heartbeat |  |
| `register_user` | POST | `/internal/register` | Registers a new user. |  |
| `get_config1` | GET | `/internal/ui-config` | (no summary in source) get config1 |  |
| `generate_keytab` | POST | `/api/v2/user/keytab/generate` | Generates a keytab for the authenticated user with the given credentials. |  |
| `remove_keytab` | DELETE | `/api/v2/user/keytab` | Removes the keytab file for the authenticated user. |  |
| `upload_keytab` | POST | `/api/v2/user/keytab/upload` | Uploads a keytab file for the authenticated user with the given credentials. |  |
| `get_current_user` | GET | `/api/v2/user` | Retrieves the currently authenticated user. |  |
| `get_user_settings` | GET | `/api/v2/user/settings` | Returns the frontend settings of the currently authenticated user. |  |
| `update_active_project` | PATCH | `/api/v2/user/project` | Updates the active project for the currently authenticated user. |  |
| `update_user_password` | PATCH | `/api/v2/user/password` | Updates the password for the currently authenticated user. |  |
| `update_user_settings` | PUT | `/api/v2/user/settings` | Updates the frontend settings of the authenticated user. |  |

## flink

70 tools.

- Product/version: Apache Flink JobManager REST API v1, Flink 1.20 (CSA 1.18 ships Flink 1.20.5)
- Spec source: https://raw.githubusercontent.com/apache/flink/release-1.20/docs/static/generated/rest_v1_dispatcher.yml (OpenAPI 3.0.1)
- Tags included: (untagged)
- Auth: JobManager REST (YARN: via RM proxy / Flink dashboard; port rest.port). No built-in auth: secure via Kerberos SPNEGO on YARN proxy, Knox (/gateway/cdp-proxy/flink-dashboard or SSB FlinkDashboard proxy), or SSL mutual auth (security.ssl.rest.*).
- Operation count: 70

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `shutdown_cluster` | DELETE | `/v1/cluster` | Shuts down the cluster |  |
| `get_dashboard_configuration` | GET | `/v1/config` | Returns the configuration of the WebUI. |  |
| `get_cluster_data_set_list` | GET | `/v1/datasets` | Returns all cluster data sets. |  |
| `get_cluster_data_set_delete_status` | GET | `/v1/datasets/delete/{triggerid}` | Returns the status for the delete operation of a cluster data set. |  |
| `delete_cluster_data_set` | DELETE | `/v1/datasets/{datasetid}` | Triggers the deletion of a cluster data set. |  |
| `get_jar_list` | GET | `/v1/jars` | Returns a list of all jars previously uploaded via '/jars/upload'. |  |
| `upload_jar` | POST | `/v1/jars/upload` | Uploads a jar to the cluster. |  |
| `delete_jar` | DELETE | `/v1/jars/{jarid}` | Deletes a jar previously uploaded via '/jars/upload'. |  |
| `generate_plan_from_jar` | POST | `/v1/jars/{jarid}/plan` | Returns the dataflow plan of a job contained in a jar previously uploaded via '/jars/upload'. |  |
| `submit_job_from_jar` | POST | `/v1/jars/{jarid}/run` | Submits a job by running a jar previously uploaded via '/jars/upload'. |  |
| `get_cluster_configuration_info` | GET | `/v1/jobmanager/config` | Returns the cluster configuration. |  |
| `get_job_manager_environment` | GET | `/v1/jobmanager/environment` | Returns the jobmanager environment. |  |
| `get_job_manager_log_list` | GET | `/v1/jobmanager/logs` | Returns the list of log files on the JobManager. |  |
| `get_job_manager_metrics` | GET | `/v1/jobmanager/metrics` | Provides access to job manager metrics. |  |
| `get_job_manager_thread_dump` | GET | `/v1/jobmanager/thread-dump` | Returns the thread dump of the JobManager. |  |
| `get_job_ids_with_statuses_overview` | GET | `/v1/jobs` | Returns an overview over all jobs and their current state. |  |
| `submit_job` | POST | `/v1/jobs` | Submits a job. |  |
| `get_aggregated_job_metrics` | GET | `/v1/jobs/metrics` | Provides access to aggregated job metrics. |  |
| `get_jobs_overview` | GET | `/v1/jobs/overview` | Returns an overview over all jobs. |  |
| `get_job_details` | GET | `/v1/jobs/{jobid}` | Returns details of a job. |  |
| `cancel_job` | PATCH | `/v1/jobs/{jobid}` | Terminates a job. |  |
| `get_job_accumulators` | GET | `/v1/jobs/{jobid}/accumulators` | Returns the accumulators for all tasks of a job, aggregated across the respective subtasks. |  |
| `get_checkpointing_statistics` | GET | `/v1/jobs/{jobid}/checkpoints` | Returns checkpointing statistics for a job. |  |
| `trigger_checkpoint` | POST | `/v1/jobs/{jobid}/checkpoints` | Triggers a checkpoint. |  |
| `get_checkpoint_config` | GET | `/v1/jobs/{jobid}/checkpoints/config` | Returns the checkpointing configuration. |  |
| `get_checkpoint_statistic_details` | GET | `/v1/jobs/{jobid}/checkpoints/details/{checkpointid}` | Returns details for a checkpoint. |  |
| `get_task_checkpoint_statistics` | GET | `/v1/jobs/{jobid}/checkpoints/details/{checkpointid}/subtasks/{vertexid}` | Returns checkpoint statistics for a task and its subtasks. |  |
| `get_checkpoint_status` | GET | `/v1/jobs/{jobid}/checkpoints/{triggerid}` | Returns the status of a checkpoint trigger operation. |  |
| `trigger_heartbeat` | PATCH | `/v1/jobs/{jobid}/clientHeartbeat` | Report the jobClient's aliveness. |  |
| `get_job_config` | GET | `/v1/jobs/{jobid}/config` | Returns the configuration of a job. |  |
| `get_job_exceptions` | GET | `/v1/jobs/{jobid}/exceptions` | Returns the most recent exceptions that have been handled by Flink for this job. |  |
| `get_job_execution_result` | GET | `/v1/jobs/{jobid}/execution-result` | Returns the result of a job execution. |  |
| `get_job_manager_job_configuration` | GET | `/v1/jobs/{jobid}/jobmanager/config` | Returns the jobmanager's configuration of a specific job. |  |
| `get_job_manager_job_environment` | GET | `/v1/jobs/{jobid}/jobmanager/environment` | Returns the jobmanager's environment of a specific job. |  |
| `get_job_manager_log_url` | GET | `/v1/jobs/{jobid}/jobmanager/log-url` | Returns the log url of jobmanager of a specific job. |  |
| `get_job_metrics` | GET | `/v1/jobs/{jobid}/metrics` | Provides access to job metrics. |  |
| `get_job_plan` | GET | `/v1/jobs/{jobid}/plan` | Returns the dataflow plan of a job. |  |
| `rescale_job` | PATCH | `/v1/jobs/{jobid}/rescaling` | Triggers the rescaling of a job. |  |
| `get_rescaling_status` | GET | `/v1/jobs/{jobid}/rescaling/{triggerid}` | Returns the status of a rescaling operation. |  |
| `get_job_resource_requirements` | GET | `/v1/jobs/{jobid}/resource-requirements` | Request details on the job's resource requirements. |  |
| `update_job_resource_requirements` | PUT | `/v1/jobs/{jobid}/resource-requirements` | Request to update job's resource requirements. |  |
| `trigger_savepoint` | POST | `/v1/jobs/{jobid}/savepoints` | Triggers a savepoint, and optionally cancels the job afterwards. |  |
| `get_savepoint_status` | GET | `/v1/jobs/{jobid}/savepoints/{triggerid}` | Returns the status of a savepoint operation. |  |
| `get_job_status_info` | GET | `/v1/jobs/{jobid}/status` | Returns the current status of a job execution. |  |
| `trigger_stop_with_savepoint` | POST | `/v1/jobs/{jobid}/stop` | Stops a job with a savepoint. |  |
| `get_task_manager_log_url` | GET | `/v1/jobs/{jobid}/taskmanagers/{taskmanagerid}/log-url` | Returns the log url of jobmanager of a specific job. |  |
| `get_job_vertex_details` | GET | `/v1/jobs/{jobid}/vertices/{vertexid}` | Returns details for a task, with a summary for each of its subtasks. |  |
| `get_job_vertex_accumulators` | GET | `/v1/jobs/{jobid}/vertices/{vertexid}/accumulators` | Returns user-defined accumulators of a task, aggregated across all subtasks. |  |
| `get_job_vertex_back_pressure` | GET | `/v1/jobs/{jobid}/vertices/{vertexid}/backpressure` | Returns back-pressure information for a job, and may initiate back-pressure sampling if necessary. |  |
| `get_job_vertex_flame_graph` | GET | `/v1/jobs/{jobid}/vertices/{vertexid}/flamegraph` | Returns flame graph information for a vertex, and may initiate flame graph sampling if necessary. |  |
| `get_job_manager_operator_metrics` | GET | `/v1/jobs/{jobid}/vertices/{vertexid}/jm-operator-metrics` | Provides access to jobmanager operator metrics. |  |
| `get_job_vertex_metrics` | GET | `/v1/jobs/{jobid}/vertices/{vertexid}/metrics` | Provides access to task metrics. |  |
| `get_subtasks_all_accumulators` | GET | `/v1/jobs/{jobid}/vertices/{vertexid}/subtasks/accumulators` | Returns all user-defined accumulators for all subtasks of a task. |  |
| `get_aggregated_subtask_metrics` | GET | `/v1/jobs/{jobid}/vertices/{vertexid}/subtasks/metrics` | Provides access to aggregated subtask metrics. |  |
| `get_subtask_current_attempt_details` | GET | `/v1/jobs/{jobid}/vertices/{vertexid}/subtasks/{subtaskindex}` | Returns details of the current or latest execution attempt of a subtask. |  |
| `get_subtask_execution_attempt_details` | GET | `/v1/jobs/{jobid}/vertices/{vertexid}/subtasks/{subtaskindex}/attempts/{attempt}` | Returns details of an execution attempt of a subtask. |  |
| `get_subtask_execution_attempt_accumulators` | GET | `/v1/jobs/{jobid}/vertices/{vertexid}/subtasks/{subtaskindex}/attempts/{attempt}/accumulators` | Returns the accumulators of an execution attempt of a subtask. |  |
| `get_subtask_metrics` | GET | `/v1/jobs/{jobid}/vertices/{vertexid}/subtasks/{subtaskindex}/metrics` | Provides access to subtask metrics. |  |
| `get_subtasks_times` | GET | `/v1/jobs/{jobid}/vertices/{vertexid}/subtasktimes` | Returns time-related information for all subtasks of a task. |  |
| `get_job_vertex_task_managers` | GET | `/v1/jobs/{jobid}/vertices/{vertexid}/taskmanagers` | Returns task information aggregated by task manager. |  |
| `get_job_vertex_watermarks` | GET | `/v1/jobs/{jobid}/vertices/{vertexid}/watermarks` | Returns the watermarks for all subtasks of a task. |  |
| `get_cluster_overview` | GET | `/v1/overview` | Returns an overview over the Flink cluster. |  |
| `trigger_savepoint_disposal` | POST | `/v1/savepoint-disposal` | Triggers the desposal of a savepoint. |  |
| `get_savepoint_disposal_status` | GET | `/v1/savepoint-disposal/{triggerid}` | Returns the status of a savepoint disposal operation. |  |
| `get_task_managers` | GET | `/v1/taskmanagers` | Returns an overview over all task managers. |  |
| `get_aggregated_task_manager_metrics` | GET | `/v1/taskmanagers/metrics` | Provides access to aggregated task manager metrics. |  |
| `get_task_manager_details` | GET | `/v1/taskmanagers/{taskmanagerid}` | Returns details for a task manager. |  |
| `get_task_manager_logs` | GET | `/v1/taskmanagers/{taskmanagerid}/logs` | Returns the list of log files on a TaskManager. |  |
| `get_task_manager_metrics` | GET | `/v1/taskmanagers/{taskmanagerid}/metrics` | Provides access to task manager metrics. |  |
| `get_task_manager_thread_dump` | GET | `/v1/taskmanagers/{taskmanagerid}/thread-dump` | Returns the thread dump of the requested TaskManager. |  |

## flink_sql_gateway

14 tools.

- Product/version: Apache Flink SQL Gateway REST API v3, Flink 1.20 (paths are prefixed /v1../v3; v3 is the latest in 1.20). Not used by SSB, which has its own engine; include only if CSA deployments run the SQL Gateway.
- Spec source: https://raw.githubusercontent.com/apache/flink/release-1.20/docs/static/generated/rest_v3_sql_gateway.yml (OpenAPI 3.0.1)
- Tags included: (untagged)
- Auth: SQL Gateway REST endpoint (sql-gateway.endpoint.rest.port, default 8083). No built-in auth; front with Knox/TLS.
- Operation count: 14

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `get_api_version` | GET | `/v3/api_versions` | Get the current available versions for the Rest Endpoint. |  |
| `get_info` | GET | `/v3/info` | Get meta data for this cluster. |  |
| `open_session` | POST | `/v3/sessions` | Opens a new session with specific properties. |  |
| `get_session_config` | GET | `/v3/sessions/{session_handle}` | Get the session configuration. |  |
| `close_session` | DELETE | `/v3/sessions/{session_handle}` | Closes the specific session. |  |
| `complete_statement` | GET | `/v3/sessions/{session_handle}/complete-statement` | Get the completion hints for the given statement at the given position. |  |
| `configure_session` | POST | `/v3/sessions/{session_handle}/configure-session` | Configures the session with the statement which could be: CREATE TABLE, DROP TABLE, ALTER TABLE, CREATE DATABASE, DROP DATABASE, ALTER DATABASE, CREATE FUNCTION, DROP FUNCTION, ALTER FUNCTION, CREATE  |  |
| `trigger_session` | POST | `/v3/sessions/{session_handle}/heartbeat` | Trigger heartbeat to tell the server that the client is active, and to keep the session alive as long as configured timeout value. |  |
| `refresh_materialized_table` | POST | `/v3/sessions/{session_handle}/materialized-tables/{identifier}/refresh` | Refresh materialized table |  |
| `cancel_operation` | POST | `/v3/sessions/{session_handle}/operations/{operation_handle}/cancel` | Cancel the operation. |  |
| `close_operation` | DELETE | `/v3/sessions/{session_handle}/operations/{operation_handle}/close` | Close the operation. |  |
| `fetch_results` | GET | `/v3/sessions/{session_handle}/operations/{operation_handle}/result/{token}` | Fetch results of Operation. |  |
| `get_operation_status` | GET | `/v3/sessions/{session_handle}/operations/{operation_handle}/status` | Get the status of operation. |  |
| `execute_statement` | POST | `/v3/sessions/{session_handle}/statements` | Execute a statement. |  |
