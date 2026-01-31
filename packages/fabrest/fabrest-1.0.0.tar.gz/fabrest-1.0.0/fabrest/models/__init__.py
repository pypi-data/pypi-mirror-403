from typing import Any, Dict, List, Optional, TypedDict
from typing import NotRequired


class Workspace(TypedDict, total=False):
    id: str
    displayName: str
    description: NotRequired[str]
    capacityId: NotRequired[str]
    state: NotRequired[str]


class Item(TypedDict, total=False):
    id: str
    displayName: str
    type: NotRequired[str]
    workspaceId: NotRequired[str]


class JobRun(TypedDict, total=False):
    id: str
    jobType: str
    status: str
    percentComplete: NotRequired[int]
    error: NotRequired[Dict[str, Any]]


class Capacity(TypedDict, total=False):
    id: str
    displayName: str
    sku: NotRequired[str]
    state: NotRequired[str]


from . import (
    admin,
    anomaly_detector,
    apache_airflow_job,
    copy_job,
    cosmos_db_database,
    data_pipeline,
    dataflow,
    digital_twin_builder,
    digital_twin_builder_flow,
    environment,
    event_schema_set,
    eventhouse,
    eventstream,
    graph_model,
    graph_query_set,
    graphql_api,
    kql_dashboard,
    kql_database,
    kql_queryset,
    lakehouse,
    map,
    mirrored_azure_databricks_catalog,
    mirrored_database,
    ml_experiment,
    ml_model,
    mounted_data_factory,
    notebook,
    ontology,
    operations_agent,
    paginated_report,
    platform,
    real_time_intelligence,
    reflex,
    report,
    semantic_model,
    snowflake_database,
    spark,
    spark_job_definition,
    sql_database,
    sql_endpoint,
    user_data_function,
    variable_library,
    warehouse,
    warehouse_snapshot,
)


__all__ = [
    "Workspace",
    "Item",
    "JobRun",
    "Capacity",
    "admin",
    "anomaly_detector",
    "apache_airflow_job",
    "copy_job",
    "cosmos_db_database",
    "data_pipeline",
    "dataflow",
    "digital_twin_builder",
    "digital_twin_builder_flow",
    "environment",
    "event_schema_set",
    "eventhouse",
    "eventstream",
    "graph_model",
    "graph_query_set",
    "graphql_api",
    "kql_dashboard",
    "kql_database",
    "kql_queryset",
    "lakehouse",
    "map",
    "mirrored_azure_databricks_catalog",
    "mirrored_database",
    "ml_experiment",
    "ml_model",
    "mounted_data_factory",
    "notebook",
    "ontology",
    "operations_agent",
    "paginated_report",
    "platform",
    "real_time_intelligence",
    "reflex",
    "report",
    "semantic_model",
    "snowflake_database",
    "spark",
    "spark_job_definition",
    "sql_database",
    "sql_endpoint",
    "user_data_function",
    "variable_library",
    "warehouse",
    "warehouse_snapshot",
]
