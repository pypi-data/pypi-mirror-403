from dataclasses import replace
from typing import Any, Dict, List, Optional

import aiohttp
import requests

from .. import routes
from ..models import Item
from ..models import paginated_report as paginated_report_models
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


class PaginatedReportsResource(ResourceBase):
    def __init__(
        self,
        workspace_id: str,
        transport=None,
        async_transport=None,
        logger=None,
    ) -> None:
        super().__init__(transport=transport, async_transport=async_transport, logger=logger)
        self.workspace_id = workspace_id

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
            url=routes.paginated_reports(self.workspace_id),
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
            url=routes.paginated_reports(self.workspace_id),
            options=opts,
            session=session,
        )
        data = await self._handle_response_async(response, opts)
        return self._extract_list(data)

    def update(
        self,
        paginated_report_id: str,
        payload: paginated_report_models.UpdatePaginatedReportRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Item:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="PATCH",
            url=routes.paginated_report(self.workspace_id, paginated_report_id),
            json=payload,
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_update(
        self,
        paginated_report_id: str,
        payload: paginated_report_models.UpdatePaginatedReportRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Item:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="PATCH",
            url=routes.paginated_report(self.workspace_id, paginated_report_id),
            json=payload,
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)
