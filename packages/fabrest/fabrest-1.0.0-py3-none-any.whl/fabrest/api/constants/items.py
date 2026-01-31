from typing import Literal


ITEM_TYPES = {
    "Item": "items",
    "AnomalyDetector": "anomalydetectors",
    "ApacheAirflowJob": "ApacheAirflowJobs",
    "CosmosDbDatabase": "cosmosDbDatabases",
    "CopyJob": "copyJobs",
    "Dashboard": "dashboards",
    "Dataflow": "dataflows",
    "DataPipeline": "dataPipelines",
    "Datamart": "datamarts",
    "DigitalTwinBuilder": "digitaltwinbuilders",
    "DigitalTwinBuilderFlow": "DigitalTwinBuilderFlows",
    "Environment": "environments",
    "Eventhouse": "eventhouses",
    "EventSchemaSet": "eventSchemaSets",
    "Eventstream": "eventstreams",
    "GraphModel": "GraphModels",
    "GraphQuerySet": "GraphQuerySets",
    "GraphQLApi": "GraphQLApis",
    "KQLDashboard": "kqlDashboards",
    "KQLDatabase": "kqlDatabases",
    "KQLQueryset": "kqlQuerysets",
    "Lakehouse": "lakehouses",
    "Map": "Maps",
    "MLExperiment": "mlExperiments",
    "MLModel": "mlModels",
    "MirroredAzureDatabricksCatalog": "mirroredAzureDatabricksCatalogs",
    "MirroredDatabase": "mirroredDatabases",
    "MirroredWarehouse": "mirroredWarehouses",
    "MountedDataFactory": "mountedDataFactories",
    "Notebook": "notebooks",
    "OperationsAgent": "OperationsAgents",
    "Ontology": "ontologies",
    "PaginatedReport": "paginatedReports",
    "Reflex": "reflexes",
    "Report": "reports",
    "SQLDatabase": "SQLDatabases",
    "SQLEndpoint": "sqlEndpoints",
    "SemanticModel": "semanticModels",
    "SnowflakeDatabase": "snowflakeDatabases",
    "SparkJobDefinition": "sparkJobDefinitions",
    "UserDataFunction": "UserDataFunctions",
    "VariableLibrary": "VariableLibraries",
    "Warehouse": "warehouses",
    "WarehouseSnapshot": "warehousesnapshots",
}

ITEM_COLLECTIONS = {
    "Job": "jobs",
    "Shortcut": "shortcuts",
    "DataAccessRole": "dataAccessRoles",
    "ExternalDataShare": "externalDataShares",
}

EXTERNAL_DATA_SHARE_OPERATIONS = {
    "Revoke": "revoke",
}

TAG_OPERATIONS = {
    "ApplyTag": "applyTags",
    "UnapplyTag": "unapplyTags",
}

ItemTypeLiteral = Literal[
    "items",
    "anomalydetectors",
    "ApacheAirflowJobs",
    "cosmosDbDatabases",
    "copyJobs",
    "dashboards",
    "dataflows",
    "dataPipelines",
    "datamarts",
    "digitaltwinbuilders",
    "DigitalTwinBuilderFlows",
    "environments",
    "eventhouses",
    "eventSchemaSets",
    "eventstreams",
    "GraphModels",
    "GraphQuerySets",
    "GraphQLApis",
    "kqlDashboards",
    "kqlDatabases",
    "kqlQuerysets",
    "lakehouses",
    "Maps",
    "mlExperiments",
    "mlModels",
    "mirroredAzureDatabricksCatalogs",
    "mirroredDatabases",
    "mirroredWarehouses",
    "mountedDataFactories",
    "notebooks",
    "OperationsAgents",
    "ontologies",
    "paginatedReports",
    "reflexes",
    "reports",
    "SQLDatabases",
    "sqlEndpoints",
    "semanticModels",
    "snowflakeDatabases",
    "sparkJobDefinitions",
    "UserDataFunctions",
    "VariableLibraries",
    "warehouses",
    "warehousesnapshots",
]


