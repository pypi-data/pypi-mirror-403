from typing import Any, Dict, Optional

import aiohttp
import requests

from .. import routes
from ..api.constant import ItemType
from ..models import ml_model as ml_model_models
from ..transport import RequestOptions
from .item_type_base import ItemTypeResource


class MLModelsResource(ItemTypeResource):
    def __init__(self, workspace_id: str, transport=None, async_transport=None, logger=None) -> None:
        super().__init__(
            workspace_id=workspace_id,
            item_type=ItemType.MLModel,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )

    def get_endpoint(
        self,
        model_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="GET",
            url=routes.ml_model_endpoint(self.workspace_id, model_id),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_get_endpoint(
        self,
        model_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="GET",
            url=routes.ml_model_endpoint(self.workspace_id, model_id),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def update_endpoint(
        self,
        model_id: str,
        payload: ml_model_models.UpdateMLModelEndpointRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="PATCH",
            url=routes.ml_model_endpoint(self.workspace_id, model_id),
            json=payload,
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_update_endpoint(
        self,
        model_id: str,
        payload: ml_model_models.UpdateMLModelEndpointRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="PATCH",
            url=routes.ml_model_endpoint(self.workspace_id, model_id),
            json=payload,
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def score(self,
        model_id: str,
        payload: ml_model_models.ScoreDataRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.ml_model_endpoint_score(self.workspace_id, model_id),
            json=payload,
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_score(
        self,
        model_id: str,
        payload: ml_model_models.ScoreDataRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.ml_model_endpoint_score(self.workspace_id, model_id),
            json=payload,
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def list_endpoint_versions(
        self,
        model_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="GET",
            url=routes.ml_model_endpoint_versions(self.workspace_id, model_id),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_list_endpoint_versions(
        self,
        model_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="GET",
            url=routes.ml_model_endpoint_versions(self.workspace_id, model_id),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def get_endpoint_version(
        self,
        model_id: str,
        version_name: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="GET",
            url=routes.ml_model_endpoint_version(self.workspace_id, model_id, version_name),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_get_endpoint_version(
        self,
        model_id: str,
        version_name: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="GET",
            url=routes.ml_model_endpoint_version(self.workspace_id, model_id, version_name),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def update_endpoint_version(
        self,
        model_id: str,
        version_name: str,
        payload: ml_model_models.UpdateMLModelEndpointVersionRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="PATCH",
            url=routes.ml_model_endpoint_version(self.workspace_id, model_id, version_name),
            json=payload,
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_update_endpoint_version(
        self,
        model_id: str,
        version_name: str,
        payload: ml_model_models.UpdateMLModelEndpointVersionRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="PATCH",
            url=routes.ml_model_endpoint_version(self.workspace_id, model_id, version_name),
            json=payload,
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def deactivate_all_versions(
        self,
        model_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.ml_model_endpoint_versions_deactivate_all(
                self.workspace_id, model_id
            ),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_deactivate_all_versions(
        self,
        model_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.ml_model_endpoint_versions_deactivate_all(
                self.workspace_id, model_id
            ),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def activate_version(
        self,
        model_id: str,
        version_name: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.ml_model_endpoint_version_activate(
                self.workspace_id, model_id, version_name
            ),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_activate_version(
        self,
        model_id: str,
        version_name: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.ml_model_endpoint_version_activate(
                self.workspace_id, model_id, version_name
            ),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def deactivate_version(
        self,
        model_id: str,
        version_name: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.ml_model_endpoint_version_deactivate(
                self.workspace_id, model_id, version_name
            ),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_deactivate_version(
        self,
        model_id: str,
        version_name: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.ml_model_endpoint_version_deactivate(
                self.workspace_id, model_id, version_name
            ),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def score_version(
        self,
        model_id: str,
        version_name: str,
        payload: ml_model_models.ScoreDataRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.ml_model_endpoint_version_score(
                self.workspace_id, model_id, version_name
            ),
            json=payload,
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_score_version(
        self,
        model_id: str,
        version_name: str,
        payload: ml_model_models.ScoreDataRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.ml_model_endpoint_version_score(
                self.workspace_id, model_id, version_name
            ),
            json=payload,
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)
