from typing import Optional, Union

from .errors import ValidationError
from .api.constants import (
    ADMIN_COLLECTIONS,
    COLLECTIONS,
    ENVIRONMENT_COLLECTIONS,
    ITEM_COLLECTIONS,
    ITEM_TYPES,
    JOB_COLLECTIONS,
    JOB_TYPES,
    LAKEHOUSE_COLLECTIONS,
    WORKSPACE_CONFIG,
    coerce_value,
)


BASE_URL = "https://api.fabric.microsoft.com"
API_VERSION = "v1"
ENDPOINT = f"{BASE_URL}/{API_VERSION}"


def _coerce_value(registry, value, field_name: str) -> str:
    try:
        return coerce_value(registry, value, field_name)
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def workspaces() -> str:
    return f"{ENDPOINT}/{COLLECTIONS['Workspace']}"


def workspace(workspace_id: str) -> str:
    return f"{workspaces()}/{workspace_id}"


def admin(admin_type: Optional[str] = None) -> str:
    url = f"{ENDPOINT}/{COLLECTIONS['Admin']}"
    if not admin_type:
        return url
    sub_path = _coerce_value(ADMIN_COLLECTIONS, admin_type, "admin_type")
    return f"{url}/{sub_path}"


def capacities() -> str:
    return f"{ENDPOINT}/{COLLECTIONS['Capacity']}"


def capacity(capacity_id: str) -> str:
    return f"{capacities()}/{capacity_id}"


def items(workspace_id: str, item_type: Optional[str] = None) -> str:
    if item_type:
        item_path = _coerce_value(ITEM_TYPES, item_type, "item_type")
    else:
        item_path = ITEM_TYPES["Item"]
    return f"{workspace(workspace_id)}/{item_path}"


def item(workspace_id: str, item_id: str, item_type: Optional[str] = None) -> str:
    return f"{items(workspace_id, item_type)}/{item_id}"


def item_definition(workspace_id: str, item_id: str) -> str:
    return f"{item(workspace_id, item_id)}/getDefinition"


def item_definition_update(workspace_id: str, item_id: str) -> str:
    return f"{item(workspace_id, item_id)}/updateDefinition?updateMetadata=True"


def item_definition_for_type(workspace_id: str, item_id: str, item_type: str) -> str:
    return f"{item(workspace_id, item_id, item_type)}/getDefinition"


def item_definition_update_for_type(
    workspace_id: str,
    item_id: str,
    item_type: str,
    update_metadata: Optional[bool] = None,
) -> str:
    url = f"{item(workspace_id, item_id, item_type)}/updateDefinition"
    if update_metadata is None:
        return url
    return f"{url}?updateMetadata={str(update_metadata).lower()}"


def reports(workspace_id: str) -> str:
    return f"{workspace(workspace_id)}/{ITEM_TYPES['Report']}"


def report(workspace_id: str, report_id: str) -> str:
    return f"{reports(workspace_id)}/{report_id}"


def report_definition(workspace_id: str, report_id: str) -> str:
    return f"{report(workspace_id, report_id)}/getDefinition"


def report_definition_update(
    workspace_id: str, report_id: str, update_metadata: Optional[bool] = None
) -> str:
    url = f"{report(workspace_id, report_id)}/updateDefinition"
    if update_metadata is None:
        return url
    return f"{url}?updateMetadata={str(update_metadata).lower()}"


def paginated_reports(workspace_id: str) -> str:
    return f"{workspace(workspace_id)}/{ITEM_TYPES['PaginatedReport']}"


def paginated_report(workspace_id: str, paginated_report_id: str) -> str:
    return f"{paginated_reports(workspace_id)}/{paginated_report_id}"


def apache_airflow_job_files(
    workspace_id: str, job_id: str, file_path: Optional[str] = None
) -> str:
    url = f"{item(workspace_id, job_id, ITEM_TYPES['ApacheAirflowJob'])}/files"
    if file_path:
        url += f"/{file_path}"
    return url


def apache_airflow_job_pool_templates(
    workspace_id: str, pool_template_id: Optional[str] = None
) -> str:
    url = f"{workspace(workspace_id)}/apacheAirflowJobs/poolTemplates"
    if pool_template_id:
        url += f"/{pool_template_id}"
    return url


