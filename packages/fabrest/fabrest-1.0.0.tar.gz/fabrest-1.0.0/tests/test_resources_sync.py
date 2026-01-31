import pytest

from fabrest import routes
from fabrest.resources import (
    AdminResource,
    AnomalyDetectorsResource,
    ApacheAirflowJobsResource,
    CapacityResource,
    CopyJobsResource,
    CosmosDbDatabasesResource,
    DashboardsResource,
    DataflowsResource,
    DataPipelinesResource,
    DatamartsResource,
    DigitalTwinBuildersResource,
    DigitalTwinBuilderFlowsResource,
    EnvironmentsResource,
    EventSchemaSetsResource,
    EventhousesResource,
    EventstreamsResource,
    GraphModelsResource,
    GraphQuerySetsResource,
    GraphQLApisResource,
    ItemsResource,
    JobsResource,
    KQLDashboardsResource,
    KQLDatabasesResource,
    KQLQuerysetsResource,
    LakehousesResource,
    MapsResource,
    MirroredAzureDatabricksCatalogsResource,
    MLExperimentsResource,
    MLModelsResource,
    MirroredDatabasesResource,
    MirroredWarehousesResource,
    MountedDataFactoriesResource,
    NotebooksResource,
    OperationsAgentsResource,
    OntologiesResource,
    PaginatedReportsResource,
    ReflexesResource,
    ReportsResource,
    SemanticModelsResource,
    SnowflakeDatabasesResource,
    SparkJobDefinitionsResource,
    SQLDatabasesResource,
    SQLEndpointsResource,
    UserDataFunctionsResource,
    VariableLibrariesResource,
    WarehousesResource,
    WarehouseSnapshotsResource,
    WorkspaceResource,
    WorkspacesResource,
)


class DummyResponse:
    def __init__(self, json_data=None):
        self._json_data = json_data or {}

    def json(self):
        return self._json_data


class DummyTransport:
    def __init__(self, json_data=None):
        self._json_data = json_data or {}
        self.calls = []
        self.invokes = []

    def request(self, **kwargs):
        self.calls.append(kwargs)
        return DummyResponse(self._json_data)

    def invoke(self, **kwargs):
        self.invokes.append(kwargs)
        return DummyResponse(self._json_data)

    @property
    def last_call(self):
        return self.calls[-1]

    @property
    def last_invoke(self):
        return self.invokes[-1]


ITEM_TYPE_RESOURCES = [
    AnomalyDetectorsResource,
    ApacheAirflowJobsResource,
    CopyJobsResource,
    CosmosDbDatabasesResource,
    DashboardsResource,
    DataflowsResource,
    DataPipelinesResource,
    DatamartsResource,
    DigitalTwinBuildersResource,
    DigitalTwinBuilderFlowsResource,
    EnvironmentsResource,
    EventSchemaSetsResource,
    EventhousesResource,
    EventstreamsResource,
    GraphModelsResource,
    GraphQuerySetsResource,
    GraphQLApisResource,
    KQLDashboardsResource,
    KQLDatabasesResource,
    KQLQuerysetsResource,
    LakehousesResource,
    MapsResource,
    MirroredAzureDatabricksCatalogsResource,
    MLExperimentsResource,
    MLModelsResource,
    MirroredDatabasesResource,
    MirroredWarehousesResource,
    MountedDataFactoriesResource,
    NotebooksResource,
    OperationsAgentsResource,
    OntologiesResource,
    ReflexesResource,
    SemanticModelsResource,
    SnowflakeDatabasesResource,
    SparkJobDefinitionsResource,
    SQLDatabasesResource,
    SQLEndpointsResource,
    UserDataFunctionsResource,
    VariableLibrariesResource,
    WarehousesResource,
    WarehouseSnapshotsResource,
]


