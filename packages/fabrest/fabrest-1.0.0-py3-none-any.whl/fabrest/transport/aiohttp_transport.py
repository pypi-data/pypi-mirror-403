from typing import Any, Dict, Optional

import aiohttp

from .options import RequestOptions
from ..api.client import AsyncClient


class AiohttpTransport:
    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    async def request(
        self,
        method: str,
        url: str,
        json: Optional[Dict[str, Any]] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> aiohttp.ClientResponse:
        opts = options or RequestOptions()
        return await self._client.request(
            method=method,
            url=url,
            session=session,
            headers=opts.headers,
            params=opts.params,
            json=json,
            timeout=opts.timeout or 120,
            wait_for_completion=opts.wait_for_completion,
            throttle_retry_interval=opts.throttle_retry_interval,
            lro_check_interval=opts.lro_check_interval,
            item_name_in_use_max_retries=opts.item_name_in_use_max_retries,
            item_name_in_use_retry_interval=opts.item_name_in_use_retry_interval,
            max_retries=opts.max_retries,
            retry_interval=opts.retry_interval,
        )

    async def invoke(
        self,
        url: str,
        json: Optional[Dict[str, Any]] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> aiohttp.ClientResponse:
        opts = options or RequestOptions()
        return await self._client._invoke(
            url=url,
            headers=opts.headers,
            session=session,
            params=opts.params,
            json=json,
            timeout=opts.timeout or 120,
            wait_for_completion=opts.wait_for_completion,
            throttle_retry_interval=opts.throttle_retry_interval,
            invoke=opts.job_check_interval,
            max_retries=opts.max_retries,
            retry_interval=opts.retry_interval,
        )

    async def close_session_if_owned(
        self, session: Optional[aiohttp.ClientSession]
    ) -> bool:
        return await self._client.close_session_if_owned(session)

    async def close(self) -> None:
        await self._client.close()
