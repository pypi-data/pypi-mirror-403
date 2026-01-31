from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class UpdateReflexDefinitionRequest(TypedDict, total=False):
    definition: ReflexDefinition

class UpdateReflexRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    description: NotRequired[str]

class CreateReflexRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    folderId: NotRequired[str]
    definition: NotRequired[ReflexDefinition]

class ReflexDefinition(TypedDict, total=False):
    format: NotRequired[str]
    parts: List[ReflexDefinitionPart]

class ReflexDefinitionPart(TypedDict, total=False):
    path: NotRequired[str]
    payload: NotRequired[str]
    payloadType: NotRequired[PayloadType]

PayloadType = Literal['InlineBase64']
