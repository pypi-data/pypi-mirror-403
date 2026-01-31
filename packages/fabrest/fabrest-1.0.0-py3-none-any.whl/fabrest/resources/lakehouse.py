from dataclasses import replace
from typing import Any, Dict, List, Optional

import aiohttp
import requests

from .. import routes
from ..api.constant import ItemType
from ..models import lakehouse as lakehouse_models
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


class LakehousesResource(ItemTypeResource):
    def __init__(self, workspace_id: str, transport=None, async_transport=None, logger=None) -> None:
        super().__init__(
            workspace_id=workspace_id,
            item_type=ItemType.Lakehouse,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )

    def list_tables(
        self,
        lakehouse_id: str,
        max_results: Optional[int] = None,
        continuation_token: Optional[str] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {}
        if max_results is not None:
            params["maxResults"] = max_results
        if continuation_token:
            params["continuationToken"] = continuation_token
        opts = _apply_params(options, params)
        response = self._require_transport().request(
            method="GET",
            url=routes.lakehouse_tables(self.workspace_id, lakehouse_id),
            options=opts,
            session=session,
        )
        data = self._handle_response(response, opts)
        return self._extract_list(data)

    async def async_list_tables(
        self,
        lakehouse_id: str,
        max_results: Optional[int] = None,
        continuation_token: Optional[str] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {}
        if max_results is not None:
            params["maxResults"] = max_results
        if continuation_token:
            params["continuationToken"] = continuation_token
        opts = _apply_params(options, params)
        response = await self._require_async_transport().request(
            method="GET",
            url=routes.lakehouse_tables(self.workspace_id, lakehouse_id),
            options=opts,
            session=session,
        )
        data = await self._handle_response_async(response, opts)
        return self._extract_list(data)

    def load_table(
        self,
        lakehouse_id: str,
        table_name: str,
        payload: lakehouse_models.LoadTableRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.lakehouse_table_load(self.workspace_id, lakehouse_id, table_name),
            json=payload,
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_load_table(
        self,
        lakehouse_id: str,
        table_name: str,
        payload: lakehouse_models.LoadTableRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.lakehouse_table_load(self.workspace_id, lakehouse_id, table_name),
            json=payload,
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def run_table_maintenance(
        self,
        lakehouse_id: str,
        payload: lakehouse_models.RunOnDemandTableMaintenanceRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.lakehouse_table_maintenance_instances(self.workspace_id, lakehouse_id),
            json=payload,
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_run_table_maintenance(
        self,
        lakehouse_id: str,
        payload: lakehouse_models.RunOnDemandTableMaintenanceRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.lakehouse_table_maintenance_instances(self.workspace_id, lakehouse_id),
            json=payload,
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def run_refresh_materialized_lake_views(
        self,
        lakehouse_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.lakehouse_refresh_mlv_instances(self.workspace_id, lakehouse_id),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_run_refresh_materialized_lake_views(
        self,
        lakehouse_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.lakehouse_refresh_mlv_instances(self.workspace_id, lakehouse_id),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def create_refresh_mlv_schedule(
        self,
        lakehouse_id: str,
        payload: lakehouse_models.CreateLakehouseRefreshMaterializedLakeViewsScheduleRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.lakehouse_refresh_mlv_schedules(self.workspace_id, lakehouse_id),
            json=payload,
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_create_refresh_mlv_schedule(
        self,
        lakehouse_id: str,
        payload: lakehouse_models.CreateLakehouseRefreshMaterializedLakeViewsScheduleRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.lakehouse_refresh_mlv_schedules(self.workspace_id, lakehouse_id),
            json=payload,
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def update_refresh_mlv_schedule(
        self,
        lakehouse_id: str,
        schedule_id: str,
        payload: lakehouse_models.UpdateLakehouseRefreshMaterializedLakeViewsScheduleRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="PATCH",
            url=routes.lakehouse_refresh_mlv_schedule(
                self.workspace_id, lakehouse_id, schedule_id
            ),
            json=payload,
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_update_refresh_mlv_schedule(
        self,
        lakehouse_id: str,
        schedule_id: str,
        payload: lakehouse_models.UpdateLakehouseRefreshMaterializedLakeViewsScheduleRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="PATCH",
            url=routes.lakehouse_refresh_mlv_schedule(
                self.workspace_id, lakehouse_id, schedule_id
            ),
            json=payload,
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def delete_refresh_mlv_schedule(
        self,
        lakehouse_id: str,
        schedule_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="DELETE",
            url=routes.lakehouse_refresh_mlv_schedule(
                self.workspace_id, lakehouse_id, schedule_id
            ),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_delete_refresh_mlv_schedule(
        self,
        lakehouse_id: str,
        schedule_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="DELETE",
            url=routes.lakehouse_refresh_mlv_schedule(
                self.workspace_id, lakehouse_id, schedule_id
            ),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def list_livy_sessions(
        self,
        lakehouse_id: str,
        continuation_token: Optional[str] = None,
        beta: Optional[bool] = None,
        submitted_date_time: Optional[str] = None,
        end_date_time: Optional[str] = None,
        submitter_id: Optional[str] = None,
        state: Optional[str] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {}
        if continuation_token:
            params["continuationToken"] = continuation_token
        if beta is not None:
            params["beta"] = beta
        if submitted_date_time:
            params["submittedDateTime"] = submitted_date_time
        if end_date_time:
            params["endDateTime"] = end_date_time
        if submitter_id:
            params["submitter.Id"] = submitter_id
        if state:
            params["state"] = state
        opts = _apply_params(options, params)
        response = self._require_transport().request(
            method="GET",
            url=routes.lakehouse_livy_sessions(self.workspace_id, lakehouse_id),
            options=opts,
            session=session,
        )
        data = self._handle_response(response, opts)
        return self._extract_list(data)

    async def async_list_livy_sessions(
        self,
        lakehouse_id: str,
        continuation_token: Optional[str] = None,
        beta: Optional[bool] = None,
        submitted_date_time: Optional[str] = None,
        end_date_time: Optional[str] = None,
        submitter_id: Optional[str] = None,
        state: Optional[str] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {}
        if continuation_token:
            params["continuationToken"] = continuation_token
        if beta is not None:
            params["beta"] = beta
        if submitted_date_time:
            params["submittedDateTime"] = submitted_date_time
        if end_date_time:
            params["endDateTime"] = end_date_time
        if submitter_id:
            params["submitter.Id"] = submitter_id
        if state:
            params["state"] = state
        opts = _apply_params(options, params)
        response = await self._require_async_transport().request(
            method="GET",
            url=routes.lakehouse_livy_sessions(self.workspace_id, lakehouse_id),
            options=opts,
            session=session,
        )
        data = await self._handle_response_async(response, opts)
        return self._extract_list(data)

    def get_livy_session(
        self,
        lakehouse_id: str,
        livy_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="GET",
            url=routes.lakehouse_livy_session(self.workspace_id, lakehouse_id, livy_id),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_get_livy_session(
        self,
        lakehouse_id: str,
        livy_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="GET",
            url=routes.lakehouse_livy_session(self.workspace_id, lakehouse_id, livy_id),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)
