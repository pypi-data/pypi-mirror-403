from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class UpdateKQLDatabaseDefinitionRequest(TypedDict, total=False):
    definition: KQLDatabaseDefinition

class UpdateKQLDatabaseRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    description: NotRequired[str]

class CreateKQLDatabaseRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    folderId: NotRequired[str]
    creationPayload: NotRequired[KQLDatabaseCreationPayload]
    definition: NotRequired[KQLDatabaseDefinition]

class KQLDatabaseDefinition(TypedDict, total=False):
    format: NotRequired[str]
    parts: List[KQLDatabaseDefinitionPart]

class KQLDatabaseCreationPayload(TypedDict, total=False):
    databaseType: KQLDatabaseType
    parentEventhouseItemId: str

class KQLDatabaseDefinitionPart(TypedDict, total=False):
    path: NotRequired[str]
    payload: NotRequired[str]
    payloadType: NotRequired[PayloadType]

KQLDatabaseType = Literal['ReadWrite', 'Shortcut']

PayloadType = Literal['InlineBase64']
