# Data services and Runtime components

Cloudera AI Workbench, Data Engineering, Ranger, Atlas, Knox, HDFS, Ozone, YARN, Livy, Oozie, HBase, Solr, Hue and Data Visualization.

Flags: **beta** = not in the GA spec; **deprecated** = marked deprecated by the vendor spec; **in built-in pack** = the existing Daedalus `hdfs`/`s3` pack already has it.

## cml_workbench_projects

33 tools.

- Product: Cloudera AI (CML) Workbench API v2
- Version: spec 24.11.21 (public cloud docs; Private Cloud 1.5.5 spec is 22.04.01 with 38 paths)
- Spec source: https://docs.cloudera.com/machine-learning/cloud/rest-api-reference/swagger.json (also served by each workbench at /api/v2/swagger.json)
- Auth: Bearer API v2 key (Authorization: Bearer <key>) created in User Settings > API Keys; base https://<workbench-domain>
- Scope: projects, collaborators, files, jobs/runs, applications
- Operations: 33

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `list_all_jobs` | GET | `/api/v2/jobs` | Returns all jobs a user has access to. |  |
| `list_project_names` | GET | `/api/v2/projectnames` | Return all the project names the user has access to, optionally filtered, sorted, and paginated. |  |
| `list_projects` | GET | `/api/v2/projects` | Return all projects, optionally filtered, sorted, and paginated. |  |
| `create_project` | POST | `/api/v2/projects` | Create a new project. |  |
| `batch_list_projects` | GET | `/api/v2/projects/batch` | Return a list of projects given a list of project IDs. This method will only return |  |
| `update_project` | PATCH | `/api/v2/projects/{project.id}` | Update an existing project. |  |
| `get_project` | GET | `/api/v2/projects/{project_id}` | Return one project. |  |
| `delete_project` | DELETE | `/api/v2/projects/{project_id}` | Delete a project. |  |
| `list_applications` | GET | `/api/v2/projects/{project_id}/applications` | List applications, optionally filtered, sorted, and paginated. |  |
| `create_application` | POST | `/api/v2/projects/{project_id}/applications` | Create an application and implicitly start it immediately. |  |
| `update_application` | PATCH | `/api/v2/projects/{project_id}/applications/{application.id}` | Update an application |  |
| `get_application` | GET | `/api/v2/projects/{project_id}/applications/{application_id}` | Get an application. |  |
| `delete_application` | DELETE | `/api/v2/projects/{project_id}/applications/{application_id}` | Delete an application. |  |
| `restart_application` | POST | `/api/v2/projects/{project_id}/applications/{application_id}:restart` | Start an application. |  |
| `stop_application` | POST | `/api/v2/projects/{project_id}/applications/{application_id}:stop` | Stop an application. |  |
| `list_project_collaborators` | GET | `/api/v2/projects/{project_id}/collaborators` | List project collaborators. |  |
| `delete_project_collaborator` | DELETE | `/api/v2/projects/{project_id}/collaborators/{username}` | Delete a project collaborator |  |
| `add_project_collaborator` | PUT | `/api/v2/projects/{project_id}/collaborators/{username}` | Add a project collaborator |  |
| `list_project_files` | GET | `/api/v2/projects/{project_id}/files/{path}` | List files/subdirectories at a specified path |  |
| `delete_project_file` | DELETE | `/api/v2/projects/{project_id}/files/{path}` | Delete a file or directory. |  |
| `update_project_file_metadata` | PATCH | `/api/v2/projects/{project_id}/files/{path}` | Update file metadata, such as renaming. |  |
| `list_jobs` | GET | `/api/v2/projects/{project_id}/jobs` | Returns all jobs, optionally filtered, sorted, and paginated. |  |
| `create_job` | POST | `/api/v2/projects/{project_id}/jobs` | Create a new job. |  |
| `update_job` | PATCH | `/api/v2/projects/{project_id}/jobs/{job.id}` | Updates a job. |  |
| `get_job` | GET | `/api/v2/projects/{project_id}/jobs/{job_id}` | Return one job. |  |
| `delete_job` | DELETE | `/api/v2/projects/{project_id}/jobs/{job_id}` | Deletes a job. |  |
| `list_job_runs` | GET | `/api/v2/projects/{project_id}/jobs/{job_id}/runs` | Lists job runs, optionally filtered, sorted, and paginated. |  |
| `create_job_run` | POST | `/api/v2/projects/{project_id}/jobs/{job_id}/runs` | Create and start a new job run for a job. |  |
| `get_job_run` | GET | `/api/v2/projects/{project_id}/jobs/{job_id}/runs/{run_id}` | Gets a job run. |  |
| `stop_job_run` | POST | `/api/v2/projects/{project_id}/jobs/{job_id}/runs/{run_id}:stop` | Stops a job run. Encoded as a custom method. |  |
| `list_all_run_as_machine_user_collaborators` | GET | `/api/v2/projects/{project_id}/machineusers` | List all run as machine user collaborators (GET /api/v2/projects/{project_id}/machineusers) |  |
| `upload_file` | POST | `/api/v2/projects/{project_id}/files` | upload a file as a multi-part upload |  |
| `download_project_file` | POST | `/api/v2/projects/{project_id}/files/{path}:download` | download a project file |  |

## cml_workbench_models

41 tools.

- Product: Cloudera AI (CML) Workbench API v2
- Version: spec 24.11.21 (public cloud docs; Private Cloud 1.5.5 spec is 22.04.01 with 38 paths)
- Spec source: https://docs.cloudera.com/machine-learning/cloud/rest-api-reference/swagger.json (also served by each workbench at /api/v2/swagger.json)
- Auth: Bearer API v2 key (Authorization: Bearer <key>) created in User Settings > API Keys; base https://<workbench-domain>
- Scope: models/builds/deployments, model registry, experiments/runs
- Operations: 41

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `list_copilot_models` | GET | `/api/v2/copilot/models` | List Copilot models, optionally filtered, sorted, and paginated. |  |
| `create_copilot_model` | POST | `/api/v2/copilot/models` | Create a Copilot model. |  |
| `update_copilot_model` | PATCH | `/api/v2/copilot/models/{copilot_model.id}` | Update a Copilot model. |  |
| `delete_copilot_model` | DELETE | `/api/v2/copilot/models/{copilot_model_id}` | Delete a Copilot model. |  |
| `list_all_experiments` | GET | `/api/v2/experiments` | Lists all experiments that belong to a user across all projects. |  |
| `list_all_models` | GET | `/api/v2/models` | List all models that belong to a user across all projects. |  |
| `update_experiment` | PATCH | `/api/v2/projects/{experiment.project_id}/experiments/{experiment.id}` | Update an existing experiment. |  |
| `list_experiments` | GET | `/api/v2/projects/{project_id}/experiments` | List all experiments in a given project. |  |
| `create_experiment` | POST | `/api/v2/projects/{project_id}/experiments` | Create an experiment. |  |
| `get_experiment` | GET | `/api/v2/projects/{project_id}/experiments/{experiment_id}` | Return one experiment. |  |
| `delete_experiment` | DELETE | `/api/v2/projects/{project_id}/experiments/{experiment_id}` | Delete an experiment that belongs to an experiment id. |  |
| `list_experiment_runs` | GET | `/api/v2/projects/{project_id}/experiments/{experiment_id}/runs` | Returns a list of Runs that belong to an experiment. |  |
| `create_experiment_run` | POST | `/api/v2/projects/{project_id}/experiments/{experiment_id}/runs` | Create a run for an experiment. |  |
| `update_experiment_run` | PATCH | `/api/v2/projects/{project_id}/experiments/{experiment_id}/runs/{run.id}` | Update an experiment run. |  |
| `get_experiment_run` | GET | `/api/v2/projects/{project_id}/experiments/{experiment_id}/runs/{run_id}` | Get metadata, metrics, params, tags and artifacts for a run. In the case where multiple metrics |  |
| `delete_experiment_run` | DELETE | `/api/v2/projects/{project_id}/experiments/{experiment_id}/runs/{run_id}` | Delete an experiment run. |  |
| `get_experiment_run_metrics` | GET | `/api/v2/projects/{project_id}/experiments/{experiment_id}/runs/{run_id}/metrics/{metric_key}` | Gets the all the recorded metrics for the key for a given run. |  |
| `delete_experiment_run_batch` | POST | `/api/v2/projects/{project_id}/experiments/{experiment_id}/runs/{run_id}:deletebatch` | Bulk delete an experiment run details like metrics, params, tags in one request. |  |
| `log_experiment_run_batch` | POST | `/api/v2/projects/{project_id}/experiments/{experiment_id}/runs/{run_id}:logbatch` | Bulk update an experiment run details like metrics, params, tags in one request. |  |
| `list_models` | GET | `/api/v2/projects/{project_id}/models` | List models, optionally filtered, sorted, and paginated. |  |
| `create_model` | POST | `/api/v2/projects/{project_id}/models` | Create a model. |  |
| `update_model` | PATCH | `/api/v2/projects/{project_id}/models/{model.id}` | Update a model. |  |
| `get_model` | GET | `/api/v2/projects/{project_id}/models/{model_id}` | Get a model. |  |
| `delete_model` | DELETE | `/api/v2/projects/{project_id}/models/{model_id}` | Delete a model. |  |
| `list_model_builds` | GET | `/api/v2/projects/{project_id}/models/{model_id}/builds` | List model builds, optionally filtered, sorted, and paginated. |  |
| `create_model_build` | POST | `/api/v2/projects/{project_id}/models/{model_id}/builds` | Create a model build. |  |
| `get_model_build` | GET | `/api/v2/projects/{project_id}/models/{model_id}/builds/{build_id}` | Get a model build. |  |
| `delete_model_build` | DELETE | `/api/v2/projects/{project_id}/models/{model_id}/builds/{build_id}` | Delete a model build. |  |
| `list_model_deployments` | GET | `/api/v2/projects/{project_id}/models/{model_id}/builds/{build_id}/deployments` | List model deployments, optionally filtered, sorted, and paginated. |  |
| `create_model_deployment` | POST | `/api/v2/projects/{project_id}/models/{model_id}/builds/{build_id}/deployments` | Create a model deployment. |  |
| `get_model_deployment` | GET | `/api/v2/projects/{project_id}/models/{model_id}/builds/{build_id}/deployments/{deployment_id}` | Get a model deployment. |  |
| `restart_model_deployment` | POST | `/api/v2/projects/{project_id}/models/{model_id}/builds/{build_id}/deployments/{deployment_id}:restart` | Restart a model deployment. |  |
| `stop_model_deployment` | POST | `/api/v2/projects/{project_id}/models/{model_id}/builds/{build_id}/deployments/{deployment_id}:stop` | Stop a model deployment. |  |
| `list_registered_models` | GET | `/api/v2/registry/models` | List registered models. |  |
| `create_registered_model` | POST | `/api/v2/registry/models` | Register a model. |  |
| `update_registered_model` | PATCH | `/api/v2/registry/models` | Update a Registered model. |  |
| `get_registered_model` | GET | `/api/v2/registry/models/{model_id}` | Get a registered model. |  |
| `delete_registered_model` | DELETE | `/api/v2/registry/models/{model_id}` | Unregister a model deletes a model. |  |
| `update_registered_model_version` | PATCH | `/api/v2/registry/models/{model_id}` | Update a Registered model version. |  |
| `get_registered_model_version` | GET | `/api/v2/registry/models/{model_id}/versions/{version_id}` | Get a registered model version |  |
| `delete_registered_model_version` | DELETE | `/api/v2/registry/models/{model_id}/versions/{version_id}` | Unregister a model version. |  |

## cml_workbench_admin

32 tools.

- Product: Cloudera AI (CML) Workbench API v2
- Version: spec 24.11.21 (public cloud docs; Private Cloud 1.5.5 spec is 22.04.01 with 38 paths)
- Spec source: https://docs.cloudera.com/machine-learning/cloud/rest-api-reference/swagger.json (also served by each workbench at /api/v2/swagger.json)
- Auth: Bearer API v2 key (Authorization: Bearer <key>) created in User Settings > API Keys; base https://<workbench-domain>
- Scope: runtimes/addons/repos, users/API keys, quotas, usage, workloads, teams, site config, copilot, node labels, newsfeeds
- Operations: 32

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `send_copilot_event` | POST | `/api/v2/copilot/event` | Send a Copilot event. |  |
| `get_copilot_model` | GET | `/api/v2/copilot/model/{copilot_model_id}` | Get a Copilot model. |  |
| `list_groups_quota` | GET | `/api/v2/groupsquota` | Return all the groups and its quotas based on the context. Admin gets all the groups details. |  |
| `list_news_feeds` | GET | `/api/v2/newsfeeds/{category}` | List the newsfeeds, optionally filtered, sorted, and paginated. |  |
| `list_all_accelerator_node_labels` | GET | `/api/v2/nodelabels` | List all Accelerator Node Label |  |
| `update_accelerator_labels_admin_config` | PATCH | `/api/v2/nodelabels/config` | Update admin_config_max_per_workload in Node Labels |  |
| `list_runtime_addons` | GET | `/api/v2/runtimeaddons` | List the available runtime addons, optionally filtered, sorted, and paginated. |  |
| `update_runtime_addon_status` | POST | `/api/v2/runtimeaddons:updatestatus` | Update runtime addons |  |
| `list_runtime_repos` | GET | `/api/v2/runtimerepos` | List Runtime repos. |  |
| `create_runtime_repo` | POST | `/api/v2/runtimerepos` | Create a  Runtime repo. |  |
| `delete_runtime_repo` | DELETE | `/api/v2/runtimerepos/{runtime_repo_id}` | Delete a Runtime repo. |  |
| `update_runtime_repo` | PATCH | `/api/v2/runtimerepos/{runtimerepo.id}` | Update a Runtime repo. |  |
| `list_runtimes` | GET | `/api/v2/runtimes` | List the available runtimes, optionally filtered, sorted, and paginated. |  |
| `register_custom_runtime` | POST | `/api/v2/runtimes` | Register a runtime, given the URL to the image in the docker registry |  |
| `update_runtime_status` | POST | `/api/v2/runtimes:update` | Update the status of selected runtimes |  |
| `validate_custom_runtime` | GET | `/api/v2/runtimes:validate` | Validate a runtime, given the URL to the image in the docker registry |  |
| `disable_engines` | POST | `/api/v2/site/config:update` | Disable engines |  |
| `create_team` | POST | `/api/v2/site/teams` | Create a team. |  |
| `delete_team` | DELETE | `/api/v2/teams/{team_name}` | Delete a team. |  |
| `get_time_series` | GET | `/api/v2/ts_data` | Return the time series data for the requested resource or property. |  |
| `list_usage` | GET | `/api/v2/usage` | Return the new usage view based on the caller context, optionally filtered, sorted, and paginated. |  |
| `get_short_user_by_id` | GET | `/api/v2/users/{user_id}` | Get short user by id (GET /api/v2/users/{user_id}) |  |
| `rotate_v1_key` | POST | `/api/v2/users/{username}/v1_key:rotate` | Rotate API V1 key |  |
| `list_v2_keys` | GET | `/api/v2/users/{username}/v2_keys` | Get all API V2 keys |  |
| `delete_v2_keys` | DELETE | `/api/v2/users/{username}/v2_keys` | Delete all API V2 keys |  |
| `create_v2_key` | POST | `/api/v2/users/{username}/v2_keys` | Create API V2 key |  |
| `delete_v2_key` | DELETE | `/api/v2/users/{username}/v2_keys/{key_id}` | Delete an API V2 key |  |
| `list_users_quota` | GET | `/api/v2/usersquota` | Return all the user names and quotas based on the context. Admin gets all the users details. |  |
| `list_workload_executions` | GET | `/api/v2/workloads/executions` | List all workloads and executions |  |
| `list_workload_status` | GET | `/api/v2/workloadstatus` | Return the workload statuses. |  |
| `list_workload_types` | GET | `/api/v2/workloadtypes` | Return the workload types. |  |
| `handle_custom_runtime_upload` | POST | `/api/v2/runtimeaddons/custom` | Create a new Custom Runtime Addon from an uploaded tarball |  |

## cde_jobs

72 tools.

- Product: Cloudera Data Engineering - Virtual Cluster Jobs API
- Version: spec 1.26.1 (CDE public cloud docs)
- Spec source: https://docs.cloudera.com/data-engineering/cloud/jobs-rest-api-reference/swagger.json
- Auth: Bearer CDP access token from the CDE gateway: GET https://<cde-service>/gateway/authtkn/knoxtoken/api/v1/token (Knox, basic workload creds) -> Authorization: Bearer <access_token>; base https://<vc-host>/dex/api/v1
- Operations: 72

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `activate_airflow_python_env` | POST | `/admin/airflow/airflow-python-env` | DEPRECATED: This API exists for compatability reasons, please use the '/admin/airflow/env' APIs group or UI instead. Can be used ONLY for th | deprecated |
| `get_active_airflow_python_env_legacy` | GET | `/admin/airflow/airflow-python-env/active` | DEPRECATED: This API exists for compatability reasons, please use the '/admin/airflow/env' APIs group or UI instead. Can be used ONLY for th | deprecated |
| `delete_airflow_dag` | DELETE | `/admin/airflow/dags/{dag-id}` | Delete an unassociated Airflow DAG |  |
| `get_active_airflow_python_env` | GET | `/admin/airflow/env` | Technical Preview: this API might change in future releases. Get the details of currently active airflow env. |  |
| `delete_airflow_env` | DELETE | `/admin/airflow/env` | Technical Preview: this API might change in future releases. Delete the airflow python environment that is currently active |  |
| `get_active_airflow_python_logs` | GET | `/admin/airflow/env/logs` | Technical Preview: this API might change in future releases. Get the logs about the airflow python environment setup. |  |
| `get_airflow_python_env_maintenance` | GET | `/admin/airflow/env/maintenance` | Technical Preview: this API might change in future releases. Details of the airflow python env that is currently handled in the maintenance  |  |
| `start_airflow_env_maintenance` | POST | `/admin/airflow/env/maintenance` | Technical Preview: this API might change in future releases. Start a maintenance session to create or update airflow python environment |  |
| `cancel_airflow_env_maintenance` | DELETE | `/admin/airflow/env/maintenance` | Technical Preview: this API might change in future releases. Cancel the airflow python environment maintenance session |  |
| `activate_airflow_env` | POST | `/admin/airflow/env/maintenance/activate` | Technical Preview: this API might change in future releases. Activate the airflow python environment in maintenance session |  |
| `build_airflow_env` | POST | `/admin/airflow/env/maintenance/build` | Technical Preview: this API might change in future releases. Build the airflow python environment in maintenance session based on the previo |  |
| `get_airflow_python_logs_maintenance` | GET | `/admin/airflow/env/maintenance/logs` | Technical Preview: this API might change in future releases. All logs of the operations of the undergoing maintenance process |  |
| `set_airflow_env_repos` | POST | `/admin/airflow/env/maintenance/repos` | Technical Preview: this API might change in future releases. Set repositories and credentials for the airflow python environment in maintena |  |
| `get_airflow_python_env_maintenance_status` | GET | `/admin/airflow/env/maintenance/status` | Technical Preview: this API might change in future releases. Get the status of airflow python env maintenance operation |  |
| `list_archives` | GET | `/admin/archives` | Lists archives from a remote storage location available for restoring |  |
| `export_local_archive` | GET | `/admin/export` | Exports jobs and resources locally |  |
| `export_remote_archive` | POST | `/admin/export` | Exports jobs and resources to a remote storage location |  |
| `import_archive` | POST | `/admin/import` | Restore one or more jobs from an archive |  |
| `list_archive` | POST | `/admin/list-archive` | Lists jobs in an archive |  |
| `list_credentials` | GET | `/credentials` | List all credential (Experimental) |  |
| `create_credential` | POST | `/credentials` | Create a credential (Experimental) |  |
| `get_credential` | GET | `/credentials/{name}` | Describe a credential (Experimental) |  |
| `delete_credential` | DELETE | `/credentials/{name}` | Delete a credential (Experimental) |  |
| `update_credential` | PATCH | `/credentials/{name}` | Update a credential (Experimental) |  |
| `info` | GET | `/info` | Information about the instance |  |
| `list_job_runs` | GET | `/job-runs` | List job runs |  |
| `get_job_run` | GET | `/job-runs/{id}` | Describe a job run |  |
| `get_fg_statuses` | GET | `/job-runs/{id}/fg-status` | Get fine-grained statuses of a job run |  |
| `kill_job_run` | POST | `/job-runs/{id}/kill` | Kill a job run |  |
| `get_job_run_log_types` | GET | `/job-runs/{id}/log-types` | List a job run's log types |  |
| `get_job_run_logs` | GET | `/job-runs/{id}/logs` | Get logs for a job run |  |
| `list_jobs` | GET | `/jobs` | List all jobs |  |
| `create_job` | POST | `/jobs` | Create a job |  |
| `pause_all_jobs` | PUT | `/jobs/schedule/pause-all` | Pause all scheduled jobs |  |
| `unpause_all_jobs` | PUT | `/jobs/schedule/unpause-all` | Unpause all scheduled jobs |  |
| `get_job` | GET | `/jobs/{name}` | Describe a job |  |
| `delete_job` | DELETE | `/jobs/{name}` | Delete a job |  |
| `update_job` | PATCH | `/jobs/{name}` | Update a job |  |
| `run_job` | POST | `/jobs/{name}/run` | Run a job |  |
| `clear` | POST | `/jobs/{name}/schedule/clear` | Clear a job schedule |  |
| `mark_success` | POST | `/jobs/{name}/schedule/mark-success` | Mark a job schedule as successful |  |
| `pause` | POST | `/jobs/{name}/schedule/pause` | Pause a job schedule |  |
| `unpause` | POST | `/jobs/{name}/schedule/unpause` | Unpause a job schedule |  |
| `list_repositories` | GET | `/repositories` | List all repositories |  |
| `create_repository` | POST | `/repositories` | Create a repository |  |
| `get_repository` | GET | `/repositories/{name}` | Describe a repository |  |
| `sync_repository` | POST | `/repositories/{name}` | Sync a git repository from its source |  |
| `delete_repository` | DELETE | `/repositories/{name}` | Delete a repository |  |
| `update_repository` | PATCH | `/repositories/{name}` | Update a repository |  |
| `get_repository_file` | GET | `/repositories/{name}/{path}` | Download a repository file |  |
| `list_resources` | GET | `/resources` | List all resources |  |
| `create_resource` | POST | `/resources` | Create a resource |  |
| `get_resource` | GET | `/resources/{name}` | Describe a resource |  |
| `put_resource_archive` | PUT | `/resources/{name}` | Extract archive into a resource |  |
| `delete_resource` | DELETE | `/resources/{name}` | Delete a resource |  |
| `update_resource` | PATCH | `/resources/{name}` | Update a resource |  |
| `get_resource_file` | GET | `/resources/{name}/{path}` | Download a resource file |  |
| `put_resource_file` | PUT | `/resources/{name}/{path}` | Upload a resource file |  |
| `delete_resource_file` | DELETE | `/resources/{name}/{path}` | Delete a resource file |  |
| `list_sessions` | GET | `/sessions` | List all sessions |  |
| `create_session` | POST | `/sessions` | Create a session |  |
| `get_session` | GET | `/sessions/{name}` | Propose a session statement [spec operationId is 'propose-session-statement' (spec bug); renamed] |  |
| `delete_session` | DELETE | `/sessions/{name}` | Delete a session from storage |  |
| `stream_session_events` | GET | `/sessions/{name}/events` | Stream session status events |  |
| `kill_session` | POST | `/sessions/{name}/kill` | Kill a session |  |
| `get_session_log_types` | GET | `/sessions/{name}/log-types` | List a session's log types |  |
| `get_session_logs` | GET | `/sessions/{name}/logs` | Get logs for a session |  |
| `list_session_statements` | GET | `/sessions/{name}/statements` | List all statements. |  |
| `submit_session_statement` | POST | `/sessions/{name}/statements` | Submit statement |  |
| `get_session_statement` | GET | `/sessions/{name}/statements/{id}` | Describe a session statement |  |
| `cancel_session_statement` | POST | `/sessions/{name}/statements/{id}` | Cancel a session statement |  |
| `user` | GET | `/user` | Information about the authenticated user |  |

