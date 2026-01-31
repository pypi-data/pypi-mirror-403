from typing import Any, Dict, List, Optional

import aiohttp
import requests

from .. import routes
from ..models import Workspace
from ..models import platform as platform_models
from ..transport import RequestOptions
from .base import ResourceBase
from .anomaly_detector import AnomalyDetectorsResource
from .apache_airflow_job import ApacheAirflowJobsResource
from .copy_job import CopyJobsResource
from .cosmos_db_database import CosmosDbDatabasesResource
from .dashboard import DashboardsResource
from .dataflow import DataflowsResource
from .data_pipeline import DataPipelinesResource
from .datamart import DatamartsResource
from .digital_twin_builder import DigitalTwinBuildersResource
from .digital_twin_builder_flow import DigitalTwinBuilderFlowsResource
from .environment import EnvironmentsResource
from .event_schema_set import EventSchemaSetsResource
from .eventhouse import EventhousesResource
from .eventstream import EventstreamsResource
from .graph_model import GraphModelsResource
from .graph_query_set import GraphQuerySetsResource
from .graphql_api import GraphQLApisResource
from .items import ItemsResource
from .kql_dashboard import KQLDashboardsResource
from .kql_database import KQLDatabasesResource
from .kql_queryset import KQLQuerysetsResource
from .lakehouse import LakehousesResource
from .map import MapsResource
from .mirrored_azure_databricks_catalog import MirroredAzureDatabricksCatalogsResource
from .ml_experiment import MLExperimentsResource
from .ml_model import MLModelsResource
from .mirrored_database import MirroredDatabasesResource
from .mirrored_warehouse import MirroredWarehousesResource
from .mounted_data_factory import MountedDataFactoriesResource
from .notebook import NotebooksResource
from .operations_agent import OperationsAgentsResource
from .ontology import OntologiesResource
from .paginated_report import PaginatedReportsResource
from .reflex import ReflexesResource
from .report import ReportsResource
from .semantic_model import SemanticModelsResource
from .snowflake_database import SnowflakeDatabasesResource
from .spark_job_definition import SparkJobDefinitionsResource
from .sql_database import SQLDatabasesResource
from .sql_endpoint import SQLEndpointsResource
from .user_data_function import UserDataFunctionsResource
from .variable_library import VariableLibrariesResource
from .warehouse import WarehousesResource
from .warehouse_snapshot import WarehouseSnapshotsResource


