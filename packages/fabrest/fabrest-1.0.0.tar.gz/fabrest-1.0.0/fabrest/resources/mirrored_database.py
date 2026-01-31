from typing import Any, Dict, Optional

import aiohttp
import requests

from .. import routes
from ..api.constant import ItemType
from ..transport import RequestOptions
from .item_type_base import ItemTypeResource


class MirroredDatabasesResource(ItemTypeResource):
    def __init__(self, workspace_id: str, transport=None, async_transport=None, logger=None) -> None:
        super().__init__(
            workspace_id=workspace_id,
            item_type=ItemType.MirroredDatabase,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )

    def get_mirroring_status(
        self,
        database_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.mirrored_database_mirroring_status(self.workspace_id, database_id),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_get_mirroring_status(
        self,
        database_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.mirrored_database_mirroring_status(self.workspace_id, database_id),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def get_tables_mirroring_status(
        self,
        database_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.mirrored_database_tables_mirroring_status(
                self.workspace_id, database_id
            ),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_get_tables_mirroring_status(
        self,
        database_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.mirrored_database_tables_mirroring_status(
                self.workspace_id, database_id
            ),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def start_mirroring(
        self,
        database_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.mirrored_database_start(self.workspace_id, database_id),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_start_mirroring(
        self,
        database_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.mirrored_database_start(self.workspace_id, database_id),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def stop_mirroring(
        self,
        database_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.mirrored_database_stop(self.workspace_id, database_id),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_stop_mirroring(
        self,
        database_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.mirrored_database_stop(self.workspace_id, database_id),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)
