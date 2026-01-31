from typing import Any, Dict, List, Optional

import aiohttp
import requests

from .. import routes
from ..models import Item
from ..models import platform as platform_models
from ..transport import RequestOptions
from .base import ResourceBase


class ItemsResource(ResourceBase):
    def __init__(
        self,
        workspace_id: Optional[str] = None,
        default_item_type: Optional[str] = None,
        transport=None,
        async_transport=None,
        logger=None,
    ) -> None:
        super().__init__(transport=transport, async_transport=async_transport, logger=logger)
        self.workspace_id = workspace_id
        self.default_item_type = default_item_type

    def _resolve_item_type(self, item_type: Optional[str]) -> Optional[str]:
        return item_type or self.default_item_type

    def list(
        self,
        item_type: Optional[str] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> List[Item]:
        if not self.workspace_id:
            raise ValueError("workspace_id is required for item listing")
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="GET",
            url=routes.items(
                self.workspace_id,
                item_type=self._resolve_item_type(item_type),
            ),
            options=opts,
            session=session,
        )
        data = self._handle_response(response, opts)
        return self._extract_list(data)

    async def async_list(
        self,
        item_type: Optional[str] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> List[Item]:
        if not self.workspace_id:
            raise ValueError("workspace_id is required for item listing")
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="GET",
            url=routes.items(
                self.workspace_id,
                item_type=self._resolve_item_type(item_type),
            ),
            options=opts,
            session=session,
        )
        data = await self._handle_response_async(response, opts)
        return self._extract_list(data)

    def get(
        self,
        item_id: str,
        item_type: Optional[str] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Item:
        if not self.workspace_id:
            raise ValueError("workspace_id is required for item retrieval")
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="GET",
            url=routes.item(
                self.workspace_id,
                item_id,
                item_type=self._resolve_item_type(item_type),
            ),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_get(
        self,
        item_id: str,
        item_type: Optional[str] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Item:
        if not self.workspace_id:
            raise ValueError("workspace_id is required for item retrieval")
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="GET",
            url=routes.item(
                self.workspace_id,
                item_id,
                item_type=self._resolve_item_type(item_type),
            ),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def create(
        self,
        payload: platform_models.CreateItemRequest,
        item_type: Optional[str] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Item:
        if not self.workspace_id:
            raise ValueError("workspace_id is required for item creation")
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.items(
                self.workspace_id,
                item_type=self._resolve_item_type(item_type),
            ),
            json=payload,
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_create(
        self,
        payload: platform_models.CreateItemRequest,
        item_type: Optional[str] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Item:
        if not self.workspace_id:
            raise ValueError("workspace_id is required for item creation")
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.items(
                self.workspace_id,
                item_type=self._resolve_item_type(item_type),
            ),
            json=payload,
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def update(
        self,
        item_id: str,
        payload: platform_models.UpdateItemRequest,
        item_type: Optional[str] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Item:
        if not self.workspace_id:
            raise ValueError("workspace_id is required for item updates")
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="PATCH",
            url=routes.item(
                self.workspace_id,
                item_id,
                item_type=self._resolve_item_type(item_type),
            ),
            json=payload,
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_update(
        self,
        item_id: str,
        payload: platform_models.UpdateItemRequest,
        item_type: Optional[str] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Item:
        if not self.workspace_id:
            raise ValueError("workspace_id is required for item updates")
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="PATCH",
            url=routes.item(
                self.workspace_id,
                item_id,
                item_type=self._resolve_item_type(item_type),
            ),
            json=payload,
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def delete(
        self,
        item_id: str,
        item_type: Optional[str] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        if not self.workspace_id:
            raise ValueError("workspace_id is required for item deletion")
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="DELETE",
            url=routes.item(
                self.workspace_id,
                item_id,
                item_type=self._resolve_item_type(item_type),
            ),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_delete(
        self,
        item_id: str,
        item_type: Optional[str] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        if not self.workspace_id:
            raise ValueError("workspace_id is required for item deletion")
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="DELETE",
            url=routes.item(
                self.workspace_id,
                item_id,
                item_type=self._resolve_item_type(item_type),
            ),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def get_definition(
        self,
        item_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        if not self.workspace_id:
            raise ValueError("workspace_id is required for item definitions")
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.item_definition(self.workspace_id, item_id),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_get_definition(
        self,
        item_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        if not self.workspace_id:
            raise ValueError("workspace_id is required for item definitions")
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.item_definition(self.workspace_id, item_id),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def update_definition(
        self,
        item_id: str,
        payload: platform_models.UpdateItemDefinitionRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        if not self.workspace_id:
            raise ValueError("workspace_id is required for item definitions")
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.item_definition_update(self.workspace_id, item_id),
            json={"definition": payload.get("definition")},
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_update_definition(
        self,
        item_id: str,
        payload: platform_models.UpdateItemDefinitionRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        if not self.workspace_id:
            raise ValueError("workspace_id is required for item definitions")
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.item_definition_update(self.workspace_id, item_id),
            json={"definition": payload.get("definition")},
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)
