from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class CreateMapRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    folderId: NotRequired[str]
    definition: NotRequired[MapPublicDefinition]

class UpdateMapRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    description: NotRequired[str]

class UpdateMapDefinitionRequest(TypedDict, total=False):
    definition: MapPublicDefinition

class MapPublicDefinition(TypedDict, total=False):
    format: NotRequired[str]
    parts: List[MapPublicDefinitionPart]

class MapPublicDefinitionPart(TypedDict, total=False):
    path: NotRequired[str]
    payload: NotRequired[str]
    payloadType: NotRequired[PayloadType]

PayloadType = Literal['InlineBase64']
