from dataclasses import replace
from typing import Any, Dict, List, Optional, cast

import aiohttp
import requests

from .. import routes
from ..api.constant import ItemType
from ..models import sql_endpoint as sql_endpoint_models
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


class SQLEndpointsResource(ItemTypeResource):
    def __init__(self, workspace_id: str, transport=None, async_transport=None, logger=None) -> None:
        super().__init__(
            workspace_id=workspace_id,
            item_type=ItemType.SQLEndpoint,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )

    def refresh_metadata(
        self,
        sql_endpoint_id: str,
        payload: Optional[sql_endpoint_models.SqlEndpointRefreshMetadataRequest] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.sql_endpoint_refresh_metadata(self.workspace_id, sql_endpoint_id),
            json=payload,
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_refresh_metadata(
        self,
        sql_endpoint_id: str,
        payload: Optional[sql_endpoint_models.SqlEndpointRefreshMetadataRequest] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.sql_endpoint_refresh_metadata(self.workspace_id, sql_endpoint_id),
            json=payload,
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def get_connection_string(
        self,
        sql_endpoint_id: str,
        guest_tenant_id: Optional[str] = None,
        private_link_type: Optional[str] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if guest_tenant_id:
            params["guestTenantId"] = guest_tenant_id
        if private_link_type:
            params["privateLinkType"] = private_link_type
        opts = _apply_params(options, params)
        response = self._require_transport().request(
            method="GET",
            url=routes.sql_endpoint_connection_string(self.workspace_id, sql_endpoint_id),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_get_connection_string(
        self,
        sql_endpoint_id: str,
        guest_tenant_id: Optional[str] = None,
        private_link_type: Optional[str] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if guest_tenant_id:
            params["guestTenantId"] = guest_tenant_id
        if private_link_type:
            params["privateLinkType"] = private_link_type
        opts = _apply_params(options, params)
        response = await self._require_async_transport().request(
            method="GET",
            url=routes.sql_endpoint_connection_string(self.workspace_id, sql_endpoint_id),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def get_sql_audit_settings(
        self,
        item_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="GET",
            url=routes.sql_endpoint_sql_audit_settings(self.workspace_id, item_id),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_get_sql_audit_settings(
        self,
        item_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="GET",
            url=routes.sql_endpoint_sql_audit_settings(self.workspace_id, item_id),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def update_sql_audit_settings(
        self,
        item_id: str,
        payload: sql_endpoint_models.SqlAuditSettingsUpdate,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="PATCH",
            url=routes.sql_endpoint_sql_audit_settings(self.workspace_id, item_id),
            json=payload,
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_update_sql_audit_settings(
        self,
        item_id: str,
        payload: sql_endpoint_models.SqlAuditSettingsUpdate,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="PATCH",
            url=routes.sql_endpoint_sql_audit_settings(self.workspace_id, item_id),
            json=payload,
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def set_sql_audit_actions_and_groups(
        self,
        item_id: str,
        actions: List[str],
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.sql_endpoint_sql_audit_set_actions(self.workspace_id, item_id),
            json=cast(Any, actions),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_set_sql_audit_actions_and_groups(
        self,
        item_id: str,
        actions: List[str],
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.sql_endpoint_sql_audit_set_actions(self.workspace_id, item_id),
            json=cast(Any, actions),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)
