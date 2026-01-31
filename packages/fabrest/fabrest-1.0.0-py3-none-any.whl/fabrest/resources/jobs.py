from typing import Any, Dict, Optional

import aiohttp
import requests

from .. import routes
from ..models import JobRun
from ..transport import RequestOptions
from .base import ResourceBase


class JobsResource(ResourceBase):
    def run(
        self,
        workspace_id: str,
        item_id: str,
        job_type: str,
        item_type: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> JobRun:
        opts = options or RequestOptions()
        response = self._require_transport().invoke(
            url=routes.job_instance(
                workspace_id=workspace_id,
                item_id=item_id,
                job_type=job_type,
                item_type=item_type,
            ),
            json=payload,
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_run(
        self,
        workspace_id: str,
        item_id: str,
        job_type: str,
        item_type: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> JobRun:
        opts = options or RequestOptions()
        response = await self._require_async_transport().invoke(
            url=routes.job_instance(
                workspace_id=workspace_id,
                item_id=item_id,
                job_type=job_type,
                item_type=item_type,
            ),
            json=payload,
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def cancel(
        self,
        workspace_id: str,
        item_id: str,
        job_id: str,
        item_type: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        url = routes.job_instance(
            workspace_id=workspace_id,
            item_id=item_id,
            job_id=job_id,
            item_type=item_type,
        )
        response = self._require_transport().request(
            method="POST",
            url=f"{url}/cancel",
            json=payload,
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_cancel(
        self,
        workspace_id: str,
        item_id: str,
        job_id: str,
        item_type: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        url = routes.job_instance(
            workspace_id=workspace_id,
            item_id=item_id,
            job_id=job_id,
            item_type=item_type,
        )
        response = await self._require_async_transport().request(
            method="POST",
            url=f"{url}/cancel",
            json=payload,
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)