## ranger_public

71 tools.

- Product: Apache Ranger Admin REST API
- Version: swagger 3.0.0-SNAPSHOT (ranger.apache.org apidocs); CDP 7.1.9 ships Ranger 2.4 - GDS and some newer ops absent there
- Spec source: https://ranger.apache.org/apidocs/ui/swagger.json
- Auth: Basic (Ranger admin user) or Kerberos SPNEGO; via Knox: Knox SSO/JWT. Base https://<ranger-host>:6182/service (paths below are relative to /service)
- Scope: Public API v2 (/public/v2/api): service defs, services, policies, zones, roles, plugin info - the stable public API
- Operations: 71

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `get_plugins_info2` | GET | `/service/public/v2/api/plugins/info` | Get plugins info2 (GET /public/v2/api/plugins/info) |  |
| `delete_policies` | DELETE | `/service/public/v2/api/policies/bulk` | Delete policies (DELETE /public/v2/api/policies/bulk) |  |
| `get_policies_for_resource2` | GET | `/service/public/v2/api/policies/{serviceDefName}/for-resource` | Get policies for resource2 (GET /public/v2/api/policies/{serviceDefName}/for-resource) |  |
| `delete_policy_by_name` | DELETE | `/service/public/v2/api/policy` | Delete policy by name (DELETE /public/v2/api/policy) |  |
| `get_policies2` | GET | `/service/public/v2/api/policy` | Get policies2 (GET /public/v2/api/policy) |  |
| `create_policy3` | POST | `/service/public/v2/api/policy` | Create policy3 (POST /public/v2/api/policy) |  |
| `apply_policy2` | POST | `/service/public/v2/api/policy/apply` | Apply policy2 (POST /public/v2/api/policy/apply) |  |
| `delete_policy_by_guid_and_service_name_and_zone_name2` | DELETE | `/service/public/v2/api/policy/guid/{guid}` | Delete policy by guid and service name and zone name2 (DELETE /public/v2/api/policy/guid/{guid}) |  |
| `get_policy_by_guid_and_service_name_and_zone_name2` | GET | `/service/public/v2/api/policy/guid/{guid}` | Get policy by guid and service name and zone name2 (GET /public/v2/api/policy/guid/{guid}) |  |
| `delete_policy3` | DELETE | `/service/public/v2/api/policy/{id}` | Delete policy3 (DELETE /public/v2/api/policy/{id}) |  |
| `get_policy3` | GET | `/service/public/v2/api/policy/{id}` | Get policy3 (GET /public/v2/api/policy/{id}) |  |
| `update_policy3` | PUT | `/service/public/v2/api/policy/{id}` | Update policy3 (PUT /public/v2/api/policy/{id}) |  |
| `get_all_roles` | GET | `/service/public/v2/api/roles` | Get all roles (GET /public/v2/api/roles) |  |
| `create_role` | POST | `/service/public/v2/api/roles` | Create role (POST /public/v2/api/roles) |  |
| `grant_role` | PUT | `/service/public/v2/api/roles/grant/{serviceName}` | Grant role (PUT /public/v2/api/roles/grant/{serviceName}) |  |
| `delete_role` | DELETE | `/service/public/v2/api/roles/name/{name}` | Delete role (DELETE /public/v2/api/roles/name/{name}) |  |
| `get_role` | GET | `/service/public/v2/api/roles/name/{name}` | Get role (GET /public/v2/api/roles/name/{name}) |  |
| `get_all_role_names` | GET | `/service/public/v2/api/roles/names` | Get all role names (GET /public/v2/api/roles/names) |  |
| `revoke_role_users_and_roles` | PUT | `/service/public/v2/api/roles/revoke/{serviceName}` | Revoke role users and roles (PUT /public/v2/api/roles/revoke/{serviceName}) |  |
| `get_user_roles` | GET | `/service/public/v2/api/roles/user/{user}` | Get user roles (GET /public/v2/api/roles/user/{user}) |  |
| `delete_role_by_id` | DELETE | `/service/public/v2/api/roles/{id}` | Delete role (DELETE /public/v2/api/roles/{id}) |  |
| `get_role_by_id` | GET | `/service/public/v2/api/roles/{id}` | Get role (GET /public/v2/api/roles/{id}) |  |
| `update_role` | PUT | `/service/public/v2/api/roles/{id}` | Update role (PUT /public/v2/api/roles/{id}) |  |
| `add_users_and_groups` | PUT | `/service/public/v2/api/roles/{id}/addUsersAndGroups` | Add users and groups (PUT /public/v2/api/roles/{id}/addUsersAndGroups) |  |
| `remove_admin_from_users_and_groups` | PUT | `/service/public/v2/api/roles/{id}/removeAdminFromUsersAndGroups` | Remove admin from users and groups (PUT /public/v2/api/roles/{id}/removeAdminFromUsersAndGroups) |  |
| `remove_users_and_groups` | PUT | `/service/public/v2/api/roles/{id}/removeUsersAndGroups` | Remove users and groups (PUT /public/v2/api/roles/{id}/removeUsersAndGroups) |  |
| `delete_policy_deltas2` | DELETE | `/service/public/v2/api/server/policydeltas` | Delete policy deltas2 (DELETE /public/v2/api/server/policydeltas) |  |
| `purge_records2` | DELETE | `/service/public/v2/api/server/purge/records` | Purge records2 (DELETE /public/v2/api/server/purge/records) |  |
| `purge_empty_policies2` | DELETE | `/service/public/v2/api/server/purgepolicies/{serviceName}` | Purge empty policies2 (DELETE /public/v2/api/server/purgepolicies/{serviceName}) |  |
| `delete_tag_deltas` | DELETE | `/service/public/v2/api/server/tagdeltas` | Delete tag deltas (DELETE /public/v2/api/server/tagdeltas) |  |
| `search_services` | GET | `/service/public/v2/api/service` | Search services (GET /public/v2/api/service) |  |
| `create_service2` | POST | `/service/public/v2/api/service` | Create service2 (POST /public/v2/api/service) |  |
| `get_service_headers` | GET | `/service/public/v2/api/service-headers` | Get service headers (GET /public/v2/api/service-headers) |  |
| `delete_service_by_name` | DELETE | `/service/public/v2/api/service/name/{name}` | Delete service by name (DELETE /public/v2/api/service/name/{name}) |  |
| `get_service_by_name2` | GET | `/service/public/v2/api/service/name/{name}` | Get service by name2 (GET /public/v2/api/service/name/{name}) |  |
| `update_service_by_name` | PUT | `/service/public/v2/api/service/name/{name}` | Update service by name (PUT /public/v2/api/service/name/{name}) |  |
| `delete_service2` | DELETE | `/service/public/v2/api/service/{id}` | Delete service2 (DELETE /public/v2/api/service/{id}) |  |
| `get_service2` | GET | `/service/public/v2/api/service/{id}` | Get service2 (GET /public/v2/api/service/{id}) |  |
| `update_service2` | PUT | `/service/public/v2/api/service/{id}` | Update service2 (PUT /public/v2/api/service/{id}) |  |
| `get_service_tags` | GET | `/service/public/v2/api/service/{serviceName}/tags` | Get service tags (GET /public/v2/api/service/{serviceName}/tags) |  |
| `import_service_tags` | PUT | `/service/public/v2/api/service/{serviceName}/tags` | Import service tags (PUT /public/v2/api/service/{serviceName}/tags) |  |
| `search_policies2` | GET | `/service/public/v2/api/service/{servicename}/policy` | Search policies2 (GET /public/v2/api/service/{servicename}/policy) |  |
| `get_policy_by_name` | GET | `/service/public/v2/api/service/{servicename}/policy/{policyname}` | Get policy by name (GET /public/v2/api/service/{servicename}/policy/{policyname}) |  |
| `update_policy_by_name` | PUT | `/service/public/v2/api/service/{servicename}/policy/{policyname}` | Update policy by name (PUT /public/v2/api/service/{servicename}/policy/{policyname}) |  |
| `search_service_defs` | GET | `/service/public/v2/api/servicedef` | Search service defs (GET /public/v2/api/servicedef) |  |
| `create_service_def2` | POST | `/service/public/v2/api/servicedef` | Create service def2 (POST /public/v2/api/servicedef) |  |
| `delete_service_def_by_name` | DELETE | `/service/public/v2/api/servicedef/name/{name}` | Delete service def by name (DELETE /public/v2/api/servicedef/name/{name}) |  |
| `get_service_def_by_name2` | GET | `/service/public/v2/api/servicedef/name/{name}` | Get service def by name2 (GET /public/v2/api/servicedef/name/{name}) |  |
| `update_service_def_by_name` | PUT | `/service/public/v2/api/servicedef/name/{name}` | Update service def by name (PUT /public/v2/api/servicedef/name/{name}) |  |
| `delete_service_def2` | DELETE | `/service/public/v2/api/servicedef/{id}` | Delete service def2 (DELETE /public/v2/api/servicedef/{id}) |  |
| `get_service_def2` | GET | `/service/public/v2/api/servicedef/{id}` | Get service def2 (GET /public/v2/api/servicedef/{id}) |  |
| `update_service_def2` | PUT | `/service/public/v2/api/servicedef/{id}` | Update service def2 (PUT /public/v2/api/servicedef/{id}) |  |
| `get_security_zone_header_info_list` | GET | `/service/public/v2/api/zone-headers` | Get List of security zone header info. |  |
| `get_security_zone_names_for_resource` | GET | `/service/public/v2/api/zone-names/{serviceName}/resource` | Get security zone names for resource (GET /public/v2/api/zone-names/{serviceName}/resource) |  |
| `get_all_zones` | GET | `/service/public/v2/api/zones` | Get all zones (GET /public/v2/api/zones) |  |
| `create_security_zone` | POST | `/service/public/v2/api/zones` | Create security zone (POST /public/v2/api/zones) |  |
| `get_all_zones_v2` | GET | `/service/public/v2/api/zones-v2` | Get all zones v2 (GET /public/v2/api/zones-v2) |  |
| `create_security_zone_zones_v2` | POST | `/service/public/v2/api/zones-v2` | Create security zone (POST /public/v2/api/zones-v2) |  |
| `get_security_zone_v2` | GET | `/service/public/v2/api/zones-v2/name/{name}` | Get security zone v2 (GET /public/v2/api/zones-v2/name/{name}) |  |
| `get_resources` | GET | `/service/public/v2/api/zones-v2/name/{name}/resources/{serviceName}` | Get resources (GET /public/v2/api/zones-v2/name/{name}/resources/{serviceName}) |  |
| `get_security_zone_v2_by_id` | GET | `/service/public/v2/api/zones-v2/{id}` | Get security zone v2 (GET /public/v2/api/zones-v2/{id}) |  |
| `update_security_zone` | PUT | `/service/public/v2/api/zones-v2/{id}` | Update security zone (PUT /public/v2/api/zones-v2/{id}) |  |
| `update_security_zone_partial` | PUT | `/service/public/v2/api/zones-v2/{id}/partial` | Update security zone (PUT /public/v2/api/zones-v2/{id}/partial) |  |
| `get_resources_by_service_name` | GET | `/service/public/v2/api/zones-v2/{id}/resources/{serviceName}` | Get resources (GET /public/v2/api/zones-v2/{id}/resources/{serviceName}) |  |
| `delete_security_zone` | DELETE | `/service/public/v2/api/zones/name/{name}` | Delete security zone (DELETE /public/v2/api/zones/name/{name}) |  |
| `get_security_zone` | GET | `/service/public/v2/api/zones/name/{name}` | Get security zone (GET /public/v2/api/zones/name/{name}) |  |
| `get_security_zone_header_info_list_by_service_id` | GET | `/service/public/v2/api/zones/zone-headers/for-service/{serviceId}` | Get List of security zone header info. |  |
| `delete_security_zone_by_id` | DELETE | `/service/public/v2/api/zones/{id}` | Delete security zone (DELETE /public/v2/api/zones/{id}) |  |
| `get_security_zone_by_id` | GET | `/service/public/v2/api/zones/{id}` | Get security zone (GET /public/v2/api/zones/{id}) |  |
| `update_security_zone_by_id` | PUT | `/service/public/v2/api/zones/{id}` | Update security zone (PUT /public/v2/api/zones/{id}) |  |
| `get_service_header_info_list_by_zone_id` | GET | `/service/public/v2/api/zones/{zoneId}/service-headers` | Get service header info List for given zone. |  |

## ranger_xusers

71 tools.

- Product: Apache Ranger Admin REST API
- Version: swagger 3.0.0-SNAPSHOT (ranger.apache.org apidocs); CDP 7.1.9 ships Ranger 2.4 - GDS and some newer ops absent there
- Spec source: https://ranger.apache.org/apidocs/ui/swagger.json
- Auth: Basic (Ranger admin user) or Kerberos SPNEGO; via Knox: Knox SSO/JWT. Base https://<ranger-host>:6182/service (paths below are relative to /service)
- Scope: XUserREST users/groups/group-users/lookups/ugsync + portal UserREST
- Operations: 71

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `search_users` | GET | `/service/users` | Implements the traditional search functionalities for UserProfile |  |
| `create` | POST | `/service/users` | Create (POST /users) |  |
| `update` | PUT | `/service/users` | Update (PUT /users) |  |
| `create_default_account_user` | POST | `/service/users/default` | Create default account user (POST /users/default) |  |
| `get_user_profile` | GET | `/service/users/profile` | This method returns the VUserProfile for the current session |  |
| `get_user_profile_for_user` | GET | `/service/users/{userId}` | Return the VUserProfile for the given userId |  |
| `deactivate_user` | POST | `/service/users/{userId}/deactivate` | Deactivate the user |  |
| `change_email_address` | POST | `/service/users/{userId}/emailchange` | Change email address (POST /users/{userId}/emailchange) |  |
| `change_password` | POST | `/service/users/{userId}/passwordchange` | Change password (POST /users/{userId}/passwordchange) |  |
| `set_user_roles` | PUT | `/service/users/{userId}/roles` | Set user roles (PUT /users/{userId}/roles) |  |
| `force_delete_external_groups` | DELETE | `/service/xusers/delete/external/groups` | Proceed with <tt>caution</tt>: Force deletes groups from the ranger db, |  |
| `force_delete_external_users` | DELETE | `/service/xusers/delete/external/users` | Proceed with <tt>caution</tt>: Force deletes users from the ranger db, |  |
| `delete_x_group_and_x_user` | DELETE | `/service/xusers/group/{groupName}/user/{userName}` | Delete x group and x user (DELETE /xusers/group/{groupName}/user/{userName}) |  |
| `search_x_groups` | GET | `/service/xusers/groups` | Implements the traditional search functionalities for XGroups |  |
| `create_x_group` | POST | `/service/xusers/groups` | Create x group (POST /xusers/groups) |  |
| `update_x_group` | PUT | `/service/xusers/groups` | Update x group (PUT /xusers/groups) |  |
| `count_x_groups` | GET | `/service/xusers/groups/count` | Count x groups (GET /xusers/groups/count) |  |
| `delete_x_group_by_group_name` | DELETE | `/service/xusers/groups/groupName/{groupName}` | Delete x group by group name (DELETE /xusers/groups/groupName/{groupName}) |  |
| `get_x_group_by_group_name` | GET | `/service/xusers/groups/groupName/{groupName}` | Get x group by group name (GET /xusers/groups/groupName/{groupName}) |  |
| `create_x_group_user_from_map` | POST | `/service/xusers/groups/groupinfo` | Create x group user from map (POST /xusers/groups/groupinfo) |  |
| `delete_x_group` | DELETE | `/service/xusers/groups/{id}` | Delete x group (DELETE /xusers/groups/{id}) |  |
| `get_x_group` | GET | `/service/xusers/groups/{id}` | Get x group (GET /xusers/groups/{id}) |  |
| `search_x_group_users` | GET | `/service/xusers/groupusers` | Implements the traditional search functionalities for XGroupUsers |  |
| `create_x_group_user` | POST | `/service/xusers/groupusers` | Create x group user (POST /xusers/groupusers) |  |
| `update_x_group_user` | PUT | `/service/xusers/groupusers` | Update x group user (PUT /xusers/groupusers) |  |
| `count_x_group_users` | GET | `/service/xusers/groupusers/count` | Count x group users (GET /xusers/groupusers/count) |  |
| `get_x_group_users_by_group_name` | GET | `/service/xusers/groupusers/groupName/{groupName}` | Implements the traditional search functionalities for XGroupUsers by Group name |  |
| `delete_x_group_user` | DELETE | `/service/xusers/groupusers/{id}` | Delete x group user (DELETE /xusers/groupusers/{id}) |  |
| `get_x_group_user` | GET | `/service/xusers/groupusers/{id}` | Get x group user (GET /xusers/groupusers/{id}) |  |
| `get_groups_lookup` | GET | `/service/xusers/lookup/groups` | Get groups lookup (GET /xusers/lookup/groups) |  |
| `get_principals_lookup` | GET | `/service/xusers/lookup/principals` | Get principals lookup (GET /xusers/lookup/principals) |  |
| `get_users_lookup` | GET | `/service/xusers/lookup/users` | Get users lookup (GET /xusers/lookup/users) |  |
| `secure_create_x_group` | POST | `/service/xusers/secure/groups` | Secure create x group (POST /xusers/secure/groups) |  |
| `delete_groups_by_group_name` | DELETE | `/service/xusers/secure/groups/delete` | Delete groups by group name (DELETE /xusers/secure/groups/delete) |  |
| `delete_single_group_by_group_id` | DELETE | `/service/xusers/secure/groups/id/{groupId}` | Delete single group by group id (DELETE /xusers/secure/groups/id/{groupId}) |  |
| `modify_groups_visibility` | PUT | `/service/xusers/secure/groups/visibility` | Modify groups visibility (PUT /xusers/secure/groups/visibility) |  |
| `delete_single_group_by_group_name` | DELETE | `/service/xusers/secure/groups/{groupName}` | Delete single group by group name (DELETE /xusers/secure/groups/{groupName}) |  |
| `secure_get_x_group` | GET | `/service/xusers/secure/groups/{id}` | Secure get x group (GET /xusers/secure/groups/{id}) |  |
| `secure_update_x_group` | PUT | `/service/xusers/secure/groups/{id}` | Secure update x group (PUT /xusers/secure/groups/{id}) |  |
| `secure_create_x_user` | POST | `/service/xusers/secure/users` | Secure create x user (POST /xusers/secure/users) |  |
| `modify_user_active_status` | PUT | `/service/xusers/secure/users/activestatus` | Modify user active status (PUT /xusers/secure/users/activestatus) |  |
| `delete_users_by_user_name` | DELETE | `/service/xusers/secure/users/delete` | Delete users by user name (DELETE /xusers/secure/users/delete) |  |
| `get_user_roles_by_external_id` | GET | `/service/xusers/secure/users/external/{userId}` | Get user roles by external id (GET /xusers/secure/users/external/{userId}) |  |
| `delete_single_user_by_user_id` | DELETE | `/service/xusers/secure/users/id/{userId}` | Delete single user by user id (DELETE /xusers/secure/users/id/{userId}) |  |
| `get_user_roles_by_name` | GET | `/service/xusers/secure/users/roles/userName/{userName}` | Get user roles by name (GET /xusers/secure/users/roles/userName/{userName}) |  |
| `set_user_roles_by_name` | PUT | `/service/xusers/secure/users/roles/userName/{userName}` | Set user roles by name (PUT /xusers/secure/users/roles/userName/{userName}) |  |
| `set_user_roles_by_external_id` | PUT | `/service/xusers/secure/users/roles/{userId}` | Set user roles by external id (PUT /xusers/secure/users/roles/{userId}) |  |
| `modify_user_visibility` | PUT | `/service/xusers/secure/users/visibility` | Modify user visibility (PUT /xusers/secure/users/visibility) |  |
| `secure_get_x_user` | GET | `/service/xusers/secure/users/{id}` | Secure get x user (GET /xusers/secure/users/{id}) |  |
| `secure_update_x_user` | PUT | `/service/xusers/secure/users/{id}` | Secure update x user (PUT /xusers/secure/users/{id}) |  |
| `delete_single_user_by_user_name` | DELETE | `/service/xusers/secure/users/{userName}` | Delete single user by user name (DELETE /xusers/secure/users/{userName}) |  |
| `post_user_group_audit_info` | POST | `/service/xusers/ugsync/auditinfo` | Post user group audit info (POST /xusers/ugsync/auditinfo) |  |
| `add_or_update_groups` | POST | `/service/xusers/ugsync/groups` | Add or update groups (POST /xusers/ugsync/groups) |  |
| `update_deleted_groups` | POST | `/service/xusers/ugsync/groups/visibility` | Update deleted groups (POST /xusers/ugsync/groups/visibility) |  |
| `get_all_group_users` | GET | `/service/xusers/ugsync/groupusers` | Get all group users (GET /xusers/ugsync/groupusers) |  |
| `add_or_update_group_users_list` | POST | `/service/xusers/ugsync/groupusers` | Add or update group users list (POST /xusers/ugsync/groupusers) |  |
| `add_or_update_users` | POST | `/service/xusers/ugsync/users` | Add or update users (POST /xusers/ugsync/users) |  |
| `update_deleted_users` | POST | `/service/xusers/ugsync/users/visibility` | Update deleted users (POST /xusers/ugsync/users/visibility) |  |
| `search_x_users` | GET | `/service/xusers/users` | Implements the traditional search functionalities for XUsers |  |
| `create_x_user` | POST | `/service/xusers/users` | Create x user (POST /xusers/users) |  |
| `update_x_user` | PUT | `/service/xusers/users` | Update x user (PUT /xusers/users) |  |
| `count_x_users` | GET | `/service/xusers/users/count` | Count x users (GET /xusers/users/count) |  |
| `create_external_user` | POST | `/service/xusers/users/external` | Create external user (POST /xusers/users/external) |  |
| `set_x_user_roles_by_name` | POST | `/service/xusers/users/roleassignments` | Set x user roles by name (POST /xusers/users/roleassignments) |  |
| `delete_x_user_by_user_name` | DELETE | `/service/xusers/users/userName/{userName}` | Delete x user by user name (DELETE /xusers/users/userName/{userName}) |  |
| `get_x_user_by_user_name` | GET | `/service/xusers/users/userName/{userName}` | Get x user by user name (GET /xusers/users/userName/{userName}) |  |
| `create_x_user_group_from_map` | POST | `/service/xusers/users/userinfo` | Create x user group from map (POST /xusers/users/userinfo) |  |
| `delete_x_user` | DELETE | `/service/xusers/users/{id}` | Delete x user (DELETE /xusers/users/{id}) |  |
| `get_x_user` | GET | `/service/xusers/users/{id}` | Get x user (GET /xusers/users/{id}) |  |
| `get_x_group_users` | GET | `/service/xusers/{groupId}/users` | Get x group users (GET /xusers/{groupId}/users) |  |
| `get_x_user_groups` | GET | `/service/xusers/{userId}/groups` | Get x user groups (GET /xusers/{userId}/groups) |  |

## ranger_permissions_audit

43 tools.

