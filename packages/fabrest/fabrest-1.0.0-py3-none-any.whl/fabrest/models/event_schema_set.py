from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class UpdateEventSchemaSetDefinitionRequest(TypedDict, total=False):
    definition: EventSchemaSetPublicDefinition

class UpdateEventSchemaSetRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    description: NotRequired[str]

class CreateEventSchemaSetRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    definition: NotRequired[EventSchemaSetPublicDefinition]

class EventSchemaSetPublicDefinition(TypedDict, total=False):
    format: NotRequired[Any]
    parts: List[EventSchemaSetPublicDefinitionPart]

class EventSchemaSetPublicDefinitionPart(TypedDict, total=False):
    path: NotRequired[str]
    payload: NotRequired[str]
    payloadType: NotRequired[PayloadType]

PayloadType = Literal['InlineBase64']
