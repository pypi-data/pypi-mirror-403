import logging
from typing import Optional

from .api.client import Client, AsyncClient
from .resources import AdminResource, CapacityResource, ItemsResource, JobsResource, WorkspaceResource, WorkspacesResource
from .transport import AiohttpTransport, RequestsTransport


class FabricClient:
    def __init__(self, credential, scopes: Optional[list] = None) -> None:
        self._client = Client(credential, scopes)
        self._transport = RequestsTransport(self._client)
        self._logger = logging.getLogger(self.__class__.__name__)

        self.workspaces = WorkspacesResource(transport=self._transport)
        self.items = ItemsResource(transport=self._transport)
        self.admin = AdminResource(transport=self._transport)
        self.capacity = CapacityResource(transport=self._transport)
        self.jobs = JobsResource(transport=self._transport)

    def workspace(self, workspace_id: str) -> WorkspaceResource:
        return WorkspaceResource(workspace_id, transport=self._transport)

    def close(self) -> None:
        self._transport.close()


class AsyncFabricClient:
    def __init__(self, credential, scopes: Optional[list] = None) -> None:
        self._client = AsyncClient(credential, scopes)
        self._transport = AiohttpTransport(self._client)
        self._logger = logging.getLogger(self.__class__.__name__)

        self.workspaces = WorkspacesResource(async_transport=self._transport)
        self.items = ItemsResource(async_transport=self._transport)
        self.admin = AdminResource(async_transport=self._transport)
        self.capacity = CapacityResource(async_transport=self._transport)
        self.jobs = JobsResource(async_transport=self._transport)

    def workspace(self, workspace_id: str) -> WorkspaceResource:
        return WorkspaceResource(workspace_id, async_transport=self._transport)

    async def close(self) -> None:
        await self._transport.close()
