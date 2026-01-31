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


class MirroredAzureDatabricksCatalogsResource(ItemTypeResource):
    def __init__(self, workspace_id: str, transport=None, async_transport=None, logger=None) -> None:
        super().__init__(
            workspace_id=workspace_id,
            item_type=ItemType.MirroredAzureDatabricksCatalog,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )

    def list_catalogs(
        self,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="GET",
            url=routes.mirrored_azure_databricks_catalogs(self.workspace_id),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_list_catalogs(
        self,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="GET",
            url=routes.mirrored_azure_databricks_catalogs(self.workspace_id),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def list_schemas(
        self,
        catalog_name: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="GET",
            url=routes.mirrored_azure_databricks_schemas(self.workspace_id, catalog_name),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_list_schemas(
        self,
        catalog_name: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="GET",
            url=routes.mirrored_azure_databricks_schemas(self.workspace_id, catalog_name),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def list_tables(
        self,
        catalog_name: str,
        schema_name: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="GET",
            url=routes.mirrored_azure_databricks_tables(
                self.workspace_id, catalog_name, schema_name
            ),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_list_tables(
        self,
        catalog_name: str,
        schema_name: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="GET",
            url=routes.mirrored_azure_databricks_tables(
                self.workspace_id, catalog_name, schema_name
            ),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)

    def refresh_catalog_metadata(
        self,
        catalog_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.mirrored_azure_databricks_refresh_metadata(
                self.workspace_id, catalog_id
            ),
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_refresh_catalog_metadata(
        self,
        catalog_id: str,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.mirrored_azure_databricks_refresh_metadata(
                self.workspace_id, catalog_id
            ),
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)