- Product: Apache Ranger Admin REST API
- Version: swagger 3.0.0-SNAPSHOT (ranger.apache.org apidocs); CDP 7.1.9 ships Ranger 2.4 - GDS and some newer ops absent there
- Spec source: https://ranger.apache.org/apidocs/ui/swagger.json
- Auth: Basic (Ranger admin user) or Kerberos SPNEGO; via Knox: Knox SSO/JWT. Base https://<ranger-host>:6182/service (paths below are relative to /service)
- Scope: XUserREST module permissions, perm/audit maps, auth sessions, user-store download + XAuditREST
- Operations: 43

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `search_x_access_audits` | GET | `/service/xaudit/access_audit` | Implements the traditional search functionalities for XAccessAudits |  |
| `count_x_access_audits` | GET | `/service/xaudit/access_audit/count` | Count x access audits (GET /xaudit/access_audit/count) |  |
| `search_x_trx_logs` | GET | `/service/xaudit/trx_log` | Implements the traditional search functionalities for XTrxLogs |  |
| `create_x_trx_log` | POST | `/service/xaudit/trx_log` | Create x trx log (POST /xaudit/trx_log) |  |
| `update_x_trx_log` | PUT | `/service/xaudit/trx_log` | Update x trx log (PUT /xaudit/trx_log) |  |
| `count_x_trx_logs` | GET | `/service/xaudit/trx_log/count` | Count x trx logs (GET /xaudit/trx_log/count) |  |
| `delete_x_trx_log` | DELETE | `/service/xaudit/trx_log/{id}` | Delete x trx log (DELETE /xaudit/trx_log/{id}) |  |
| `get_x_trx_log` | GET | `/service/xaudit/trx_log/{id}` | Get x trx log (GET /xaudit/trx_log/{id}) |  |
| `search_x_audit_maps` | GET | `/service/xusers/auditmaps` | Implements the traditional search functionalities for XAuditMaps |  |
| `create_x_audit_map` | POST | `/service/xusers/auditmaps` | Create x audit map (POST /xusers/auditmaps) |  |
| `update_x_audit_map` | PUT | `/service/xusers/auditmaps` | Update x audit map (PUT /xusers/auditmaps) |  |
| `count_x_audit_maps` | GET | `/service/xusers/auditmaps/count` | Count x audit maps (GET /xusers/auditmaps/count) |  |
| `delete_x_audit_map` | DELETE | `/service/xusers/auditmaps/{id}` | Delete x audit map (DELETE /xusers/auditmaps/{id}) |  |
| `get_x_audit_map` | GET | `/service/xusers/auditmaps/{id}` | Get x audit map (GET /xusers/auditmaps/{id}) |  |
| `get_auth_sessions` | GET | `/service/xusers/authSessions` | Get auth sessions (GET /xusers/authSessions) |  |
| `get_auth_session` | GET | `/service/xusers/authSessions/info` | Get auth session (GET /xusers/authSessions/info) |  |
| `get_ranger_user_store_if_updated` | GET | `/service/xusers/download/{serviceName}` | Get ranger user store if updated (GET /xusers/download/{serviceName}) |  |
| `search_x_module_def` | GET | `/service/xusers/permission` | Search x module def (GET /xusers/permission) |  |
| `create_x_module_def_permission` | POST | `/service/xusers/permission` | Create x module def permission (POST /xusers/permission) |  |
| `count_x_module_def` | GET | `/service/xusers/permission/count` | Count x module def (GET /xusers/permission/count) |  |
| `search_x_group_permission` | GET | `/service/xusers/permission/group` | Search x group permission (GET /xusers/permission/group) |  |
| `create_x_group_permission` | POST | `/service/xusers/permission/group` | Create x group permission (POST /xusers/permission/group) |  |
| `count_x_group_permission` | GET | `/service/xusers/permission/group/count` | Count x group permission (GET /xusers/permission/group/count) |  |
| `delete_x_group_permission` | DELETE | `/service/xusers/permission/group/{id}` | Delete x group permission (DELETE /xusers/permission/group/{id}) |  |
| `get_x_group_permission` | GET | `/service/xusers/permission/group/{id}` | Get x group permission (GET /xusers/permission/group/{id}) |  |
| `update_x_group_permission` | PUT | `/service/xusers/permission/group/{id}` | Update x group permission (PUT /xusers/permission/group/{id}) |  |
| `search_x_user_permission` | GET | `/service/xusers/permission/user` | Search x user permission (GET /xusers/permission/user) |  |
| `create_x_user_permission` | POST | `/service/xusers/permission/user` | Create x user permission (POST /xusers/permission/user) |  |
| `count_x_user_permission` | GET | `/service/xusers/permission/user/count` | Count x user permission (GET /xusers/permission/user/count) |  |
| `delete_x_user_permission` | DELETE | `/service/xusers/permission/user/{id}` | Delete x user permission (DELETE /xusers/permission/user/{id}) |  |
| `get_x_user_permission` | GET | `/service/xusers/permission/user/{id}` | Get x user permission (GET /xusers/permission/user/{id}) |  |
| `update_x_user_permission` | PUT | `/service/xusers/permission/user/{id}` | Update x user permission (PUT /xusers/permission/user/{id}) |  |
| `delete_x_module_def_permission` | DELETE | `/service/xusers/permission/{id}` | Delete x module def permission (DELETE /xusers/permission/{id}) |  |
| `get_x_module_def_permission` | GET | `/service/xusers/permission/{id}` | Get x module def permission (GET /xusers/permission/{id}) |  |
| `update_x_module_def_permission` | PUT | `/service/xusers/permission/{id}` | Update x module def permission (PUT /xusers/permission/{id}) |  |
| `search_x_module_def_list` | GET | `/service/xusers/permissionlist` | Search x module def list (GET /xusers/permissionlist) |  |
| `search_x_perm_maps` | GET | `/service/xusers/permmaps` | Implements the traditional search functionalities for XPermMaps |  |
| `create_x_perm_map` | POST | `/service/xusers/permmaps` | Create x perm map (POST /xusers/permmaps) |  |
| `update_x_perm_map` | PUT | `/service/xusers/permmaps` | Update x perm map (PUT /xusers/permmaps) |  |
| `count_x_perm_maps` | GET | `/service/xusers/permmaps/count` | Count x perm maps (GET /xusers/permmaps/count) |  |
| `delete_x_perm_map` | DELETE | `/service/xusers/permmaps/{id}` | Delete x perm map (DELETE /xusers/permmaps/{id}) |  |
| `get_x_perm_map` | GET | `/service/xusers/permmaps/{id}` | Get x perm map (GET /xusers/permmaps/{id}) |  |
| `get_secure_ranger_user_store_if_updated` | GET | `/service/xusers/secure/download/{serviceName}` | Get secure ranger user store if updated (GET /xusers/secure/download/{serviceName}) |  |

## ranger_service_internal

53 tools.

- Product: Apache Ranger Admin REST API
- Version: swagger 3.0.0-SNAPSHOT (ranger.apache.org apidocs); CDP 7.1.9 ships Ranger 2.4 - GDS and some newer ops absent there
- Spec source: https://ranger.apache.org/apidocs/ui/swagger.json
- Auth: Basic (Ranger admin user) or Kerberos SPNEGO; via Knox: Knox SSO/JWT. Base https://<ranger-host>:6182/service (paths below are relative to /service)
- Scope: ServiceREST (/plugins): internal policy/service/service-def management used by the UI and plugins
- Operations: 53

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `check_sso` | GET | `/service/plugins/checksso` | Check sso (GET /plugins/checksso) |  |
| `delete_cluster_services` | DELETE | `/service/plugins/cluster-services/{clusterName}` | Delete services/ repos associated with cluster. |  |
| `get_csrf_properties` | GET | `/service/plugins/csrfconf` | Get csrf properties (GET /plugins/csrfconf) |  |
| `get_service_defs` | GET | `/service/plugins/definitions` | Get service defs (GET /plugins/definitions) |  |
| `create_service_def` | POST | `/service/plugins/definitions` | Create service def (POST /plugins/definitions) |  |
| `get_service_def_by_name` | GET | `/service/plugins/definitions/name/{name}` | Get service def by name (GET /plugins/definitions/name/{name}) |  |
| `delete_service_def` | DELETE | `/service/plugins/definitions/{id}` | Delete service def (DELETE /plugins/definitions/{id}) |  |
| `get_service_def` | GET | `/service/plugins/definitions/{id}` | Get service def (GET /plugins/definitions/{id}) |  |
| `update_service_def` | PUT | `/service/plugins/definitions/{id}` | Update service def (PUT /plugins/definitions/{id}) |  |
| `get_metric_by_type` | GET | `/service/plugins/metrics/type/{type}` | Get metric by type (GET /plugins/metrics/type/{type}) |  |
| `delete_plugins_info` | DELETE | `/service/plugins/plugins/info` | Delete plugins info (DELETE /plugins/plugins/info) |  |
| `get_plugins_info` | GET | `/service/plugins/plugins/info` | Get plugins info (GET /plugins/plugins/info) |  |
| `delete_plugins_info_by_id` | DELETE | `/service/plugins/plugins/info/{id}` | Delete plugins info (DELETE /plugins/plugins/info/{id}) |  |
| `get_policies` | GET | `/service/plugins/policies` | Get policies (GET /plugins/policies) |  |
| `create_policy` | POST | `/service/plugins/policies` | Create policy (POST /plugins/policies) |  |
| `apply_policy` | POST | `/service/plugins/policies/apply` | Apply policy (POST /plugins/policies/apply) |  |
| `reset_policy_cache` | GET | `/service/plugins/policies/cache/reset` | Resets/ removes service policy cache for given service. |  |
| `reset_policy_cache_all` | GET | `/service/plugins/policies/cache/reset-all` | Resets/ removes service policy cache for all. |  |
| `count_policies` | GET | `/service/plugins/policies/count` | Count policies (GET /plugins/policies/count) |  |
| `get_policies_in_csv` | GET | `/service/plugins/policies/csv` | Get policies in csv (GET /plugins/policies/csv) | deprecated |
| `get_service_policies_if_updated` | GET | `/service/plugins/policies/download/{serviceName}` | Get service policies if updated (GET /plugins/policies/download/{serviceName}) |  |
| `get_policies_in_excel` | GET | `/service/plugins/policies/downloadExcel` | Get policies in excel (GET /plugins/policies/downloadExcel) | deprecated |
| `get_policy_from_event_time` | GET | `/service/plugins/policies/eventTime` | Get policy from event time (GET /plugins/policies/eventTime) |  |
| `get_policies_in_json` | GET | `/service/plugins/policies/exportJson` | Get policies in json (GET /plugins/policies/exportJson) |  |
| `delete_policy_by_guid_and_service_name_and_zone_name` | DELETE | `/service/plugins/policies/guid/{guid}` | Delete policy by guid and service name and zone name (DELETE /plugins/policies/guid/{guid}) |  |
| `get_policy_by_guid_and_service_name_and_zone_name` | GET | `/service/plugins/policies/guid/{guid}` | Get policy by guid and service name and zone name (GET /plugins/policies/guid/{guid}) |  |
| `import_policies_from_file` | POST | `/service/plugins/policies/importPoliciesFromFile` | Import policies from file (POST /plugins/policies/importPoliciesFromFile) |  |
| `get_service_policies_by_name` | GET | `/service/plugins/policies/service/name/{name}` | Get service policies by name (GET /plugins/policies/service/name/{name}) |  |
| `get_service_policies` | GET | `/service/plugins/policies/service/{id}` | Get service policies (GET /plugins/policies/service/{id}) |  |
| `delete_policy` | DELETE | `/service/plugins/policies/{id}` | Delete policy (DELETE /plugins/policies/{id}) |  |
| `get_policy` | GET | `/service/plugins/policies/{id}` | Get policy (GET /plugins/policies/{id}) |  |
| `update_policy` | PUT | `/service/plugins/policies/{id}` | Update policy (PUT /plugins/policies/{id}) |  |
| `get_policies_for_resource` | GET | `/service/plugins/policies/{serviceDefName}/for-resource` | Get policies for resource (GET /plugins/policies/{serviceDefName}/for-resource) |  |
| `get_policy_for_version_number` | GET | `/service/plugins/policy/{policyId}/version/{versionNo}` | Get policy for version number (GET /plugins/policy/{policyId}/version/{versionNo}) |  |
| `get_policy_version_list` | GET | `/service/plugins/policy/{policyId}/versionList` | Get policy version list (GET /plugins/policy/{policyId}/versionList) |  |
| `get_policy_labels` | GET | `/service/plugins/policyLabels` | Get policy labels (GET /plugins/policyLabels) |  |
| `get_secure_service_policies_if_updated` | GET | `/service/plugins/secure/policies/download/{serviceName}` | Get secure service policies if updated (GET /plugins/secure/policies/download/{serviceName}) |  |
| `secure_grant_access` | POST | `/service/plugins/secure/services/grant/{serviceName}` | Secure grant access (POST /plugins/secure/services/grant/{serviceName}) |  |
| `secure_revoke_access` | POST | `/service/plugins/secure/services/revoke/{serviceName}` | Secure revoke access (POST /plugins/secure/services/revoke/{serviceName}) |  |
| `delete_policy_deltas` | DELETE | `/service/plugins/server/policydeltas` | Delete policy deltas (DELETE /plugins/server/policydeltas) |  |
| `purge_records` | DELETE | `/service/plugins/server/purge/records` | Purge records (DELETE /plugins/server/purge/records) |  |
| `purge_empty_policies` | DELETE | `/service/plugins/server/purgepolicies/{serviceName}` | Purge empty policies (DELETE /plugins/server/purgepolicies/{serviceName}) |  |
| `get_services` | GET | `/service/plugins/services` | Get services (GET /plugins/services) |  |
| `create_service` | POST | `/service/plugins/services` | Create service (POST /plugins/services) |  |
| `count_services` | GET | `/service/plugins/services/count` | Count services (GET /plugins/services/count) |  |
| `grant_access` | POST | `/service/plugins/services/grant/{serviceName}` | Grant access (POST /plugins/services/grant/{serviceName}) |  |
| `lookup_resource` | POST | `/service/plugins/services/lookupResource/{serviceName}` | Lookup resource (POST /plugins/services/lookupResource/{serviceName}) |  |
| `get_service_by_name` | GET | `/service/plugins/services/name/{name}` | Get service by name (GET /plugins/services/name/{name}) |  |
| `revoke_access` | POST | `/service/plugins/services/revoke/{serviceName}` | Revoke access (POST /plugins/services/revoke/{serviceName}) |  |
| `validate_config` | POST | `/service/plugins/services/validateConfig` | Validate config (POST /plugins/services/validateConfig) |  |
| `delete_service` | DELETE | `/service/plugins/services/{id}` | Delete service (DELETE /plugins/services/{id}) |  |
| `get_service` | GET | `/service/plugins/services/{id}` | Get service (GET /plugins/services/{id}) |  |
| `update_service` | PUT | `/service/plugins/services/{id}` | Update service (PUT /plugins/services/{id}) |  |

## ranger_tags

47 tools.

- Product: Apache Ranger Admin REST API
- Version: swagger 3.0.0-SNAPSHOT (ranger.apache.org apidocs); CDP 7.1.9 ships Ranger 2.4 - GDS and some newer ops absent there
- Spec source: https://ranger.apache.org/apidocs/ui/swagger.json
- Auth: Basic (Ranger admin user) or Kerberos SPNEGO; via Knox: Knox SSO/JWT. Base https://<ranger-host>:6182/service (paths below are relative to /service)
- Scope: TagREST (/tags): tag defs, tags, tagged resources, maps
- Operations: 47

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `get_service_tags_if_updated` | GET | `/service/tags/download/{serviceName}` | Get service tags if updated (GET /tags/download/{serviceName}) |  |
| `import_service_tags2` | PUT | `/service/tags/importservicetags` | Import service tags2 (PUT /tags/importservicetags) |  |
| `delete_service_resource_by_guid` | DELETE | `/service/tags/resource/guid/{guid}` | Delete service resource by guid (DELETE /tags/resource/guid/{guid}) |  |
| `get_service_resource_by_guid` | GET | `/service/tags/resource/guid/{guid}` | Get service resource by guid (GET /tags/resource/guid/{guid}) |  |
| `update_service_resource_by_guid` | PUT | `/service/tags/resource/guid/{guid}` | Update service resource by guid (PUT /tags/resource/guid/{guid}) |  |
| `get_service_resource_by_resource` | GET | `/service/tags/resource/service/{serviceName}/resource` | Get service resource by resource (GET /tags/resource/service/{serviceName}/resource) |  |
| `get_service_resource_by_service_and_resource_signature` | GET | `/service/tags/resource/service/{serviceName}/signature/{resourceSignature}` | Get service resource by service and resource signature (GET /tags/resource/service/{serviceName}/signature/{resourceSignature}) |  |
| `delete_service_resource` | DELETE | `/service/tags/resource/{id}` | Delete service resource (DELETE /tags/resource/{id}) |  |
| `get_service_resource` | GET | `/service/tags/resource/{id}` | Get service resource (GET /tags/resource/{id}) |  |
| `update_service_resource` | PUT | `/service/tags/resource/{id}` | Update service resource (PUT /tags/resource/{id}) |  |
| `get_all_service_resources` | GET | `/service/tags/resources` | Get all service resources (GET /tags/resources) |  |
| `create_service_resource` | POST | `/service/tags/resources` | Create service resource (POST /tags/resources) |  |
| `get_service_resources_with_tags` | GET | `/service/tags/resources/paginated` | Get service resources with tags (GET /tags/resources/paginated) |  |
| `get_service_resources_by_service` | GET | `/service/tags/resources/service/{serviceName}` | Get service resources by service (GET /tags/resources/service/{serviceName}) |  |
| `get_secure_service_tags_if_updated` | GET | `/service/tags/secure/download/{serviceName}` | Get secure service tags if updated (GET /tags/secure/download/{serviceName}) |  |
| `delete_tag_deltas2` | DELETE | `/service/tags/server/tagdeltas` | Delete tag deltas2 (DELETE /tags/server/tagdeltas) |  |
| `delete_tag_by_guid` | DELETE | `/service/tags/tag/guid/{guid}` | Delete tag by guid (DELETE /tags/tag/guid/{guid}) |  |
| `get_tag_by_guid` | GET | `/service/tags/tag/guid/{guid}` | Get tag by guid (GET /tags/tag/guid/{guid}) |  |
| `update_tag_by_guid` | PUT | `/service/tags/tag/guid/{guid}` | Update tag by guid (PUT /tags/tag/guid/{guid}) |  |
| `delete_tag` | DELETE | `/service/tags/tag/{id}` | Delete tag (DELETE /tags/tag/{id}) |  |
| `get_tag` | GET | `/service/tags/tag/{id}` | Get tag (GET /tags/tag/{id}) |  |
| `update_tag` | PUT | `/service/tags/tag/{id}` | Update tag (PUT /tags/tag/{id}) |  |
| `delete_tag_def_by_guid` | DELETE | `/service/tags/tagdef/guid/{guid}` | Delete tag def by guid (DELETE /tags/tagdef/guid/{guid}) |  |
| `get_tag_def_by_guid` | GET | `/service/tags/tagdef/guid/{guid}` | Get tag def by guid (GET /tags/tagdef/guid/{guid}) |  |
| `get_tag_def_by_name` | GET | `/service/tags/tagdef/name/{name}` | Get tag def by name (GET /tags/tagdef/name/{name}) |  |
| `delete_tag_def` | DELETE | `/service/tags/tagdef/{id}` | Delete tag def (DELETE /tags/tagdef/{id}) |  |
| `get_tag_def` | GET | `/service/tags/tagdef/{id}` | Get tag def (GET /tags/tagdef/{id}) |  |
| `update_tag_def` | PUT | `/service/tags/tagdef/{id}` | Update tag def (PUT /tags/tagdef/{id}) |  |
| `get_all_tag_defs` | GET | `/service/tags/tagdefs` | Get all tag defs (GET /tags/tagdefs) |  |
| `create_tag_def` | POST | `/service/tags/tagdefs` | Create tag def (POST /tags/tagdefs) |  |
| `get_tag_defs` | GET | `/service/tags/tagdefs/paginated` | Get tag defs (GET /tags/tagdefs/paginated) |  |
| `delete_tag_resource_map_by_guid` | DELETE | `/service/tags/tagresourcemap/guid/{guid}` | Delete tag resource map by guid (DELETE /tags/tagresourcemap/guid/{guid}) |  |
| `get_tag_resource_map_by_guid` | GET | `/service/tags/tagresourcemap/guid/{guid}` | Get tag resource map by guid (GET /tags/tagresourcemap/guid/{guid}) |  |
| `get_tag_resource_map` | GET | `/service/tags/tagresourcemap/tag-resource-guid` | Get tag resource map (GET /tags/tagresourcemap/tag-resource-guid) |  |
| `delete_tag_resource_map` | DELETE | `/service/tags/tagresourcemap/{id}` | Delete tag resource map (DELETE /tags/tagresourcemap/{id}) |  |
| `get_tag_resource_map_by_id` | GET | `/service/tags/tagresourcemap/{id}` | Get tag resource map (GET /tags/tagresourcemap/{id}) |  |
| `delete_tag_resource_map_tagresourcemaps` | DELETE | `/service/tags/tagresourcemaps` | Delete tag resource map (DELETE /tags/tagresourcemaps) |  |
| `get_all_tag_resource_maps` | GET | `/service/tags/tagresourcemaps` | Get all tag resource maps (GET /tags/tagresourcemaps) |  |
| `create_tag_resource_map` | POST | `/service/tags/tagresourcemaps` | Create tag resource map (POST /tags/tagresourcemaps) |  |
| `get_tag_resource_maps` | GET | `/service/tags/tagresourcemaps/paginated` | Get tag resource maps (GET /tags/tagresourcemaps/paginated) |  |
| `get_all_tags` | GET | `/service/tags/tags` | Get all tags (GET /tags/tags) |  |
| `create_tag` | POST | `/service/tags/tags` | Create tag (POST /tags/tags) |  |
| `reset_tag_cache` | GET | `/service/tags/tags/cache/reset` | Resets/ removes tag policy cache for given service. |  |
| `reset_tag_cache_all` | GET | `/service/tags/tags/cache/reset-all` | Resets/ removes tag policy cache for all. |  |
| `get_tags` | GET | `/service/tags/tags/paginated` | Get tags (GET /tags/tags/paginated) |  |
| `get_tags_by_type` | GET | `/service/tags/tags/type/{type}` | Get tags by type (GET /tags/tags/type/{type}) |  |
| `get_tag_types` | GET | `/service/tags/types` | Get tag types (GET /tags/types) |  |

## ranger_roles_zones

30 tools.

