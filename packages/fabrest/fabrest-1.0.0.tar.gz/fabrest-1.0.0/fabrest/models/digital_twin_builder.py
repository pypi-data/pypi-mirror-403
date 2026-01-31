from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class UpdateDigitalTwinBuilderRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    description: NotRequired[str]

class UpdateDigitalTwinBuilderDefinitionRequest(TypedDict, total=False):
    definition: DigitalTwinBuilderDefinition

class CreateDigitalTwinBuilderRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    definition: NotRequired[DigitalTwinBuilderDefinition]

class DigitalTwinBuilderDefinition(TypedDict, total=False):
    format: NotRequired[str]
    parts: List[DigitalTwinBuilderDefinitionPart]

class DigitalTwinBuilderDefinitionPart(TypedDict, total=False):
    path: NotRequired[str]
    payload: NotRequired[str]
    payloadType: NotRequired[PayloadType]

PayloadType = Literal['InlineBase64']