def apache_airflow_job_settings(workspace_id: str) -> str:
    return f"{workspace(workspace_id)}/apacheAirflowJobs/settings"


def sql_endpoint_refresh_metadata(workspace_id: str, sql_endpoint_id: str) -> str:
    return (
        f"{item(workspace_id, sql_endpoint_id, ITEM_TYPES['SQLEndpoint'])}/refreshMetadata"
    )


def sql_endpoint_connection_string(workspace_id: str, sql_endpoint_id: str) -> str:
    return (
        f"{item(workspace_id, sql_endpoint_id, ITEM_TYPES['SQLEndpoint'])}/connectionString"
    )


def sql_endpoint_sql_audit_settings(workspace_id: str, item_id: str) -> str:
    return f"{item(workspace_id, item_id, ITEM_TYPES['SQLEndpoint'])}/settings/sqlAudit"


def sql_endpoint_sql_audit_set_actions(workspace_id: str, item_id: str) -> str:
    return f"{sql_endpoint_sql_audit_settings(workspace_id, item_id)}/setAuditActionsAndGroups"


def warehouse_connection_string(workspace_id: str, warehouse_id: str) -> str:
    return (
        f"{item(workspace_id, warehouse_id, ITEM_TYPES['Warehouse'])}/connectionString"
    )


def warehouse_sql_audit_settings(workspace_id: str, item_id: str) -> str:
    return f"{item(workspace_id, item_id, ITEM_TYPES['Warehouse'])}/settings/sqlAudit"


def warehouse_sql_audit_set_actions(workspace_id: str, item_id: str) -> str:
    return f"{warehouse_sql_audit_settings(workspace_id, item_id)}/setAuditActionsAndGroups"


def warehouse_restore_points(workspace_id: str, warehouse_id: str) -> str:
    return f"{item(workspace_id, warehouse_id, ITEM_TYPES['Warehouse'])}/restorePoints"


def warehouse_restore_point(
    workspace_id: str, warehouse_id: str, restore_point_id: str
) -> str:
    return f"{warehouse_restore_points(workspace_id, warehouse_id)}/{restore_point_id}"


def warehouse_restore_point_restore(
    workspace_id: str, warehouse_id: str, restore_point_id: str
) -> str:
    return f"{warehouse_restore_point(workspace_id, warehouse_id, restore_point_id)}/restore"


def dataflow_execute_query(workspace_id: str, dataflow_id: str) -> str:
    return f"{item(workspace_id, dataflow_id, ITEM_TYPES['Dataflow'])}/executeQuery"


def dataflow_parameters(workspace_id: str, dataflow_id: str) -> str:
    return f"{item(workspace_id, dataflow_id, ITEM_TYPES['Dataflow'])}/parameters"


def lakehouse_tables(workspace_id: str, lakehouse_id: str) -> str:
    return f"{item(workspace_id, lakehouse_id, ITEM_TYPES['Lakehouse'])}/tables"


def lakehouse_table_load(workspace_id: str, lakehouse_id: str, table_name: str) -> str:
    return f"{lakehouse_tables(workspace_id, lakehouse_id)}/{table_name}/load"


def lakehouse_table_maintenance_instances(workspace_id: str, lakehouse_id: str) -> str:
    return (
        f"{item(workspace_id, lakehouse_id, ITEM_TYPES['Lakehouse'])}"
        "/jobs/TableMaintenance/instances"
    )


def lakehouse_refresh_mlv_instances(workspace_id: str, lakehouse_id: str) -> str:
    return (
        f"{item(workspace_id, lakehouse_id, ITEM_TYPES['Lakehouse'])}"
        "/jobs/RefreshMaterializedLakeViews/instances"
    )


def lakehouse_refresh_mlv_schedules(workspace_id: str, lakehouse_id: str) -> str:
    return (
        f"{item(workspace_id, lakehouse_id, ITEM_TYPES['Lakehouse'])}"
        "/jobs/RefreshMaterializedLakeViews/schedules"
    )


def lakehouse_refresh_mlv_schedule(
    workspace_id: str, lakehouse_id: str, schedule_id: str
) -> str:
    return f"{lakehouse_refresh_mlv_schedules(workspace_id, lakehouse_id)}/{schedule_id}"