- Product: Apache Ranger Admin REST API
- Version: swagger 3.0.0-SNAPSHOT (ranger.apache.org apidocs); CDP 7.1.9 ships Ranger 2.4 - GDS and some newer ops absent there
- Spec source: https://ranger.apache.org/apidocs/ui/swagger.json
- Auth: Basic (Ranger admin user) or Kerberos SPNEGO; via Knox: Knox SSO/JWT. Base https://<ranger-host>:6182/service (paths below are relative to /service)
- Scope: RoleREST (/roles) + SecurityZoneREST (/zones)
- Operations: 30

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `get_ranger_roles_if_updated` | GET | `/service/roles/download/{serviceName}` | Get ranger roles if updated (GET /roles/download/{serviceName}) |  |
| `get_all_roles_for_user` | GET | `/service/roles/lookup/roles` | Get all roles for user (GET /roles/lookup/roles) |  |
| `lookup_all_roles_names` | GET | `/service/roles/lookup/roles/names` | Lookup all roles names (GET /roles/lookup/roles/names) |  |
| `get_all_roles2` | GET | `/service/roles/roles` | Get all roles2 (GET /roles/roles) |  |
| `create_role2` | POST | `/service/roles/roles` | Create role2 (POST /roles/roles) |  |
| `get_roles_in_json` | GET | `/service/roles/roles/exportJson` | Get roles in json (GET /roles/roles/exportJson) |  |
| `grant_role2` | PUT | `/service/roles/roles/grant/{serviceName}` | Grant role2 (PUT /roles/roles/grant/{serviceName}) |  |
| `import_roles_from_file` | POST | `/service/roles/roles/importRolesFromFile` | Import roles from file (POST /roles/roles/importRolesFromFile) |  |
| `delete_role2` | DELETE | `/service/roles/roles/name/{name}` | Delete role2 (DELETE /roles/roles/name/{name}) |  |
| `get_role2` | GET | `/service/roles/roles/name/{name}` | Get role2 (GET /roles/roles/name/{name}) |  |
| `get_all_role_names2` | GET | `/service/roles/roles/names` | Get all role names2 (GET /roles/roles/names) |  |
| `revoke_role` | PUT | `/service/roles/roles/revoke/{serviceName}` | Revoke role (PUT /roles/roles/revoke/{serviceName}) |  |
| `get_user_roles2` | GET | `/service/roles/roles/user/{user}` | Get user roles2 (GET /roles/roles/user/{user}) |  |
| `delete_role2_by_id` | DELETE | `/service/roles/roles/{id}` | Delete role2 (DELETE /roles/roles/{id}) |  |
| `get_role2_by_id` | GET | `/service/roles/roles/{id}` | Get role2 (GET /roles/roles/{id}) |  |
| `update_role2` | PUT | `/service/roles/roles/{id}` | Update role2 (PUT /roles/roles/{id}) |  |
| `add_users_and_groups2` | PUT | `/service/roles/roles/{id}/addUsersAndGroups` | Add users and groups2 (PUT /roles/roles/{id}/addUsersAndGroups) |  |
| `remove_admin_from_users_and_groups2` | PUT | `/service/roles/roles/{id}/removeAdminFromUsersAndGroups` | Remove admin from users and groups2 (PUT /roles/roles/{id}/removeAdminFromUsersAndGroups) |  |
| `remove_users_and_groups2` | PUT | `/service/roles/roles/{id}/removeUsersAndGroups` | Remove users and groups2 (PUT /roles/roles/{id}/removeUsersAndGroups) |  |
| `get_secure_ranger_roles_if_updated` | GET | `/service/roles/secure/download/{serviceName}` | Get secure ranger roles if updated (GET /roles/secure/download/{serviceName}) |  |
| `get_zones_summary` | GET | `/service/zones/summary` | Get zones summary (GET /zones/summary) |  |
| `get_zone_names_for_resource` | GET | `/service/zones/zone-names/{serviceName}/resource` | Get zone names for resource (GET /zones/zone-names/{serviceName}/resource) |  |
| `get_all_zones2` | GET | `/service/zones/zones` | Get all zones2 (GET /zones/zones) |  |
| `create_security_zone2` | POST | `/service/zones/zones` | Create security zone2 (POST /zones/zones) |  |
| `delete_security_zone2` | DELETE | `/service/zones/zones/name/{name}` | Delete security zone2 (DELETE /zones/zones/name/{name}) |  |
| `get_security_zone2` | GET | `/service/zones/zones/name/{name}` | Get security zone2 (GET /zones/zones/name/{name}) |  |
| `get_security_zone_header_info_list_by_service_id2` | GET | `/service/zones/zones/zone-headers/for-service/{serviceId}` | Get security zone header info list by service id2 (GET /zones/zones/zone-headers/for-service/{serviceId}) |  |
| `delete_security_zone2_by_id` | DELETE | `/service/zones/zones/{id}` | Delete security zone2 (DELETE /zones/zones/{id}) |  |
| `get_security_zone2_by_id` | GET | `/service/zones/zones/{id}` | Get security zone2 (GET /zones/zones/{id}) |  |
| `update_security_zone2` | PUT | `/service/zones/zones/{id}` | Update security zone2 (PUT /zones/zones/{id}) |  |

## ranger_gds

54 tools.

- Product: Apache Ranger Admin REST API
- Version: swagger 3.0.0-SNAPSHOT (ranger.apache.org apidocs); CDP 7.1.9 ships Ranger 2.4 - GDS and some newer ops absent there
- Spec source: https://ranger.apache.org/apidocs/ui/swagger.json
- Auth: Basic (Ranger admin user) or Kerberos SPNEGO; via Knox: Knox SSO/JWT. Base https://<ranger-host>:6182/service (paths below are relative to /service)
- Scope: GdsREST (/gds) governed data sharing: datasets, projects, datashares (Ranger 2.5+/3.0; not in CDP 7.1.x)
- Operations: 54

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `search_datasets` | GET | `/service/gds/dataset` | Search datasets (GET /gds/dataset) |  |
| `create_dataset` | POST | `/service/gds/dataset` | Create dataset (POST /gds/dataset) |  |
| `get_enhanced_dataset_summary` | GET | `/service/gds/dataset/enhancedsummary` | Get enhanced dataset summary (GET /gds/dataset/enhancedsummary) |  |
| `list_dataset_names` | GET | `/service/gds/dataset/names` | List dataset names (GET /gds/dataset/names) |  |
| `search_dataset_in_projects` | GET | `/service/gds/dataset/project` | Search dataset in projects (GET /gds/dataset/project) |  |
| `add_dataset_in_project` | POST | `/service/gds/dataset/project` | Add dataset in project (POST /gds/dataset/project) |  |
| `remove_dataset_in_project` | DELETE | `/service/gds/dataset/project/{id}` | Remove dataset in project (DELETE /gds/dataset/project/{id}) |  |
| `get_dataset_in_project` | GET | `/service/gds/dataset/project/{id}` | Get dataset in project (GET /gds/dataset/project/{id}) |  |
| `update_dataset_in_project` | PUT | `/service/gds/dataset/project/{id}` | Update dataset in project (PUT /gds/dataset/project/{id}) |  |
| `get_dataset_summary` | GET | `/service/gds/dataset/summary` | Get dataset summary (GET /gds/dataset/summary) |  |
| `delete_dataset` | DELETE | `/service/gds/dataset/{id}` | Delete dataset (DELETE /gds/dataset/{id}) |  |
| `get_dataset` | GET | `/service/gds/dataset/{id}` | Get dataset (GET /gds/dataset/{id}) |  |
| `update_dataset` | PUT | `/service/gds/dataset/{id}` | Update dataset (PUT /gds/dataset/{id}) |  |
| `add_data_shares_in_dataset` | POST | `/service/gds/dataset/{id}/datashare` | Add data shares in dataset (POST /gds/dataset/{id}/datashare) |  |
| `update_data_set_grants` | PUT | `/service/gds/dataset/{id}/grant` | Update data set grants (PUT /gds/dataset/{id}/grant) |  |
| `get_data_set_grants` | GET | `/service/gds/dataset/{id}/grants` | Get data set grants (GET /gds/dataset/{id}/grants) |  |
| `get_dataset_policies` | GET | `/service/gds/dataset/{id}/policy` | Get dataset policies (GET /gds/dataset/{id}/policy) |  |
| `add_dataset_policy` | POST | `/service/gds/dataset/{id}/policy` | Add dataset policy (POST /gds/dataset/{id}/policy) |  |
| `delete_dataset_policy` | DELETE | `/service/gds/dataset/{id}/policy/{policyId}` | Delete dataset policy (DELETE /gds/dataset/{id}/policy/{policyId}) |  |
| `get_dataset_policy` | GET | `/service/gds/dataset/{id}/policy/{policyId}` | Get dataset policy (GET /gds/dataset/{id}/policy/{policyId}) |  |
| `update_dataset_policy` | PUT | `/service/gds/dataset/{id}/policy/{policyId}` | Update dataset policy (PUT /gds/dataset/{id}/policy/{policyId}) |  |
| `add_dataset_resources` | POST | `/service/gds/dataset/{id}/resources/{serviceName}` | Add dataset resources (POST /gds/dataset/{id}/resources/{serviceName}) |  |
| `search_data_shares` | GET | `/service/gds/datashare` | Search data shares (GET /gds/datashare) |  |
| `create_data_share` | POST | `/service/gds/datashare` | Create data share (POST /gds/datashare) |  |
| `search_data_share_in_datasets` | GET | `/service/gds/datashare/dataset` | Search data share in datasets (GET /gds/datashare/dataset) |  |
| `add_data_share_in_dataset` | POST | `/service/gds/datashare/dataset` | Add data share in dataset (POST /gds/datashare/dataset) |  |
| `get_dsh_in_ds_summary` | GET | `/service/gds/datashare/dataset/summary` | Get dsh in ds summary (GET /gds/datashare/dataset/summary) |  |
| `remove_data_share_in_dataset` | DELETE | `/service/gds/datashare/dataset/{id}` | Remove data share in dataset (DELETE /gds/datashare/dataset/{id}) |  |
| `get_data_share_in_dataset` | GET | `/service/gds/datashare/dataset/{id}` | Get data share in dataset (GET /gds/datashare/dataset/{id}) |  |
| `update_data_share_in_dataset` | PUT | `/service/gds/datashare/dataset/{id}` | Update data share in dataset (PUT /gds/datashare/dataset/{id}) |  |
| `get_data_share_summary` | GET | `/service/gds/datashare/summary` | Get data share summary (GET /gds/datashare/summary) |  |
| `delete_data_share` | DELETE | `/service/gds/datashare/{id}` | Delete data share (DELETE /gds/datashare/{id}) |  |
| `get_data_share` | GET | `/service/gds/datashare/{id}` | Get data share (GET /gds/datashare/{id}) |  |
| `update_data_share` | PUT | `/service/gds/datashare/{id}` | Update data share (PUT /gds/datashare/{id}) |  |
| `get_service_gds_info_if_updated` | GET | `/service/gds/download/{serviceName}` | Get service gds info if updated (GET /gds/download/{serviceName}) |  |
| `search_projects` | GET | `/service/gds/project` | Search projects (GET /gds/project) |  |
| `create_project` | POST | `/service/gds/project` | Create project (POST /gds/project) |  |
| `list_project_names` | GET | `/service/gds/project/names` | List project names (GET /gds/project/names) |  |
| `delete_project` | DELETE | `/service/gds/project/{id}` | Delete project (DELETE /gds/project/{id}) |  |
| `get_project` | GET | `/service/gds/project/{id}` | Get project (GET /gds/project/{id}) |  |
| `update_project` | PUT | `/service/gds/project/{id}` | Update project (PUT /gds/project/{id}) |  |
| `get_project_policies` | GET | `/service/gds/project/{id}/policy` | Get project policies (GET /gds/project/{id}/policy) |  |
| `add_project_policy` | POST | `/service/gds/project/{id}/policy` | Add project policy (POST /gds/project/{id}/policy) |  |
| `delete_project_policy` | DELETE | `/service/gds/project/{id}/policy/{policyId}` | Delete project policy (DELETE /gds/project/{id}/policy/{policyId}) |  |
| `get_project_policy` | GET | `/service/gds/project/{id}/policy/{policyId}` | Get project policy (GET /gds/project/{id}/policy/{policyId}) |  |
| `update_project_policy` | PUT | `/service/gds/project/{id}/policy/{policyId}` | Update project policy (PUT /gds/project/{id}/policy/{policyId}) |  |
| `search_shared_resources` | GET | `/service/gds/resource` | Search shared resources (GET /gds/resource) |  |
| `add_shared_resource` | POST | `/service/gds/resource` | Add shared resource (POST /gds/resource) |  |
| `remove_shared_resource` | DELETE | `/service/gds/resource/{id}` | Remove shared resource (DELETE /gds/resource/{id}) |  |
| `get_shared_resource` | GET | `/service/gds/resource/{id}` | Get shared resource (GET /gds/resource/{id}) |  |
| `update_shared_resource` | PUT | `/service/gds/resource/{id}` | Update shared resource (PUT /gds/resource/{id}) |  |
| `remove_shared_resources` | DELETE | `/service/gds/resources` | Remove shared resources (DELETE /gds/resources) |  |
| `add_shared_resources` | POST | `/service/gds/resources` | Add shared resources (POST /gds/resources) |  |
| `get_secure_service_gds_info_if_updated` | GET | `/service/gds/secure/download/{serviceName}` | Get secure service gds info if updated (GET /gds/secure/download/{serviceName}) |  |

## ranger_admin_misc

51 tools.

- Product: Apache Ranger Admin REST API
- Version: swagger 3.0.0-SNAPSHOT (ranger.apache.org apidocs); CDP 7.1.9 ships Ranger 2.4 - GDS and some newer ops absent there
- Spec source: https://ranger.apache.org/apidocs/ui/swagger.json
- Auth: Basic (Ranger admin user) or Kerberos SPNEGO; via Knox: Knox SSO/JWT. Base https://<ranger-host>:6182/service (paths below are relative to /service)
- Scope: AssetREST, legacy public API v1, XKeyREST (KMS keys), metrics, health, admin log level
- Operations: 51

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `get_ranger_server_health` | GET | `/service/actuator/health` | Get ranger server health (GET /actuator/health) |  |
| `set_log_level` | POST | `/service/admin/set-logger-level` | An endpoint to set the log level for a specific class or package. |  |
| `get_access_logs` | GET | `/service/assets/accessAudit` | Get access logs (GET /assets/accessAudit) |  |
| `search_x_assets` | GET | `/service/assets/assets` | Search x assets (GET /assets/assets) |  |
| `create_x_asset` | POST | `/service/assets/assets` | Create x asset (POST /assets/assets) |  |
| `count_x_assets` | GET | `/service/assets/assets/count` | Count x assets (GET /assets/assets/count) |  |
| `config_test` | POST | `/service/assets/assets/testConfig` | Config test (POST /assets/assets/testConfig) |  |
| `delete_x_asset` | DELETE | `/service/assets/assets/{id}` | Delete x asset (DELETE /assets/assets/{id}) |  |
| `get_x_asset` | GET | `/service/assets/assets/{id}` | Get x asset (GET /assets/assets/{id}) |  |
| `update_x_asset` | PUT | `/service/assets/assets/{id}` | Update x asset (PUT /assets/assets/{id}) |  |
| `search_x_credential_stores` | GET | `/service/assets/credstores` | Search x credential stores (GET /assets/credstores) |  |
| `create_x_credential_store` | POST | `/service/assets/credstores` | Create x credential store (POST /assets/credstores) |  |
| `update_x_credential_store` | PUT | `/service/assets/credstores` | Update x credential store (PUT /assets/credstores) |  |
| `count_x_credential_stores` | GET | `/service/assets/credstores/count` | Count x credential stores (GET /assets/credstores/count) |  |
| `delete_x_credential_store` | DELETE | `/service/assets/credstores/{id}` | Delete x credential store (DELETE /assets/credstores/{id}) |  |
| `get_x_credential_store` | GET | `/service/assets/credstores/{id}` | Get x credential store (GET /assets/credstores/{id}) |  |
| `search_x_policy_export_audits` | GET | `/service/assets/exportAudit` | Search x policy export audits (GET /assets/exportAudit) |  |
| `get_report_logs` | GET | `/service/assets/report` | Get report logs (GET /assets/report) |  |
| `get_transaction_report` | GET | `/service/assets/report/{transactionId}` | Get transaction report (GET /assets/report/{transactionId}) |  |
| `search_x_resources` | GET | `/service/assets/resources` | Search x resources (GET /assets/resources) |  |
| `create_x_resource` | POST | `/service/assets/resources` | Create x resource (POST /assets/resources) |  |
| `count_x_resources` | GET | `/service/assets/resources/count` | Count x resources (GET /assets/resources/count) |  |
| `grant_permission` | POST | `/service/assets/resources/grant` | Grant permission (POST /assets/resources/grant) |  |
| `revoke_permission` | POST | `/service/assets/resources/revoke` | Revoke permission (POST /assets/resources/revoke) |  |
| `delete_x_resource` | DELETE | `/service/assets/resources/{id}` | Delete x resource (DELETE /assets/resources/{id}) |  |
| `get_x_resource` | GET | `/service/assets/resources/{id}` | Get x resource (GET /assets/resources/{id}) |  |
| `update_x_resource` | PUT | `/service/assets/resources/{id}` | Update x resource (PUT /assets/resources/{id}) |  |
| `get_ugsync_audits` | GET | `/service/assets/ugsyncAudits` | Get ugsync audits (GET /assets/ugsyncAudits) |  |
| `get_ugsync_audits_by_sync_source` | GET | `/service/assets/ugsyncAudits/{syncSource}` | Get ugsync audits by sync source (GET /assets/ugsyncAudits/{syncSource}) |  |
| `get_report_logs_v2` | GET | `/service/assets/v2/report` | Get report logs v2 (GET /assets/v2/report) |  |
| `get_transaction_report_v2` | GET | `/service/assets/v2/report/{transactionId}` | Get transaction report v2 (GET /assets/v2/report/{transactionId}) |  |
| `create_key` | POST | `/service/keys/key` | Implements the create key functionality |  |
| `rollover_key` | PUT | `/service/keys/key` | Implements the Rollover key functionality |  |
| `delete_key` | DELETE | `/service/keys/key/{alias}` | Implements the delete key functionality |  |
| `get_key` | GET | `/service/keys/key/{alias}` | Get key (GET /keys/key/{alias}) |  |
| `search_keys` | GET | `/service/keys/keys` | Implements the traditional search functionalities for Keys |  |
| `get_metrics_json` | GET | `/service/metrics/json` | Get metrics json (GET /metrics/json) |  |
| `get_metrics_prometheus` | GET | `/service/metrics/prometheus` | Get metrics prometheus (GET /metrics/prometheus) |  |
| `get_status` | GET | `/service/metrics/status` | Get status (GET /metrics/status) |  |
| `search_policies` | GET | `/service/public/api/policy` | Search policies (GET /public/api/policy) |  |
| `create_policy2` | POST | `/service/public/api/policy` | Create policy2 (POST /public/api/policy) |  |
| `count_policies2` | GET | `/service/public/api/policy/count` | Count policies2 (GET /public/api/policy/count) |  |
| `delete_policy2` | DELETE | `/service/public/api/policy/{id}` | Delete policy2 (DELETE /public/api/policy/{id}) |  |
| `get_policy2` | GET | `/service/public/api/policy/{id}` | Get policy2 (GET /public/api/policy/{id}) |  |
| `update_policy2` | PUT | `/service/public/api/policy/{id}` | Update policy2 (PUT /public/api/policy/{id}) |  |
| `search_repositories` | GET | `/service/public/api/repository` | Search repositories (GET /public/api/repository) |  |
| `create_repository` | POST | `/service/public/api/repository` | Create repository (POST /public/api/repository) |  |
| `count_repositories` | GET | `/service/public/api/repository/count` | Count repositories (GET /public/api/repository/count) |  |
| `delete_repository` | DELETE | `/service/public/api/repository/{id}` | Delete repository (DELETE /public/api/repository/{id}) |  |
| `get_repository` | GET | `/service/public/api/repository/{id}` | Get repository (GET /public/api/repository/{id}) |  |
| `update_repository` | PUT | `/service/public/api/repository/{id}` | Update repository (PUT /public/api/repository/{id}) |  |

## atlas_entities

45 tools.

- Product: Apache Atlas REST API v2
- Version: swagger 2.5.0 (atlas.apache.org); CDP 7.1.9 ships Atlas 2.1 - a few newer ops may be missing
- Spec source: https://atlas.apache.org/api/v2/ui/swagger.json
- Auth: Basic (file/LDAP) or Kerberos SPNEGO; Knox SSO/JWT via Knox proxy. Base https://<atlas-host>:31443/api/atlas
- Scope: EntityREST, RelationshipREST, LineageREST, NotificationREST
- Operations: 45

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `create_or_update` | POST | `/api/atlas/v2/entity` | Create new entity or update existing entity in Atlas. |  |
| `delete_by_guids` | DELETE | `/api/atlas/v2/entity/bulk` | Bulk API to delete list of entities identified by its GUIDs |  |
| `get_by_guids` | GET | `/api/atlas/v2/entity/bulk` | Bulk API to retrieve list of entities identified by its GUIDs. |  |
| `create_or_update_bulk` | POST | `/api/atlas/v2/entity/bulk` | Bulk API to create new entities or updates existing entities in Atlas. |  |
| `add_classification` | POST | `/api/atlas/v2/entity/bulk/classification` | Bulk API to associate a tag to multiple entities. |  |
| `get_entity_headers` | GET | `/api/atlas/v2/entity/bulk/headers` | Get entity headers (GET /api/atlas/v2/entity/bulk/headers) |  |
| `set_classifications` | POST | `/api/atlas/v2/entity/bulk/setClassifications` | Set classifications (POST /api/atlas/v2/entity/bulk/setClassifications) |  |
| `get_entities_by_unique_attributes` | GET | `/api/atlas/v2/entity/bulk/uniqueAttribute/type/{typeName}` | Bulk API to retrieve list of entities identified by its unique attributes. |  |
| `import_bm_attributes` | POST | `/api/atlas/v2/entity/businessmetadata/import` | Upload the file for creating Business Metadata in BULK |  |
| `produce_template` | GET | `/api/atlas/v2/entity/businessmetadata/import/template` | Get the sample Template for uploading/creating bulk BusinessMetaData |  |
| `delete_by_guid` | DELETE | `/api/atlas/v2/entity/guid/{guid}` | Delete an entity identified by its GUID. |  |
| `get_by_id` | GET | `/api/atlas/v2/entity/guid/{guid}` | Fetch complete definition of an entity given its GUID. |  |
| `partial_update_entity_attr_by_guid` | PUT | `/api/atlas/v2/entity/guid/{guid}` | Entity Partial Update - Add/Update entity attribute identified by its GUID. |  |
| `remove_business_attributes` | DELETE | `/api/atlas/v2/entity/guid/{guid}/businessmetadata` | Remove business attributes (DELETE /api/atlas/v2/entity/guid/{guid}/businessmetadata) |  |
| `add_or_update_business_attributes` | POST | `/api/atlas/v2/entity/guid/{guid}/businessmetadata` | Add or update business attributes (POST /api/atlas/v2/entity/guid/{guid}/businessmetadata) |  |
| `remove_business_attributes_by_bm_name` | DELETE | `/api/atlas/v2/entity/guid/{guid}/businessmetadata/{bmName}` | Remove business attributes by bm name (DELETE /api/atlas/v2/entity/guid/{guid}/businessmetadata/{bmName}) |  |
| `add_or_update_business_attributes_by_bm_name` | POST | `/api/atlas/v2/entity/guid/{guid}/businessmetadata/{bmName}` | Add or update business attributes by bm name (POST /api/atlas/v2/entity/guid/{guid}/businessmetadata/{bmName}) |  |
| `delete_classification` | DELETE | `/api/atlas/v2/entity/guid/{guid}/classification/{classificationName}` | Deletes a given classification from an existing entity represented by a guid. |  |
| `get_classification` | GET | `/api/atlas/v2/entity/guid/{guid}/classification/{classificationName}` | Gets the list of classifications for a given entity represented by a guid. |  |
| `get_classifications` | GET | `/api/atlas/v2/entity/guid/{guid}/classifications` | Gets the list of classifications for a given entity represented by a guid. |  |
| `add_classifications` | POST | `/api/atlas/v2/entity/guid/{guid}/classifications` | Adds classifications to an existing entity represented by a guid. |  |
| `update_classifications` | PUT | `/api/atlas/v2/entity/guid/{guid}/classifications` | Updates classifications to an existing entity represented by a guid. |  |
| `get_header_by_id` | GET | `/api/atlas/v2/entity/guid/{guid}/header` | Get entity header given its GUID. |  |
| `remove_labels` | DELETE | `/api/atlas/v2/entity/guid/{guid}/labels` | delete given labels to a given entity |  |
| `set_labels` | POST | `/api/atlas/v2/entity/guid/{guid}/labels` | Set labels to a given entity |  |
| `add_labels` | PUT | `/api/atlas/v2/entity/guid/{guid}/labels` | add given labels to a given entity |  |
| `delete_by_unique_attribute` | DELETE | `/api/atlas/v2/entity/uniqueAttribute/type/{typeName}` | Delete an entity identified by its type and unique attributes. |  |
| `get_by_unique_attributes` | GET | `/api/atlas/v2/entity/uniqueAttribute/type/{typeName}` | Fetch complete definition of an entity given its type and unique attribute. |  |
| `partial_update_entity_by_unique_attrs` | PUT | `/api/atlas/v2/entity/uniqueAttribute/type/{typeName}` | Entity Partial Update - Allows a subset of attributes to be updated on |  |
| `delete_classification_by_unique_attribute` | DELETE | `/api/atlas/v2/entity/uniqueAttribute/type/{typeName}/classification/{classificationName}` | Deletes a given classification from an entity identified by its type and unique attributes. |  |
| `add_classifications_by_unique_attribute` | POST | `/api/atlas/v2/entity/uniqueAttribute/type/{typeName}/classifications` | Adds classification to the entity identified by its type and unique attributes. |  |
| `update_classifications_by_unique_attribute` | PUT | `/api/atlas/v2/entity/uniqueAttribute/type/{typeName}/classifications` | Updates classification on an entity identified by its type and unique attributes. |  |
| `get_entity_header_by_unique_attributes` | GET | `/api/atlas/v2/entity/uniqueAttribute/type/{typeName}/header` | Fetch AtlasEntityHeader given its type and unique attribute. |  |
| `remove_labels_by_unique_attribute` | DELETE | `/api/atlas/v2/entity/uniqueAttribute/type/{typeName}/labels` | Remove labels by unique attribute (DELETE /api/atlas/v2/entity/uniqueAttribute/type/{typeName}/labels) |  |
| `set_labels_by_unique_attribute` | POST | `/api/atlas/v2/entity/uniqueAttribute/type/{typeName}/labels` | Set labels by unique attribute (POST /api/atlas/v2/entity/uniqueAttribute/type/{typeName}/labels) |  |
| `add_labels_by_unique_attribute` | PUT | `/api/atlas/v2/entity/uniqueAttribute/type/{typeName}/labels` | Add labels by unique attribute (PUT /api/atlas/v2/entity/uniqueAttribute/type/{typeName}/labels) |  |
| `get_audit_events` | GET | `/api/atlas/v2/entity/{guid}/audit` | Get audit events (GET /api/atlas/v2/entity/{guid}/audit) |  |
| `get_lineage_by_unique_attribute` | GET | `/api/atlas/v2/lineage/uniqueAttribute/type/{typeName}` | Returns lineage info about entity. |  |
| `get_lineage_graph` | GET | `/api/atlas/v2/lineage/{guid}` | Returns lineage info about entity. |  |
| `get_lineage_graph2` | POST | `/api/atlas/v2/lineage/{guid}` | Returns lineage info about entity. |  |
| `handle_notifications` | POST | `/api/atlas/v2/notification/topic/{topicName}` | Publish notifications on Kafka topic |  |
| `create` | POST | `/api/atlas/v2/relationship` | Create a new relationship between entities. |  |
| `update` | PUT | `/api/atlas/v2/relationship` | Update an existing relationship between entities. |  |
| `delete_by_id` | DELETE | `/api/atlas/v2/relationship/guid/{guid}` | Delete a relationship between entities using guid. |  |
| `get_by_id2` | GET | `/api/atlas/v2/relationship/guid/{guid}` | Get relationship information between entities using guid. |  |

