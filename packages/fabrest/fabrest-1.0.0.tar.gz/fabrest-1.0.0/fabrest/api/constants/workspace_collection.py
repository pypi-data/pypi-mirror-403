from .items import ITEM_TYPES
from .utils import coerce_value
from .workspace_config import WORKSPACE_CONFIG


WORKSPACE_COLLECTIONS = {**WORKSPACE_CONFIG, **ITEM_TYPES}


def coerce_workspace_collection(value: str) -> str:
    return coerce_value(WORKSPACE_COLLECTIONS, value, "workspace_collection")