def lakehouse_livy_sessions(workspace_id: str, lakehouse_id: str) -> str:
    return f"{item(workspace_id, lakehouse_id, ITEM_TYPES['Lakehouse'])}/livySessions"


def lakehouse_livy_session(
    workspace_id: str, lakehouse_id: str, livy_id: str
) -> str:
    return f"{lakehouse_livy_sessions(workspace_id, lakehouse_id)}/{livy_id}"


def notebook_livy_sessions(workspace_id: str, notebook_id: str) -> str:
    return f"{item(workspace_id, notebook_id, ITEM_TYPES['Notebook'])}/livySessions"


def notebook_livy_session(workspace_id: str, notebook_id: str, livy_id: str) -> str:
    return f"{notebook_livy_sessions(workspace_id, notebook_id)}/{livy_id}"


def workspace_config(workspace_id: str, config_type: str, config_id: Optional[str] = None) -> str:
    config_path = _coerce_value(WORKSPACE_CONFIG, config_type, "config_type")
    url = f"{workspace(workspace_id)}/{config_path}"
    if config_id:
        url += f"/{config_id}"
    return url


def table(workspace_id: str, lakehouse_id: str, table_name: Optional[str] = None) -> str:
    lakehouse_url = item(workspace_id, lakehouse_id, ITEM_TYPES["Lakehouse"])
    url = f"{lakehouse_url}/{LAKEHOUSE_COLLECTIONS['Table']}"
    if table_name:
        url += f"/{table_name}/load"
    return url


def eventstream_topology(workspace_id: str, eventstream_id: str) -> str:
    return f"{item(workspace_id, eventstream_id, ITEM_TYPES['Eventstream'])}/topology"


def eventstream_pause(workspace_id: str, eventstream_id: str) -> str:
    return f"{item(workspace_id, eventstream_id, ITEM_TYPES['Eventstream'])}/pause"


def eventstream_resume(workspace_id: str, eventstream_id: str) -> str:
    return f"{item(workspace_id, eventstream_id, ITEM_TYPES['Eventstream'])}/resume"


def eventstream_source(workspace_id: str, eventstream_id: str, source_id: str) -> str:
    return (
        f"{item(workspace_id, eventstream_id, ITEM_TYPES['Eventstream'])}/sources/{source_id}"
    )


def eventstream_source_connection(
    workspace_id: str, eventstream_id: str, source_id: str
) -> str:
    return f"{eventstream_source(workspace_id, eventstream_id, source_id)}/connection"


def eventstream_source_pause(workspace_id: str, eventstream_id: str, source_id: str) -> str:
    return f"{eventstream_source(workspace_id, eventstream_id, source_id)}/pause"


def eventstream_source_resume(workspace_id: str, eventstream_id: str, source_id: str) -> str:
    return f"{eventstream_source(workspace_id, eventstream_id, source_id)}/resume"


def eventstream_destination(
    workspace_id: str, eventstream_id: str, destination_id: str
) -> str:
    return (
        f"{item(workspace_id, eventstream_id, ITEM_TYPES['Eventstream'])}/destinations/"
        f"{destination_id}"
    )


def eventstream_destination_connection(
    workspace_id: str, eventstream_id: str, destination_id: str
) -> str:
    return (
        f"{eventstream_destination(workspace_id, eventstream_id, destination_id)}/connection"
    )


def eventstream_destination_pause(
    workspace_id: str, eventstream_id: str, destination_id: str
) -> str:
    return f"{eventstream_destination(workspace_id, eventstream_id, destination_id)}/pause"


def eventstream_destination_resume(
    workspace_id: str, eventstream_id: str, destination_id: str
) -> str:
    return f"{eventstream_destination(workspace_id, eventstream_id, destination_id)}/resume"


def graph_model_execute_query(workspace_id: str, graph_model_id: str) -> str:
    return f"{item(workspace_id, graph_model_id, ITEM_TYPES['GraphModel'])}/executeQuery"


def graph_model_queryable_type(workspace_id: str, graph_model_id: str) -> str:
    return f"{item(workspace_id, graph_model_id, ITEM_TYPES['GraphModel'])}/getQueryableGraphType"


def environment_libraries(workspace_id: str, environment_id: str) -> str:
    return (
        f"{item(workspace_id, environment_id, ITEM_TYPES['Environment'])}/libraries"
    )