@pytest.mark.parametrize("resource_cls", ITEM_TYPE_RESOURCES)
def test_item_type_resource_list_calls_transport(resource_cls):
    transport = DummyTransport({"value": []})
    resource = resource_cls("workspace-id", transport=transport)

    result = resource.list()

    expected_url = routes.items("workspace-id", item_type=resource.item_type)
    call = transport.last_call
    assert result == []
    assert call["method"] == "GET"
    assert call["url"] == expected_url


def test_admin_list_calls_transport():
    transport = DummyTransport({"value": []})
    resource = AdminResource(transport=transport)

    result = resource.list("Workspace")

    call = transport.last_call
    assert result == []
    assert call["method"] == "GET"
    assert call["url"] == routes.admin("Workspace")


def test_capacity_list_calls_transport():
    transport = DummyTransport({"value": []})
    resource = CapacityResource(transport=transport)

    result = resource.list()

    call = transport.last_call
    assert result == []
    assert call["method"] == "GET"
    assert call["url"] == routes.capacities()


def test_workspaces_list_calls_transport():
    transport = DummyTransport({"value": []})
    resource = WorkspacesResource(transport=transport)

    result = resource.list()

    call = transport.last_call
    assert result == []
    assert call["method"] == "GET"
    assert call["url"] == routes.workspaces()


def test_paginated_reports_list_calls_transport():
    transport = DummyTransport({"value": []})
    resource = PaginatedReportsResource("workspace-id", transport=transport)

    result = resource.list()

    call = transport.last_call
    assert result == []
    assert call["method"] == "GET"
    assert call["url"] == routes.paginated_reports("workspace-id")


def test_reports_list_calls_transport():
    transport = DummyTransport({"value": []})
    resource = ReportsResource("workspace-id", transport=transport)

    result = resource.list()

    call = transport.last_call
    assert result == []
    assert call["method"] == "GET"
    assert call["url"] == routes.reports("workspace-id")


def test_items_create_calls_transport_with_item_type():
    transport = DummyTransport({})
    resource = ItemsResource("workspace-id", transport=transport)
    payload = {"displayName": "Lakehouse Item"}

    resource.create(payload, item_type="Lakehouse")

    call = transport.last_call
    assert call["method"] == "POST"
    assert call["url"] == routes.items("workspace-id", item_type="Lakehouse")
    assert call["json"] == payload


def test_items_update_definition_wraps_definition():
    transport = DummyTransport({})
    resource = ItemsResource("workspace-id", transport=transport)
    payload = {"definition": {"parts": []}}

    resource.update_definition("item-id", payload)

    call = transport.last_call
    assert call["method"] == "POST"
    assert call["url"] == routes.item_definition_update("workspace-id", "item-id")
    assert call["json"] == {"definition": payload["definition"]}


def test_jobs_run_uses_invoke():
    transport = DummyTransport({})
    resource = JobsResource(transport=transport)
    payload = {"run": True}

    resource.run("workspace-id", "item-id", "Execute", item_type="Dataflow", payload=payload)

    call = transport.last_invoke
    assert call["url"] == routes.job_instance(
        "workspace-id",
        "item-id",
        job_type="Execute",
        item_type="Dataflow",
    )
    assert call["json"] == payload


def test_jobs_cancel_calls_transport():
    transport = DummyTransport({})
    resource = JobsResource(transport=transport)
    payload = {"reason": "stop"}

    resource.cancel("workspace-id", "item-id", "job-id", item_type="Dataflow", payload=payload)

    call = transport.last_call
    expected_url = f"{routes.job_instance('workspace-id', 'item-id', item_type='Dataflow', job_id='job-id')}/cancel"
    assert call["method"] == "POST"
    assert call["url"] == expected_url
    assert call["json"] == payload


def test_workspace_resource_exposes_items():
    transport = DummyTransport({})
    resource = WorkspaceResource("workspace-id", transport=transport)

    items_resource = resource.items

    assert isinstance(items_resource, ItemsResource)
    assert items_resource.workspace_id == "workspace-id"

