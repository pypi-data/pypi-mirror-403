from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class CreateSQLDatabaseRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    folderId: NotRequired[str]
    creationPayload: NotRequired[SQLDatabaseCreationPayload]
    definition: NotRequired[SQLDatabaseDefinition]

class UpdateSQLDatabaseDefinitionRequest(TypedDict, total=False):
    definition: SQLDatabaseDefinition

class UpdateSQLDatabaseRequest(TypedDict, total=False):
    description: NotRequired[str]

class SQLDatabaseCreationPayload(TypedDict, total=False):
    creationMode: CreationMode
    backupRetentionDays: NotRequired[int]
    restorePointInTime: NotRequired[str]
    sourceDatabaseReference: NotRequired[ItemReference]

class SQLDatabaseDefinition(TypedDict, total=False):
    parts: List[SQLDatabasePublicDefinitionPart]

CreationMode = Literal['New', 'Restore']

class ItemReference(TypedDict, total=False):
    referenceType: ItemReferenceType

class SQLDatabasePublicDefinitionPart(TypedDict, total=False):
    path: NotRequired[str]
    payload: NotRequired[str]
    payloadType: NotRequired[PayloadType]

ItemReferenceType = Literal['ById']

PayloadType = Literal['InlineBase64']
