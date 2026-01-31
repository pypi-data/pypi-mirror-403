from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class UpdateGraphModelRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    description: NotRequired[str]

class UpdateGraphModelDefinitionRequest(TypedDict, total=False):
    definition: GraphModelPublicDefinition

class CreateGraphModelRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    folderId: NotRequired[str]
    definition: NotRequired[GraphModelPublicDefinition]

class ExecuteQueryRequest(TypedDict, total=False):
    query: str

class GraphModelPublicDefinition(TypedDict, total=False):
    format: NotRequired[Literal['json']]
    parts: List[GraphModelPublicDefinitionPart]

class GraphModelPublicDefinitionPart(TypedDict, total=False):
    path: NotRequired[str]
    payload: NotRequired[str]
    payloadType: NotRequired[PayloadType]

PayloadType = Literal['InlineBase64']
