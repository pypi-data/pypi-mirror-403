from dataclasses import replace
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

import aiohttp
import requests

from .. import routes
from ..api.constant import ItemType
from ..models import Item
from ..transport import RequestOptions
from .base import ResourceBase


def _apply_params(
    options: Optional[RequestOptions], params: Optional[Dict[str, Any]]
) -> RequestOptions:
    if not params:
        return options or RequestOptions()
    if options:
        merged = {**(options.params or {}), **params}
        return replace(options, params=merged)
    return RequestOptions(params=params)


CreatePayloadT = TypeVar("CreatePayloadT", bound=Dict[str, Any])
UpdatePayloadT = TypeVar("UpdatePayloadT", bound=Dict[str, Any])
DefinitionPayloadT = TypeVar("DefinitionPayloadT", bound=Dict[str, Any])


class ItemTypeResource(ResourceBase, Generic[CreatePayloadT, UpdatePayloadT, DefinitionPayloadT]):
    def __init__(
        self,
        workspace_id: str,
        item_type: Union[str, ItemType],
        transport=None,
        async_transport=None,
        logger=None,
    ) -> None:
        super().__init__(transport=transport, async_transport=async_transport, logger=logger)
        self.workspace_id = workspace_id
        self.item_type = item_type

    def _item_type_value(self) -> str:
        return str(self.item_type)

    def list(
        self,
        recursive: Optional[bool] = None,
        root_folder_id: Optional[str] = None,
        continuation_token: Optional[str] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> List[Item]:
        params: Dict[str, Any] = {}
        if recursive is not None:
            params["recursive"] = recursive
        if root_folder_id:
            params["rootFolderId"] = root_folder_id
        if continuation_token:
            params["continuationToken"] = continuation_token
        opts = _apply_params(options, params)
        response = self._require_transport().request(
            method="GET",
            url=routes.items(self.workspace_id, item_type=self._item_type_value()),
            options=opts,
            session=session,
        )
        data = self._handle_response(response, opts)
        return self._extract_list(data)

    async def async_list(
        self,
        recursive: Optional[bool] = None,
        root_folder_id: Optional[str] = None,
        continuation_token: Optional[str] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> List[Item]:
        params: Dict[str, Any] = {}
        if recursive is not None:
            params["recursive"] = recursive
        if root_folder_id:
            params["rootFolderId"] = root_folder_id
        if continuation_token:
            params["continuationToken"] = continuation_token
        opts = _apply_params(options, params)
        response = await self._require_async_transport().request(
            method="GET",
            url=routes.items(self.workspace_id, item_type=self._item_type_value()),
            options=opts,
            session=session,
        )
        data = await self._handle_response_async(response, opts)
        return self._extract_list(data)

    def create(
        self,
        payload: CreatePayloadT,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Item:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.items(self.workspace_id, item_type=self._item_type_value()),
            json=payload,
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_create(
        self,
        payload: CreatePayloadT,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Item:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.items(self.workspace_id, item_type=self._item_type_value()),
            json=payload,
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def get(
        self,
        item_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Item:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="GET",
            url=routes.item(self.workspace_id, item_id, item_type=self._item_type_value()),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_get(
        self,
        item_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Item:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="GET",
            url=routes.item(self.workspace_id, item_id, item_type=self._item_type_value()),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def update(
        self,
        item_id: str,
        payload: UpdatePayloadT,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Item:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="PATCH",
            url=routes.item(self.workspace_id, item_id, item_type=self._item_type_value()),
            json=payload,
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_update(
        self,
        item_id: str,
        payload: UpdatePayloadT,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Item:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="PATCH",
            url=routes.item(self.workspace_id, item_id, item_type=self._item_type_value()),
            json=payload,
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def delete(
        self,
        item_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="DELETE",
            url=routes.item(self.workspace_id, item_id, item_type=self._item_type_value()),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_delete(
        self,
        item_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="DELETE",
            url=routes.item(self.workspace_id, item_id, item_type=self._item_type_value()),
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
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.item_definition_for_type(
                self.workspace_id, item_id, item_type=self._item_type_value()
            ),
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
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.item_definition_for_type(
                self.workspace_id, item_id, item_type=self._item_type_value()
            ),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def update_definition(
        self,
        item_id: str,
        payload: DefinitionPayloadT,
        update_metadata: Optional[bool] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.item_definition_update_for_type(
                self.workspace_id,
                item_id,
                item_type=self._item_type_value(),
                update_metadata=update_metadata,
            ),
            json=payload,
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_update_definition(
        self,
        item_id: str,
        payload: DefinitionPayloadT,
        update_metadata: Optional[bool] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.item_definition_update_for_type(
                self.workspace_id,
                item_id,
                item_type=self._item_type_value(),
                update_metadata=update_metadata,
            ),
            json=payload,
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)
