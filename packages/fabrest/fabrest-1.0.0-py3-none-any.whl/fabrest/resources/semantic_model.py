from typing import Any, Dict, Optional

import aiohttp
import requests

from .. import routes
from ..api.constant import ItemType
from ..models import semantic_model as semantic_model_models
from ..transport import RequestOptions
from .item_type_base import ItemTypeResource


class SemanticModelsResource(ItemTypeResource):
    def __init__(self, workspace_id: str, transport=None, async_transport=None, logger=None) -> None:
        super().__init__(
            workspace_id=workspace_id,
            item_type=ItemType.SemanticModel,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )

    def bind_connection(
        self,
        semantic_model_id: str,
        payload: semantic_model_models.BindSemanticModelConnectionRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[requests.Session] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = self._require_transport().request(
            method="POST",
            url=routes.semantic_model_bind_connection(self.workspace_id, semantic_model_id),
            json=payload,
            options=opts,
            session=session,
        )
        return self._handle_response(response, opts)

    async def async_bind_connection(
        self,
        semantic_model_id: str,
        payload: semantic_model_models.BindSemanticModelConnectionRequest,
        options: Optional[RequestOptions] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Dict[str, Any]:
        opts = options or RequestOptions()
        response = await self._require_async_transport().request(
            method="POST",
            url=routes.semantic_model_bind_connection(self.workspace_id, semantic_model_id),
            json=payload,
            options=opts,
            session=session,
        )
        return await self._handle_response_async(response, opts)
