from ..api.constant import ItemType
from .item_type_base import ItemTypeResource


class EventSchemaSetsResource(ItemTypeResource):
    def __init__(self, workspace_id: str, transport=None, async_transport=None, logger=None) -> None:
        super().__init__(
            workspace_id=workspace_id,
            item_type=ItemType.EventSchemaSet,
            transport=transport,
            async_transport=async_transport,
            logger=logger,
        )
