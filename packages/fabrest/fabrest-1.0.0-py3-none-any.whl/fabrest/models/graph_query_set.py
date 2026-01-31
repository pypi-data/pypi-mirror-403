from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class UpdateGraphQuerySetRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    description: NotRequired[str]

class CreateGraphQuerySetRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    definition: NotRequired[GraphQuerySetPublicDefinition]

class UpdateGraphQuerySetDefinitionRequest(TypedDict, total=False):
    definition: GraphQuerySetPublicDefinition

class GraphQuerySetPublicDefinition(TypedDict, total=False):
    format: NotRequired[str]
    parts: List[GraphQuerySetPublicDefinitionPart]

class GraphQuerySetPublicDefinitionPart(TypedDict, total=False):
    path: NotRequired[str]
    payload: NotRequired[str]
    payloadType: NotRequired[PayloadType]

PayloadType = Literal['InlineBase64']
