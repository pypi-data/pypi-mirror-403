from typing import Any, Dict, List, Optional

import aiohttp
import requests

from .. import routes
from ..models import Capacity
from ..transport import RequestOptions
from .base import ResourceBase


class CapacityResource(ResourceBase):
    def list(
        self,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> List[Capacity]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="GET",
            url=routes.capacities(),
            options=opts,
            session=session,
        )
        data = self._handle_response(response, opts)
        return self._extract_list(data)

    async def async_list(
        self,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> List[Capacity]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="GET",
            url=routes.capacities(),
            options=opts,
            session=session,
        )
        data = await self._handle_response_async(response, opts)
        return self._extract_list(data)

    def get(
        self,
        capacity_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Capacity:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="GET",
            url=routes.capacity(capacity_id),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_get(
        self,
        capacity_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Capacity:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="GET",
            url=routes.capacity(capacity_id),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)