class WorkspacesResource(ResourceBase):
    def list(
        self,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> List[Workspace]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="GET",
            url=routes.workspaces(),
            options=opts,
            session=session,
        )
        data = self._handle_response(response, opts)
        return self._extract_list(data)

    async def async_list(
        self,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> List[Workspace]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="GET",
            url=routes.workspaces(),
            options=opts,
            session=session,
        )
        data = await self._handle_response_async(response, opts)
        return self._extract_list(data)

    def get(
        self,
        workspace_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Workspace:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="GET",
            url=routes.workspace(workspace_id),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_get(
        self,
        workspace_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Workspace:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="GET",
            url=routes.workspace(workspace_id),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def create(
        self,
        payload: platform_models.CreateWorkspaceRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Workspace:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.workspaces(),
            json=payload,
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_create(
        self,
        payload: platform_models.CreateWorkspaceRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Workspace:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.workspaces(),
            json=payload,
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def update(
        self,
        workspace_id: str,
        payload: platform_models.UpdateWorkspaceRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Workspace:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="PATCH",
            url=routes.workspace(workspace_id),
            json=payload,
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_update(
        self,
        workspace_id: str,
        payload: platform_models.UpdateWorkspaceRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Workspace:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="PATCH",
            url=routes.workspace(workspace_id),
            json=payload,
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def delete(
        self,
        workspace_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="DELETE",
            url=routes.workspace(workspace_id),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_delete(
        self,
        workspace_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="DELETE",
            url=routes.workspace(workspace_id),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)


class WorkspaceResource(ResourceBase):
    def __init__(
        self,
        workspace_id: str,
        transport=None,
        async_transport=None,
        logger=None,
    ) -> None:
        super().__init__(transport=transport, async_transport=async_transport, logger=logger)
        self.workspace_id = workspace_id
        self._items = ItemsResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._anomaly_detectors = AnomalyDetectorsResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._apache_airflow_jobs = ApacheAirflowJobsResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._copy_jobs = CopyJobsResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._cosmos_db_databases = CosmosDbDatabasesResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._dashboards = DashboardsResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._dataflows = DataflowsResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._data_pipelines = DataPipelinesResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._datamarts = DatamartsResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._digital_twin_builders = DigitalTwinBuildersResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._digital_twin_builder_flows = DigitalTwinBuilderFlowsResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._environments = EnvironmentsResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._event_schema_sets = EventSchemaSetsResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._eventhouses = EventhousesResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._eventstreams = EventstreamsResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._graph_models = GraphModelsResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._graph_query_sets = GraphQuerySetsResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._graphql_apis = GraphQLApisResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._kql_dashboards = KQLDashboardsResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._kql_databases = KQLDatabasesResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._kql_querysets = KQLQuerysetsResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._lakehouses = LakehousesResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._maps = MapsResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._mirrored_azure_databricks_catalogs = MirroredAzureDatabricksCatalogsResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._ml_experiments = MLExperimentsResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._ml_models = MLModelsResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._mirrored_databases = MirroredDatabasesResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._mirrored_warehouses = MirroredWarehousesResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._mounted_data_factories = MountedDataFactoriesResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._notebooks = NotebooksResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._operations_agents = OperationsAgentsResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._ontologies = OntologiesResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._reports = ReportsResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._paginated_reports = PaginatedReportsResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._reflexes = ReflexesResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._semantic_models = SemanticModelsResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._snowflake_databases = SnowflakeDatabasesResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._spark_job_definitions = SparkJobDefinitionsResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._sql_databases = SQLDatabasesResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._sql_endpoints = SQLEndpointsResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._user_data_functions = UserDataFunctionsResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._variable_libraries = VariableLibrariesResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._warehouses = WarehousesResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
        self._warehouse_snapshots = WarehouseSnapshotsResource(
            workspace_id=workspace_id,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )

    @property
    def items(self) -> ItemsResource:
        return self._items

    @property
    def anomaly_detectors(self) -> AnomalyDetectorsResource:
        return self._anomaly_detectors

    @property
    def apache_airflow_jobs(self) -> ApacheAirflowJobsResource:
        return self._apache_airflow_jobs

    @property
    def copy_jobs(self) -> CopyJobsResource:
        return self._copy_jobs

    @property
    def cosmos_db_databases(self) -> CosmosDbDatabasesResource:
        return self._cosmos_db_databases

    @property
    def dashboards(self) -> DashboardsResource:
        return self._dashboards

    @property
    def dataflows(self) -> DataflowsResource:
        return self._dataflows

    @property
    def data_pipelines(self) -> DataPipelinesResource:
        return self._data_pipelines

    @property
    def datamarts(self) -> DatamartsResource:
        return self._datamarts

    @property
    def digital_twin_builders(self) -> DigitalTwinBuildersResource:
        return self._digital_twin_builders

    @property
    def digital_twin_builder_flows(self) -> DigitalTwinBuilderFlowsResource:
        return self._digital_twin_builder_flows

    @property
    def environments(self) -> EnvironmentsResource:
        return self._environments

    @property
    def event_schema_sets(self) -> EventSchemaSetsResource:
        return self._event_schema_sets

    @property
    def eventhouses(self) -> EventhousesResource:
        return self._eventhouses

    @property
    def eventstreams(self) -> EventstreamsResource:
        return self._eventstreams

    @property
    def graph_models(self) -> GraphModelsResource:
        return self._graph_models

    @property
    def graph_query_sets(self) -> GraphQuerySetsResource:
        return self._graph_query_sets

    @property
    def graphql_apis(self) -> GraphQLApisResource:
        return self._graphql_apis

    @property
    def kql_dashboards(self) -> KQLDashboardsResource:
        return self._kql_dashboards

    @property
    def kql_databases(self) -> KQLDatabasesResource:
        return self._kql_databases

    @property
    def kql_querysets(self) -> KQLQuerysetsResource:
        return self._kql_querysets

    @property
    def lakehouses(self) -> LakehousesResource:
        return self._lakehouses

    @property
    def maps(self) -> MapsResource:
        return self._maps

    @property
    def mirrored_azure_databricks_catalogs(self) -> MirroredAzureDatabricksCatalogsResource:
        return self._mirrored_azure_databricks_catalogs

    @property
    def ml_experiments(self) -> MLExperimentsResource:
        return self._ml_experiments

    @property
    def ml_models(self) -> MLModelsResource:
        return self._ml_models

    @property
    def mirrored_databases(self) -> MirroredDatabasesResource:
        return self._mirrored_databases

    @property
    def mirrored_warehouses(self) -> MirroredWarehousesResource:
        return self._mirrored_warehouses

    @property
    def mounted_data_factories(self) -> MountedDataFactoriesResource:
        return self._mounted_data_factories

    @property
    def notebooks(self) -> NotebooksResource:
        return self._notebooks

    @property
    def operations_agents(self) -> OperationsAgentsResource:
        return self._operations_agents

    @property
    def ontologies(self) -> OntologiesResource:
        return self._ontologies

    @property
    def reports(self) -> ReportsResource:
        return self._reports

    @property
    def paginated_reports(self) -> PaginatedReportsResource:
        return self._paginated_reports

    @property
    def reflexes(self) -> ReflexesResource:
        return self._reflexes

    @property
    def semantic_models(self) -> SemanticModelsResource:
        return self._semantic_models

    @property
    def snowflake_databases(self) -> SnowflakeDatabasesResource:
        return self._snowflake_databases

    @property
    def spark_job_definitions(self) -> SparkJobDefinitionsResource:
        return self._spark_job_definitions

    @property
    def sql_databases(self) -> SQLDatabasesResource:
        return self._sql_databases

    @property
    def sql_endpoints(self) -> SQLEndpointsResource:
        return self._sql_endpoints

    @property
    def user_data_functions(self) -> UserDataFunctionsResource:
        return self._user_data_functions

    @property
    def variable_libraries(self) -> VariableLibrariesResource:
        return self._variable_libraries

    @property
    def warehouses(self) -> WarehousesResource:
        return self._warehouses

    @property
    def warehouse_snapshots(self) -> WarehouseSnapshotsResource:
        return self._warehouse_snapshots

    def items_for(self, item_type: str) -> ItemsResource:
        return ItemsResource(
            workspace_id=self.workspace_id,
            default_item_type=item_type,
            transport=self._transport,
            async_transport=self._async_transport,
            logger=self._logger,
        )
