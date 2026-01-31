from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class UpdateEventstreamRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    description: NotRequired[str]

class DataSourceStartRequest(TypedDict, total=False):
    startType: DataSourceStartType
    customStartDateTime: NotRequired[str]

class UpdateEventstreamDefinitionRequest(TypedDict, total=False):
    definition: EventstreamDefinition

class CreateEventstreamRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    folderId: NotRequired[str]
    definition: NotRequired[EventstreamDefinition]

DataSourceStartType = Literal['Now', 'WhenLastStopped', 'CustomTime']

class EventstreamDefinition(TypedDict, total=False):
    format: NotRequired[str]
    parts: List[EventstreamDefinitionPart]

class EventstreamDefinitionPart(TypedDict, total=False):
    path: NotRequired[str]
    payload: NotRequired[str]
    payloadType: NotRequired[PayloadType]

PayloadType = Literal['InlineBase64']
