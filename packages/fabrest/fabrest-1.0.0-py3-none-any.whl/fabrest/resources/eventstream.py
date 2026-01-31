from dataclasses import replace
from typing import Any, Dict, Optional

import aiohttp
import requests

from .. import routes
from ..api.constant import ItemType
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


class EventstreamsResource(ItemTypeResource):
    def __init__(self, workspace_id: str, transport=None, async_transport=None, logger=None) -> None:
        super().__init__(
            workspace_id=workspace_id,
            item_type=ItemType.Eventstream,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )

    def get_topology(
        self,
        eventstream_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="GET",
            url=routes.eventstream_topology(self.workspace_id, eventstream_id),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_get_topology(
        self,
        eventstream_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="GET",
            url=routes.eventstream_topology(self.workspace_id, eventstream_id),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def pause(self, eventstream_id: str, options: Optional[RequestOptions] = None,
              session: Optional[requests.Session] = None) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.eventstream_pause(self.workspace_id, eventstream_id),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_pause(
        self,
        eventstream_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.eventstream_pause(self.workspace_id, eventstream_id),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def resume(
        self,
        eventstream_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.eventstream_resume(self.workspace_id, eventstream_id),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_resume(
        self,
        eventstream_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.eventstream_resume(self.workspace_id, eventstream_id),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def get_source(
        self,
        eventstream_id: str,
        source_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="GET",
            url=routes.eventstream_source(self.workspace_id, eventstream_id, source_id),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_get_source(
        self,
        eventstream_id: str,
        source_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="GET",
            url=routes.eventstream_source(self.workspace_id, eventstream_id, source_id),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def get_source_connection(
        self,
        eventstream_id: str,
        source_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="GET",
            url=routes.eventstream_source_connection(
                self.workspace_id, eventstream_id, source_id
            ),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_get_source_connection(
        self,
        eventstream_id: str,
        source_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="GET",
            url=routes.eventstream_source_connection(
                self.workspace_id, eventstream_id, source_id
            ),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def pause_source(
        self,
        eventstream_id: str,
        source_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.eventstream_source_pause(self.workspace_id, eventstream_id, source_id),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_pause_source(
        self,
        eventstream_id: str,
        source_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.eventstream_source_pause(self.workspace_id, eventstream_id, source_id),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def resume_source(
        self,
        eventstream_id: str,
        source_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.eventstream_source_resume(self.workspace_id, eventstream_id, source_id),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_resume_source(
        self,
        eventstream_id: str,
        source_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.eventstream_source_resume(self.workspace_id, eventstream_id, source_id),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def get_destination(
        self,
        eventstream_id: str,
        destination_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="GET",
            url=routes.eventstream_destination(
                self.workspace_id, eventstream_id, destination_id
            ),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_get_destination(
        self,
        eventstream_id: str,
        destination_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="GET",
            url=routes.eventstream_destination(
                self.workspace_id, eventstream_id, destination_id
            ),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def get_destination_connection(
        self,
        eventstream_id: str,
        destination_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="GET",
            url=routes.eventstream_destination_connection(
                self.workspace_id, eventstream_id, destination_id
            ),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_get_destination_connection(
        self,
        eventstream_id: str,
        destination_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="GET",
            url=routes.eventstream_destination_connection(
                self.workspace_id, eventstream_id, destination_id
            ),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def pause_destination(
        self,
        eventstream_id: str,
        destination_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.eventstream_destination_pause(
                self.workspace_id, eventstream_id, destination_id
            ),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_pause_destination(
        self,
        eventstream_id: str,
        destination_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.eventstream_destination_pause(
                self.workspace_id, eventstream_id, destination_id
            ),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def resume_destination(
        self,
        eventstream_id: str,
        destination_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.eventstream_destination_resume(
                self.workspace_id, eventstream_id, destination_id
            ),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_resume_destination(
        self,
        eventstream_id: str,
        destination_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.eventstream_destination_resume(
                self.workspace_id, eventstream_id, destination_id
            ),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)