## atlas_types

20 tools.

- Product: Apache Atlas REST API v2
- Version: swagger 2.5.0 (atlas.apache.org); CDP 7.1.9 ships Atlas 2.1 - a few newer ops may be missing
- Spec source: https://atlas.apache.org/api/v2/ui/swagger.json
- Auth: Basic (file/LDAP) or Kerberos SPNEGO; Knox SSO/JWT via Knox proxy. Base https://<atlas-host>:31443/api/atlas
- Scope: TypesREST typedefs
- Operations: 20

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `get_business_metadata_def_by_guid` | GET | `/api/atlas/v2/types/businessmetadatadef/guid/{guid}` | Get the businessMetadata definition for the given guid |  |
| `get_business_metadata_def_by_name` | GET | `/api/atlas/v2/types/businessmetadatadef/name/{name}` | Get the businessMetadata definition by it's name (unique) |  |
| `get_classification_def_by_guid` | GET | `/api/atlas/v2/types/classificationdef/guid/{guid}` | Get the classification definition for the given guid |  |
| `get_classification_def_by_name` | GET | `/api/atlas/v2/types/classificationdef/name/{name}` | Get the classification definition by it's name (unique) |  |
| `get_entity_def_by_guid` | GET | `/api/atlas/v2/types/entitydef/guid/{guid}` | Get the Entity definition for the given guid |  |
| `get_entity_def_by_name` | GET | `/api/atlas/v2/types/entitydef/name/{name}` | Get the entity definition by it's name (unique) |  |
| `get_enum_def_by_guid` | GET | `/api/atlas/v2/types/enumdef/guid/{guid}` | Get the enum definition for the given guid |  |
| `get_enum_def_by_name` | GET | `/api/atlas/v2/types/enumdef/name/{name}` | Get the enum definition by it's name (unique) |  |
| `get_relationship_def_by_guid` | GET | `/api/atlas/v2/types/relationshipdef/guid/{guid}` | Get the relationship definition for the given guid |  |
| `get_relationship_def_by_name` | GET | `/api/atlas/v2/types/relationshipdef/name/{name}` | Get the relationship definition by it's name (unique) |  |
| `get_struct_def_by_guid` | GET | `/api/atlas/v2/types/structdef/guid/{guid}` | Get the struct definition for the given guid |  |
| `get_struct_def_by_name` | GET | `/api/atlas/v2/types/structdef/name/{name}` | Get the struct definition by it's name (unique) |  |
| `get_type_def_by_guid` | GET | `/api/atlas/v2/types/typedef/guid/{guid}` | Get type def by guid (GET /api/atlas/v2/types/typedef/guid/{guid}) |  |
| `get_type_def_by_name` | GET | `/api/atlas/v2/types/typedef/name/{name}` | Get type definition by it's name |  |
| `delete_atlas_type_by_name` | DELETE | `/api/atlas/v2/types/typedef/name/{typeName}` | Delete API for type identified by its name. |  |
| `delete_atlas_type_defs` | DELETE | `/api/atlas/v2/types/typedefs` | Bulk delete API for all types |  |
| `get_all_type_defs` | GET | `/api/atlas/v2/types/typedefs` | Bulk retrieval API for retrieving all type definitions in Atlas |  |
| `create_atlas_type_defs` | POST | `/api/atlas/v2/types/typedefs` | Bulk create APIs for all atlas type definitions, only new definitions will be created. |  |
| `update_atlas_type_defs` | PUT | `/api/atlas/v2/types/typedefs` | Bulk update API for all types, changes detected in the type definitions would be persisted |  |
| `get_type_def_headers` | GET | `/api/atlas/v2/types/typedefs/headers` | Bulk retrieval API for all type definitions returned as a list of minimal information header |  |

## atlas_glossary

32 tools.

- Product: Apache Atlas REST API v2
- Version: swagger 2.5.0 (atlas.apache.org); CDP 7.1.9 ships Atlas 2.1 - a few newer ops may be missing
- Spec source: https://atlas.apache.org/api/v2/ui/swagger.json
- Auth: Basic (file/LDAP) or Kerberos SPNEGO; Knox SSO/JWT via Knox proxy. Base https://<atlas-host>:31443/api/atlas
- Scope: GlossaryREST
- Operations: 32

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `get_glossaries` | GET | `/api/atlas/v2/glossary` | Retrieve all glossaries registered with Atlas |  |
| `create_glossary` | POST | `/api/atlas/v2/glossary` | Create a glossary |  |
| `create_glossary_categories` | POST | `/api/atlas/v2/glossary/categories` | Create glossary category in bulk |  |
| `create_glossary_category` | POST | `/api/atlas/v2/glossary/category` | Create glossary category |  |
| `delete_glossary_category` | DELETE | `/api/atlas/v2/glossary/category/{categoryGuid}` | Delete a glossary category |  |
| `get_glossary_category` | GET | `/api/atlas/v2/glossary/category/{categoryGuid}` | Get specific glossary category |  |
| `update_glossary_category` | PUT | `/api/atlas/v2/glossary/category/{categoryGuid}` | Update the given glossary category |  |
| `partial_update_glossary_category` | PUT | `/api/atlas/v2/glossary/category/{categoryGuid}/partial` | Partially update the glossary category |  |
| `get_related_categories` | GET | `/api/atlas/v2/glossary/category/{categoryGuid}/related` | Get all related categories (parent and children) |  |
| `get_category_terms` | GET | `/api/atlas/v2/glossary/category/{categoryGuid}/terms` | Get all terms associated with the specific category |  |
| `import_glossary_data` | POST | `/api/atlas/v2/glossary/import` | Upload glossary file for creating AtlasGlossaryTerms in bulk |  |
| `produce_template2` | GET | `/api/atlas/v2/glossary/import/template` | Get sample template for uploading/creating bulk AtlasGlossaryTerm |  |
| `create_glossary_term` | POST | `/api/atlas/v2/glossary/term` | Create a glossary term |  |
| `delete_glossary_term` | DELETE | `/api/atlas/v2/glossary/term/{termGuid}` | Delete a glossary term |  |
| `get_glossary_term` | GET | `/api/atlas/v2/glossary/term/{termGuid}` | Get specific glossary term |  |
| `update_glossary_term` | PUT | `/api/atlas/v2/glossary/term/{termGuid}` | Update the given glossary term |  |
| `partial_update_glossary_term` | PUT | `/api/atlas/v2/glossary/term/{termGuid}/partial` | Partially update the glossary term |  |
| `create_glossary_terms` | POST | `/api/atlas/v2/glossary/terms` | Create glossary terms in bulk |  |
| `remove_term_assignment_from_entities` | DELETE | `/api/atlas/v2/glossary/terms/{termGuid}/assignedEntities` | Remove the term assignment for the given list of entity headers |  |
| `get_entities_assigned_with_term` | GET | `/api/atlas/v2/glossary/terms/{termGuid}/assignedEntities` | Get all entity headers assigned with the specified term |  |
| `assign_term_to_entities` | POST | `/api/atlas/v2/glossary/terms/{termGuid}/assignedEntities` | Assign the given term to the provided list of entity headers |  |
| `disassociate_term_assignment_from_entities` | PUT | `/api/atlas/v2/glossary/terms/{termGuid}/assignedEntities` | Remove the term assignment for the given list of entity headers |  |
| `get_related_terms` | GET | `/api/atlas/v2/glossary/terms/{termGuid}/related` | Get all related terms for a specific term |  |
| `delete_glossary` | DELETE | `/api/atlas/v2/glossary/{glossaryGuid}` | Delete a glossary |  |
| `get_glossary` | GET | `/api/atlas/v2/glossary/{glossaryGuid}` | Get a specific Glossary |  |
| `update_glossary` | PUT | `/api/atlas/v2/glossary/{glossaryGuid}` | Update the given glossary |  |
| `get_glossary_categories` | GET | `/api/atlas/v2/glossary/{glossaryGuid}/categories` | Get the categories belonging to a specific glossary |  |
| `get_glossary_categories_headers` | GET | `/api/atlas/v2/glossary/{glossaryGuid}/categories/headers` | Get the categories belonging to a specific glossary |  |
| `get_detailed_glossary` | GET | `/api/atlas/v2/glossary/{glossaryGuid}/detailed` | Get a specific Glossary |  |
| `partial_update_glossary` | PUT | `/api/atlas/v2/glossary/{glossaryGuid}/partial` | Partially update the glossary |  |
| `get_glossary_terms` | GET | `/api/atlas/v2/glossary/{glossaryGuid}/terms` | Get terms belonging to a specific glossary |  |
| `get_glossary_term_headers` | GET | `/api/atlas/v2/glossary/{glossaryGuid}/terms/headers` | Get term headers belonging to a specific glossary |  |

## atlas_discovery

24 tools.

- Product: Apache Atlas REST API v2
- Version: swagger 2.5.0 (atlas.apache.org); CDP 7.1.9 ships Atlas 2.1 - a few newer ops may be missing
- Spec source: https://atlas.apache.org/api/v2/ui/swagger.json
- Auth: Basic (file/LDAP) or Kerberos SPNEGO; Knox SSO/JWT via Knox proxy. Base https://<atlas-host>:31443/api/atlas
- Scope: DiscoveryREST search + saved searches, IndexRecoveryREST
- Operations: 24

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `get_index_recovery_data` | GET | `/api/atlas/v2/indexrecovery` | Get index recovery data (GET /api/atlas/v2/indexrecovery) |  |
| `start_custom_index_recovery` | POST | `/api/atlas/v2/indexrecovery/start` | Start custom index recovery (POST /api/atlas/v2/indexrecovery/start) |  |
| `search_using_attribute` | GET | `/api/atlas/v2/search/attribute` | Retrieve data for the specified attribute search query |  |
| `search_using_basic` | GET | `/api/atlas/v2/search/basic` | Retrieve data for the specified fulltext query |  |
| `search_with_parameters` | POST | `/api/atlas/v2/search/basic` | Attribute based search for entities satisfying the search parameters |  |
| `basic_search_create_file` | POST | `/api/atlas/v2/search/basic/download/create_file` | Basic search create file (POST /api/atlas/v2/search/basic/download/create_file) |  |
| `get_search_result_download_status` | GET | `/api/atlas/v2/search/download/status` | Get search result download status (GET /api/atlas/v2/search/download/status) |  |
| `download_search_result_file` | GET | `/api/atlas/v2/search/download/{filename}` | Download search result file (GET /api/atlas/v2/search/download/{filename}) |  |
| `search_using_dsl` | GET | `/api/atlas/v2/search/dsl` | Retrieve data for the specified DSL |  |
| `dsl_search_create_file` | POST | `/api/atlas/v2/search/dsl/download/create_file` | Dsl search create file (POST /api/atlas/v2/search/dsl/download/create_file) |  |
| `search_using_full_text` | GET | `/api/atlas/v2/search/fulltext` | Retrieve data for the specified fulltext query |  |
| `quick_search` | GET | `/api/atlas/v2/search/quick` | Attribute based search for entities satisfying the search parameters |  |
| `quick_search2` | POST | `/api/atlas/v2/search/quick` | Attribute based search for entities satisfying the search parameters |  |
| `relation_search` | GET | `/api/atlas/v2/search/relations` | Relationship search to search for relations(edges) |  |
| `relation_search2` | POST | `/api/atlas/v2/search/relations` | Relationship search to search for relations(edges) |  |
| `search_related_entities` | GET | `/api/atlas/v2/search/relationship` | Relationship search to search for related entities satisfying the search parameters |  |
| `get_saved_searches` | GET | `/api/atlas/v2/search/saved` | Get saved searches (GET /api/atlas/v2/search/saved) |  |
| `add_saved_search` | POST | `/api/atlas/v2/search/saved` | Add saved search (POST /api/atlas/v2/search/saved) |  |
| `update_saved_search` | PUT | `/api/atlas/v2/search/saved` | Update saved search (PUT /api/atlas/v2/search/saved) |  |
| `execute_saved_search_by_guid` | GET | `/api/atlas/v2/search/saved/execute/guid/{guid}` | Attribute based search for entities satisfying the search parameters |  |
| `execute_saved_search_by_name` | GET | `/api/atlas/v2/search/saved/execute/{name}` | Attribute based search for entities satisfying the search parameters |  |
| `delete_saved_search` | DELETE | `/api/atlas/v2/search/saved/{guid}` | Delete saved search (DELETE /api/atlas/v2/search/saved/{guid}) |  |
| `get_saved_search` | GET | `/api/atlas/v2/search/saved/{name}` | Get saved search (GET /api/atlas/v2/search/saved/{name}) |  |
| `get_suggestions` | GET | `/api/atlas/v2/search/suggestions` | Get suggestions (GET /api/atlas/v2/search/suggestions) |  |

## atlas_admin

33 tools.

- Product: Apache Atlas admin REST API (non-v2)
- Version: Atlas master AdminResource.java (2.4+/3.x); CDP 7.1.9 (Atlas 2.1) lacks async import, tasks, debug metrics, liveness/readiness
- Spec source: https://github.com/apache/atlas/blob/master/webapp/src/main/java/org/apache/atlas/web/resources/AdminResource.java (from source; not in swagger)
- Auth: Same as Atlas v2
- Operations: 33

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `get_thread_dump` | GET | `/api/atlas/admin/stack` | Get thread dump |  |
| `get_version` | GET | `/api/atlas/admin/version` | Get version |  |
| `get_status` | GET | `/api/atlas/admin/status` | Get status |  |
| `get_user_profile` | GET | `/api/atlas/admin/session` | Get user profile |  |
| `get_metrics` | GET | `/api/atlas/admin/metrics` | Get metrics |  |
| `get_all_metrics` | GET | `/api/atlas/admin/metricsstats` | Get all metrics |  |
| `get_metrics_by_collection_time` | GET | `/api/atlas/admin/metricsstat/{collectionTime}` | Get metrics by collection time |  |
| `get_metrics_in_time_range` | GET | `/api/atlas/admin/metricsstats/range` | Get metrics in time range |  |
| `get_metrics_for_chart_by_type_names` | GET | `/api/atlas/admin/metricsstats/charts` | Get metrics for chart by type names |  |
| `export` | POST | `/api/atlas/admin/export` | Export |  |
| `import_data` | POST | `/api/atlas/admin/import` | Import data |  |
| `import_async` | POST | `/api/atlas/admin/async/import` | Import async |  |
| `abort_async_import` | DELETE | `/api/atlas/admin/async/import/{importId}` | Abort async import |  |
| `get_async_import_status` | GET | `/api/atlas/admin/async/import/status` | Get async import status |  |
| `get_async_import_status_by_id` | GET | `/api/atlas/admin/async/import/status/{importId}` | Get async import status by id |  |
| `purge_by_ids` | PUT | `/api/atlas/admin/purge` | Purge by ids |  |
| `import_file` | POST | `/api/atlas/admin/importfile` | Import file |  |
| `get_cluster` | GET | `/api/atlas/admin/server/{serverName}` | Get cluster |  |
| `get_export_import_audit` | GET | `/api/atlas/admin/expimp/audit` | Get export import audit |  |
| `ageout_audit_data` | POST | `/api/atlas/admin/audits/ageout` | Ageout audit data |  |
| `get_atlas_audits` | POST | `/api/atlas/admin/audits` | Get atlas audits |  |
| `get_audit_details` | GET | `/api/atlas/admin/audit/{auditGuid}/details` | Get audit details |  |
| `get_purge_audit_summary` | GET | `/api/atlas/admin/audit/{auditGuid}/summary` | Get purge audit summary |  |
| `get_purge_audit_batches` | GET | `/api/atlas/admin/audit/{auditGuid}/batches` | Get purge audit batches |  |
| `get_active_searches` | GET | `/api/atlas/admin/activeSearches` | Get active searches |  |
| `terminate_active_search` | DELETE | `/api/atlas/admin/activeSearches/{id}` | Terminate active search |  |
| `check_state` | POST | `/api/atlas/admin/checkstate` | Check state |  |
| `get_atlas_patches` | GET | `/api/atlas/admin/patches` | Get atlas patches |  |
| `get_task_status` | GET | `/api/atlas/admin/tasks` | Get task status |  |
| `delete_task` | DELETE | `/api/atlas/admin/tasks` | Delete task |  |
| `get_debug_metrics` | GET | `/api/atlas/admin/debug/metrics` | Get debug metrics |  |
| `service_liveliness` | GET | `/api/atlas/admin/liveness` | Service liveliness |  |
| `service_readiness` | GET | `/api/atlas/admin/readiness` | Service readiness |  |

## knox

43 tools. **Partial source:** from HTML reference pages; may be incomplete.

- Product: Apache Knox Admin, Metadata, Session and KnoxToken APIs
- Version: Knox master source (gateway-service-admin/-knoxtoken/-metadata/-session); CDP 7.1.9 ships Knox 2.0.0 - token batch ops/servicedefinitions present, metadata API may be absent
- Spec source: https://knox.apache.org/books/knox-2-0-0/user-guide.html + JAX-RS resources in https://github.com/apache/knox (from source/HTML; may be partial). Excludes knoxtoken v2 (/knoxtoken/api/v2: renew=PUT, revoke=DELETE), apikey/clientid token variants
- Auth: Admin API: Knox admin topology (Basic/LDAP or Knox SSO JWT; admin role via ACLs). KnoxToken: whatever the topology's authn provider is (Basic/LDAP, Kerberos/SPNEGO, SSO cookie) -> returns JWT for Authorization: Bearer on token-federated topologies (e.g. cdp-proxy-api)
- Operations: 43

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `get_version` | GET | `/gateway/admin/api/v1/version` | Knox version and hash |  |
| `list_topologies` | GET | `/gateway/admin/api/v1/topologies` | List deployed topologies |  |
| `get_topology` | GET | `/gateway/admin/api/v1/topologies/{id}` | Get a topology |  |
| `put_topology` | PUT | `/gateway/admin/api/v1/topologies/{id}` | Deploy/replace a topology |  |
| `delete_topology` | DELETE | `/gateway/admin/api/v1/topologies/{id}` | Delete a topology |  |
| `list_provider_configs` | GET | `/gateway/admin/api/v1/providerconfig` | List shared provider configurations |  |
| `get_provider_config` | GET | `/gateway/admin/api/v1/providerconfig/{name}` | Get a provider configuration |  |
| `put_provider_config` | PUT | `/gateway/admin/api/v1/providerconfig/{name}` | Upload a provider configuration |  |
| `delete_provider_config` | DELETE | `/gateway/admin/api/v1/providerconfig/{name}` | Delete a provider configuration (?force) |  |
| `list_descriptors` | GET | `/gateway/admin/api/v1/descriptors` | List simple descriptors |  |
| `get_descriptor` | GET | `/gateway/admin/api/v1/descriptors/{name}` | Get a simple descriptor |  |
| `put_descriptor` | PUT | `/gateway/admin/api/v1/descriptors/{name}` | Upload a simple descriptor |  |
| `delete_descriptor` | DELETE | `/gateway/admin/api/v1/descriptors/{name}` | Delete a simple descriptor |  |
| `list_aliases` | GET | `/gateway/admin/api/v1/aliases/{topology}` | List credential aliases for a topology |  |
| `put_alias` | PUT | `/gateway/admin/api/v1/aliases/{topology}/{alias}` | Add/replace an alias (value form param) |  |
| `post_alias` | POST | `/gateway/admin/api/v1/aliases/{topology}/{alias}` | Add/replace an alias (POST variant) |  |
| `delete_alias` | DELETE | `/gateway/admin/api/v1/aliases/{topology}/{alias}` | Delete an alias |  |
| `list_service_definitions` | GET | `/gateway/admin/api/v1/servicedefinitions` | List service definitions |  |
| `get_service_definitions_by_name` | GET | `/gateway/admin/api/v1/servicedefinitions/{name}` | Service definitions for a service |  |
| `get_service_definitions_by_role` | GET | `/gateway/admin/api/v1/servicedefinitions/{name}/{role}` | Service definitions for service+role |  |
| `get_service_definition` | GET | `/gateway/admin/api/v1/servicedefinitions/{name}/{role}/{version}` | One service definition |  |
| `create_service_definition` | POST | `/gateway/admin/api/v1/servicedefinitions` | Add a service definition |  |
| `update_service_definition` | PUT | `/gateway/admin/api/v1/servicedefinitions` | Add or update a service definition |  |
| `delete_service_definition` | DELETE | `/gateway/admin/api/v1/servicedefinitions/{name}/{role}/{version}` | Delete a service definition |  |
| `list_service_discoveries` | GET | `/gateway/admin/api/v1/servicediscoveries` | List service discovery implementations |  |
| `get_metadata_info` | GET | `/gateway/metadata/api/v1/metadata/info` | General proxy information |  |
| `get_public_cert` | GET | `/gateway/metadata/api/v1/metadata/publicCert` | Gateway public cert (pem/jks) |  |
| `list_metadata_topologies` | GET | `/gateway/metadata/api/v1/metadata/topologies` | Topologies with service URLs visible to user |  |
| `get_metadata_topology` | GET | `/gateway/metadata/api/v1/metadata/topologies/{name}` | Service URLs of a topology |  |
| `get_metadata_profile` | GET | `/gateway/metadata/api/v1/metadata/profiles/{profile}` | Token-generation profile |  |
| `get_session_info` | GET | `/gateway/{topology}/session/api/v1/sessioninfo` | Current user session info |  |
| `get_token` | GET | `/gateway/{topology}/knoxtoken/api/v1/token` | Issue a JWT for the authenticated user (lifespan, md_* metadata) |  |
| `post_token` | POST | `/gateway/{topology}/knoxtoken/api/v1/token` | Issue a JWT (POST variant) |  |
| `get_user_tokens` | GET | `/gateway/{topology}/knoxtoken/api/v1/token/getUserTokens` | List a user's tokens (userName, md_* filters) |  |
| `get_tss_status` | GET | `/gateway/{topology}/knoxtoken/api/v1/token/getTssStatus` | Token state service status |  |
| `renew_token` | POST | `/gateway/{topology}/knoxtoken/api/v1/token/renew` | Renew a token (body: token) |  |
| `revoke_token` | POST | `/gateway/{topology}/knoxtoken/api/v1/token/revoke` | Revoke a token (body: token or id) |  |
| `revoke_tokens` | DELETE | `/gateway/{topology}/knoxtoken/api/v1/token/revokeTokens` | Batch revoke tokens |  |
| `enable_token` | PUT | `/gateway/{topology}/knoxtoken/api/v1/token/enable` | Enable a token |  |
| `enable_tokens` | PUT | `/gateway/{topology}/knoxtoken/api/v1/token/enableTokens` | Batch enable tokens |  |
| `disable_token` | PUT | `/gateway/{topology}/knoxtoken/api/v1/token/disable` | Disable a token |  |
| `disable_tokens` | PUT | `/gateway/{topology}/knoxtoken/api/v1/token/disableTokens` | Batch disable tokens |  |
| `get_jwks` | GET | `/gateway/{topology}/knoxtoken/api/v1/jwks.json` | JWKS public keys for token verification |  |