class ItemType:
    Item = ITEM_TYPES["Item"]
    AnomalyDetector = ITEM_TYPES["AnomalyDetector"]
    ApacheAirflowJob = ITEM_TYPES["ApacheAirflowJob"]
    CosmosDbDatabase = ITEM_TYPES["CosmosDbDatabase"]
    CopyJob = ITEM_TYPES["CopyJob"]
    Dashboard = ITEM_TYPES["Dashboard"]
    Dataflow = ITEM_TYPES["Dataflow"]
    DataPipeline = ITEM_TYPES["DataPipeline"]
    Datamart = ITEM_TYPES["Datamart"]
    DigitalTwinBuilder = ITEM_TYPES["DigitalTwinBuilder"]
    DigitalTwinBuilderFlow = ITEM_TYPES["DigitalTwinBuilderFlow"]
    Environment = ITEM_TYPES["Environment"]
    Eventhouse = ITEM_TYPES["Eventhouse"]
    EventSchemaSet = ITEM_TYPES["EventSchemaSet"]
    Eventstream = ITEM_TYPES["Eventstream"]
    GraphModel = ITEM_TYPES["GraphModel"]
    GraphQuerySet = ITEM_TYPES["GraphQuerySet"]
    GraphQLApi = ITEM_TYPES["GraphQLApi"]
    KQLDashboard = ITEM_TYPES["KQLDashboard"]
    KQLDatabase = ITEM_TYPES["KQLDatabase"]
    KQLQueryset = ITEM_TYPES["KQLQueryset"]
    Lakehouse = ITEM_TYPES["Lakehouse"]
    Map = ITEM_TYPES["Map"]
    MLExperiment = ITEM_TYPES["MLExperiment"]
    MLModel = ITEM_TYPES["MLModel"]
    MirroredAzureDatabricksCatalog = ITEM_TYPES["MirroredAzureDatabricksCatalog"]
    MirroredDatabase = ITEM_TYPES["MirroredDatabase"]
    MirroredWarehouse = ITEM_TYPES["MirroredWarehouse"]
    MountedDataFactory = ITEM_TYPES["MountedDataFactory"]
    Notebook = ITEM_TYPES["Notebook"]
    OperationsAgent = ITEM_TYPES["OperationsAgent"]
    Ontology = ITEM_TYPES["Ontology"]
    PaginatedReport = ITEM_TYPES["PaginatedReport"]
    Reflex = ITEM_TYPES["Reflex"]
    Report = ITEM_TYPES["Report"]
    SQLDatabase = ITEM_TYPES["SQLDatabase"]
    SQLEndpoint = ITEM_TYPES["SQLEndpoint"]
    SemanticModel = ITEM_TYPES["SemanticModel"]
    SnowflakeDatabase = ITEM_TYPES["SnowflakeDatabase"]
    SparkJobDefinition = ITEM_TYPES["SparkJobDefinition"]
    UserDataFunction = ITEM_TYPES["UserDataFunction"]
    VariableLibrary = ITEM_TYPES["VariableLibrary"]
    Warehouse = ITEM_TYPES["Warehouse"]
    WarehouseSnapshot = ITEM_TYPES["WarehouseSnapshot"]


class ItemCollection:
    Job = ITEM_COLLECTIONS["Job"]
    Shortcut = ITEM_COLLECTIONS["Shortcut"]
    DataAccessRole = ITEM_COLLECTIONS["DataAccessRole"]
    ExternalDataShare = ITEM_COLLECTIONS["ExternalDataShare"]


class ExternalDataShareOperation:
    Revoke = EXTERNAL_DATA_SHARE_OPERATIONS["Revoke"]


class TagOperation:
    ApplyTag = TAG_OPERATIONS["ApplyTag"]
    UnapplyTag = TAG_OPERATIONS["UnapplyTag"]
