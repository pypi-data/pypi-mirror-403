from dataclasses import replace
from typing import Any, Dict, Optional

import aiohttp
import requests

from .. import routes
from ..api.constant import ItemType, JobType
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


class SparkJobDefinitionsResource(ItemTypeResource):
    def __init__(self, workspace_id: str, transport=None, async_transport=None, logger=None) -> None:
        super().__init__(
            workspace_id=workspace_id,
            item_type=ItemType.SparkJobDefinition,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )

    def run_spark_job(
        self,
        spark_job_definition_id: str,
        payload: Optional[Dict[str, Any]] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> list:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.job_instances_for_type(
                self.workspace_id,
                spark_job_definition_id,
                ItemType.SparkJobDefinition,
                JobType.SparkJobDefinition,
            ),
            json=payload,
            options=opts,
            session=session,
        )
        data = self._handle_response(response, opts)
        return self._extract_list(data)

    async def async_run_spark_job(
        self,
        spark_job_definition_id: str,
        payload: Optional[Dict[str, Any]] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> list:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.job_instances_for_type(
                self.workspace_id,
                spark_job_definition_id,
                ItemType.SparkJobDefinition,
                JobType.SparkJobDefinition,
            ),
            json=payload,
            options=opts,
            session=session,
        )
        data = await self._handle_response_async(response, opts)
        return self._extract_list(data)

    def list_livy_sessions(
        self,
        spark_job_definition_id: str,
        continuation_token: Optional[str] = None,
        beta: Optional[bool] = None,
        submitted_date_time: Optional[str] = None,
        end_date_time: Optional[str] = None,
        submitter_id: Optional[str] = None,
        state: Optional[str] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
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
            url=routes.spark_job_definition_livy_sessions(
                self.workspace_id, spark_job_definition_id
            ),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_list_livy_sessions(
        self,
        spark_job_definition_id: str,
        continuation_token: Optional[str] = None,
        beta: Optional[bool] = None,
        submitted_date_time: Optional[str] = None,
        end_date_time: Optional[str] = None,
        submitter_id: Optional[str] = None,
        state: Optional[str] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
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
            url=routes.spark_job_definition_livy_sessions(
                self.workspace_id, spark_job_definition_id
            ),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def get_livy_session(
        self,
        spark_job_definition_id: str,
        livy_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="GET",
            url=routes.spark_job_definition_livy_session(
                self.workspace_id, spark_job_definition_id, livy_id
            ),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_get_livy_session(
        self,
        spark_job_definition_id: str,
        livy_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="GET",
            url=routes.spark_job_definition_livy_session(
                self.workspace_id, spark_job_definition_id, livy_id
            ),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)