## webhdfs

64 tools.

- Product: HDFS WebHDFS / HttpFS REST API
- Version: Hadoop 3.4.1 docs (CDP 7.1.x = Hadoop 3.1.1 + backports); ops marked [3.3+]/[3.4+] may be absent on CDP NameNodes/HttpFS
- Spec source: https://hadoop.apache.org/docs/r3.4.1/hadoop-project-dist/hadoop-hdfs/WebHDFS.html (from HTML docs; op list extracted by script)
- Auth: Kerberos SPNEGO (secure clusters), delegation token (?delegation=), or ?user.name= pseudo-auth (insecure); via Knox: Basic/JWT at /gateway/<topology>/webhdfs/v1. HttpFS on :14000 uses the same ops
- Note: Built-in hdfs pack already covers: CREATE, DELETE, GETFILESTATUS, LISTSTATUS, MKDIRS, OPEN, RENAME (as list_directory, get_file_status, make_directory, move, delete, download_file, upload_file, copy).
- Operations: 64

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `open` | GET | `/webhdfs/v1/{path}?op=OPEN` | Open and read a file | in built-in pack |
| `get_file_status` | GET | `/webhdfs/v1/{path}?op=GETFILESTATUS` | Status of a file/directory | in built-in pack |
| `list_status` | GET | `/webhdfs/v1/{path}?op=LISTSTATUS` | List a directory | in built-in pack |
| `list_status_batch` | GET | `/webhdfs/v1/{path}?op=LISTSTATUS_BATCH` | Iteratively list a directory |  |
| `get_content_summary` | GET | `/webhdfs/v1/{path}?op=GETCONTENTSUMMARY` | Get content summary of a directory |  |
| `get_quota_usage` | GET | `/webhdfs/v1/{path}?op=GETQUOTAUSAGE` | Get quota usage of a directory [3.3+] |  |
| `get_file_checksum` | GET | `/webhdfs/v1/{path}?op=GETFILECHECKSUM` | Get file checksum |  |
| `get_home_directory` | GET | `/webhdfs/v1/{path}?op=GETHOMEDIRECTORY` | Get home directory |  |
| `get_delegation_token` | GET | `/webhdfs/v1/{path}?op=GETDELEGATIONTOKEN` | Get delegation token |  |
| `get_trash_root` | GET | `/webhdfs/v1/{path}?op=GETTRASHROOT` | Get trash root |  |
| `get_xattrs` | GET | `/webhdfs/v1/{path}?op=GETXATTRS` | Get one, several or all XAttrs |  |
| `list_xattrs` | GET | `/webhdfs/v1/{path}?op=LISTXATTRS` | List all XAttr names |  |
| `get_acl_status` | GET | `/webhdfs/v1/{path}?op=GETACLSTATUS` | Get ACL status |  |
| `check_access` | GET | `/webhdfs/v1/{path}?op=CHECKACCESS` | Check access for an fsaction |  |
| `get_all_storage_policy` | GET | `/webhdfs/v1/{path}?op=GETALLSTORAGEPOLICY` | Get all storage policies |  |
| `get_storage_policy` | GET | `/webhdfs/v1/{path}?op=GETSTORAGEPOLICY` | Get storage policy of a path |  |
| `get_snapshot_diff` | GET | `/webhdfs/v1/{path}?op=GETSNAPSHOTDIFF` | Get snapshot diff |  |
| `get_snapshot_diff_listing` | GET | `/webhdfs/v1/{path}?op=GETSNAPSHOTDIFFLISTING` | Get snapshot diff iteratively [3.3+] |  |
| `get_snapshottable_directory_list` | GET | `/webhdfs/v1/{path}?op=GETSNAPSHOTTABLEDIRECTORYLIST` | Get snapshottable directory list |  |
| `get_snapshot_list` | GET | `/webhdfs/v1/{path}?op=GETSNAPSHOTLIST` | Get snapshot list of a directory [3.3+] |  |
| `get_file_block_locations` | GET | `/webhdfs/v1/{path}?op=GETFILEBLOCKLOCATIONS` | Get file block locations [3.3+] |  |
| `get_ec_policy` | GET | `/webhdfs/v1/{path}?op=GETECPOLICY` | Get erasure-coding policy of a path [3.3+] |  |
| `get_server_defaults` | GET | `/webhdfs/v1/{path}?op=GETSERVERDEFAULTS` | Get server defaults [3.3+] |  |
| `get_link_target` | GET | `/webhdfs/v1/{path}?op=GETLINKTARGET` | Get symlink target [3.3+] |  |
| `get_file_link_status` | GET | `/webhdfs/v1/{path}?op=GETFILELINKSTATUS` | Get file status without resolving symlink [3.3+] |  |
| `get_status` | GET | `/webhdfs/v1/{path}?op=GETSTATUS` | Get filesystem status (capacity/used/remaining) [3.3+] |  |
| `get_ec_policies` | GET | `/webhdfs/v1/{path}?op=GETECPOLICIES` | Get all erasure-coding policies [3.3+] |  |
| `get_all_ec_codecs` | GET | `/webhdfs/v1/{path}?op=GETALLECCODECS` | Get all erasure-coding codecs [3.3+] |  |
| `get_trash_roots` | GET | `/webhdfs/v1/{path}?op=GETTRASHROOTS` | Get all trash roots [3.3+] |  |
| `create` | PUT | `/webhdfs/v1/{path}?op=CREATE` | Create and write to a file | in built-in pack |
| `mkdirs` | PUT | `/webhdfs/v1/{path}?op=MKDIRS` | Make a directory | in built-in pack |
| `create_symlink` | PUT | `/webhdfs/v1/{path}?op=CREATESYMLINK` | Create a symbolic link |  |
| `rename` | PUT | `/webhdfs/v1/{path}?op=RENAME` | Rename a file/directory | in built-in pack |
| `set_replication` | PUT | `/webhdfs/v1/{path}?op=SETREPLICATION` | Set replication factor |  |
| `set_owner` | PUT | `/webhdfs/v1/{path}?op=SETOWNER` | Set owner/group |  |
| `set_permission` | PUT | `/webhdfs/v1/{path}?op=SETPERMISSION` | Set permission |  |
| `set_times` | PUT | `/webhdfs/v1/{path}?op=SETTIMES` | Set access or modification time |  |
| `set_quota` | PUT | `/webhdfs/v1/{path}?op=SETQUOTA` | Set namespace/storage-space quota [3.4+] |  |
| `set_quota_by_storage_type` | PUT | `/webhdfs/v1/{path}?op=SETQUOTABYSTORAGETYPE` | Set quota by storage type [3.4+] |  |
| `modify_acl_entries` | PUT | `/webhdfs/v1/{path}?op=MODIFYACLENTRIES` | Modify ACL entries |  |
| `remove_acl_entries` | PUT | `/webhdfs/v1/{path}?op=REMOVEACLENTRIES` | Remove ACL entries |  |
| `remove_default_acl` | PUT | `/webhdfs/v1/{path}?op=REMOVEDEFAULTACL` | Remove default ACL |  |
| `remove_acl` | PUT | `/webhdfs/v1/{path}?op=REMOVEACL` | Remove ACL |  |
| `set_acl` | PUT | `/webhdfs/v1/{path}?op=SETACL` | Set ACL |  |
| `renew_delegation_token` | PUT | `/webhdfs/v1/{path}?op=RENEWDELEGATIONTOKEN` | Renew delegation token |  |
| `cancel_delegation_token` | PUT | `/webhdfs/v1/{path}?op=CANCELDELEGATIONTOKEN` | Cancel delegation token |  |
| `allow_snapshot` | PUT | `/webhdfs/v1/{path}?op=ALLOWSNAPSHOT` | Allow snapshots on a directory [3.3+] |  |
| `disallow_snapshot` | PUT | `/webhdfs/v1/{path}?op=DISALLOWSNAPSHOT` | Disallow snapshots on a directory [3.3+] |  |
| `create_snapshot` | PUT | `/webhdfs/v1/{path}?op=CREATESNAPSHOT` | Create snapshot |  |
| `rename_snapshot` | PUT | `/webhdfs/v1/{path}?op=RENAMESNAPSHOT` | Rename snapshot |  |
| `set_xattr` | PUT | `/webhdfs/v1/{path}?op=SETXATTR` | Set XAttr |  |
| `remove_xattr` | PUT | `/webhdfs/v1/{path}?op=REMOVEXATTR` | Remove XAttr |  |
| `set_storage_policy` | PUT | `/webhdfs/v1/{path}?op=SETSTORAGEPOLICY` | Set storage policy |  |
| `satisfy_storage_policy` | PUT | `/webhdfs/v1/{path}?op=SATISFYSTORAGEPOLICY` | Satisfy storage policy (SPS) [3.3+] |  |
| `enable_ec_policy` | PUT | `/webhdfs/v1/{path}?op=ENABLEECPOLICY` | Enable erasure-coding policy [3.3+] |  |
| `disable_ec_policy` | PUT | `/webhdfs/v1/{path}?op=DISABLEECPOLICY` | Disable erasure-coding policy [3.3+] |  |
| `set_ec_policy` | PUT | `/webhdfs/v1/{path}?op=SETECPOLICY` | Set erasure-coding policy on a path [3.3+] |  |
| `append` | POST | `/webhdfs/v1/{path}?op=APPEND` | Append to a file |  |
| `concat` | POST | `/webhdfs/v1/{path}?op=CONCAT` | Concat files |  |
| `truncate` | POST | `/webhdfs/v1/{path}?op=TRUNCATE` | Truncate a file |  |
| `unset_storage_policy` | POST | `/webhdfs/v1/{path}?op=UNSETSTORAGEPOLICY` | Unset storage policy |  |
| `unset_ec_policy` | POST | `/webhdfs/v1/{path}?op=UNSETECPOLICY` | Unset erasure-coding policy [3.3+] |  |
| `delete` | DELETE | `/webhdfs/v1/{path}?op=DELETE` | Delete a file/directory | in built-in pack |
| `delete_snapshot` | DELETE | `/webhdfs/v1/{path}?op=DELETESNAPSHOT` | Delete snapshot |  |

## ozone_s3

26 tools. **Partial source:** from HTML reference pages; may be incomplete.

- Product: Apache Ozone S3 Gateway (S3-compatible)
- Version: Ozone master docs S3.md (CDP 7.1.9 ships Ozone 1.3/1.4-based)
- Spec source: https://github.com/apache/ozone/blob/master/hadoop-hdds/docs/content/interface/S3.md (from HTML/Markdown docs; may be partial)
- Auth: AWS SigV4 with Ozone S3 secret (ozone s3 getsecret, Kerberos needed when secure); base https://<s3g-host>:9879 (9878 http)
- Note: Built-in s3 pack already covers ListBuckets, ListObjectsV2, HeadObject, GetObject, PutObject, DeleteObject, CopyObject (+UploadPartCopy multipart).
- Operations: 26

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `list_buckets` | GET | `/` | ListBuckets: list all buckets of the user (s3v volume) | in built-in pack |
| `create_bucket` | PUT | `/{bucket}` | CreateBucket |  |
| `head_bucket` | HEAD | `/{bucket}` | HeadBucket: check bucket exists |  |
| `delete_bucket` | DELETE | `/{bucket}` | DeleteBucket (must be empty) |  |
| `list_objects_v2` | GET | `/{bucket}?list-type=2` | ListObjectsV2 with prefix/delimiter/continuation | in built-in pack |
| `list_objects` | GET | `/{bucket}` | ListObjects (v1) - implemented by Ozone, not in docs table |  |
| `get_bucket_acl` | GET | `/{bucket}?acl` | GetBucketAcl - partial (Ozone ACL model), not in docs table |  |
| `put_bucket_acl` | PUT | `/{bucket}?acl` | PutBucketAcl - partial (Ozone ACL model), not in docs table |  |
| `get_object` | GET | `/{bucket}/{key}` | GetObject (supports Range) | in built-in pack |
| `head_object` | HEAD | `/{bucket}/{key}` | HeadObject: object metadata | in built-in pack |
| `put_object` | PUT | `/{bucket}/{key}` | PutObject | in built-in pack |
| `copy_object` | PUT | `/{bucket}/{key} (x-amz-copy-source)` | CopyObject (COPY/REPLACE metadata directive) | in built-in pack |
| `delete_object` | DELETE | `/{bucket}/{key}` | DeleteObject | in built-in pack |
| `delete_objects` | POST | `/{bucket}?delete` | DeleteObjects (bulk delete) |  |
| `put_object_tagging` | PUT | `/{bucket}/{key}?tagging` | PutObjectTagging |  |
| `get_object_tagging` | GET | `/{bucket}/{key}?tagging` | GetObjectTagging |  |
| `delete_object_tagging` | DELETE | `/{bucket}/{key}?tagging` | DeleteObjectTagging |  |
| `create_multipart_upload` | POST | `/{bucket}/{key}?uploads` | CreateMultipartUpload |  |
| `upload_part` | PUT | `/{bucket}/{key}?partNumber&uploadId` | UploadPart |  |
| `upload_part_copy` | PUT | `/{bucket}/{key}?partNumber&uploadId (x-amz-copy-source)` | UploadPartCopy - implemented, not in docs table |  |
| `list_multipart_uploads` | GET | `/{bucket}?uploads` | ListMultipartUploads |  |
| `list_parts` | GET | `/{bucket}/{key}?uploadId` | ListParts |  |
| `complete_multipart_upload` | POST | `/{bucket}/{key}?uploadId` | CompleteMultipartUpload |  |
| `abort_multipart_upload` | DELETE | `/{bucket}/{key}?uploadId` | AbortMultipartUpload |  |
| `health_live` | GET | `/health/live (admin port 19878)` | S3G liveness (newer Ozone only) |  |
| `health_ready` | GET | `/health/ready (admin port 19878)` | S3G readiness (newer Ozone only) |  |

## ozone_recon

50 tools.

- Product: Apache Ozone Recon REST API
- Version: recon-api.yaml in Ozone master (OpenAPI 3); CDP Ozone 1.3/1.4 Recon has a subset
- Spec source: https://github.com/apache/ozone/blob/master/hadoop-hdds/docs/themes/ozonedoc/static/swagger-resources/recon-api.yaml
- Auth: Kerberos SPNEGO when secure (ozone.recon.http.auth.type=kerberos), otherwise simple; admin-only endpoints need Ozone admin. Base http(s)://<recon-host>:9888/api/v1
- Operations: 50

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `get_container_info` | GET | `/api/v1/containers` | Get all Container Metadata information |  |
| `get_scm_deleted_containers` | GET | `/api/v1/containers/deleted` | Return all DELETED containers in SCM |  |
| `get_missing_containers` | GET | `/api/v1/containers/missing` | Get the MissingContainerMetadata for all missing containers | deprecated |
| `get_quasi_closed_containers` | GET | `/api/v1/containers/quasiClosed` | List containers in QUASI_CLOSED state, paginated by container ID. |  |
| `get_replica_history_for_container` | GET | `/api/v1/containers/{id}/replicaHistory` | Get all the Replica history for a given container id |  |
| `get_unhealthy_containers` | GET | `/api/v1/containers/unhealthy` | Get UnhealthyContainerMetadata for all the unhealthy containers |  |
| `get_unhealthy_containers_with_state` | GET | `/api/v1/containers/unhealthy/{state}` | Returns UnhealthyContainerMetadata for all the unhealthy containers with the specified state |  |
| `list_unhealthy_export_jobs` | GET | `/api/v1/containers/unhealthy/export` | List all unhealthy-container export jobs (any status). |  |
| `start_unhealthy_export` | POST | `/api/v1/containers/unhealthy/export` | Start an async CSV export job for unhealthy containers in the given state. |  |
| `get_unhealthy_export_status` | GET | `/api/v1/containers/unhealthy/export/{jobId}` | Get the current status of an export job. |  |
| `cancel_unhealthy_export` | DELETE | `/api/v1/containers/unhealthy/export/{jobId}` | Cancel a queued or running export job. |  |
| `download_unhealthy_export` | GET | `/api/v1/containers/unhealthy/export/{jobId}/download` | Download the TAR archive for a completed export job. |  |
| `get_container_mis_match_insights` | GET | `/api/v1/containers/mismatch` | Returns the list of mis-matched containers between OM and SCM |  |
| `get_om_containers_deleted_in_scm` | GET | `/api/v1/containers/mismatch/deleted` | Returns the list of DELETED containers in SCM that are present in OM |  |
| `get_volumes` | GET | `/api/v1/volumes` | Returns the set of all volumes present |  |
| `get_buckets` | GET | `/api/v1/buckets` | Returns the set of all buckets across all volumes |  |
| `get_open_key_info` | GET | `/api/v1/keys/open` | Returns the set of keys/files which are open |  |
| `get_open_key_summary` | GET | `/api/v1/keys/open/summary` | Returns the summary of all open keys info |  |
| `get_open_mpu_key_summary` | GET | `/api/v1/keys/open/mpu/summary` | Returns the summary of all open multipart-upload keys |  |
| `get_deleted_key_info` | GET | `/api/v1/keys/deletePending` | Returns the set of keys/files which are pending for deletion |  |
| `get_deleted_dir_info` | GET | `/api/v1/keys/deletePending/dirs` | Returns the set of keys/files which are pending for deletion |  |
| `get_deleted_key_summary` | GET | `/api/v1/keys/deletePending/summary` | Returns the summary of all keys pending deletion info |  |
| `get_deleted_directory_summary` | GET | `/api/v1/keys/deletePending/dirs/summary` | Retrieves the summary of deleted directories. |  |
| `list_keys` | GET | `/api/v1/keys/listKeys` | List committed keys under a prefix with optional filters. |  |
| `get_keys_for_container` | GET | `/api/v1/containers/{id}/keys` | Get the Key metadata for all keys present in the given container ID |  |
| `get_blocks_pending_deletion` | GET | `/api/v1/blocks/deletePending` | Fetch the list of blocks pending for deletion |  |
| `get_basic_info` | GET | `/api/v1/namespace/summary` | Returns a basic summary of the path, including entity type and aggregate count of objects under the path. |  |
| `get_disk_usage` | GET | `/api/v1/namespace/usage` | Returns namespace usage of all sub-paths under the path. |  |
| `get_quota_usage` | GET | `/api/v1/namespace/quota` | Returns the quota allowed and used under the path. Only volumes and buckets have quota. Other types are not applicable to the quota request. |  |
| `get_file_size_distribution` | GET | `/api/v1/namespace/dist` | Returns the file size distribution of all keys under the path. |  |
| `get_cluster_state` | GET | `/api/v1/clusterState` | Returns the summary of the current state of the Ozone cluster. |  |
| `get_datanodes` | GET | `/api/v1/datanodes` | Returns all the datanodes in the cluster. |  |
| `get_decommissioning_datanodes` | GET | `/api/v1/datanodes/decommission/info` | Returns all the datanodes in the decommissioning state |  |
| `get_decommission_info_for_datanode` | GET | `/api/v1/datanodes/decommission/info/datanode` | Returns info of a specific datanode for which decommissioning is initiated |  |
| `remove_datanodes` | PUT | `/api/v1/datanodes/remove` | Removes datanodes from Recon's memory and nodes table in Recon DB. |  |
| `get_pipelines` | GET | `/api/v1/pipelines` | Returns all the pipelines in the cluster. |  |
| `get_task_times` | GET | `/api/v1/task/status` | Returns the status of all the Recon tasks. |  |
| `get_file_counts` | GET | `/api/v1/utilization/fileCount` | Returns file counts by size bin, with fileSize representing the bin upper bound. |  |
| `get_container_counts` | GET | `/api/v1/utilization/containerCount` | Returns the container counts within the given container size. |  |
| `get_metrics_response` | GET | `/api/v1/metrics/{api}` | This is a proxy endpoint for Prometheus, and helps to fetch different metrics for Ozone |  |
| `get_read_access_heat_map` | GET | `/api/v1/heatmap/readaccess` | Returns the top-N prefixes by read access as a tree of `EntityReadAccessHeatMap` nodes |  |
| `get_heat_map_health_check` | GET | `/api/v1/heatmap/healthCheck` | Health check for the configured HeatMap provider |  |
| `get_disabled_features` | GET | `/api/v1/features/disabledFeatures` | Lists Recon features that are currently disabled |  |
| `trigger_omdb_sync` | GET | `/api/v1/triggerdbsync/om` | Triggers an immediate OM DB sync from Recon |  |
| `trigger_scmdb_snapshot_sync` | POST | `/api/v1/triggerdbsync/scm/snapshot` | Trigger an SCM DB snapshot sync from SCM to Recon. |  |
| `get_scmdb_snapshot_sync_status` | GET | `/api/v1/triggerdbsync/scm/snapshot/status` | Get the current status of an SCM DB snapshot sync. |  |
| `cancel_scmdb_snapshot_sync` | POST | `/api/v1/triggerdbsync/scm/snapshot/cancel` | Cancel an in-progress SCM DB snapshot sync. |  |
| `get_storage_distribution` | GET | `/api/v1/storageDistribution` | Retrieves storage capacity distribution across datanodes including global storage, namespace, and used space breakdown |  |
| `get_pending_deletion_by_component` | GET | `/api/v1/pendingDeletion` | Returns pending deletion information for the specified component (scm, om, or dn) |  |
| `download_data_node_storage_distribution` | GET | `/api/v1/storageDistribution/download` | Downloads per-datanode storage and pending deletion statistics as a CSV file |  |

## yarn_rm

48 tools.