def environment_libraries_export(workspace_id: str, environment_id: str) -> str:
    return f"{environment_libraries(workspace_id, environment_id)}/exportExternalLibraries"


def environment_spark_compute(workspace_id: str, environment_id: str) -> str:
    return f"{item(workspace_id, environment_id, ITEM_TYPES['Environment'])}/sparkcompute"


def environment_staging_cancel_publish(workspace_id: str, environment_id: str) -> str:
    return (
        f"{item(workspace_id, environment_id, ITEM_TYPES['Environment'])}/staging/cancelPublish"
    )


def environment_staging_libraries(workspace_id: str, environment_id: str) -> str:
    return (
        f"{item(workspace_id, environment_id, ITEM_TYPES['Environment'])}/staging/libraries"
    )


def environment_staging_library(
    workspace_id: str, environment_id: str, library_name: str
) -> str:
    return f"{environment_staging_libraries(workspace_id, environment_id)}/{library_name}"


def environment_staging_libraries_export(workspace_id: str, environment_id: str) -> str:
    return f"{environment_staging_libraries(workspace_id, environment_id)}/exportExternalLibraries"


def environment_staging_libraries_import(workspace_id: str, environment_id: str) -> str:
    return f"{environment_staging_libraries(workspace_id, environment_id)}/importExternalLibraries"


def environment_staging_libraries_remove_external(
    workspace_id: str, environment_id: str
) -> str:
    return f"{environment_staging_libraries(workspace_id, environment_id)}/removeExternalLibrary"


def environment_staging_publish(workspace_id: str, environment_id: str) -> str:
    return f"{item(workspace_id, environment_id, ITEM_TYPES['Environment'])}/staging/publish"


def environment_staging_spark_compute(workspace_id: str, environment_id: str) -> str:
    return f"{item(workspace_id, environment_id, ITEM_TYPES['Environment'])}/staging/sparkcompute"


def mirrored_azure_databricks_catalogs(workspace_id: str) -> str:
    return f"{workspace(workspace_id)}/azuredatabricks/catalogs"


def mirrored_azure_databricks_schemas(
    workspace_id: str, catalog_name: str
) -> str:
    return f"{mirrored_azure_databricks_catalogs(workspace_id)}/{catalog_name}/schemas"


def mirrored_azure_databricks_tables(
    workspace_id: str, catalog_name: str, schema_name: str
) -> str:
    return (
        f"{mirrored_azure_databricks_schemas(workspace_id, catalog_name)}/{schema_name}/tables"
    )


def mirrored_azure_databricks_refresh_metadata(
    workspace_id: str, catalog_id: str
) -> str:
    return (
        f"{item(workspace_id, catalog_id, ITEM_TYPES['MirroredAzureDatabricksCatalog'])}"
        "/refreshCatalogMetadata"
    )


def mirrored_database_mirroring_status(
    workspace_id: str, database_id: str
) -> str:
    return (
        f"{item(workspace_id, database_id, ITEM_TYPES['MirroredDatabase'])}/getMirroringStatus"
    )


def mirrored_database_tables_mirroring_status(
    workspace_id: str, database_id: str
) -> str:
    return (
        f"{item(workspace_id, database_id, ITEM_TYPES['MirroredDatabase'])}"
        "/getTablesMirroringStatus"
    )


def mirrored_database_start(workspace_id: str, database_id: str) -> str:
    return f"{item(workspace_id, database_id, ITEM_TYPES['MirroredDatabase'])}/startMirroring"


def mirrored_database_stop(workspace_id: str, database_id: str) -> str:
    return f"{item(workspace_id, database_id, ITEM_TYPES['MirroredDatabase'])}/stopMirroring"


def ml_model_endpoint(workspace_id: str, model_id: str) -> str:
    return f"{workspace(workspace_id)}/mlmodels/{model_id}/endpoint"


def ml_model_endpoint_score(workspace_id: str, model_id: str) -> str:
    return f"{workspace(workspace_id)}/mlModels/{model_id}/endpoint/score"


def ml_model_endpoint_versions(workspace_id: str, model_id: str) -> str:
    return f"{ml_model_endpoint(workspace_id, model_id)}/versions"


def ml_model_endpoint_version(
    workspace_id: str, model_id: str, version_name: str
) -> str:
    return f"{ml_model_endpoint_versions(workspace_id, model_id)}/{version_name}"


