from dataclasses import replace
from typing import Any, Dict, List, Optional, cast

import aiohttp
import requests

from .. import routes
from ..api.constant import ItemType
from ..models import warehouse as warehouse_models
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


class WarehousesResource(ItemTypeResource):
    def __init__(self, workspace_id: str, transport=None, async_transport=None, logger=None) -> None:
        super().__init__(
            workspace_id=workspace_id,
            item_type=ItemType.Warehouse,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )

    def get_connection_string(
        self,
        warehouse_id: str,
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
            url=routes.warehouse_connection_string(self.workspace_id, warehouse_id),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_get_connection_string(
        self,
        warehouse_id: str,
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
            url=routes.warehouse_connection_string(self.workspace_id, warehouse_id),
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
            url=routes.warehouse_sql_audit_settings(self.workspace_id, item_id),
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
            url=routes.warehouse_sql_audit_settings(self.workspace_id, item_id),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def update_sql_audit_settings(
        self,
        item_id: str,
        payload: warehouse_models.SqlAuditSettingsUpdate,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="PATCH",
            url=routes.warehouse_sql_audit_settings(self.workspace_id, item_id),
            json=payload,
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_update_sql_audit_settings(
        self,
        item_id: str,
        payload: warehouse_models.SqlAuditSettingsUpdate,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="PATCH",
            url=routes.warehouse_sql_audit_settings(self.workspace_id, item_id),
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
            url=routes.warehouse_sql_audit_set_actions(self.workspace_id, item_id),
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
            url=routes.warehouse_sql_audit_set_actions(self.workspace_id, item_id),
            json=cast(Any, actions),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def list_restore_points(
        self,
        warehouse_id: str,
        continuation_token: Optional[str] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {}
        if continuation_token:
            params["continuationToken"] = continuation_token
        opts = _apply_params(options, params)
        response = self._require_transport().request(
            method="GET",
            url=routes.warehouse_restore_points(self.workspace_id, warehouse_id),
            options=opts,
            session=session,
        )
        data = self._handle_response(response, opts)
        return self._extract_list(data)

    async def async_list_restore_points(
        self,
        warehouse_id: str,
        continuation_token: Optional[str] = None,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {}
        if continuation_token:
            params["continuationToken"] = continuation_token
        opts = _apply_params(options, params)
        response = await self._require_async_transport().request(
            method="GET",
            url=routes.warehouse_restore_points(self.workspace_id, warehouse_id),
            options=opts,
            session=session,
        )
        data = await self._handle_response_async(response, opts)
        return self._extract_list(data)

    def create_restore_point(
        self,
        warehouse_id: str,
        payload: warehouse_models.CreateRestorePointRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.warehouse_restore_points(self.workspace_id, warehouse_id),
            json=payload,
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_create_restore_point(
        self,
        warehouse_id: str,
        payload: warehouse_models.CreateRestorePointRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.warehouse_restore_points(self.workspace_id, warehouse_id),
            json=payload,
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def get_restore_point(
        self,
        warehouse_id: str,
        restore_point_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="GET",
            url=routes.warehouse_restore_point(
                self.workspace_id, warehouse_id, restore_point_id
            ),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_get_restore_point(
        self,
        warehouse_id: str,
        restore_point_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="GET",
            url=routes.warehouse_restore_point(
                self.workspace_id, warehouse_id, restore_point_id
            ),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def update_restore_point(
        self,
        warehouse_id: str,
        restore_point_id: str,
        payload: warehouse_models.UpdateRestorePointRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="PATCH",
            url=routes.warehouse_restore_point(
                self.workspace_id, warehouse_id, restore_point_id
            ),
            json=payload,
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_update_restore_point(
        self,
        warehouse_id: str,
        restore_point_id: str,
        payload: warehouse_models.UpdateRestorePointRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="PATCH",
            url=routes.warehouse_restore_point(
                self.workspace_id, warehouse_id, restore_point_id
            ),
            json=payload,
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def delete_restore_point(
        self,
        warehouse_id: str,
        restore_point_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="DELETE",
            url=routes.warehouse_restore_point(
                self.workspace_id, warehouse_id, restore_point_id
            ),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_delete_restore_point(
        self,
        warehouse_id: str,
        restore_point_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="DELETE",
            url=routes.warehouse_restore_point(
                self.workspace_id, warehouse_id, restore_point_id
            ),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def restore_to_restore_point(
        self,
        warehouse_id: str,
        restore_point_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.warehouse_restore_point_restore(
                self.workspace_id, warehouse_id, restore_point_id
            ),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_restore_to_restore_point(
        self,
        warehouse_id: str,
        restore_point_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.warehouse_restore_point_restore(
                self.workspace_id, warehouse_id, restore_point_id
            ),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)
