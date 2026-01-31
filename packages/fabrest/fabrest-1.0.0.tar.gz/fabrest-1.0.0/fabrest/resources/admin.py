from typing import Any, Dict, List, Optional

import aiohttp
import requests

from .. import routes
from ..transport import RequestOptions
from .base import ResourceBase


class AdminResource(ResourceBase):
    def list(
        self,
        admin_type: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> List[Dict[str, Any]]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="GET",
            url=routes.admin(admin_type),
            options=opts,
            session=session,
        )
        data = self._handle_response(response, opts)
        return self._extract_list(data)

    async def async_list(
        self,
        admin_type: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> List[Dict[str, Any]]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="GET",
            url=routes.admin(admin_type),
            options=opts,
            session=session,
        )
        data = await self._handle_response_async(response, opts)
        return self._extract_list(data)