- Product: YARN ResourceManager REST API (/ws/v1/cluster)
- Version: Hadoop branch-3.1 RMWebServices.java (CDP 7.1.x baseline) cross-checked with 3.1.1/3.4.1 ResourceManagerRest docs
- Spec source: https://github.com/apache/hadoop/blob/branch-3.1/.../resourcemanager/webapp/RMWebServices.java + https://hadoop.apache.org/docs/r3.1.1/hadoop-yarn/hadoop-yarn-site/ResourceManagerRest.html (from source)
- Auth: Kerberos SPNEGO (secure) or ?user.name= (simple); writes (kill/move/submit) need SPNEGO + ACLs; via Knox: /gateway/<topology>/resourcemanager/v1/cluster with Basic/JWT
- Operations: 48

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `get_cluster_info` | GET | `/ws/v1/cluster/info` | Cluster information |  |
| `get_cluster_user_info` | GET | `/ws/v1/cluster/userinfo` | Current user info |  |
| `get_cluster_metrics_info` | GET | `/ws/v1/cluster/metrics` | Cluster metrics |  |
| `get_scheduler_info` | GET | `/ws/v1/cluster/scheduler` | Scheduler info and queue tree |  |
| `dump_scheduler_logs` | POST | `/ws/v1/cluster/scheduler/logs` | Dump scheduler debug logs |  |
| `get_nodes` | GET | `/ws/v1/cluster/nodes` | List nodes |  |
| `get_node` | GET | `/ws/v1/cluster/nodes/{nodeId}` | Get a node |  |
| `get_apps` | GET | `/ws/v1/cluster/apps` | List applications (state, user, queue, tags, limit...) |  |
| `get_activities` | GET | `/ws/v1/cluster/scheduler/activities` | Scheduler activities |  |
| `get_app_activities` | GET | `/ws/v1/cluster/scheduler/app-activities` | Application activities |  |
| `get_app_statistics` | GET | `/ws/v1/cluster/appstatistics` | Application statistics by state/type |  |
| `get_app` | GET | `/ws/v1/cluster/apps/{appid}` | Get an application |  |
| `get_app_attempts` | GET | `/ws/v1/cluster/apps/{appid}/appattempts` | Application attempts |  |
| `get_containers` | GET | `/ws/v1/cluster/apps/{appid}/appattempts/{appattemptid}/containers` | Containers of an app attempt |  |
| `get_container` | GET | `/ws/v1/cluster/apps/{appid}/appattempts/{appattemptid}/containers/{containerid}` | One container of an app attempt |  |
| `get_app_state` | GET | `/ws/v1/cluster/apps/{appid}/state` | Get app state |  |
| `update_app_state` | PUT | `/ws/v1/cluster/apps/{appid}/state` | Kill an application (PUT state=KILLED) |  |
| `get_node_to_labels` | GET | `/ws/v1/cluster/get-node-to-labels` | Node-to-labels mapping |  |
| `get_labels_to_nodes` | GET | `/ws/v1/cluster/label-mappings` | Labels-to-nodes mapping |  |
| `replace_labels_on_nodes` | POST | `/ws/v1/cluster/replace-node-to-labels` | Replace labels on nodes |  |
| `replace_labels_on_node` | POST | `/ws/v1/cluster/nodes/{nodeId}/replace-labels` | Replace labels on one node |  |
| `get_cluster_node_labels` | GET | `/ws/v1/cluster/get-node-labels` | Cluster node labels |  |
| `add_to_cluster_node_labels` | POST | `/ws/v1/cluster/add-node-labels` | Add cluster node labels |  |
| `remove_from_cluser_node_labels` | POST | `/ws/v1/cluster/remove-node-labels` | Remove cluster node labels |  |
| `get_labels_on_node` | GET | `/ws/v1/cluster/nodes/{nodeId}/get-labels` | Labels on a node |  |
| `get_app_priority` | GET | `/ws/v1/cluster/apps/{appid}/priority` | Get app priority |  |
| `update_application_priority` | PUT | `/ws/v1/cluster/apps/{appid}/priority` | Update app priority |  |
| `get_app_queue` | GET | `/ws/v1/cluster/apps/{appid}/queue` | Get app queue |  |
| `update_app_queue` | PUT | `/ws/v1/cluster/apps/{appid}/queue` | Move app to another queue |  |
| `create_new_application` | POST | `/ws/v1/cluster/apps/new-application` | Obtain a new application id |  |
| `submit_application` | POST | `/ws/v1/cluster/apps` | Submit an application |  |
| `post_delegation_token` | POST | `/ws/v1/cluster/delegation-token` | Create RM delegation token |  |
| `post_delegation_token_expiration` | POST | `/ws/v1/cluster/delegation-token/expiration` | Renew RM delegation token |  |
| `cancel_delegation_token` | DELETE | `/ws/v1/cluster/delegation-token` | Cancel RM delegation token |  |
| `create_new_reservation` | POST | `/ws/v1/cluster/reservation/new-reservation` | New reservation id |  |
| `submit_reservation` | POST | `/ws/v1/cluster/reservation/submit` | Submit reservation |  |
| `update_reservation` | POST | `/ws/v1/cluster/reservation/update` | Update reservation |  |
| `delete_reservation` | POST | `/ws/v1/cluster/reservation/delete` | Delete reservation |  |
| `list_reservation` | GET | `/ws/v1/cluster/reservation/list` | List reservations |  |
| `get_app_timeout` | GET | `/ws/v1/cluster/apps/{appid}/timeouts/{type}` | Get app timeout of a type |  |
| `get_app_timeouts` | GET | `/ws/v1/cluster/apps/{appid}/timeouts` | Get app timeouts |  |
| `update_application_timeout` | PUT | `/ws/v1/cluster/apps/{appid}/timeout` | Update app timeout |  |
| `validate_and_get_scheduler_configuration` | POST | `/ws/v1/cluster/scheduler-conf/validate` | Validate a scheduler config mutation |  |
| `update_scheduler_configuration` | PUT | `/ws/v1/cluster/scheduler-conf` | Mutate scheduler (queue) configuration |  |
| `format_scheduler_configuration` | GET | `/ws/v1/cluster/scheduler-conf/format` | Format (reset) scheduler config store |  |
| `get_scheduler_configuration` | GET | `/ws/v1/cluster/scheduler-conf` | Get scheduler configuration |  |
| `get_scheduler_configuration_version` | GET | `/ws/v1/cluster/scheduler-conf/version` | Scheduler config version |  |
| `check_user_access_to_queue` | GET | `/ws/v1/cluster/queues/{queue}/access` | Check user access to a queue |  |

## yarn_nm

9 tools.

- Product: YARN NodeManager REST API (/ws/v1/node)
- Version: Hadoop branch-3.1 NMWebServices.java
- Spec source: https://github.com/apache/hadoop/blob/branch-3.1/.../nodemanager/webapp/NMWebServices.java (from source)
- Auth: Kerberos SPNEGO or simple; per-NodeManager host :8042/:8044
- Operations: 9

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `get_node_info` | GET | `/ws/v1/node/info` | Get node info |  |
| `get_node_apps` | GET | `/ws/v1/node/apps` | Get node apps |  |
| `get_node_app` | GET | `/ws/v1/node/apps/{appid}` | Get node app |  |
| `get_node_containers` | GET | `/ws/v1/node/containers` | Get node containers |  |
| `get_node_container` | GET | `/ws/v1/node/containers/{containerid}` | Get node container |  |
| `get_container_logs_info` | GET | `/ws/v1/node/containers/{containerid}/logs` | Get container logs info |  |
| `get_container_log_file` | GET | `/ws/v1/node/containers/{containerid}/logs/{filename}` | Get container log file |  |
| `get_logs` | GET | `/ws/v1/node/containerlogs/{containerid}/{filename}` | Get logs |  |
| `get_nm_resource_info` | GET | `/ws/v1/node/resources/{resourcename}` | Get nm resource info |  |

## yarn_history

51 tools.

- Product: MapReduce JobHistory Server, YARN Application History (AHS) and Timeline Service v1/v2 readers
- Version: Hadoop branch-3.1 HsWebServices/AHSWebServices/TimelineWebServices/TimelineReaderWebServices (cluster-scoped /clusters/{clusterid}/... variants of TSv2 omitted; they mirror the default-cluster paths)
- Spec source: https://github.com/apache/hadoop/tree/branch-3.1 (from source) + HistoryServerRest.html / TimelineServer.html / TimelineServiceV2.html
- Auth: Kerberos SPNEGO or simple. JHS :19888/:19890, AHS/ATS v1.5 :8188/:8190, TSv2 reader :8198. Via Knox: jobhistory / yarnuiv2 services
- Operations: 51

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `jhs_get_history_info` | GET | `/ws/v1/history/info` | JHS: Get history info |  |
| `jhs_get_jobs` | GET | `/ws/v1/history/mapreduce/jobs` | JHS: Get jobs |  |
| `jhs_get_job` | GET | `/ws/v1/history/mapreduce/jobs/{jobid}` | JHS: Get job |  |
| `jhs_get_job_attempts` | GET | `/ws/v1/history/mapreduce/jobs/{jobid}/jobattempts` | JHS: Get job attempts |  |
| `jhs_get_job_counters` | GET | `/ws/v1/history/mapreduce/jobs/{jobid}/counters` | JHS: Get job counters |  |
| `jhs_get_job_conf` | GET | `/ws/v1/history/mapreduce/jobs/{jobid}/conf` | JHS: Get job conf |  |
| `jhs_get_job_tasks` | GET | `/ws/v1/history/mapreduce/jobs/{jobid}/tasks` | JHS: Get job tasks |  |
| `jhs_get_job_task` | GET | `/ws/v1/history/mapreduce/jobs/{jobid}/tasks/{taskid}` | JHS: Get job task |  |
| `jhs_get_single_task_counters` | GET | `/ws/v1/history/mapreduce/jobs/{jobid}/tasks/{taskid}/counters` | JHS: Get single task counters |  |
| `jhs_get_job_task_attempts` | GET | `/ws/v1/history/mapreduce/jobs/{jobid}/tasks/{taskid}/attempts` | JHS: Get job task attempts |  |
| `jhs_get_job_task_attempt_id` | GET | `/ws/v1/history/mapreduce/jobs/{jobid}/tasks/{taskid}/attempts/{attemptid}` | JHS: Get job task attempt id |  |
| `jhs_get_job_task_attempt_id_counters` | GET | `/ws/v1/history/mapreduce/jobs/{jobid}/tasks/{taskid}/attempts/{attemptid}/counters` | JHS: Get job task attempt id counters |  |
| `ahs_about` | GET | `/ws/v1/applicationhistory/about` | AHS: About |  |
| `ahs_get_apps` | GET | `/ws/v1/applicationhistory/apps` | AHS: Get apps |  |
| `ahs_get_app` | GET | `/ws/v1/applicationhistory/apps/{appid}` | AHS: Get app |  |
| `ahs_get_app_attempts` | GET | `/ws/v1/applicationhistory/apps/{appid}/appattempts` | AHS: Get app attempts |  |
| `ahs_get_app_attempt` | GET | `/ws/v1/applicationhistory/apps/{appid}/appattempts/{appattemptid}` | AHS: Get app attempt |  |
| `ahs_get_containers` | GET | `/ws/v1/applicationhistory/apps/{appid}/appattempts/{appattemptid}/containers` | AHS: Get containers |  |
| `ahs_get_container` | GET | `/ws/v1/applicationhistory/apps/{appid}/appattempts/{appattemptid}/containers/{containerid}` | AHS: Get container |  |
| `ahs_get_container_logs_info` | GET | `/ws/v1/applicationhistory/containers/{containerid}/logs` | AHS: Get container logs info |  |
| `ahs_get_container_log_file` | GET | `/ws/v1/applicationhistory/containers/{containerid}/logs/{filename}` | AHS: Get container log file |  |
| `ahs_get_logs` | GET | `/ws/v1/applicationhistory/containerlogs/{containerid}/{filename}` | AHS: Get logs |  |
| `timeline_about` | GET | `/ws/v1/timeline` | Timeline server (v1/v1.5) about |  |
| `timeline_get_entities` | GET | `/ws/v1/timeline/{entityType}` | Query timeline entities of a type |  |
| `timeline_get_entity` | GET | `/ws/v1/timeline/{entityType}/{entityId}` | Get one timeline entity |  |
| `timeline_get_events` | GET | `/ws/v1/timeline/{entityType}/events` | Get events for entities |  |
| `timeline_post_entities` | POST | `/ws/v1/timeline` | Post timeline entities |  |
| `timeline_put_domain` | PUT | `/ws/v1/timeline/domain` | Create/update a timeline domain |  |
| `timeline_get_domain` | GET | `/ws/v1/timeline/domain/{domainId}` | Get a timeline domain |  |
| `timeline_get_domains` | GET | `/ws/v1/timeline/domain` | List timeline domains of an owner |  |
| `tsv2_about` | GET | `/ws/v2/timeline` | Timeline reader v2 about |  |
| `tsv2_health` | GET | `/ws/v2/timeline/health` | Timeline reader health |  |
| `tsv2_get_flows` | GET | `/ws/v2/timeline/flows/` | List active flows |  |
| `tsv2_get_flow_runs` | GET | `/ws/v2/timeline/users/{userid}/flows/{flowname}/runs/` | List runs of a flow |  |
| `tsv2_get_flow_run` | GET | `/ws/v2/timeline/users/{userid}/flows/{flowname}/runs/{flowrunid}/` | Get one flow run |  |
| `tsv2_get_flow_apps` | GET | `/ws/v2/timeline/users/{userid}/flows/{flowname}/apps/` | Apps of a flow |  |
| `tsv2_get_flow_run_apps` | GET | `/ws/v2/timeline/users/{userid}/flows/{flowname}/runs/{flowrunid}/apps/` | Apps of a flow run |  |
| `tsv2_get_app` | GET | `/ws/v2/timeline/apps/{appid}/` | Get app entity |  |
| `tsv2_get_app_attempts` | GET | `/ws/v2/timeline/apps/{appid}/appattempts` | App attempts of an app |  |
| `tsv2_get_app_attempt` | GET | `/ws/v2/timeline/apps/{appid}/appattempts/{appattemptid}` | One app attempt |  |
| `tsv2_get_containers` | GET | `/ws/v2/timeline/apps/{appid}/appattempts/{appattemptid}/containers` | Containers of an attempt |  |
| `tsv2_get_container` | GET | `/ws/v2/timeline/apps/{appid}/containers/{containerid}` | One container |  |
| `tsv2_get_entity_types` | GET | `/ws/v2/timeline/apps/{appid}/entity-types` | Entity types of an app |  |
| `tsv2_get_entities` | GET | `/ws/v2/timeline/apps/{appid}/entities/{entitytype}` | Generic entities within an app |  |
| `tsv2_get_entity` | GET | `/ws/v2/timeline/apps/{appid}/entities/{entitytype}/{entityid}/` | One generic entity within an app |  |
| `tsv2_get_sub_app_entities` | GET | `/ws/v2/timeline/users/{userid}/entities/{entitytype}` | Sub-application entities of a user |  |
| `tsv2_get_sub_app_entity` | GET | `/ws/v2/timeline/users/{userid}/entities/{entitytype}/{entityid}` | One sub-application entity |  |
| `tsv2_get_entity_by_uid` | GET | `/ws/v2/timeline/entity-uid/{uid}/` | Entity by UID |  |
| `tsv2_get_app_by_uid` | GET | `/ws/v2/timeline/app-uid/{uid}/` | App by UID |  |
| `tsv2_get_flow_run_by_uid` | GET | `/ws/v2/timeline/run-uid/{uid}/` | Flow run by UID |  |
| `tsv2_get_flow_runs_by_uid` | GET | `/ws/v2/timeline/flow-uid/{uid}/runs/` | Flow runs by flow UID |  |

## livy

17 tools.

- Product: Apache Livy REST API
- Version: Livy 0.7/0.8 docs (CDP ships Livy for Spark 2/3)
- Spec source: https://livy.apache.org/docs/latest/rest-api.html (from HTML docs)
- Auth: Kerberos SPNEGO (secure clusters; proxyUser/doAs), Knox Basic/JWT at /gateway/<topology>/livy/v1; port 28998 (Spark3) / 8998
- Operations: 17

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `list_sessions` | GET | `/sessions` | List interactive sessions |  |
| `create_session` | POST | `/sessions` | Create an interactive session (kind, proxyUser, conf...) |  |
| `get_session` | GET | `/sessions/{sessionId}` | Get session info |  |
| `get_session_state` | GET | `/sessions/{sessionId}/state` | Get session state |  |
| `delete_session` | DELETE | `/sessions/{sessionId}` | Kill/delete a session |  |
| `get_session_log` | GET | `/sessions/{sessionId}/log` | Get session log lines |  |
| `list_statements` | GET | `/sessions/{sessionId}/statements` | List statements in a session |  |
| `run_statement` | POST | `/sessions/{sessionId}/statements` | Run a code statement in a session |  |
| `get_statement` | GET | `/sessions/{sessionId}/statements/{statementId}` | Get statement status/output |  |
| `cancel_statement` | POST | `/sessions/{sessionId}/statements/{statementId}/cancel` | Cancel a statement |  |
| `code_completion` | POST | `/sessions/{sessionId}/completion` | Code completion candidates |  |
| `list_batches` | GET | `/batches` | List batch sessions |  |
| `create_batch` | POST | `/batches` | Submit a batch job (file, className, args, conf...) |  |
| `get_batch` | GET | `/batches/{batchId}` | Get batch info |  |
| `get_batch_state` | GET | `/batches/{batchId}/state` | Get batch state |  |
| `delete_batch` | DELETE | `/batches/{batchId}` | Kill/delete a batch |  |
| `get_batch_log` | GET | `/batches/{batchId}/log` | Get batch log lines |  |

## oozie

45 tools. **Partial source:** from HTML reference pages; may be incomplete.

- Product: Apache Oozie Web Services API v1/v2
- Version: Oozie 5.2.1 docs (CDP 7.1.x ships Oozie 5.1)
- Spec source: https://oozie.apache.org/docs/5.2.1/WebServicesAPI.html (from HTML docs; may be partial - action= / show= variants split into tools)
- Auth: Kerberos SPNEGO (secure) or ?user.name=; Knox Basic/JWT at /gateway/<topology>/oozie; port 11000/11443
- Operations: 45

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `get_versions` | GET | `/oozie/versions` | Supported web-service protocol versions |  |
| `get_system_status` | GET | `/oozie/v1/admin/status` | System mode (NORMAL/NOWEBSERVICE/SAFEMODE) |  |
| `set_system_mode` | PUT | `/oozie/v1/admin/status?systemmode={mode}` | Change system mode |  |
| `get_os_env` | GET | `/oozie/v1/admin/os-env` | Server OS environment |  |
| `get_java_sys_properties` | GET | `/oozie/v1/admin/java-sys-properties` | Server Java system properties |  |
| `get_configuration` | GET | `/oozie/v1/admin/configuration` | Oozie server configuration |  |
| `get_instrumentation` | GET | `/oozie/v1/admin/instrumentation` | Instrumentation (if instrumentation service) |  |
| `get_metrics` | GET | `/oozie/v2/admin/metrics` | Metrics (if metrics service) |  |
| `get_build_version` | GET | `/oozie/v1/admin/build-version` | Oozie build version |  |
| `get_available_timezones` | GET | `/oozie/v1/admin/available-timezones` | Available time zones |  |
| `get_queue_dump` | GET | `/oozie/v1/admin/queue-dump` | Dump of callable queue |  |
| `get_available_oozie_servers` | GET | `/oozie/v2/admin/available-oozie-servers` | Oozie servers (HA) |  |
| `list_sharelib` | GET | `/oozie/v2/admin/list_sharelib` | List sharelib (optionally ?lib=) |  |
| `update_sharelib` | GET | `/oozie/v2/admin/update_sharelib` | Reload sharelib |  |
| `purge` | GET | `/oozie/v2/admin/purge` | Purge old wf/coord/bundle records |  |
| `get_jms_info` | GET | `/oozie/v2/admin/jmsinfo` | JMS connection info |  |
| `submit_job` | POST | `/oozie/v1/jobs` | Submit a workflow/coordinator/bundle job (XML config; ?action=start to also start) |  |
| `submit_proxy_job` | POST | `/oozie/v1/jobs?jobtype={mapreduce\|pig\|hive\|sqoop}` | Proxy submission of MR/Pig/Hive/Sqoop job |  |
| `list_jobs` | GET | `/oozie/v1/jobs` | List jobs (filter, jobtype, offset, len) |  |
| `bulk_job_action` | PUT | `/oozie/v1/jobs?action={kill\|suspend\|resume}` | Bulk kill/suspend/resume jobs matching a filter |  |
| `bulk_job_info` | GET | `/oozie/v1/jobs?bulk={filter}` | Bulk coordinator action info for a bundle |  |
| `start_job` | PUT | `/oozie/v1/job/{id}?action=start` | Start a job |  |
| `suspend_job` | PUT | `/oozie/v1/job/{id}?action=suspend` | Suspend a job |  |
| `resume_job` | PUT | `/oozie/v1/job/{id}?action=resume` | Resume a job |  |
| `kill_job` | PUT | `/oozie/v1/job/{id}?action=kill` | Kill a job |  |
| `dryrun_job` | POST | `/oozie/v1/jobs?action=dryrun` | Dry-run a job submission |  |
| `rerun_workflow` | PUT | `/oozie/v1/job/{id}?action=rerun` | Rerun a workflow |  |
| `rerun_coordinator` | PUT | `/oozie/v1/job/{id}?action=coord-rerun` | Rerun coordinator actions |  |
| `rerun_bundle` | PUT | `/oozie/v1/job/{id}?action=bundle-rerun` | Rerun bundle coordinators |  |
| `change_coordinator` | PUT | `/oozie/v1/job/{id}?action=change` | Change endtime/concurrency/pausetime |  |
| `update_coordinator` | PUT | `/oozie/v2/job/{id}?action=update` | Update coordinator definition/properties |  |
| `ignore_job` | PUT | `/oozie/v2/job/{id}?action=ignore` | Ignore coordinator job/actions |  |
| `sla_enable` | PUT | `/oozie/v2/job/{id}?action=sla-enable` | Enable SLA alerts |  |
| `sla_disable` | PUT | `/oozie/v2/job/{id}?action=sla-disable` | Disable SLA alerts |  |
| `sla_change` | PUT | `/oozie/v2/job/{id}?action=sla-change` | Change SLA parameters |  |
| `get_job_info` | GET | `/oozie/v1/job/{id}?show=info` | Job info (offset/len/filter/order for coords) |  |
| `get_job_allruns` | GET | `/oozie/v2/job/{id}?show=allruns` | All runs of a coordinator action |  |
| `get_job_definition` | GET | `/oozie/v1/job/{id}?show=definition` | Job definition XML |  |
| `get_job_log` | GET | `/oozie/v1/job/{id}?show=log` | Job log (logfilter) |  |
| `get_job_error_log` | GET | `/oozie/v2/job/{id}?show=errorlog` | Job error log |  |
| `get_job_audit_log` | GET | `/oozie/v2/job/{id}?show=auditlog` | Job audit log |  |
| `get_job_graph` | GET | `/oozie/v1/job/{id}?show=graph` | Workflow DAG (png/svg/dot) |  |
| `get_job_status` | GET | `/oozie/v2/job/{id}?show=status` | Job status only |  |
| `validate_xml` | POST | `/oozie/v2/validate?file={path}` | Validate workflow/coord/bundle XML |  |
| `get_sla` | GET | `/oozie/v2/sla` | SLA summary (filter by id/app_name/nominal time) |  |

## hbase_rest

30 tools.

