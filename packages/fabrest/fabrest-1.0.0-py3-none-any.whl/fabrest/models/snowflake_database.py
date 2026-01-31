from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class CreateSnowflakeDatabaseRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    type: NotRequired[Literal['SnowflakeDatabase']]
    creationPayload: NotRequired[SnowflakeDatabaseCreationPayload]
    definition: NotRequired[SnowflakeDatabaseDefinition]

class UpdateSnowflakeDatabaseRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    description: NotRequired[str]

class UpdateSnowflakeDatabaseDefinitionRequest(TypedDict, total=False):
    definition: SnowflakeDatabaseDefinition

class SnowflakeDatabaseCreationPayload(TypedDict, total=False):
    snowflakeDatabaseName: NotRequired[str]
    connectionId: NotRequired[str]

class SnowflakeDatabaseDefinition(TypedDict, total=False):
    format: NotRequired[str]
    parts: List[SnowflakeDatabaseDefinitionPart]

class SnowflakeDatabaseDefinitionPart(TypedDict, total=False):
    path: NotRequired[str]
    payload: NotRequired[str]
    payloadType: NotRequired[PayloadType]

PayloadType = Literal['InlineBase64']
