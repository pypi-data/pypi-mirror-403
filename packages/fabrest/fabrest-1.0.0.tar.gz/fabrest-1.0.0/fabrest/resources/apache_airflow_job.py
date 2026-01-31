from dataclasses import replace
from typing import Any, Dict, List, Optional

import aiohttp
import requests

from .. import routes
from ..api.constant import ItemType
from ..models import apache_airflow_job as apache_airflow_job_models
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


class ApacheAirflowJobsResource(ItemTypeResource):
    def __init__(self, workspace_id: str, transport=None, async_transport=None, logger=None) -> None:
        super().__init__(
            workspace_id=workspace_id,
            item_type=ItemType.ApacheAirflowJob,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )

    def list_files(
        self,
        job_id: str,
        beta: Optional[bool] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if beta is not None:
            params["beta"] = beta
        opts = _apply_params(options, params)
        response = self._require_transport().request(
            method="GET",
            url=routes.apache_airflow_job_files(self.workspace_id, job_id),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_list_files(
        self,
        job_id: str,
        beta: Optional[bool] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if beta is not None:
            params["beta"] = beta
        opts = _apply_params(options, params)
        response = await self._require_async_transport().request(
            method="GET",
            url=routes.apache_airflow_job_files(self.workspace_id, job_id),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def get_file(
        self,
        job_id: str,
        file_path: str,
        beta: Optional[bool] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if beta is not None:
            params["beta"] = beta
        opts = _apply_params(options, params)
        response = self._require_transport().request(
            method="GET",
            url=routes.apache_airflow_job_files(self.workspace_id, job_id, file_path),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_get_file(
        self,
        job_id: str,
        file_path: str,
        beta: Optional[bool] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if beta is not None:
            params["beta"] = beta
        opts = _apply_params(options, params)
        response = await self._require_async_transport().request(
            method="GET",
            url=routes.apache_airflow_job_files(self.workspace_id, job_id, file_path),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def update_file(
        self,
        job_id: str,
        file_path: str,
        payload: Dict[str, Any],
        beta: Optional[bool] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if beta is not None:
            params["beta"] = beta
        opts = _apply_params(options, params)
        response = self._require_transport().request(
            method="PUT",
            url=routes.apache_airflow_job_files(self.workspace_id, job_id, file_path),
            json=payload,
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_update_file(
        self,
        job_id: str,
        file_path: str,
        payload: Dict[str, Any],
        beta: Optional[bool] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if beta is not None:
            params["beta"] = beta
        opts = _apply_params(options, params)
        response = await self._require_async_transport().request(
            method="PUT",
            url=routes.apache_airflow_job_files(self.workspace_id, job_id, file_path),
            json=payload,
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def delete_file(
        self,
        job_id: str,
        file_path: str,
        beta: Optional[bool] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if beta is not None:
            params["beta"] = beta
        opts = _apply_params(options, params)
        response = self._require_transport().request(
            method="DELETE",
            url=routes.apache_airflow_job_files(self.workspace_id, job_id, file_path),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_delete_file(
        self,
        job_id: str,
        file_path: str,
        beta: Optional[bool] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if beta is not None:
            params["beta"] = beta
        opts = _apply_params(options, params)
        response = await self._require_async_transport().request(
            method="DELETE",
            url=routes.apache_airflow_job_files(self.workspace_id, job_id, file_path),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def list_pool_templates(
        self,
        beta: Optional[bool] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if beta is not None:
            params["beta"] = beta
        opts = _apply_params(options, params)
        response = self._require_transport().request(
            method="GET",
            url=routes.apache_airflow_job_pool_templates(self.workspace_id),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_list_pool_templates(
        self,
        beta: Optional[bool] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if beta is not None:
            params["beta"] = beta
        opts = _apply_params(options, params)
        response = await self._require_async_transport().request(
            method="GET",
            url=routes.apache_airflow_job_pool_templates(self.workspace_id),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def get_pool_template(
        self,
        pool_template_id: str,
        beta: Optional[bool] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if beta is not None:
            params["beta"] = beta
        opts = _apply_params(options, params)
        response = self._require_transport().request(
            method="GET",
            url=routes.apache_airflow_job_pool_templates(self.workspace_id, pool_template_id),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_get_pool_template(
        self,
        pool_template_id: str,
        beta: Optional[bool] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if beta is not None:
            params["beta"] = beta
        opts = _apply_params(options, params)
        response = await self._require_async_transport().request(
            method="GET",
            url=routes.apache_airflow_job_pool_templates(self.workspace_id, pool_template_id),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def create_pool_template(
        self,
        payload: apache_airflow_job_models.CreateAirflowPoolTemplateRequest,
        beta: Optional[bool] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if beta is not None:
            params["beta"] = beta
        opts = _apply_params(options, params)
        response = self._require_transport().request(
            method="POST",
            url=routes.apache_airflow_job_pool_templates(self.workspace_id),
            json=payload,
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_create_pool_template(
        self,
        payload: apache_airflow_job_models.CreateAirflowPoolTemplateRequest,
        beta: Optional[bool] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if beta is not None:
            params["beta"] = beta
        opts = _apply_params(options, params)
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.apache_airflow_job_pool_templates(self.workspace_id),
            json=payload,
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def delete_pool_template(
        self,
        pool_template_id: str,
        beta: Optional[bool] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if beta is not None:
            params["beta"] = beta
        opts = _apply_params(options, params)
        response = self._require_transport().request(
            method="DELETE",
            url=routes.apache_airflow_job_pool_templates(self.workspace_id, pool_template_id),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_delete_pool_template(
        self,
        pool_template_id: str,
        beta: Optional[bool] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if beta is not None:
            params["beta"] = beta
        opts = _apply_params(options, params)
        response = await self._require_async_transport().request(
            method="DELETE",
            url=routes.apache_airflow_job_pool_templates(self.workspace_id, pool_template_id),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def get_settings(
        self,
        beta: Optional[bool] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if beta is not None:
            params["beta"] = beta
        opts = _apply_params(options, params)
        response = self._require_transport().request(
            method="GET",
            url=routes.apache_airflow_job_settings(self.workspace_id),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_get_settings(
        self,
        beta: Optional[bool] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if beta is not None:
            params["beta"] = beta
        opts = _apply_params(options, params)
        response = await self._require_async_transport().request(
            method="GET",
            url=routes.apache_airflow_job_settings(self.workspace_id),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def update_settings(
        self,
        payload: apache_airflow_job_models.UpdateAirflowWorkspaceSettingsRequest,
        beta: Optional[bool] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if beta is not None:
            params["beta"] = beta
        opts = _apply_params(options, params)
        response = self._require_transport().request(
            method="PATCH",
            url=routes.apache_airflow_job_settings(self.workspace_id),
            json=payload,
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_update_settings(
        self,
        payload: apache_airflow_job_models.UpdateAirflowWorkspaceSettingsRequest,
        beta: Optional[bool] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if beta is not None:
            params["beta"] = beta
        opts = _apply_params(options, params)
        response = await self._require_async_transport().request(
            method="PATCH",
            url=routes.apache_airflow_job_settings(self.workspace_id),
            json=payload,
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)