- Product: Apache HBase REST server (Stargate)
- Version: HBase reference guide (CDP 7.1.x HBase 2.4)
- Spec source: https://hbase.apache.org/book.html#_rest (from HTML docs; query-string variants folded into one tool)
- Auth: Kerberos SPNEGO when hbase.rest.authentication.type=kerberos; Knox Basic/JWT at /gateway/<topology>/hbase; default port 20550 (CDP). COD exposes the same REST via its Knox gateway
- Operations: 30

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `get_cluster_version` | GET | `/version/cluster` | HBase version of the cluster |  |
| `get_rest_version` | GET | `/version/rest` | REST server version |  |
| `get_cluster_status` | GET | `/status/cluster` | Cluster status |  |
| `list_tables` | GET | `/` | List non-system tables |  |
| `list_namespaces` | GET | `/namespaces` | List namespaces |  |
| `get_namespace` | GET | `/namespaces/{namespace}` | Describe a namespace |  |
| `create_namespace` | POST | `/namespaces/{namespace}` | Create a namespace |  |
| `alter_namespace` | PUT | `/namespaces/{namespace}` | Alter a namespace (currently unused) |  |
| `delete_namespace` | DELETE | `/namespaces/{namespace}` | Delete an empty namespace |  |
| `list_namespace_tables` | GET | `/namespaces/{namespace}/tables` | List tables in a namespace |  |
| `table_exists` | GET | `/{table}/exists` | Check table exists |  |
| `get_table_schema` | GET | `/{table}/schema` | Describe table schema |  |
| `update_table_schema` | POST | `/{table}/schema` | Update table with a schema fragment |  |
| `create_or_replace_table` | PUT | `/{table}/schema` | Create table or replace schema |  |
| `delete_table` | DELETE | `/{table}/schema` | Delete (drop) the table |  |
| `get_table_regions` | GET | `/{table}/regions` | List table regions |  |
| `get_row` | GET | `/{table}/{row}[/{column}[:{qualifier}][/{timestamp}]]` | Get a row / column / cell (?v=versions, ?e=b64) |  |
| `get_rows_by_prefix` | GET | `/{table}/{row_prefix}*[/{column}]` | Get rows matching a row-key prefix |  |
| `multi_get` | GET | `/{table}/multiget?row=...` | Multi-get rows/columns (filter, filter_b64, e=b64) |  |
| `stateless_scan` | GET | `/{table}/*` | Stateless scan (limit, startrow, endrow, column, reversed, filter) |  |
| `create_scanner` | PUT | `/{table}/scanner` | Create a stateful scanner (batch, filter); returns Location |  |
| `scanner_next` | GET | `/{table}/scanner/{scanner_id}` | Get next batch from scanner (204 when exhausted) |  |
| `delete_scanner` | DELETE | `/{table}/scanner/{scanner_id}` | Delete a scanner |  |
| `put_row` | PUT | `/{table}/{row_key}` | Write cells (CellSet; base64 row/column/value) |  |
| `post_row` | POST | `/{table}/{row_key}` | Write cells (POST variant) |  |
| `delete_row` | DELETE | `/{table}/{row}[/{column}[:{qualifier}][/{timestamp}]]` | Delete row / family / column / version |  |
| `check_and_put` | PUT | `/{table}/{row_key}?check=put` | Conditional put |  |
| `check_and_delete` | DELETE | `/{table}/{row_key}[/{column}...]?check=delete` | Conditional delete |  |
| `append` | PUT | `/{table}/{row_key}?check=append` | Append to cell value |  |
| `increment` | PUT | `/{table}/{row_key}?check=increment` | Increment cell value |  |

## solr

66 tools.

- Product: Apache Solr (Cloudera Search) Collections, Core Admin, ConfigSets + core handlers
- Version: Solr 8.11 Reference Guide (CDP 7.1.9 ships Solr 8.11)
- Spec source: https://solr.apache.org/guide/8_11/collections-api.html (+ coreadmin-api, configsets-api, cluster-node-management, shard/replica/alias management) (from HTML docs)
- Auth: Kerberos SPNEGO (CDP secure default) or Basic (Solr auth plugin); Ranger authorizes; Knox Basic/JWT at /gateway/<topology>/solr; port 8985 (TLS)/8983
- Operations: 66

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `collections_create` | GET | `/solr/admin/collections?action=CREATE` | Create a collection |  |
| `collections_modifycollection` | GET | `/solr/admin/collections?action=MODIFYCOLLECTION` | Modify collection attributes |  |
| `collections_reload` | GET | `/solr/admin/collections?action=RELOAD` | Reload a collection |  |
| `collections_list` | GET | `/solr/admin/collections?action=LIST` | List collections |  |
| `collections_rename` | GET | `/solr/admin/collections?action=RENAME` | Rename a collection (via alias) |  |
| `collections_delete` | GET | `/solr/admin/collections?action=DELETE` | Delete a collection |  |
| `collections_collectionprop` | GET | `/solr/admin/collections?action=COLLECTIONPROP` | Set/remove a collection property |  |
| `collections_migrate` | GET | `/solr/admin/collections?action=MIGRATE` | Migrate documents to another collection |  |
| `collections_reindexcollection` | GET | `/solr/admin/collections?action=REINDEXCOLLECTION` | Re-index a collection |  |
| `collections_colstatus` | GET | `/solr/admin/collections?action=COLSTATUS` | Detailed collection status |  |
| `collections_backup` | GET | `/solr/admin/collections?action=BACKUP` | Backup a collection |  |
| `collections_restore` | GET | `/solr/admin/collections?action=RESTORE` | Restore a collection |  |
| `collections_rebalanceleaders` | GET | `/solr/admin/collections?action=REBALANCELEADERS` | Rebalance preferred leaders |  |
| `collections_clusterstatus` | GET | `/solr/admin/collections?action=CLUSTERSTATUS` | Cluster status |  |
| `collections_clusterprop` | GET | `/solr/admin/collections?action=CLUSTERPROP` | Set a cluster property |  |
| `collections_balanceshardunique` | GET | `/solr/admin/collections?action=BALANCESHARDUNIQUE` | Balance a property across shards |  |
| `collections_utilizenode` | GET | `/solr/admin/collections?action=UTILIZENODE` | Move replicas to utilize a node |  |
| `collections_replacenode` | GET | `/solr/admin/collections?action=REPLACENODE` | Move all replicas from one node to another |  |
| `collections_deletenode` | GET | `/solr/admin/collections?action=DELETENODE` | Delete all replicas on a node |  |
| `collections_addrole` | GET | `/solr/admin/collections?action=ADDROLE` | Add a role (overseer) to a node |  |
| `collections_removerole` | GET | `/solr/admin/collections?action=REMOVEROLE` | Remove a role from a node |  |
| `collections_overseerstatus` | GET | `/solr/admin/collections?action=OVERSEERSTATUS` | Overseer status and stats |  |
| `collections_migratestateformat` | GET | `/solr/admin/collections?action=MIGRATESTATEFORMAT` | Migrate cluster state format |  |
| `collections_splitshard` | GET | `/solr/admin/collections?action=SPLITSHARD` | Split a shard |  |
| `collections_createshard` | GET | `/solr/admin/collections?action=CREATESHARD` | Create a shard (implicit router) |  |
| `collections_deleteshard` | GET | `/solr/admin/collections?action=DELETESHARD` | Delete a shard |  |
| `collections_forceleader` | GET | `/solr/admin/collections?action=FORCELEADER` | Force leader election in a shard |  |
| `collections_syncshard` | GET | `/solr/admin/collections?action=SYNCSHARD` | Sync replicas of a shard |  |
| `collections_addreplica` | GET | `/solr/admin/collections?action=ADDREPLICA` | Add a replica |  |
| `collections_movereplica` | GET | `/solr/admin/collections?action=MOVEREPLICA` | Move a replica |  |
| `collections_deletereplica` | GET | `/solr/admin/collections?action=DELETEREPLICA` | Delete a replica |  |
| `collections_addreplicaprop` | GET | `/solr/admin/collections?action=ADDREPLICAPROP` | Add a replica property |  |
| `collections_deletereplicaprop` | GET | `/solr/admin/collections?action=DELETEREPLICAPROP` | Delete a replica property |  |
| `collections_createalias` | GET | `/solr/admin/collections?action=CREATEALIAS` | Create/modify an alias |  |
| `collections_listaliases` | GET | `/solr/admin/collections?action=LISTALIASES` | List aliases |  |
| `collections_aliasprop` | GET | `/solr/admin/collections?action=ALIASPROP` | Set alias properties |  |
| `collections_deletealias` | GET | `/solr/admin/collections?action=DELETEALIAS` | Delete an alias |  |
| `collections_requeststatus` | GET | `/solr/admin/collections?action=REQUESTSTATUS` | Status of an async request |  |
| `collections_deletestatus` | GET | `/solr/admin/collections?action=DELETESTATUS` | Delete async request status |  |
| `cores_status` | GET | `/solr/admin/cores?action=STATUS` | Core status |  |
| `cores_create` | GET | `/solr/admin/cores?action=CREATE` | Create a core |  |
| `cores_reload` | GET | `/solr/admin/cores?action=RELOAD` | Reload a core |  |
| `cores_rename` | GET | `/solr/admin/cores?action=RENAME` | Rename a core |  |
| `cores_swap` | GET | `/solr/admin/cores?action=SWAP` | Swap two cores |  |
| `cores_unload` | GET | `/solr/admin/cores?action=UNLOAD` | Unload a core |  |
| `cores_mergeindexes` | GET | `/solr/admin/cores?action=MERGEINDEXES` | Merge indexes into a core |  |
| `cores_split` | GET | `/solr/admin/cores?action=SPLIT` | Split a core index |  |
| `cores_requeststatus` | GET | `/solr/admin/cores?action=REQUESTSTATUS` | Status of an async core request |  |
| `cores_requestrecovery` | GET | `/solr/admin/cores?action=REQUESTRECOVERY` | Request recovery of a core |  |
| `configsets_list` | GET | `/solr/admin/configs?action=LIST` | List configsets |  |
| `configsets_upload` | POST | `/solr/admin/configs?action=UPLOAD` | Upload a configset (zip) |  |
| `configsets_create` | GET | `/solr/admin/configs?action=CREATE` | Create a configset from a base |  |
| `configsets_delete` | GET | `/solr/admin/configs?action=DELETE` | Delete a configset |  |
| `select` | GET | `/solr/{collection}/select` | Query (q, fq, fl, sort, rows, start, facet...) |  |
| `query_json` | POST | `/solr/{collection}/query` | JSON Request API query |  |
| `update_docs` | POST | `/solr/{collection}/update` | Add/delete documents (JSON/XML; commit param) |  |
| `realtime_get` | GET | `/solr/{collection}/get` | Real-time get by id(s) |  |
| `ping` | GET | `/solr/{collection}/admin/ping` | Ping a collection |  |
| `get_schema` | GET | `/solr/{collection}/schema` | Read full schema |  |
| `list_schema_fields` | GET | `/solr/{collection}/schema/fields` | List schema fields |  |
| `modify_schema` | POST | `/solr/{collection}/schema` | Schema API commands (add-field, ...) |  |
| `get_config` | GET | `/solr/{collection}/config` | Read effective solrconfig |  |
| `modify_config` | POST | `/solr/{collection}/config` | Config API commands (set-property, ...) |  |
| `system_info` | GET | `/solr/admin/info/system` | Node system info |  |
| `health_check` | GET | `/solr/admin/info/health` | Node health check (SolrCloud) |  |
| `get_metrics` | GET | `/solr/admin/metrics` | Metrics API |  |

## hue

45 tools. **Partial source:** from HTML reference pages; may be incomplete.

- Product: Hue REST API (/api/v1)
- Version: Hue docs (gethue.com, Hue 4.11+); CDP 7.1.x Hue may lack /api/v1/storage, importer and connectors endpoints
- Spec source: https://docs.gethue.com/developer/api/rest/ (from HTML docs; may be partial)
- Auth: JWT from POST /api/v1/token/auth (username/password) -> Authorization: Bearer; or custom JWT auth backend; or session cookie. Via Knox: /gateway/<topology>/hue
- Operations: 45

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `auth_token` | POST | `/api/v1/token/auth/` | Obtain JWT (username/password) |  |
| `verify_token` | POST | `/api/v1/token/verify/` | Validate a JWT |  |
| `refresh_token` | POST | `/api/v1/token/refresh/` | Refresh a JWT |  |
| `execute_query` | POST | `/api/v1/editor/execute/{dialect}` | Execute a SQL statement |  |
| `check_status` | POST | `/api/v1/editor/check_status` | Check query status |  |
| `fetch_result_data` | POST | `/api/v1/editor/fetch_result_data` | Fetch query results |  |
| `get_logs` | POST | `/api/v1/editor/get_logs` | Get query logs |  |
| `create_notebook` | POST | `/api/v1/editor/create_notebook` | Create a notebook/editor session |  |
| `autocomplete` | POST | `/api/v1/editor/autocomplete/[{db}/[{table}/[{column}/]]]` | List databases/tables/columns/functions |  |
| `describe` | POST | `/api/v1/editor/describe/{db}/[{table}/]` | Describe database or table |  |
| `analyze` | POST | `/api/v1/{dialect}/analyze/{db}/{table}/[{column}/]` | Table/column statistics |  |
| `sample` | POST | `/api/v1/editor/sample/{db}/{table}/[{column}/]` | Sample rows |  |
| `get_history` | GET | `/api/v1/editor/get_history` | Query history |  |
| `get_config` | POST | `/api/v1/get_config/` | Hue app configuration |  |
| `get_filesystems` | GET | `/api/v1/storage/filesystems` | List available filesystems |  |
| `view_path` | GET | `/api/v1/storage/view={path}` | List directory or preview file |  |
| `download_file` | GET | `/api/v1/storage/download={path}` | Download a file |  |
| `upload_file` | POST | `/api/v1/storage/upload/file` | Upload a file |  |
| `mkdir` | POST | `/api/v1/storage/mkdir` | Create directory |  |
| `touch` | POST | `/api/v1/storage/touch` | Create empty file |  |
| `rename` | POST | `/api/v1/storage/rename` | Rename |  |
| `move` | POST | `/api/v1/storage/move` | Move |  |
| `copy` | POST | `/api/v1/storage/copy` | Copy |  |
| `content_summary` | GET | `/api/v1/storage/content_summary` | Content summary |  |
| `rmtree` | POST | `/api/v1/storage/rmtree` | Delete path |  |
| `set_replication` | POST | `/api/v1/storage/set_replication` | Set HDFS replication |  |
| `trash_restore` | POST | `/api/v1/storage/trash/restore` | Restore from trash |  |
| `trash_purge` | POST | `/api/v1/storage/trash/purge` | Purge trash |  |
| `importer_upload_file` | POST | `/api/v1/importer/upload/file/` | Upload local file for import |  |
| `importer_guess_metadata` | GET | `/api/v1/importer/file/guess_metadata/` | Guess file metadata |  |
| `importer_guess_header` | GET | `/api/v1/importer/file/guess_header/` | Guess file header |  |
| `importer_preview` | GET | `/api/v1/importer/file/preview/` | Preview import |  |
| `importer_sql_type_mapping` | GET | `/api/v1/importer/sql_type_mapping/` | SQL type mapping for a dialect |  |
| `list_connectors` | GET | `/api/v1/connector/instances` | List connectors |  |
| `list_connector_types` | GET | `/api/v1/connector/types` | List connector types |  |
| `new_connector` | POST | `/api/v1/connector/instance/new/{dialect}/{interface}` | Connector template |  |
| `get_connector` | GET | `/api/v1/connector/instance/get/{id}` | Get connector |  |
| `update_connector` | POST | `/api/v1/connector/instance/update` | Create/update connector |  |
| `delete_connector` | POST | `/api/v1/connector/instance/delete` | Delete connector |  |
| `test_connector` | POST | `/api/v1/connector/instance/test/` | Test connector |  |
| `install_connector_examples` | POST | `/api/v1/connector/examples/install/` | Install examples |  |
| `get_users` | GET | `/api/v1/iam/get_users` | List users |  |
| `get_users_by_id` | GET | `/api/v1/iam/users` | Users by ids |  |
| `autocomplete_users` | GET | `/api/v1/iam/users/autocomplete` | User autocomplete |  |
| `search_entities` | POST | `/api/v1/metadata/search/entities_interactive/` | Data catalog entity search |  |

## cdv

61 tools. **Partial source:** from HTML reference pages; may be incomplete.

- Product: Cloudera Data Visualization Admin API v1 + non-admin + Data API
- Version: CDV 8.1.x docs
- Spec source: https://docs.cloudera.com/data-visualization/8/ref-admin-api/viz-ref-admin-api.pdf + howto-swagger-api-docs (from HTML/PDF docs; may be partial - full swagger only at https://<cdv>/arc/apps/apidemo-v2/ behind login)
- Auth: Authorization: apikey <key> (keys from /arc/apps/apikeys) or session login at /arc/apps/login; Admin API must be enabled; Data API disabled by default
- Operations: 61

| tool | method | path | summary | flags |
|---|---|---|---|---|
| `list_users` | GET | `/arc/adminapi/v1/users` | List users (?detail=1 for full data) |  |
| `get_user` | GET | `/arc/adminapi/v1/users/{id_or_name}` | Get one of users (?detail=1) |  |
| `create_user` | POST | `/arc/adminapi/v1/users` | Create user (form field data=[{...}]; connections support validate=true) |  |
| `update_user` | POST | `/arc/adminapi/v1/users/{id}` | Update user (merge top-level fields) |  |
| `delete_user` | DELETE | `/arc/adminapi/v1/users/{id}` | Delete user |  |
| `list_groups` | GET | `/arc/adminapi/v1/groups` | List groups (?detail=1 for full data) |  |
| `get_group` | GET | `/arc/adminapi/v1/groups/{id_or_name}` | Get one of groups (?detail=1) |  |
| `create_group` | POST | `/arc/adminapi/v1/groups` | Create group (form field data=[{...}]; connections support validate=true) |  |
| `update_group` | POST | `/arc/adminapi/v1/groups/{id}` | Update group (merge top-level fields) |  |
| `delete_group` | DELETE | `/arc/adminapi/v1/groups/{id}` | Delete group |  |
| `list_roles` | GET | `/arc/adminapi/v1/roles` | List roles (?detail=1 for full data) |  |
| `get_role` | GET | `/arc/adminapi/v1/roles/{id_or_name}` | Get one of roles (?detail=1) |  |
| `create_role` | POST | `/arc/adminapi/v1/roles` | Create role (form field data=[{...}]; connections support validate=true) |  |
| `update_role` | POST | `/arc/adminapi/v1/roles/{id}` | Update role (merge top-level fields) |  |
| `delete_role` | DELETE | `/arc/adminapi/v1/roles/{id}` | Delete role |  |
| `list_segments` | GET | `/arc/adminapi/v1/segments` | List segments (?detail=1 for full data) |  |
| `get_segment` | GET | `/arc/adminapi/v1/segments/{id_or_name}` | Get one of segments (?detail=1) |  |
| `create_segment` | POST | `/arc/adminapi/v1/segments` | Create segment (form field data=[{...}]; connections support validate=true) |  |
| `update_segment` | POST | `/arc/adminapi/v1/segments/{id}` | Update segment (merge top-level fields) |  |
| `delete_segment` | DELETE | `/arc/adminapi/v1/segments/{id}` | Delete segment |  |
| `list_filterassociations` | GET | `/arc/adminapi/v1/filterassociations` | List filterassociations (?detail=1 for full data) |  |
| `get_filterassociation` | GET | `/arc/adminapi/v1/filterassociations/{id_or_name}` | Get one of filterassociations (?detail=1) |  |
| `create_filterassociation` | POST | `/arc/adminapi/v1/filterassociations` | Create filterassociation (form field data=[{...}]; connections support validate=true) |  |
| `update_filterassociation` | POST | `/arc/adminapi/v1/filterassociations/{id}` | Update filterassociation (merge top-level fields) |  |
| `delete_filterassociation` | DELETE | `/arc/adminapi/v1/filterassociations/{id}` | Delete filterassociation |  |
| `list_workspaces` | GET | `/arc/adminapi/v1/workspaces` | List workspaces (?detail=1 for full data) |  |
| `get_workspace` | GET | `/arc/adminapi/v1/workspaces/{id_or_name}` | Get one of workspaces (?detail=1) |  |
| `create_workspace` | POST | `/arc/adminapi/v1/workspaces` | Create workspace (form field data=[{...}]; connections support validate=true) |  |
| `update_workspace` | POST | `/arc/adminapi/v1/workspaces/{id}` | Update workspace (merge top-level fields) |  |
| `delete_workspace` | DELETE | `/arc/adminapi/v1/workspaces/{id}` | Delete workspace |  |
| `list_datasets` | GET | `/arc/adminapi/v1/datasets` | List datasets (?detail=1 for full data) |  |
| `get_dataset` | GET | `/arc/adminapi/v1/datasets/{id_or_name}` | Get one of datasets (?detail=1) |  |
| `create_dataset` | POST | `/arc/adminapi/v1/datasets` | Create dataset (form field data=[{...}]; connections support validate=true) |  |
| `update_dataset` | POST | `/arc/adminapi/v1/datasets/{id}` | Update dataset (merge top-level fields) |  |
| `delete_dataset` | DELETE | `/arc/adminapi/v1/datasets/{id}` | Delete dataset |  |
| `list_visuals` | GET | `/arc/adminapi/v1/visuals` | List visuals (?detail=1 for full data) |  |
| `get_visual` | GET | `/arc/adminapi/v1/visuals/{id_or_name}` | Get one of visuals (?detail=1) |  |
| `create_visual` | POST | `/arc/adminapi/v1/visuals` | Create visual (form field data=[{...}]; connections support validate=true) |  |
| `update_visual` | POST | `/arc/adminapi/v1/visuals/{id}` | Update visual (merge top-level fields) |  |
| `delete_visual` | DELETE | `/arc/adminapi/v1/visuals/{id}` | Delete visual |  |
| `list_connections` | GET | `/arc/adminapi/v1/connections` | List connections (?detail=1 for full data) |  |
| `get_connection` | GET | `/arc/adminapi/v1/connections/{id_or_name}` | Get one of connections (?detail=1) |  |
| `create_connection` | POST | `/arc/adminapi/v1/connections` | Create connection (form field data=[{...}]; connections support validate=true) |  |
| `update_connection` | POST | `/arc/adminapi/v1/connections/{id}` | Update connection (merge top-level fields) |  |
| `delete_connection` | DELETE | `/arc/adminapi/v1/connections/{id}` | Delete connection |  |
| `migration_import` | POST | `/arc/migration/api/import/` | Import visual artifacts (JSON export file) |  |
| `migration_export` | GET | `/arc/migration/api/export/` | Export visual artifacts (method unverified) |  |
| `edit_user_profile` | POST | `/arc/adminapi/edituserprofile/{username}` | Edit a user profile (method unverified) |  |
| `gc_monitor` | GET | `/arc/adminapi/gcmonitor` | GC monitor |  |
| `gc_stats` | GET | `/arc/adminapi/gcstats` | GC statistics |  |
| `list_log_levels` | GET | `/arc/adminapi/loglevel` | List logger levels |  |
| `get_log_level` | GET | `/arc/adminapi/loglevel/{logger_name}` | Get logger level |  |
| `set_log_level` | POST | `/arc/adminapi/loglevel/{logger_name}` | Set logger level ({"level":"DEBUG"}) |  |
| `toggle_cprofile` | POST | `/arc/adminapi/toggle_cprofile` | Toggle cProfile (method unverified) |  |
| `reset_dataset_cache` | POST | `/arc/datasets/dataset/cache_reset/{id}` | Reset dataset cache (method unverified) |  |
| `reset_connection_cache` | POST | `/arc/datasets/dataconnection/cache_reset/{id}` | Reset data-connection cache (method unverified) |  |
| `run_job` | POST | `/arc/jobs/api/run/` | Run a scheduled job (method unverified) |  |
| `run_extract` | POST | `/arc/jobs/api/extracts/run` | Run a data extract (method unverified) |  |
| `create_extract` | POST | `/arc/jobs/api/extracts/create` | Create a data extract (method unverified) |  |
| `data_api_query` | POST | `/arc/api/data` | Data API: run a dataset query (disabled by default) |  |
| `data_api_app` | POST | `/arc/apps/dataapi` | Data API app endpoint (disabled by default; method unverified) |  |
