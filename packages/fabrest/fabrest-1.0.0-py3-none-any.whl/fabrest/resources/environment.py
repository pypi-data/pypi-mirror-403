from dataclasses import replace
from typing import Any, Dict, Optional, Union

import aiohttp
import requests

from .. import routes
from ..api.constant import ItemType
from ..models import environment as environment_models
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


class EnvironmentsResource(ItemTypeResource):
    def __init__(self, workspace_id: str, transport=None, async_transport=None, logger=None) -> None:
        super().__init__(
            workspace_id=workspace_id,
            item_type=ItemType.Environment,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )

    def list_libraries(
        self,
        environment_id: str,
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
            url=routes.environment_libraries(self.workspace_id, environment_id),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_list_libraries(
        self,
        environment_id: str,
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
            url=routes.environment_libraries(self.workspace_id, environment_id),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def export_external_libraries(
        self,
        environment_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="GET",
            url=routes.environment_libraries_export(self.workspace_id, environment_id),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_export_external_libraries(
        self,
        environment_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="GET",
            url=routes.environment_libraries_export(self.workspace_id, environment_id),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def get_spark_compute(
        self,
        environment_id: str,
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
            url=routes.environment_spark_compute(self.workspace_id, environment_id),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_get_spark_compute(
        self,
        environment_id: str,
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
            url=routes.environment_spark_compute(self.workspace_id, environment_id),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def cancel_publish(
        self,
        environment_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.environment_staging_cancel_publish(self.workspace_id, environment_id),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_cancel_publish(
        self,
        environment_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.environment_staging_cancel_publish(self.workspace_id, environment_id),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def list_staging_libraries(
        self,
        environment_id: str,
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
            url=routes.environment_staging_libraries(self.workspace_id, environment_id),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_list_staging_libraries(
        self,
        environment_id: str,
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
            url=routes.environment_staging_libraries(self.workspace_id, environment_id),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def delete_staging_libraries(
        self,
        environment_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="DELETE",
            url=routes.environment_staging_libraries(self.workspace_id, environment_id),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_delete_staging_libraries(
        self,
        environment_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="DELETE",
            url=routes.environment_staging_libraries(self.workspace_id, environment_id),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def add_staging_library(
        self,
        environment_id: str,
        payload: Dict[str, Any],
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.environment_staging_libraries(self.workspace_id, environment_id),
            json=payload,
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_add_staging_library(
        self,
        environment_id: str,
        payload: Dict[str, Any],
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.environment_staging_libraries(self.workspace_id, environment_id),
            json=payload,
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def upsert_staging_library(
        self,
        environment_id: str,
        library_name: str,
        payload: Dict[str, Any],
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.environment_staging_library(
                self.workspace_id, environment_id, library_name
            ),
            json=payload,
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_upsert_staging_library(
        self,
        environment_id: str,
        library_name: str,
        payload: Dict[str, Any],
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.environment_staging_library(
                self.workspace_id, environment_id, library_name
            ),
            json=payload,
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def delete_staging_library(
        self,
        environment_id: str,
        library_name: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="DELETE",
            url=routes.environment_staging_library(
                self.workspace_id, environment_id, library_name
            ),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_delete_staging_library(
        self,
        environment_id: str,
        library_name: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="DELETE",
            url=routes.environment_staging_library(
                self.workspace_id, environment_id, library_name
            ),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def export_staging_external_libraries(
        self,
        environment_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="GET",
            url=routes.environment_staging_libraries_export(self.workspace_id, environment_id),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_export_staging_external_libraries(
        self,
        environment_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="GET",
            url=routes.environment_staging_libraries_export(self.workspace_id, environment_id),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def import_staging_external_libraries(
        self,
        environment_id: str,
        payload: Dict[str, Any],
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.environment_staging_libraries_import(self.workspace_id, environment_id),
            json=payload,
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_import_staging_external_libraries(
        self,
        environment_id: str,
        payload: Dict[str, Any],
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.environment_staging_libraries_import(self.workspace_id, environment_id),
            json=payload,
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def remove_staging_external_library(
        self,
        environment_id: str,
        payload: environment_models.RemoveExternalLibrariesRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.environment_staging_libraries_remove_external(
                self.workspace_id, environment_id
            ),
            json=payload,
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_remove_staging_external_library(
        self,
        environment_id: str,
        payload: environment_models.RemoveExternalLibrariesRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.environment_staging_libraries_remove_external(
                self.workspace_id, environment_id
            ),
            json=payload,
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def publish_staging(
        self,
        environment_id: str,
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
            url=routes.environment_staging_publish(self.workspace_id, environment_id),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_publish_staging(
        self,
        environment_id: str,
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
            url=routes.environment_staging_publish(self.workspace_id, environment_id),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def get_staging_spark_compute(
        self,
        environment_id: str,
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
            url=routes.environment_staging_spark_compute(self.workspace_id, environment_id),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_get_staging_spark_compute(
        self,
        environment_id: str,
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
            url=routes.environment_staging_spark_compute(self.workspace_id, environment_id),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def update_staging_spark_compute(
        self,
        environment_id: str,
        payload: Union[
            environment_models.UpdateEnvironmentSparkComputeRequest,
            environment_models.UpdateEnvironmentSparkComputeRequestPreview,
        ],
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
            url=routes.environment_staging_spark_compute(self.workspace_id, environment_id),
            json=payload,
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_update_staging_spark_compute(
        self,
        environment_id: str,
        payload: Union[
            environment_models.UpdateEnvironmentSparkComputeRequest,
            environment_models.UpdateEnvironmentSparkComputeRequestPreview,
        ],
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
            url=routes.environment_staging_spark_compute(self.workspace_id, environment_id),
            json=payload,
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)
