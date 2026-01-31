from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class UpdateEventhouseDefinitionRequest(TypedDict, total=False):
    definition: EventhouseDefinition

class CreateEventhouseRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    folderId: NotRequired[str]
    creationPayload: NotRequired[EventhouseCreationPayload]
    definition: NotRequired[EventhouseDefinition]

class UpdateEventhouseRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    description: NotRequired[str]

class EventhouseDefinition(TypedDict, total=False):
    format: NotRequired[str]
    parts: List[EventhouseDefinitionPart]

class EventhouseCreationPayload(TypedDict, total=False):
    minimumConsumptionUnits: NotRequired[float]

class EventhouseDefinitionPart(TypedDict, total=False):
    path: str
    payload: str
    payloadType: PayloadType

PayloadType = Literal['InlineBase64']