def ml_model_endpoint_versions_deactivate_all(workspace_id: str, model_id: str) -> str:
    return f"{ml_model_endpoint_versions(workspace_id, model_id)}/deactivateAll"


def ml_model_endpoint_version_activate(
    workspace_id: str, model_id: str, version_name: str
) -> str:
    return f"{ml_model_endpoint_version(workspace_id, model_id, version_name)}/activate"


def ml_model_endpoint_version_deactivate(
    workspace_id: str, model_id: str, version_name: str
) -> str:
    return f"{ml_model_endpoint_version(workspace_id, model_id, version_name)}/deactivate"


def ml_model_endpoint_version_score(
    workspace_id: str, model_id: str, version_name: str
) -> str:
    return f"{ml_model_endpoint_version(workspace_id, model_id, version_name)}/score"


def semantic_model_bind_connection(workspace_id: str, semantic_model_id: str) -> str:
    return (
        f"{item(workspace_id, semantic_model_id, ITEM_TYPES['SemanticModel'])}/bindConnection"
    )


def spark_job_definition_livy_sessions(workspace_id: str, item_id: str) -> str:
    return (
        f"{item(workspace_id, item_id, ITEM_TYPES['SparkJobDefinition'])}/livySessions"
    )


def spark_job_definition_livy_session(
    workspace_id: str, item_id: str, livy_id: str
) -> str:
    return f"{spark_job_definition_livy_sessions(workspace_id, item_id)}/{livy_id}"


def sql_database_start_mirroring(workspace_id: str, database_id: str) -> str:
    return f"{item(workspace_id, database_id, ITEM_TYPES['SQLDatabase'])}/startMirroring"


def sql_database_stop_mirroring(workspace_id: str, database_id: str) -> str:
    return f"{item(workspace_id, database_id, ITEM_TYPES['SQLDatabase'])}/stopMirroring"


def environment(
    workspace_id: str,
    environment_id: str,
    env_sub_type: Optional[str] = None,
    staging: bool = False,
) -> str:
    if env_sub_type:
        env_sub_type = _coerce_value(ENVIRONMENT_COLLECTIONS, env_sub_type, "env_sub_type")
    url = f"{workspace(workspace_id)}/{ITEM_TYPES['Environment']}/{environment_id}"
    if staging:
        url += "/staging"
    if env_sub_type:
        url += f"/{env_sub_type}"
    return url


def job_instance(
    workspace_id: str,
    item_id: str,
    job_type: Optional[str] = None,
    item_type: Optional[str] = None,
    job_id: Optional[str] = None,
) -> str:
    if job_type and job_id:
        raise ValidationError("job_type and job_id are mutually exclusive")

    url = (
        f"{item(workspace_id, item_id, item_type)}/"
        f"{ITEM_COLLECTIONS['Job']}/{JOB_COLLECTIONS['Instance']}"
    )
    if job_type:
        job_value = _coerce_value(JOB_TYPES, job_type, "job_type")
        url += f"?jobType={job_value}"
    elif job_id:
        url += f"/{job_id}"
    return url


def job_instances_for_type(
    workspace_id: str,
    item_id: str,
    item_type: str,
    job_type: str,
) -> str:
    item_type_value = _coerce_value(ITEM_TYPES, item_type, "item_type")
    job_type_value = _coerce_value(JOB_TYPES, job_type, "job_type")
    return (
        f"{workspace(workspace_id)}/{item_type_value}/{item_id}/"
        f"{ITEM_COLLECTIONS['Job']}/{job_type_value}/{JOB_COLLECTIONS['Instance']}"
    )


def job_schedule(
    workspace_id: str,
    item_id: str,
    item_type: str,
    job_type: str,
    schedule_id: Optional[str] = None,
) -> str:
    item_type_value = _coerce_value(ITEM_TYPES, item_type, "item_type")
    job_type_value = _coerce_value(JOB_TYPES, job_type, "job_type")
    url = (
        f"{workspace(workspace_id)}/{item_type_value}/{item_id}/"
        f"{ITEM_COLLECTIONS['Job']}/{job_type_value}/{JOB_COLLECTIONS['Schedule']}"
    )
    if schedule_id:
        url += f"/{schedule_id}"
    return url
