from typing import Any, Dict, Optional

import logging

from ..transport import AiohttpTransport, RequestOptions, RequestsTransport


class ResourceBase:
    def __init__(
        self,
        transport: Optional[RequestsTransport] = None,
        async_transport: Optional[AiohttpTransport] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self._transport = transport
        self._async_transport = async_transport
        self._logger = logger or logging.getLogger(self.__class__.__name__)

    def _require_transport(self) -> RequestsTransport:
        if not self._transport:
            raise RuntimeError("Sync transport is not configured.")
        return self._transport

    def _require_async_transport(self) -> AiohttpTransport:
        if not self._async_transport:
            raise RuntimeError("Async transport is not configured.")
        return self._async_transport

    def _parse_json(self, response: Any) -> Dict[str, Any]:
        try:
            return response.json()
        except Exception:
            return {}

    async def _parse_json_async(self, response: Any) -> Dict[str, Any]:
        try:
            return await response.json()
        except Exception:
            return {}

    def _extract_list(self, data: Any) -> list:
        if isinstance(data, dict):
            if "value" in data and isinstance(data.get("value"), list):
                return data.get("value", [])
            if "data" in data and isinstance(data.get("data"), list):
                return data.get("data", [])
        if isinstance(data, list):
            return data
        return []

    def _handle_response(self, response: Any, options: RequestOptions) -> Any:
        if options.raw_response:
            return response
        return self._parse_json(response)

    async def _handle_response_async(self, response: Any, options: RequestOptions) -> Any:
        if options.raw_response:
            return response
        return await self._parse_json_async(response)
