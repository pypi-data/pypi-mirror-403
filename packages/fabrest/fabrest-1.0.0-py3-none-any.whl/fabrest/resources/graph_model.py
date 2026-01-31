from typing import Any, Dict, Optional

import aiohttp
import requests

from .. import routes
from ..api.constant import ItemType, JobType
from ..models import graph_model as graph_model_models
from ..transport import RequestOptions
from .item_type_base import ItemTypeResource


class GraphModelsResource(ItemTypeResource):
    def __init__(self, workspace_id: str, transport=None, async_transport=None, logger=None) -> None:
        super().__init__(
            workspace_id=workspace_id,
            item_type=ItemType.GraphModel,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )

    def execute_query(
        self,
        graph_model_id: str,
        payload: graph_model_models.ExecuteQueryRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.graph_model_execute_query(self.workspace_id, graph_model_id),
            json=payload,
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_execute_query(
        self,
        graph_model_id: str,
        payload: graph_model_models.ExecuteQueryRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.graph_model_execute_query(self.workspace_id, graph_model_id),
            json=payload,
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def get_queryable_graph_type(
        self,
        graph_model_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="GET",
            url=routes.graph_model_queryable_type(self.workspace_id, graph_model_id),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_get_queryable_graph_type(
        self,
        graph_model_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="GET",
            url=routes.graph_model_queryable_type(self.workspace_id, graph_model_id),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def run_refresh_graph(
        self,
        graph_model_id: str,
        payload: Optional[Dict[str, Any]] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.job_instances_for_type(
                self.workspace_id,
                graph_model_id,
                ItemType.GraphModel,
                JobType.RefreshGraph,
            ),
            json=payload,
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_run_refresh_graph(
        self,
        graph_model_id: str,
        payload: Optional[Dict[str, Any]] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.job_instances_for_type(
                self.workspace_id,
                graph_model_id,
                ItemType.GraphModel,
                JobType.RefreshGraph,
            ),
            json=payload,
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)
