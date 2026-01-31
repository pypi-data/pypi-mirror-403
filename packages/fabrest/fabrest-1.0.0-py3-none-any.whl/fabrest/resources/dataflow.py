from dataclasses import replace
from typing import Any, Dict, Optional

import aiohttp
import requests

from .. import routes
from ..api.constant import ItemType, JobType
from ..models import dataflow as dataflow_models
from ..transport import RequestOptions
from .item_type_base import ItemTypeResource


def _apply_params(
    options: Optional[RequestOptions], params: Optional[Dict[str, Any]]
) -> RequestOptions:
    if not params:
        return options or RequestOptions()
    if options:
        merged = {**(options.params or {}), **params}
        return replace(options, params=merged)
    return RequestOptions(params=params)


class DataflowsResource(ItemTypeResource):
    def __init__(self, workspace_id: str, transport=None, async_transport=None, logger=None) -> None:
        super().__init__(
            workspace_id=workspace_id,
            item_type=ItemType.Dataflow,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )

    def execute_query(
        self,
        dataflow_id: str,
        payload: dataflow_models.ExecuteQueryRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.dataflow_execute_query(self.workspace_id, dataflow_id),
            json=payload,
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_execute_query(
        self,
        dataflow_id: str,
        payload: dataflow_models.ExecuteQueryRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.dataflow_execute_query(self.workspace_id, dataflow_id),
            json=payload,
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def list_parameters(
        self,
        dataflow_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="GET",
            url=routes.dataflow_parameters(self.workspace_id, dataflow_id),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_list_parameters(
        self,
        dataflow_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="GET",
            url=routes.dataflow_parameters(self.workspace_id, dataflow_id),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def run_apply_changes(
        self,
        dataflow_id: str,
        payload: Optional[dataflow_models.RunOnDemandDataflowExecuteJobRequest] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.job_instances_for_type(
                self.workspace_id, dataflow_id, ItemType.Dataflow, JobType.ApplyChange
            ),
            json=payload,
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_run_apply_changes(
        self,
        dataflow_id: str,
        payload: Optional[dataflow_models.RunOnDemandDataflowExecuteJobRequest] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.job_instances_for_type(
                self.workspace_id, dataflow_id, ItemType.Dataflow, JobType.ApplyChange
            ),
            json=payload,
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def run_execute(
        self,
        dataflow_id: str,
        payload: Optional[dataflow_models.RunOnDemandDataflowExecuteJobRequest] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.job_instances_for_type(
                self.workspace_id, dataflow_id, ItemType.Dataflow, JobType.Execute
            ),
            json=payload,
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_run_execute(
        self,
        dataflow_id: str,
        payload: Optional[dataflow_models.RunOnDemandDataflowExecuteJobRequest] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.job_instances_for_type(
                self.workspace_id, dataflow_id, ItemType.Dataflow, JobType.Execute
            ),
            json=payload,
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def create_apply_changes_schedule(
        self,
        dataflow_id: str,
        payload: dataflow_models.CreateDataflowApplyChangesScheduleRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.job_schedule(
                self.workspace_id, dataflow_id, ItemType.Dataflow, JobType.ApplyChange
            ),
            json=payload,
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_create_apply_changes_schedule(
        self,
        dataflow_id: str,
        payload: dataflow_models.CreateDataflowApplyChangesScheduleRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.job_schedule(
                self.workspace_id, dataflow_id, ItemType.Dataflow, JobType.ApplyChange
            ),
            json=payload,
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def create_execute_schedule(
        self,
        dataflow_id: str,
        payload: dataflow_models.CreateDataflowExecuteScheduleRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.job_schedule(
                self.workspace_id, dataflow_id, ItemType.Dataflow, JobType.Execute
            ),
            json=payload,
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_create_execute_schedule(
        self,
        dataflow_id: str,
        payload: dataflow_models.CreateDataflowExecuteScheduleRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.job_schedule(
                self.workspace_id, dataflow_id, ItemType.Dataflow, JobType.Execute
            ),
            json=payload,
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)
